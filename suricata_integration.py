"""
Suricata EVE JSON Parser & AI-Firewall Integratie
Leest Suricata EVE logs en stuurt flows naar AI model
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from inference import AIFirewallInference
from utils import Logger, PredictionLogger

class SuricataEveParser:
    """Parser voor Suricata EVE JSON logs"""
    
    def __init__(self):
        self.logger = Logger(__name__)
        
    def parse_eve_flow(self, eve_record: Dict) -> Optional[Dict]:
        """
        Converteer Suricata EVE flow record naar CICIDS2017 format
        
        Args:
            eve_record: Suricata EVE JSON record
            
        Returns:
            Flow dictionary in CICIDS2017 format
        """
        try:
            event_type = eve_record.get('event_type')
            
            if event_type != 'flow':
                return None
            
            flow = eve_record.get('flow', {})
            
            # Basis flow info
            flow_dict = {
                'Destination Port': eve_record.get('dest_port', 0),
                'Flow Duration': flow.get('age', 0) * 1000000,  # naar microseconds
                'Protocol': 6 if eve_record.get('proto', 'TCP') == 'TCP' else 17,
                
                # Packet counts
                'Total Fwd Packets': flow.get('pkts_toserver', 0),
                'Total Backward Packets': flow.get('pkts_toclient', 0),
                
                # Bytes
                'Total Length of Fwd Packets': flow.get('bytes_toserver', 0),
                'Total Length of Bwd Packets': flow.get('bytes_toclient', 0),
                
                # Flow rates (berekend)
                'Flow Bytes/s': 0,  # Berekenen hieronder
                'Flow Packets/s': 0,
                'Fwd Packets/s': 0,
                'Bwd Packets/s': 0,
            }
            
            # Bereken rates
            duration_sec = flow.get('age', 1)
            if duration_sec > 0:
                total_bytes = flow.get('bytes_toserver', 0) + flow.get('bytes_toclient', 0)
                total_packets = flow.get('pkts_toserver', 0) + flow.get('pkts_toclient', 0)
                
                flow_dict['Flow Bytes/s'] = total_bytes / duration_sec
                flow_dict['Flow Packets/s'] = total_packets / duration_sec
                flow_dict['Fwd Packets/s'] = flow.get('pkts_toserver', 0) / duration_sec
                flow_dict['Bwd Packets/s'] = flow.get('pkts_toclient', 0) / duration_sec
            
            # TCP flags (als beschikbaar)
            tcp = eve_record.get('tcp', {})
            flow_dict['PSH Flag Count'] = 1 if tcp.get('psh') else 0
            flow_dict['URG Flag Count'] = 1 if tcp.get('urg') else 0
            flow_dict['FIN Flag Count'] = 1 if tcp.get('fin') else 0
            flow_dict['SYN Flag Count'] = 1 if tcp.get('syn') else 0
            flow_dict['RST Flag Count'] = 1 if tcp.get('rst') else 0
            flow_dict['ACK Flag Count'] = 1 if tcp.get('ack') else 0
            
            # Vul resterende features met defaults
            # (Voor betere resultaten: implementeer volledige feature extraction)
            default_features = [
                'Fwd Packet Length Max', 'Fwd Packet Length Min', 'Fwd Packet Length Mean',
                'Bwd Packet Length Max', 'Bwd Packet Length Min', 'Bwd Packet Length Mean',
                'Flow IAT Mean', 'Flow IAT Max', 'Flow IAT Min', 'Flow IAT Std',
                'Active Mean', 'Active Std', 'Active Max', 'Active Min',
                'Idle Mean', 'Idle Std', 'Idle Max', 'Idle Min'
            ]
            
            for feature in default_features:
                if feature not in flow_dict:
                    flow_dict[feature] = 0
            
            return flow_dict
            
        except Exception as e:
            self.logger.error(f"Error parsing EVE record: {e}")
            return None

class SuricataIntegration:
    """
    Real-time Suricata integratie
    Monitort EVE log file en classificeert flows real-time
    """
    
    def __init__(self, eve_log_path: str, model_path: str = "models"):
        """
        Args:
            eve_log_path: Pad naar Suricata eve.json log
            model_path: Pad naar model directory
        """
        self.logger = Logger(__name__)
        self.eve_log_path = Path(eve_log_path)
        self.parser = SuricataEveParser()
        self.firewall = AIFirewallInference(model_dir=model_path)
        self.prediction_logger = PredictionLogger()
        
        self.stats = {
            'total_flows': 0,
            'classified': 0,
            'benign': 0,
            'malicious': 0,
            'errors': 0
        }
        
    def process_eve_line(self, line: str):
        """
        Process single EVE JSON line
        
        Args:
            line: JSON line from EVE log
        """
        try:
            # Parse JSON
            eve_record = json.loads(line)
            
            # Converteer naar flow format
            flow_dict = self.parser.parse_eve_flow(eve_record)
            
            if flow_dict is None:
                return
            
            self.stats['total_flows'] += 1
            
            # Classificeer flow
            result = self.firewall.predict_single_flow(flow_dict)
            
            self.stats['classified'] += 1
            
            if result['prediction'] == 'MALICIOUS':
                self.stats['malicious'] += 1
                
                # Log malicious flow
                self.logger.warning(
                    f"🚨 MALICIOUS FLOW DETECTED! "
                    f"Score: {result['ensemble_score']:.3f} | "
                    f"Src: {eve_record.get('src_ip')}:{eve_record.get('src_port')} -> "
                    f"Dst: {eve_record.get('dest_ip')}:{eve_record.get('dest_port')}"
                )
                
                # Save prediction
                self.prediction_logger.log_prediction(
                    flow_dict,
                    result,
                    metadata={
                        'source': 'suricata',
                        'src_ip': eve_record.get('src_ip'),
                        'dest_ip': eve_record.get('dest_ip'),
                        'timestamp': eve_record.get('timestamp')
                    }
                )
            else:
                self.stats['benign'] += 1
                
        except json.JSONDecodeError:
            pass  # Skip non-JSON lines
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing EVE line: {e}")
    
    def tail_eve_log(self):
        """
        Tail EVE log file (zoals tail -f)
        """
        self.logger.info(f"📡 Monitoring Suricata EVE log: {self.eve_log_path}")
        
        try:
            with open(self.eve_log_path, 'r') as f:
                # Ga naar einde van file
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    
                    if line:
                        self.process_eve_line(line.strip())
                    else:
                        # Wacht op nieuwe data
                        time.sleep(0.1)
                        
                        # Print stats elke 10 seconden
                        if self.stats['total_flows'] % 100 == 0 and self.stats['total_flows'] > 0:
                            self.print_stats()
                            
        except KeyboardInterrupt:
            self.logger.info("\n⏹️  Stopping Suricata integration...")
            self.print_stats()
        except Exception as e:
            self.logger.error(f"Error tailing EVE log: {e}")
    
    def print_stats(self):
        """Print statistieken"""
        malicious_pct = (self.stats['malicious'] / self.stats['classified'] * 100) if self.stats['classified'] > 0 else 0
        
        self.logger.info(
            f"\n📊 STATS: "
            f"Flows: {self.stats['total_flows']} | "
            f"Classified: {self.stats['classified']} | "
            f"Benign: {self.stats['benign']} | "
            f"Malicious: {self.stats['malicious']} ({malicious_pct:.1f}%) | "
            f"Errors: {self.stats['errors']}"
        )

class ZeekLogParser:
    """
    Parser voor Zeek (Bro) conn.log
    Alternatief voor Suricata
    """
    
    def __init__(self):
        self.logger = Logger(__name__)
    
    def parse_conn_log(self, log_line: str) -> Optional[Dict]:
        """
        Parse Zeek conn.log line naar flow format
        
        Zeek conn.log format:
        ts, uid, id.orig_h, id.orig_p, id.resp_h, id.resp_p, proto, service,
        duration, orig_bytes, resp_bytes, conn_state, local_orig, local_resp,
        missed_bytes, history, orig_pkts, orig_ip_bytes, resp_pkts, resp_ip_bytes
        """
        try:
            # Skip comments
            if log_line.startswith('#'):
                return None
            
            fields = log_line.split('\t')
            
            if len(fields) < 20:
                return None
            
            # Parse fields
            duration = float(fields[8]) if fields[8] != '-' else 0
            orig_bytes = int(fields[9]) if fields[9] != '-' else 0
            resp_bytes = int(fields[10]) if fields[10] != '-' else 0
            orig_pkts = int(fields[16]) if fields[16] != '-' else 0
            resp_pkts = int(fields[18]) if fields[18] != '-' else 0
            
            flow_dict = {
                'Destination Port': int(fields[5]),
                'Flow Duration': duration * 1000000,  # naar microseconds
                'Protocol': 6 if fields[6] == 'tcp' else 17,
                
                'Total Fwd Packets': orig_pkts,
                'Total Backward Packets': resp_pkts,
                'Total Length of Fwd Packets': orig_bytes,
                'Total Length of Bwd Packets': resp_bytes,
                
                # Bereken rates
                'Flow Bytes/s': (orig_bytes + resp_bytes) / duration if duration > 0 else 0,
                'Flow Packets/s': (orig_pkts + resp_pkts) / duration if duration > 0 else 0,
                'Fwd Packets/s': orig_pkts / duration if duration > 0 else 0,
                'Bwd Packets/s': resp_pkts / duration if duration > 0 else 0,
            }
            
            # Defaults voor overige features
            return flow_dict
            
        except Exception as e:
            self.logger.error(f"Error parsing Zeek log: {e}")
            return None

def main():
    """CLI voor Suricata/Zeek integratie"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-Firewall Suricata/Zeek Integration")
    parser.add_argument('--eve-log', type=str, default='/var/log/suricata/eve.json',
                       help='Path to Suricata EVE JSON log')
    parser.add_argument('--model-dir', type=str, default='models',
                       help='Path to model directory')
    
    args = parser.parse_args()
    
    # Start integration
    integration = SuricataIntegration(
        eve_log_path=args.eve_log,
        model_path=args.model_dir
    )
    
    integration.tail_eve_log()

if __name__ == "__main__":
    main()
