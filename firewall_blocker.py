"""
Automatic Firewall Blocker
Blokkeert malicious traffic automatisch via iptables/nftables
"""

import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set, Dict, List
from utils import Logger, Config

class FirewallBlocker:
    """
    Automatic firewall blocker voor malicious traffic
    Gebruikt iptables (Linux) of Windows Firewall
    """
    
    def __init__(self, reload_config=True):
        self.logger = Logger(__name__).logger
        
        # Force reload config if needed
        if reload_config:
            import importlib
            import utils
            importlib.reload(utils)
        
        self.config = Config()
        
        # Blocked IPs tracking
        self.blocked_ips: Set[str] = set()
        self.block_history: List[Dict] = []
        
        # Thresholds
        self.block_threshold = self.config.get('firewall.block_threshold', 0.7)
        self.auto_block_enabled = self.config.get('firewall.auto_block', False)
        self.block_duration_hours = self.config.get('firewall.block_duration', 24)
        
        # Whitelist (never block these)
        self.whitelist = set(self.config.get('firewall.whitelist', [
            '127.0.0.1',
            '192.168.1.1',  # Router
            '8.8.8.8',      # Google DNS
        ]))
        
        self.logger.info("FirewallBlocker initialized")
        self.logger.info(f"Auto-block: {self.auto_block_enabled}")
        self.logger.info(f"Threshold: {self.block_threshold}")
        
    def is_linux(self) -> bool:
        """Check if running on Linux"""
        import platform
        return platform.system() == 'Linux'
    
    def is_windows(self) -> bool:
        """Check if running on Windows"""
        import platform
        return platform.system() == 'Windows'
    
    def block_ip_linux(self, ip: str, reason: str = "Malicious traffic") -> bool:
        """
        Block IP using iptables (Linux)
        
        Args:
            ip: IP address to block
            reason: Reason for blocking
            
        Returns:
            True if successful
        """
        try:
            # Check if already blocked
            if ip in self.blocked_ips:
                self.logger.info(f"IP {ip} already blocked")
                return True
            
            # Check whitelist
            if ip in self.whitelist:
                self.logger.warning(f"IP {ip} is whitelisted - NOT blocking")
                return False
            
            # Block with iptables
            cmd = [
                'sudo', 'iptables',
                '-A', 'INPUT',
                '-s', ip,
                '-j', 'DROP',
                '-m', 'comment',
                '--comment', f'AI-Firewall: {reason}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.blocked_ips.add(ip)
                self.log_block(ip, reason, 'iptables')
                self.logger.info(f"✅ BLOCKED IP: {ip} ({reason})")
                return True
            else:
                self.logger.error(f"Failed to block {ip}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error blocking IP {ip}: {e}")
            return False
    
    def block_ip_windows(self, ip: str, reason: str = "Malicious traffic") -> bool:
        """
        Block IP using Windows Firewall
        
        Args:
            ip: IP address to block
            reason: Reason for blocking
            
        Returns:
            True if successful
        """
        try:
            # Check if already blocked
            if ip in self.blocked_ips:
                self.logger.info(f"IP {ip} already blocked")
                return True
            
            # Check whitelist
            if ip in self.whitelist:
                self.logger.warning(f"IP {ip} is whitelisted - NOT blocking")
                return False
            
            # Create firewall rule name
            rule_name = f"AI-Firewall-Block-{ip.replace('.', '-')}"
            
            # Block with netsh
            cmd = [
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                f'name={rule_name}',
                'dir=in',
                'action=block',
                f'remoteip={ip}',
                f'description={reason}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                self.blocked_ips.add(ip)
                self.log_block(ip, reason, 'windows_firewall')
                self.logger.info(f"✅ BLOCKED IP: {ip} ({reason})")
                return True
            else:
                self.logger.error(f"Failed to block {ip}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error blocking IP {ip}: {e}")
            return False
    
    def block_ip(self, ip: str, reason: str = "Malicious traffic") -> bool:
        """
        Block IP address (platform independent)
        
        Args:
            ip: IP address to block
            reason: Reason for blocking
            
        Returns:
            True if successful
        """
        if not self.auto_block_enabled:
            self.logger.warning(f"Auto-block DISABLED - Would block {ip} ({reason})")
            return False
        
        if self.is_linux():
            return self.block_ip_linux(ip, reason)
        elif self.is_windows():
            return self.block_ip_windows(ip, reason)
        else:
            self.logger.error("Unsupported platform for firewall blocking")
            return False
    
    def unblock_ip_linux(self, ip: str) -> bool:
        """Unblock IP on Linux"""
        try:
            cmd = [
                'sudo', 'iptables',
                '-D', 'INPUT',
                '-s', ip,
                '-j', 'DROP'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.blocked_ips.discard(ip)
                self.logger.info(f"✅ UNBLOCKED IP: {ip}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error unblocking IP {ip}: {e}")
            return False
    
    def unblock_ip_windows(self, ip: str) -> bool:
        """Unblock IP on Windows"""
        try:
            rule_name = f"AI-Firewall-Block-{ip.replace('.', '-')}"
            
            cmd = [
                'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                f'name={rule_name}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                self.blocked_ips.discard(ip)
                self.logger.info(f"✅ UNBLOCKED IP: {ip}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error unblocking IP {ip}: {e}")
            return False
    
    def unblock_ip(self, ip: str) -> bool:
        """Unblock IP address (platform independent)"""
        if self.is_linux():
            return self.unblock_ip_linux(ip)
        elif self.is_windows():
            return self.unblock_ip_windows(ip)
        else:
            return False
    
    def process_prediction(self, flow_data: Dict, prediction_result: Dict) -> bool:
        """
        Process AI prediction en block indien nodig
        
        Args:
            flow_data: Flow metadata (src_ip, dst_ip, etc.)
            prediction_result: AI model output
            
        Returns:
            True if IP was blocked
        """
        # Extract prediction
        prediction = prediction_result.get('prediction', 'BENIGN')
        confidence = prediction_result.get('confidence', 0)
        ensemble_score = prediction_result.get('ensemble_score', 0)
        
        # Check if malicious
        if prediction == 'MALICIOUS' and ensemble_score >= self.block_threshold:
            # Get source IP
            src_ip = flow_data.get('src_ip', flow_data.get('source_ip'))
            
            if src_ip:
                reason = f"Malicious score: {ensemble_score:.3f}"
                blocked = self.block_ip(src_ip, reason)
                
                if blocked:
                    # Send alert
                    self.send_alert(src_ip, flow_data, prediction_result)
                
                return blocked
        
        return False
    
    def log_block(self, ip: str, reason: str, method: str):
        """Log blocked IP"""
        block_record = {
            'timestamp': datetime.now().isoformat(),
            'ip': ip,
            'reason': reason,
            'method': method
        }
        
        self.block_history.append(block_record)
        
        # Save to file
        log_file = Path('logs/blocked_ips.json')
        log_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(block_record) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to log block: {e}")
    
    def send_alert(self, ip: str, flow_data: Dict, prediction: Dict):
        """
        Send alert over blocked IP
        Kan uitgebreid worden met email, Slack, etc.
        """
        alert = f"""
        🚨 MALICIOUS IP BLOCKED 🚨
        
        IP Address: {ip}
        Score: {prediction.get('ensemble_score', 0):.3f}
        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Flow Details:
        - Destination: {flow_data.get('dst_ip', 'Unknown')}:{flow_data.get('dst_port', 'Unknown')}
        - Protocol: {flow_data.get('protocol', 'Unknown')}
        - Bytes: {flow_data.get('total_bytes', 0)}
        
        Action: IP BLOCKED via firewall
        """
        
        self.logger.warning(alert)
        
        # TODO: Implement email/Slack notifications
        # self.send_email(alert)
        # self.send_slack(alert)
    
    def cleanup_expired_blocks(self):
        """Remove blocks ouder dan block_duration"""
        cutoff_time = datetime.now() - timedelta(hours=self.block_duration_hours)
        
        for record in self.block_history:
            block_time = datetime.fromisoformat(record['timestamp'])
            
            if block_time < cutoff_time:
                ip = record['ip']
                if ip in self.blocked_ips:
                    self.unblock_ip(ip)
                    self.logger.info(f"Expired block removed: {ip}")
    
    def get_blocked_ips(self) -> List[str]:
        """Get list of currently blocked IPs"""
        return list(self.blocked_ips)
    
    def get_stats(self) -> Dict:
        """Get blocking statistics"""
        return {
            'total_blocked': len(self.blocked_ips),
            'auto_block_enabled': self.auto_block_enabled,
            'block_threshold': self.block_threshold,
            'whitelist_size': len(self.whitelist),
            'total_blocks_history': len(self.block_history)
        }

# Example usage voor integration met inference
if __name__ == "__main__":
    # Test blocker
    blocker = FirewallBlocker()
    
    # Simulate malicious flow
    flow_data = {
        'src_ip': '192.168.1.100',
        'dst_ip': '8.8.8.8',
        'dst_port': 80,
        'protocol': 'TCP'
    }
    
    prediction = {
        'prediction': 'MALICIOUS',
        'confidence': 0.95,
        'ensemble_score': 0.85
    }
    
    # Process (will block if enabled)
    blocker.process_prediction(flow_data, prediction)
    
    # Show stats
    print(blocker.get_stats())
    print("Blocked IPs:", blocker.get_blocked_ips())
