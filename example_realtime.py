"""
Example Real-time Network Monitor Integration
Voorbeeld van hoe je de AI Firewall kunt integreren met live netwerkverkeer.
"""

import time
from datetime import datetime
from typing import Dict, Any
import random

from inference import AIFirewallInference, create_example_flow
from utils import Config, Logger


class NetworkMonitor:
    """Simuleert een netwerkmonitor die flows genereert."""
    
    def __init__(self):
        """Initialiseert network monitor."""
        self.logger = Logger("NetworkMonitor").get_logger()
    
    def get_live_flow(self) -> Dict[str, Any]:
        """
        Simuleert het ophalen van een live netwerkflow.
        
        In productie zou dit data van Suricata, Zeek, of netwerkinterface zijn.
        
        Returns:
            Dictionary met flow features
        """
        # Simuleer verschillende soorten verkeer
        flow_types = ['normal_http', 'normal_https', 'suspicious', 'malicious']
        flow_type = random.choice(flow_types)
        
        if flow_type == 'normal_http':
            return self._generate_normal_http_flow()
        elif flow_type == 'normal_https':
            return self._generate_normal_https_flow()
        elif flow_type == 'suspicious':
            return self._generate_suspicious_flow()
        else:
            return self._generate_malicious_flow()
    
    def _generate_normal_http_flow(self) -> Dict[str, Any]:
        """Genereert normale HTTP flow."""
        # Start met complete template
        flow = create_example_flow()
        
        # Randomize voor variatie
        flow['Destination Port'] = 80
        flow['Flow Duration'] = random.randint(500000, 2000000)
        flow['Total Fwd Packets'] = random.randint(5, 15)
        flow['Total Backward Packets'] = random.randint(5, 15)
        flow['Total Length of Fwd Packets'] = random.randint(2000, 8000)
        flow['Total Length of Bwd Packets'] = random.randint(1500, 6000)
        flow['Flow Bytes/s'] = random.uniform(3000, 8000)
        flow['Flow Packets/s'] = random.uniform(8, 15)
        flow['PSH Flag Count'] = random.randint(1, 3)
        flow['ACK Flag Count'] = random.randint(10, 20)
        
        return flow
    
    def _generate_normal_https_flow(self) -> Dict[str, Any]:
        """Genereert normale HTTPS flow."""
        flow = self._generate_normal_http_flow()
        flow['Destination Port'] = 443
        return flow
    
    def _generate_suspicious_flow(self) -> Dict[str, Any]:
        """Genereert verdachte flow (edge case)."""
        flow = self._generate_normal_http_flow()
        # Maak het verdacht maar niet overduidelijk malicious
        flow['Flow Packets/s'] = random.uniform(50, 100)  # Hoger dan normaal
        flow['Flow Bytes/s'] = random.uniform(15000, 30000)
        flow['Total Fwd Packets'] = random.randint(50, 100)
        return flow
    
    def _generate_malicious_flow(self) -> Dict[str, Any]:
        """Genereert duidelijk malicious flow (DDoS/Port Scan pattern)."""
        # Start met complete template
        flow = create_example_flow()
        
        # Modificeer voor malicious pattern
        flow['Destination Port'] = random.randint(1, 65535)  # Random port
        flow['Flow Duration'] = random.randint(10000, 500000)  # Kort
        flow['Total Fwd Packets'] = random.randint(1, 5)  # Weinig packets
        flow['Total Backward Packets'] = random.randint(0, 2)  # Weinig/geen response
        flow['Total Length of Fwd Packets'] = random.randint(60, 300)  # Klein
        flow['Total Length of Bwd Packets'] = random.randint(0, 100)
        flow['Flow Bytes/s'] = random.uniform(100, 1000)  # Laag
        flow['Flow Packets/s'] = random.uniform(200, 1000)  # Hoog (scan pattern)
        flow['Flow IAT Mean'] = random.uniform(1000, 10000)  # Snel
        flow['PSH Flag Count'] = 0
        flow['ACK Flag Count'] = random.randint(0, 2)
        flow['SYN Flag Count'] = random.randint(1, 10)  # Veel SYN (scan)
        flow['FIN Flag Count'] = 0
        
        return flow


class RealTimeFirewall:
    """Real-time firewall met AI classificatie."""
    
    def __init__(self):
        """Initialiseert real-time firewall."""
        self.config = Config()
        self.logger = Logger("RealTimeFirewall", self.config).get_logger()
        
        # Load AI engine
        self.logger.info("Initialiseren van AI Firewall engine...")
        self.ai_engine = AIFirewallInference(config=self.config)
        
        # Statistieken
        self.stats = {
            'total_flows': 0,
            'benign_flows': 0,
            'malicious_flows': 0,
            'alerts': 0,
            'blocked_ips': set()
        }
    
    def process_flow(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verwerkt een enkele flow.
        
        Args:
            flow_data: Flow features
            
        Returns:
            Processing resultaat
        """
        # Classificeer flow
        result = self.ai_engine.predict_single_flow(flow_data)
        
        # Update statistieken
        self.stats['total_flows'] += 1
        
        if result['prediction'] == 'malicious':
            self.stats['malicious_flows'] += 1
            
            if result['is_alert']:
                self.stats['alerts'] += 1
                self._handle_alert(flow_data, result)
        else:
            self.stats['benign_flows'] += 1
        
        return result
    
    def _handle_alert(self, flow_data: Dict[str, Any], result: Dict[str, Any]):
        """
        Handelt alert af (block IP, notify admin, etc.).
        
        Args:
            flow_data: Flow data
            result: Classificatie resultaat
        """
        # In productie: extract source IP van flow_data
        source_ip = flow_data.get('Source IP', '0.0.0.0')
        
        self.logger.warning(
            f"🚨 ALERT: Malicious flow detected! "
            f"Score={result['ensemble_score']:.4f} "
            f"IP={source_ip}"
        )
        
        # Simuleer blokkeren van IP
        self.stats['blocked_ips'].add(source_ip)
        
        # In productie: voeg firewall regel toe
        # firewall.block_ip(source_ip)
        
        # In productie: stuur notificatie
        # notify_admin(f"Blocked {source_ip}")
    
    def print_stats(self):
        """Print statistieken."""
        total = self.stats['total_flows']
        if total == 0:
            return
        
        print("\n" + "=" * 60)
        print("FIREWALL STATISTIEKEN")
        print("=" * 60)
        print(f"Total Flows:     {total}")
        print(f"Benign:          {self.stats['benign_flows']} ({self.stats['benign_flows']/total*100:.1f}%)")
        print(f"Malicious:       {self.stats['malicious_flows']} ({self.stats['malicious_flows']/total*100:.1f}%)")
        print(f"Alerts:          {self.stats['alerts']}")
        print(f"Blocked IPs:     {len(self.stats['blocked_ips'])}")
        print("=" * 60 + "\n")
    
    def run(self, duration_seconds: int = 60, flows_per_second: float = 2.0):
        """
        Draait firewall voor een bepaalde tijd.
        
        Args:
            duration_seconds: Hoelang te draaien (seconden)
            flows_per_second: Aantal flows per seconde
        """
        self.logger.info(f"Starting real-time firewall for {duration_seconds}s...")
        
        monitor = NetworkMonitor()
        start_time = time.time()
        flow_interval = 1.0 / flows_per_second
        
        try:
            while (time.time() - start_time) < duration_seconds:
                # Haal flow op
                flow = monitor.get_live_flow()
                
                # Process flow
                result = self.process_flow(flow)
                
                # Log
                status = "🚨 ALERT" if result['is_alert'] else \
                        ("⚠️  MALICIOUS" if result['prediction'] == 'malicious' else "✓  BENIGN")
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {status} | "
                      f"Score: {result['ensemble_score']:.3f} | "
                      f"Confidence: {result['confidence']:.3f}")
                
                # Wait voor volgende flow
                time.sleep(flow_interval)
        
        except KeyboardInterrupt:
            self.logger.info("\nFirewall gestopt door gebruiker")
        
        # Print finale statistieken
        self.print_stats()


def main():
    """Main entry point voor real-time firewall demo."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🔥 AI FIREWALL - REAL-TIME DEMO 🔥                  ║
║                                                              ║
║     Simuleert real-time netwerkverkeer classificatie         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Initialiseer firewall
    firewall = RealTimeFirewall()
    
    # Run demo
    print("\n🚀 Starting real-time monitoring...")
    print("   (Press Ctrl+C to stop)\n")
    
    firewall.run(
        duration_seconds=30,  # Run voor 30 seconden
        flows_per_second=2.0   # 2 flows per seconde
    )
    
    print("\n✅ Demo compleet!")


if __name__ == "__main__":
    main()
