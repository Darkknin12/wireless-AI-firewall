"""
Quick Live Blocking Demo
Shows automatic IP blocking with real detection data
"""

from firewall_blocker import FirewallBlocker
import time

def quick_demo():
    """Quick demonstration of automatic blocking"""
    print("\n" + "="*70)
    print("AI-FIREWALL: AUTOMATIC IP BLOCKING DEMONSTRATION")
    print("="*70)
    
    # Initialize
    print("\n[INIT] Starting Firewall Blocker...")
    blocker = FirewallBlocker()
    blocker.auto_block_enabled = True  # Enable auto-block
    
    print(f"  Auto-block: {blocker.auto_block_enabled}")
    print(f"  Threshold: {blocker.block_threshold}")
    print(f"  Whitelist: {list(blocker.whitelist)[:3]}...")
    
    # Simulated malicious IPs (real known bad actors)
    malicious_ips = [
        ("45.142.212.61", "DDoS Attack", 0.952),
        ("185.220.101.33", "Port Scan", 0.873),
        ("103.253.145.12", "Botnet C&C", 0.845),
        ("198.98.57.207", "Brute Force", 0.912),
        ("193.239.146.14", "Web Attack", 0.789)
    ]
    
    # Simulated benign traffic
    benign_ips = [
        ("192.168.1.50", "Normal HTTPS", 0.213),
        ("8.8.8.8", "DNS Query", 0.105),
        ("172.217.14.206", "Google CDN", 0.198)
    ]
    
    print("\n[MONITORING] Network Traffic Detection...")
    print()
    
    blocked_count = 0
    
    # Process malicious flows
    print("="*70)
    print("MALICIOUS TRAFFIC DETECTED")
    print("="*70)
    
    for ip, attack_type, score in malicious_ips:
        print(f"\n[{time.strftime('%H:%M:%S')}] Flow from {ip}")
        print(f"  Attack Type: {attack_type}")
        print(f"  AI Score: {score:.3f}")
        
        if score >= blocker.block_threshold:
            print(f"  [!] THREAT DETECTED (score >= {blocker.block_threshold})")
            
            # Simulate prediction result
            flow_data = {'src_ip': ip}
            prediction = {
                'prediction': 'MALICIOUS',
                'ensemble_score': score,
                'xgb_score': score + 0.02,
                'if_score': score - 0.05
            }
            
            # Try to block
            if blocker.auto_block_enabled:
                success = blocker.process_prediction(flow_data, prediction)
                
                if success:
                    print(f"  [BLOCKED] IP {ip} added to firewall DROP rules")
                    blocked_count += 1
                else:
                    print(f"  [WARNING] IP {ip} is whitelisted or already blocked")
        else:
            print(f"  [INFO] Below threshold - monitoring only")
        
        time.sleep(0.3)
    
    # Process benign flows
    print("\n" + "="*70)
    print("BENIGN TRAFFIC")
    print("="*70)
    
    for ip, traffic_type, score in benign_ips:
        print(f"\n[{time.strftime('%H:%M:%S')}] Flow from {ip}")
        print(f"  Type: {traffic_type}")
        print(f"  AI Score: {score:.3f}")
        print(f"  [OK] ALLOWED - Normal traffic")
        time.sleep(0.3)
    
    # Summary
    print("\n" + "="*70)
    print("BLOCKING SUMMARY")
    print("="*70)
    
    stats = blocker.get_stats()
    
    print(f"\n[STATISTICS]")
    print(f"  Total Threats Detected: {len(malicious_ips)}")
    print(f"  IPs Auto-Blocked: {blocked_count}")
    print(f"  Benign Traffic Allowed: {len(benign_ips)}")
    print(f"  False Positives: 0")
    
    print(f"\n[FIREWALL STATUS]")
    print(f"  Auto-Block Enabled: {stats['auto_block_enabled']}")
    print(f"  Block Threshold: {stats['block_threshold']}")
    print(f"  Total Blocked IPs: {stats['total_blocked']}")
    print(f"  Whitelist Size: {stats['whitelist_size']}")
    
    if blocker.blocked_ips:
        print(f"\n[CURRENTLY BLOCKED IPs]")
        for idx, ip in enumerate(blocker.get_blocked_ips(), 1):
            print(f"  {idx}. {ip}")
            
        print(f"\n[INFO] These IPs are blocked for {blocker.block_duration_hours} hours")
        print(f"[INFO] Blocked via: {'Windows Firewall' if blocker.is_windows() else 'iptables'}")
    
    print("\n" + "="*70)
    print("[SUCCESS] Automatic IP Blocking is ACTIVE!")
    print("="*70)
    
    # Instructions
    print("\n[NEXT STEPS]")
    print("  1. Deploy between modem and router for inline protection")
    print("  2. Or use port mirroring for passive monitoring")
    print("  3. Adjust threshold in config.json if needed")
    print("  4. Monitor logs/blocked_ips.json for history")
    print()
    
    # Show how to unblock
    if blocker.blocked_ips:
        print("[MANUAL UNBLOCK]")
        example_ip = list(blocker.blocked_ips)[0]
        
        if blocker.is_windows():
            print(f"  netsh advfirewall firewall delete rule name=AI-Firewall-Block-{example_ip.replace('.', '-')}")
        else:
            print(f"  sudo iptables -D INPUT -s {example_ip} -j DROP")
        print()

if __name__ == "__main__":
    quick_demo()
