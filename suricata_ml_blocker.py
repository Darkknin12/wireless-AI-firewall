"""
Suricata + ML Blocker voor Raspberry Pi
Leest Suricata EVE alerts en gebruikt ML voor extra validatie
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict
import redis

from utils import Logger, Config
from firewall_blocker import FirewallBlocker
from suricata_integration import SuricataEveParser
from inference import AIFirewallInference

class SuricataMLBlocker:
    """
    Combineert Suricata IDS alerts met ML predictions
    - Suricata: Signature-based detection (fast, known threats)
    - ML: Behavioral detection (slow, unknown threats)
    """
    
    def __init__(self):
        self.logger = Logger(__name__).get_logger()
        self.config = Config()
        
        # Initialize components
        self.blocker = FirewallBlocker()
        self.suricata_parser = SuricataEveParser()
        self.ml_engine = AIFirewallInference()
        
        # Load ML models (only if needed)
        self.use_ml = self.config.get('ml_validation', True)
        if self.use_ml:
            self.logger.info("Loading ML models for validation...")
            self.ml_engine.load_models()
        else:
            self.logger.info("ML validation disabled - using Suricata only")
        
        # Redis for deduplication
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            self.logger.info(f"Connected to Redis: {redis_url}")
        except:
            self.logger.warning("Redis not available - using local cache")
            self.redis = None
        
        # EVE log path
        self.eve_log = Path(os.getenv('SURICATA_EVE_LOG', '/app/suricata_logs/eve.json'))
        
        # Statistics
        self.stats = {
            'suricata_alerts': 0,
            'ml_validated': 0,
            'blocked': 0,
            'false_positives': 0,
            'total_flows': 0,
            'start_time': time.time()
        }
        
        # Attack type mapping
        self.attack_priorities = {
            'attempted-dos': 1,
            'successful-dos': 1,
            'denial-of-service': 1,
            'attempted-admin': 1,
            'successful-admin': 1,
            'trojan-activity': 1,
            'command-and-control': 1,
            'coin-mining': 1,
            'web-application-attack': 1,
            'exploit-kit': 1,
            'network-scan': 2,
            'attempted-recon': 2,
            'suspicious-login': 2,
            'policy-violation': 3,
            'misc-attack': 3
        }
    
    def is_already_processed(self, src_ip: str, flow_id: str) -> bool:
        """Check if flow already processed (deduplication)"""
        if self.redis:
            key = f"processed:{src_ip}:{flow_id}"
            if self.redis.exists(key):
                return True
            self.redis.setex(key, 300, "1")  # 5 min cache
            return False
        return False
    
    def should_validate_with_ml(self, alert: Dict) -> bool:
        """
        Bepaal of ML validatie nodig is
        High-priority Suricata alerts → Direct block
        Medium/Low priority → ML validation
        """
        if not self.use_ml:
            return False
        
        classification = alert.get('alert', {}).get('category', '')
        priority = self.attack_priorities.get(classification, 3)
        
        # Priority 1 = Critical → Direct block (trust Suricata)
        # Priority 2/3 = Medium/Low → ML validation (reduce false positives)
        return priority >= 2
    
    def validate_with_ml(self, flow_data: Dict) -> Optional[Dict]:
        """Validate Suricata alert with ML"""
        try:
            result = self.ml_engine.predict_single_flow(flow_data)
            self.stats['ml_validated'] += 1
            return result
        except Exception as e:
            self.logger.error(f"ML validation failed: {e}")
            return None
    
    def process_alert(self, alert: Dict):
        """Process single Suricata alert"""
        try:
            # Parse alert
            src_ip = alert.get('src_ip')
            dest_ip = alert.get('dest_ip')
            alert_info = alert.get('alert', {})
            classification = alert_info.get('category', 'unknown')
            signature = alert_info.get('signature', 'Unknown')
            severity = alert_info.get('severity', 3)
            
            if not src_ip:
                return
            
            # Deduplication
            flow_id = alert.get('flow_id', '')
            if self.is_already_processed(src_ip, flow_id):
                return
            
            self.stats['suricata_alerts'] += 1
            
            # Publish raw alert to dashboard
            self.publish_alert({
                'src_ip': src_ip,
                'dest_ip': dest_ip,
                'signature': signature,
                'severity': severity,
                'action': 'alert'
            })
            
            self.logger.info(f"[SURICATA] Alert from {src_ip}")
            self.logger.info(f"  Signature: {signature}")
            self.logger.info(f"  Category: {classification}")
            self.logger.info(f"  Severity: {severity}")
            
            # Check priority
            priority = self.attack_priorities.get(classification, 3)
            
            # Critical threats → Block immediately
            if priority == 1:
                self.logger.warning(f"[CRITICAL] High-priority threat detected!")
                self.block_ip(src_ip, f"Suricata: {signature}", threat_score=0.95)
                
                # Publish block event
                self.publish_alert({
                    'src_ip': src_ip,
                    'signature': signature,
                    'action': 'block',
                    'reason': 'Critical Priority'
                })
                return
            
            # Medium/Low threats → ML validation
            if self.should_validate_with_ml(alert):
                self.logger.info("[ML] Validating with machine learning...")
                
                # Convert to CICIDS2017 format
                flow_data = self.suricata_parser.parse_eve_flow(alert)
                
                if flow_data:
                    ml_result = self.validate_with_ml(flow_data)
                    
                    if ml_result:
                        is_malicious = ml_result['prediction'].upper() == 'MALICIOUS'
                        score = ml_result['ensemble_score']
                        
                        self.logger.info(f"  ML Prediction: {ml_result['prediction']}")
                        self.logger.info(f"  ML Score: {score:.3f}")
                        
                        if is_malicious and score >= self.blocker.block_threshold:
                            self.logger.warning(f"[CONFIRMED] ML confirms threat!")
                            self.block_ip(src_ip, f"Suricata+ML: {signature}", threat_score=score)
                            
                            # Publish block event
                            self.publish_alert({
                                'src_ip': src_ip,
                                'signature': signature,
                                'action': 'block',
                                'reason': 'ML Confirmed',
                                'score': score
                            })
                        else:
                            self.logger.info(f"[FALSE POSITIVE] ML says benign (score: {score:.3f})")
                            self.stats['false_positives'] += 1
                    else:
                        # ML failed → Trust Suricata for priority 2
                        if priority == 2:
                            self.block_ip(src_ip, f"Suricata: {signature}", threat_score=0.75)
                            
                            # Publish block event
                            self.publish_alert({
                                'src_ip': src_ip,
                                'signature': signature,
                                'action': 'block',
                                'reason': 'Priority 2 Fallback'
                            })
                else:
                    self.logger.warning("[ML] Could not convert flow format")
            else:
                # No ML validation needed → Block based on Suricata
                self.block_ip(src_ip, f"Suricata: {signature}", threat_score=0.80)
                
                # Publish block event
                self.publish_alert({
                    'src_ip': src_ip,
                    'signature': signature,
                    'action': 'block',
                    'reason': 'Suricata Only'
                })
                
        except Exception as e:
            self.logger.error(f"Error processing alert: {e}")
    
    def block_ip(self, ip: str, reason: str, threat_score: float):
        """Block IP address"""
        flow_data = {'src_ip': ip}
        result = {
            'prediction': 'MALICIOUS',
            'ensemble_score': threat_score,
            'xgboost_prob': threat_score,
            'isolation_forest_score': -1
        }
        
        blocked = self.blocker.process_prediction(flow_data, result, reason=reason)
        
        if blocked:
            self.stats['blocked'] += 1
            self.logger.warning(f"[BLOCKED] {ip} - {reason}")
        else:
            self.logger.error(f"[FAILED] Could not block {ip}")
    
    def tail_eve_log(self):
        """Tail Suricata EVE JSON log"""
        self.logger.info(f"Monitoring Suricata EVE log: {self.eve_log}")
        
        if not self.eve_log.exists():
            self.logger.error(f"EVE log not found: {self.eve_log}")
            self.logger.info("Waiting for Suricata to start...")
            time.sleep(10)
        
        # Open log file
        with open(self.eve_log, 'r') as f:
            # Go to end
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                
                if not line:
                    time.sleep(0.1)  # Wait for new data
                    continue
                
                try:
                    event = json.loads(line)
                    event_type = event.get('event_type')
                    
                    # Process events
                    if event_type == 'alert':
                        self.process_alert(event)
                    elif event_type == 'flow':
                        self.process_flow(event)
                    elif event_type == 'stats':
                        self.process_stats(event)
                    
                except json.JSONDecodeError:
                    continue
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.logger.error(f"Error reading EVE log: {e}")
    
    def process_flow(self, event: Dict):
        """Process flow event (for stats)"""
        self.stats['total_flows'] += 1
        
        # Publish stats to Redis every 10 flows or if it's an alert
        if self.stats['total_flows'] % 10 == 0:
            self.publish_stats()

    def process_stats(self, event: Dict):
        """Process Suricata stats event"""
        pass

    def publish_stats(self):
        """Publish stats to Redis for dashboard"""
        if not self.redis:
            return
            
        try:
            stats_data = {
                'type': 'stats',
                'total_flows': self.stats['total_flows'],
                'suricata_alerts': self.stats['suricata_alerts'],
                'blocked': self.stats['blocked'],
                'timestamp': datetime.now().isoformat()
            }
            self.redis.publish('firewall_events', json.dumps(stats_data))
        except Exception as e:
            self.logger.error(f"Failed to publish stats: {e}")

    def publish_alert(self, alert_data: Dict):
        """Publish alert to Redis for dashboard"""
        if not self.redis:
            return
            
        try:
            alert_data['type'] = 'alert'
            alert_data['timestamp'] = datetime.now().isoformat()
            self.redis.publish('firewall_events', json.dumps(alert_data))
        except Exception as e:
            self.logger.error(f"Failed to publish alert: {e}")
    
    def print_stats(self):
        """Print statistics"""
        uptime = time.time() - self.stats['start_time']
        
        print("\n" + "="*70)
        print("SURICATA + ML BLOCKER STATISTICS")
        print("="*70)
        print(f"Uptime: {uptime/60:.1f} minutes")
        print(f"Suricata Alerts: {self.stats['suricata_alerts']}")
        print(f"ML Validations: {self.stats['ml_validated']}")
        print(f"IPs Blocked: {self.stats['blocked']}")
        print(f"False Positives Prevented: {self.stats['false_positives']}")
        print("="*70 + "\n")
    
    def run(self):
        """Main loop"""
        self.logger.info("="*70)
        self.logger.info("SURICATA + ML AUTOMATIC BLOCKER - Raspberry Pi 4")
        self.logger.info("="*70)
        self.logger.info(f"Auto-block: {self.blocker.auto_block_enabled}")
        self.logger.info(f"Threshold: {self.blocker.block_threshold}")
        self.logger.info(f"ML Validation: {self.use_ml}")
        self.logger.info("="*70)
        
        try:
            # Monitor EVE log
            self.tail_eve_log()
        except KeyboardInterrupt:
            self.logger.info("\nShutting down...")
            self.print_stats()
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise

if __name__ == "__main__":
    blocker = SuricataMLBlocker()
    blocker.run()
