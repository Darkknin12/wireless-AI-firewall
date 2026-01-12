"""
Live Auto-Blocking Demo
Simuleert real-world malicious traffic en toont automatic blocking
"""

from firewall_blocker import FirewallBlocker
from inference import AIFirewallInference
from utils import Logger
import random
import time

def generate_malicious_flow(attacker_ip):
    """Generate realistic DDoS/PortScan flow"""
    return {
        # Attack characteristics
        'flow_duration': random.uniform(0.1, 1.0),
        'total_fwd_packets': random.randint(500, 2000),
        'total_backward_packets': 0,
        'total_length_of_fwd_packets': random.randint(30000, 120000),
        'total_length_of_bwd_packets': 0,
        
        # Packet lengths (small, uniform - typical DDoS)
        'fwd_packet_length_max': 60,
        'fwd_packet_length_min': 60,
        'fwd_packet_length_mean': 60,
        'fwd_packet_length_std': 0,
        'bwd_packet_length_max': 0,
        'bwd_packet_length_min': 0,
        'bwd_packet_length_mean': 0,
        'bwd_packet_length_std': 0,
        
        # High flow rates
        'flow_bytes_s': random.randint(80000, 200000),
        'flow_packets_s': random.randint(1500, 3000),
        
        # Inter-arrival times (very short)
        'flow_iat_mean': random.uniform(0.0003, 0.001),
        'flow_iat_std': 0.0001,
        'flow_iat_max': 0.002,
        'flow_iat_min': 0.0001,
        
        'fwd_iat_total': random.uniform(0.1, 1.0),
        'fwd_iat_mean': random.uniform(0.0003, 0.001),
        'fwd_iat_std': 0.0001,
        'fwd_iat_max': 0.002,
        'fwd_iat_min': 0.0001,
        
        'bwd_iat_total': 0,
        'bwd_iat_mean': 0,
        'bwd_iat_std': 0,
        'bwd_iat_max': 0,
        'bwd_iat_min': 0,
        
        # TCP flags (SYN flood)
        'fwd_psh_flags': 0,
        'bwd_psh_flags': 0,
        'fwd_urg_flags': 0,
        'bwd_urg_flags': 0,
        'fwd_header_length': 20,
        'bwd_header_length': 0,
        'fwd_packets_s': random.randint(1500, 3000),
        'bwd_packets_s': 0,
        
        # Packet stats
        'min_packet_length': 60,
        'max_packet_length': 60,
        'packet_length_mean': 60,
        'packet_length_std': 0,
        'packet_length_variance': 0,
        
        # Flags
        'fin_flag_count': 0,
        'syn_flag_count': random.randint(500, 2000),  # SYN flood!
        'rst_flag_count': 0,
        'psh_flag_count': 0,
        'ack_flag_count': 0,
        'urg_flag_count': 0,
        'cwe_flag_count': 0,
        'ece_flag_count': 0,
        
        # Additional
        'down_up_ratio': 0,
        'average_packet_size': 60,
        'avg_fwd_segment_size': 60,
        'avg_bwd_segment_size': 0,
        
        'fwd_avg_bytes_bulk': 0,
        'fwd_avg_packets_bulk': 0,
        'fwd_avg_bulk_rate': 0,
        'bwd_avg_bytes_bulk': 0,
        'bwd_avg_packets_bulk': 0,
        'bwd_avg_bulk_rate': 0,
        
        'subflow_fwd_packets': random.randint(500, 2000),
        'subflow_fwd_bytes': random.randint(30000, 120000),
        'subflow_bwd_packets': 0,
        'subflow_bwd_bytes': 0,
        
        'init_win_bytes_forward': 5840,
        'init_win_bytes_backward': 0,
        
        'active_mean': random.uniform(0.1, 1.0),
        'active_std': 0,
        'active_max': random.uniform(0.1, 1.0),
        'active_min': random.uniform(0.1, 1.0),
        
        'idle_mean': 0,
        'idle_std': 0,
        'idle_max': 0,
        'idle_min': 0,
        
        # Protocol and IPs
        'protocol': 6,  # TCP
        'source_port': random.randint(49152, 65535),
        'destination_port': random.choice([22, 80, 443, 3389, 8080])
    }

def generate_benign_flow():
    """Generate realistic normal HTTPS traffic"""
    return {
        'flow_duration': random.uniform(2.0, 10.0),
        'total_fwd_packets': random.randint(10, 50),
        'total_backward_packets': random.randint(8, 45),
        'total_length_of_fwd_packets': random.randint(800, 5000),
        'total_length_of_bwd_packets': random.randint(6000, 50000),
        
        'fwd_packet_length_max': random.randint(100, 1500),
        'fwd_packet_length_min': 60,
        'fwd_packet_length_mean': random.randint(80, 500),
        'fwd_packet_length_std': random.randint(20, 200),
        
        'bwd_packet_length_max': 1460,
        'bwd_packet_length_min': 60,
        'bwd_packet_length_mean': random.randint(400, 1200),
        'bwd_packet_length_std': random.randint(100, 400),
        
        'flow_bytes_s': random.randint(1000, 10000),
        'flow_packets_s': random.uniform(5, 20),
        
        'flow_iat_mean': random.uniform(0.1, 0.5),
        'flow_iat_std': random.uniform(0.05, 0.2),
        'flow_iat_max': random.uniform(0.5, 2.0),
        'flow_iat_min': random.uniform(0.01, 0.1),
        
        'fwd_iat_total': random.uniform(2.0, 10.0),
        'fwd_iat_mean': random.uniform(0.2, 0.6),
        'fwd_iat_std': random.uniform(0.1, 0.3),
        'fwd_iat_max': random.uniform(0.5, 2.0),
        'fwd_iat_min': random.uniform(0.05, 0.2),
        
        'bwd_iat_total': random.uniform(2.0, 10.0),
        'bwd_iat_mean': random.uniform(0.2, 0.6),
        'bwd_iat_std': random.uniform(0.1, 0.3),
        'bwd_iat_max': random.uniform(0.4, 1.5),
        'bwd_iat_min': random.uniform(0.05, 0.25),
        
        'fwd_psh_flags': 1,
        'bwd_psh_flags': 1,
        'fwd_urg_flags': 0,
        'bwd_urg_flags': 0,
        'fwd_header_length': 20,
        'bwd_header_length': 20,
        'fwd_packets_s': random.uniform(3, 15),
        'bwd_packets_s': random.uniform(2, 12),
        
        'min_packet_length': 60,
        'max_packet_length': 1460,
        'packet_length_mean': random.randint(300, 800),
        'packet_length_std': random.randint(200, 500),
        'packet_length_variance': random.randint(40000, 250000),
        
        'fin_flag_count': 2,
        'syn_flag_count': 1,
        'rst_flag_count': 0,
        'psh_flag_count': random.randint(2, 10),
        'ack_flag_count': random.randint(15, 50),
        'urg_flag_count': 0,
        'cwe_flag_count': 0,
        'ece_flag_count': 0,
        
        'down_up_ratio': random.uniform(5, 15),
        'average_packet_size': random.randint(300, 800),
        'avg_fwd_segment_size': random.randint(80, 500),
        'avg_bwd_segment_size': random.randint(400, 1200),
        
        'fwd_avg_bytes_bulk': 0,
        'fwd_avg_packets_bulk': 0,
        'fwd_avg_bulk_rate': 0,
        'bwd_avg_bytes_bulk': 0,
        'bwd_avg_packets_bulk': 0,
        'bwd_avg_bulk_rate': 0,
        
        'subflow_fwd_packets': random.randint(10, 50),
        'subflow_fwd_bytes': random.randint(800, 5000),
        'subflow_bwd_packets': random.randint(8, 45),
        'subflow_bwd_bytes': random.randint(6000, 50000),
        
        'init_win_bytes_forward': 65535,
        'init_win_bytes_backward': 65535,
        
        'active_mean': random.uniform(1.5, 5.0),
        'active_std': random.uniform(0.2, 1.0),
        'active_max': random.uniform(3.0, 8.0),
        'active_min': random.uniform(0.5, 2.0),
        
        'idle_mean': random.uniform(0.05, 0.3),
        'idle_std': random.uniform(0.02, 0.15),
        'idle_max': random.uniform(0.1, 0.5),
        'idle_min': random.uniform(0.01, 0.1),
        
        'protocol': 6,
        'source_port': random.randint(49152, 65535),
        'destination_port': 443  # HTTPS
    }

def live_demo():
    """Run live automatic blocking demo"""
    print("\n" + "="*70)
    print("AI-FIREWALL LIVE AUTOMATIC BLOCKING DEMO")
    print("="*70)
    
    # Initialize
    print("\n[1] Initializing AI-Firewall...")
    blocker = FirewallBlocker()
    blocker.auto_block_enabled = True  # Force enable
    
    inference_engine = AIFirewallInference()
    inference_engine.load_models()
    
    print(f"    Auto-block: {blocker.auto_block_enabled}")
    print(f"    Threshold: {blocker.block_threshold}")
    
    # Attacker IPs (simulated)
    attackers = [
        "45.142.212.61",   # Known malicious IP
        "185.220.101.33",  # Tor exit node
        "103.253.145.12",  # Botnet C&C
        "198.98.57.207",   # Scanner
        "193.239.146.14"   # DDoS source
    ]
    
    # Trusted IPs
    trusted = [
        "192.168.1.50",    # Local PC
        "8.8.8.8",         # Google DNS
        "192.168.1.100"    # Server
    ]
    
    print("\n[2] Simulating Network Traffic...")
    print("    Monitoring flows...")
    print()
    
    blocked_count = 0
    benign_count = 0
    total_flows = 0
    
    # Simulate 10 flows
    for i in range(10):
        total_flows += 1
        
        # 50% chance of malicious
        is_attack = random.random() < 0.5
        
        if is_attack:
            # Malicious flow
            attacker_ip = random.choice(attackers)
            target_ip = random.choice(trusted)
            flow_data = generate_malicious_flow(attacker_ip)
            flow_data['src_ip'] = attacker_ip
            flow_data['dst_ip'] = target_ip
            
            print(f"Flow #{total_flows}: {attacker_ip} -> {target_ip}:{flow_data['destination_port']}")
            
            # Predict
            result = inference_engine.predict_single_flow(flow_data)
            
            print(f"  Type: ATTACK (SYN Flood)")
            print(f"  Prediction: {result['prediction']}")
            print(f"  Score: {result['ensemble_score']:.3f}")
            
            if result['prediction'].upper() == 'MALICIOUS' and result['ensemble_score'] >= blocker.block_threshold:
                print(f"  [!] THREAT DETECTED!")
                
                if blocker.auto_block_enabled:
                    blocked = blocker.process_prediction(flow_data, result)
                    if blocked:
                        print(f"  [BLOCKED] IP {attacker_ip} automatically blocked!")
                        blocked_count += 1
                    else:
                        print(f"  [WARN] Failed to block (may already be blocked or whitelisted)")
            else:
                print(f"  [OK] Below threshold")
        else:
            # Benign flow
            client_ip = random.choice(trusted)
            server_ip = "172.217.14.206"  # Google
            flow_data = generate_benign_flow()
            flow_data['src_ip'] = client_ip
            flow_data['dst_ip'] = server_ip
            
            print(f"Flow #{total_flows}: {client_ip} -> {server_ip}:443")
            
            # Predict
            result = inference_engine.predict_single_flow(flow_data)
            
            print(f"  Type: Normal HTTPS")
            print(f"  Prediction: {result['prediction']}")
            print(f"  Score: {result['ensemble_score']:.3f}")
            print(f"  [OK] Allowed")
            benign_count += 1
        
        print()
        time.sleep(0.5)  # Simulate time between flows
    
    # Summary
    print("\n" + "="*70)
    print("DEMO SUMMARY")
    print("="*70)
    
    stats = blocker.get_stats()
    
    print(f"\n[RESULTS]:")
    print(f"  Total flows: {total_flows}")
    print(f"  Malicious detected: {total_flows - benign_count}")
    print(f"  Benign allowed: {benign_count}")
    print(f"  IPs blocked: {blocked_count}")
    
    print(f"\n[FIREWALL STATUS]:")
    print(f"  Auto-block: {stats['auto_block_enabled']}")
    print(f"  Threshold: {stats['block_threshold']}")
    print(f"  Total blocked IPs: {stats['total_blocked']}")
    
    if blocker.blocked_ips:
        print(f"\n[BLOCKED IPs]:")
        for ip in blocker.get_blocked_ips():
            print(f"   - {ip}")
    
    print("\n" + "="*70)
    print("[OK] Demo Complete - Automatic Blocking is ACTIVE!")
    print("="*70)
    print()

if __name__ == "__main__":
    live_demo()
