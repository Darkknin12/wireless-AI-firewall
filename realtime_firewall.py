"""
Real-time AI Firewall met Automatic Blocking
Monitort network traffic en blockt malicious flows automatisch
"""

import time
import json
from datetime import datetime
from pathlib import Path
from scapy.all import sniff, IP, TCP, UDP
from typing import Dict, Optional
from inference import load_models, predict_flow
from firewall_blocker import FirewallBlocker
from utils import Logger, Config

class RealtimeAIFirewall:
    """
    Real-time AI Firewall
    - Capture packets met Scapy
    - Analyze met XGBoost + Isolation Forest
    - Block malicious IPs automatisch
    """
    
    def __init__(self, interface: Optional[str] = None):
        self.logger = Logger(__name__).logger
        self.config = Config()
        
        # Load AI models
        self.logger.info("Loading AI models...")
        self.models = load_models()
        self.logger.info("Models loaded successfully")
        
        # Initialize firewall blocker
        self.blocker = FirewallBlocker()
        
        # Network interface
        self.interface = interface
        
        # Flow tracking
        self.flows = {}
        self.flow_timeout = 60  # seconds
        
        # Statistics
        self.stats = {
            'total_packets': 0,
            'total_flows': 0,
            'benign_flows': 0,
            'malicious_flows': 0,
            'blocked_ips': 0
        }
        
        self.logger.info("RealtimeAIFirewall initialized")
        self.logger.info(f"Interface: {interface or 'default'}")
    
    def packet_to_flow_key(self, packet) -> Optional[str]:
        """
        Convert packet to flow key
        Flow = (src_ip, dst_ip, src_port, dst_port, protocol)
        """
        try:
            if IP not in packet:
                return None
            
            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            protocol = ip_layer.proto
            
            # Get ports
            src_port = 0
            dst_port = 0
            
            if TCP in packet:
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
                proto_name = 'TCP'
            elif UDP in packet:
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
                proto_name = 'UDP'
            else:
                proto_name = str(protocol)
            
            # Create flow key
            flow_key = f"{src_ip}:{src_port}->{dst_ip}:{dst_port}:{proto_name}"
            return flow_key
            
        except Exception as e:
            self.logger.error(f"Error creating flow key: {e}")
            return None
    
    def packet_to_features(self, packet, flow_data: Dict) -> Dict:
        """
        Extract features from packet voor AI model
        """
        try:
            features = {}
            
            if IP not in packet:
                return features
            
            ip_layer = packet[IP]
            
            # Basic features
            features['src_ip'] = ip_layer.src
            features['dst_ip'] = ip_layer.dst
            features['protocol'] = ip_layer.proto
            features['total_length_of_fwd_packets'] = len(packet)
            features['total_length_of_bwd_packets'] = 0
            
            # Flow statistics (simplified)
            features['flow_duration'] = flow_data.get('duration', 0)
            features['total_fwd_packets'] = flow_data.get('fwd_packets', 1)
            features['total_backward_packets'] = flow_data.get('bwd_packets', 0)
            features['flow_bytes_s'] = flow_data.get('bytes_per_sec', 0)
            features['flow_packets_s'] = flow_data.get('packets_per_sec', 0)
            
            # TCP flags
            if TCP in packet:
                tcp_layer = packet[TCP]
                features['fwd_psh_flags'] = 1 if tcp_layer.flags & 0x08 else 0
                features['bwd_psh_flags'] = 0
                features['fwd_urg_flags'] = 1 if tcp_layer.flags & 0x20 else 0
                features['bwd_urg_flags'] = 0
                features['fin_flag_count'] = 1 if tcp_layer.flags & 0x01 else 0
                features['syn_flag_count'] = 1 if tcp_layer.flags & 0x02 else 0
                features['rst_flag_count'] = 1 if tcp_layer.flags & 0x04 else 0
                features['psh_flag_count'] = 1 if tcp_layer.flags & 0x08 else 0
                features['ack_flag_count'] = 1 if tcp_layer.flags & 0x10 else 0
                features['urg_flag_count'] = 1 if tcp_layer.flags & 0x20 else 0
                features['ece_flag_count'] = 1 if tcp_layer.flags & 0x40 else 0
                
                # Ports
                features['source_port'] = tcp_layer.sport
                features['destination_port'] = tcp_layer.dport
            elif UDP in packet:
                features['source_port'] = packet[UDP].sport
                features['destination_port'] = packet[UDP].dport
                
                # No flags for UDP
                features['fwd_psh_flags'] = 0
                features['bwd_psh_flags'] = 0
                features['fwd_urg_flags'] = 0
                features['bwd_urg_flags'] = 0
                features['fin_flag_count'] = 0
                features['syn_flag_count'] = 0
                features['rst_flag_count'] = 0
                features['psh_flag_count'] = 0
                features['ack_flag_count'] = 0
                features['urg_flag_count'] = 0
                features['ece_flag_count'] = 0
            
            # Packet lengths
            features['fwd_packet_length_max'] = len(packet)
            features['fwd_packet_length_min'] = len(packet)
            features['fwd_packet_length_mean'] = len(packet)
            features['fwd_packet_length_std'] = 0
            
            features['bwd_packet_length_max'] = 0
            features['bwd_packet_length_min'] = 0
            features['bwd_packet_length_mean'] = 0
            features['bwd_packet_length_std'] = 0
            
            # Timing (simplified)
            features['flow_iat_mean'] = 0
            features['flow_iat_std'] = 0
            features['flow_iat_max'] = 0
            features['flow_iat_min'] = 0
            
            features['fwd_iat_total'] = 0
            features['fwd_iat_mean'] = 0
            features['fwd_iat_std'] = 0
            features['fwd_iat_max'] = 0
            features['fwd_iat_min'] = 0
            
            features['bwd_iat_total'] = 0
            features['bwd_iat_mean'] = 0
            features['bwd_iat_std'] = 0
            features['bwd_iat_max'] = 0
            features['bwd_iat_min'] = 0
            
            # Header lengths
            features['fwd_header_length'] = ip_layer.ihl * 4
            features['bwd_header_length'] = 0
            
            # Window size
            if TCP in packet:
                features['init_win_bytes_forward'] = packet[TCP].window
                features['init_win_bytes_backward'] = 0
            else:
                features['init_win_bytes_forward'] = 0
                features['init_win_bytes_backward'] = 0
            
            # Active/Idle times (simplified)
            features['active_mean'] = 0
            features['active_std'] = 0
            features['active_max'] = 0
            features['active_min'] = 0
            
            features['idle_mean'] = 0
            features['idle_std'] = 0
            features['idle_max'] = 0
            features['idle_min'] = 0
            
            # Subflow (simplified)
            features['subflow_fwd_packets'] = 1
            features['subflow_fwd_bytes'] = len(packet)
            features['subflow_bwd_packets'] = 0
            features['subflow_bwd_bytes'] = 0
            
            # Additional features
            features['fwd_avg_bytes_bulk'] = 0
            features['fwd_avg_packets_bulk'] = 0
            features['fwd_avg_bulk_rate'] = 0
            
            features['bwd_avg_bytes_bulk'] = 0
            features['bwd_avg_packets_bulk'] = 0
            features['bwd_avg_bulk_rate'] = 0
            
            features['min_packet_length'] = len(packet)
            features['max_packet_length'] = len(packet)
            features['packet_length_mean'] = len(packet)
            features['packet_length_std'] = 0
            features['packet_length_variance'] = 0
            
            features['down_up_ratio'] = 0
            features['average_packet_size'] = len(packet)
            features['avg_fwd_segment_size'] = len(packet)
            features['avg_bwd_segment_size'] = 0
            
            # CWE flag count (simplified)
            if TCP in packet:
                features['cwe_flag_count'] = 1 if packet[TCP].flags & 0x80 else 0
            else:
                features['cwe_flag_count'] = 0
            
            features['fwd_packets_s'] = flow_data.get('fwd_packets_per_sec', 0)
            features['bwd_packets_s'] = flow_data.get('bwd_packets_per_sec', 0)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            return {}
    
    def update_flow(self, flow_key: str, packet):
        """Update flow statistics"""
        if flow_key not in self.flows:
            self.flows[flow_key] = {
                'start_time': time.time(),
                'last_packet': time.time(),
                'fwd_packets': 0,
                'bwd_packets': 0,
                'fwd_bytes': 0,
                'bwd_bytes': 0,
                'packets': []
            }
        
        flow = self.flows[flow_key]
        current_time = time.time()
        
        # Update timing
        flow['last_packet'] = current_time
        flow['duration'] = current_time - flow['start_time']
        
        # Update packet count
        flow['fwd_packets'] += 1
        flow['fwd_bytes'] += len(packet)
        
        # Calculate rates
        if flow['duration'] > 0:
            flow['bytes_per_sec'] = flow['fwd_bytes'] / flow['duration']
            flow['packets_per_sec'] = flow['fwd_packets'] / flow['duration']
            flow['fwd_packets_per_sec'] = flow['fwd_packets'] / flow['duration']
            flow['bwd_packets_per_sec'] = flow['bwd_packets'] / flow['duration']
        else:
            flow['bytes_per_sec'] = 0
            flow['packets_per_sec'] = 0
            flow['fwd_packets_per_sec'] = 0
            flow['bwd_packets_per_sec'] = 0
        
        return flow
    
    def analyze_packet(self, packet):
        """
        Analyze packet met AI en block indien malicious
        """
        try:
            self.stats['total_packets'] += 1
            
            # Get flow key
            flow_key = self.packet_to_flow_key(packet)
            if not flow_key:
                return
            
            # Update flow
            flow_data = self.update_flow(flow_key, packet)
            
            # Only analyze after minimum packets
            if flow_data['fwd_packets'] >= 5:
                # Extract features
                features = self.packet_to_features(packet, flow_data)
                
                if features:
                    # AI prediction
                    prediction = predict_flow(features, self.models)
                    
                    # Update stats
                    self.stats['total_flows'] += 1
                    
                    if prediction['prediction'] == 'MALICIOUS':
                        self.stats['malicious_flows'] += 1
                        
                        # LOG THREAT
                        self.logger.warning(f"🚨 MALICIOUS FLOW: {flow_key}")
                        self.logger.warning(f"   Score: {prediction['ensemble_score']:.3f}")
                        
                        # AUTOMATIC BLOCKING
                        blocked = self.blocker.process_prediction(features, prediction)
                        
                        if blocked:
                            self.stats['blocked_ips'] += 1
                            self.logger.warning(f"   ✅ IP BLOCKED: {features['src_ip']}")
                    else:
                        self.stats['benign_flows'] += 1
                    
                    # Clean up flow (analyzed)
                    del self.flows[flow_key]
            
        except Exception as e:
            self.logger.error(f"Error analyzing packet: {e}")
    
    def cleanup_flows(self):
        """Remove expired flows"""
        current_time = time.time()
        expired = []
        
        for flow_key, flow in self.flows.items():
            if current_time - flow['last_packet'] > self.flow_timeout:
                expired.append(flow_key)
        
        for flow_key in expired:
            del self.flows[flow_key]
    
    def print_stats(self):
        """Print statistics"""
        print("\n" + "="*60)
        print("AI FIREWALL STATISTICS")
        print("="*60)
        print(f"Total Packets:     {self.stats['total_packets']:,}")
        print(f"Total Flows:       {self.stats['total_flows']:,}")
        print(f"Benign Flows:      {self.stats['benign_flows']:,}")
        print(f"Malicious Flows:   {self.stats['malicious_flows']:,}")
        print(f"Blocked IPs:       {self.stats['blocked_ips']:,}")
        print(f"Active Flows:      {len(self.flows):,}")
        print("="*60)
        
        # Blocker stats
        blocker_stats = self.blocker.get_stats()
        print(f"\nFirewall Blocker:")
        print(f"  Auto-block:      {blocker_stats['auto_block_enabled']}")
        print(f"  Blocked IPs:     {blocker_stats['total_blocked']}")
        print(f"  Threshold:       {blocker_stats['block_threshold']}")
        print("="*60 + "\n")
    
    def start(self, packet_count: int = 0):
        """
        Start real-time monitoring
        
        Args:
            packet_count: Number of packets to capture (0 = infinite)
        """
        self.logger.info("="*60)
        self.logger.info("🚀 STARTING REAL-TIME AI FIREWALL")
        self.logger.info("="*60)
        self.logger.info(f"Interface: {self.interface or 'default'}")
        self.logger.info(f"Auto-block: {self.blocker.auto_block_enabled}")
        self.logger.info("Press Ctrl+C to stop")
        self.logger.info("="*60)
        
        try:
            # Start packet capture
            sniff(
                iface=self.interface,
                prn=self.analyze_packet,
                count=packet_count,
                store=False  # Don't store packets in memory
            )
            
        except KeyboardInterrupt:
            self.logger.info("\n\nStopping AI Firewall...")
            self.print_stats()
            
        except Exception as e:
            self.logger.error(f"Error in packet capture: {e}")
            self.logger.error("Make sure you run this with administrator/root privileges!")

def main():
    """
    Main entry point
    
    Usage:
        # Linux (requires sudo)
        sudo python realtime_firewall.py
        
        # Windows (requires admin PowerShell)
        python realtime_firewall.py
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-time AI Firewall')
    parser.add_argument('-i', '--interface', help='Network interface (e.g., eth0, wlan0)')
    parser.add_argument('-c', '--count', type=int, default=0, help='Number of packets to capture (0=infinite)')
    args = parser.parse_args()
    
    # Create firewall
    firewall = RealtimeAIFirewall(interface=args.interface)
    
    # Start monitoring
    firewall.start(packet_count=args.count)

if __name__ == "__main__":
    main()
