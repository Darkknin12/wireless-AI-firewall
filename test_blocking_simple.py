"""
Simple Test: AI-Firewall met Automatic Blocking
Test met echte CICIDS2017 data
"""

from firewall_blocker import FirewallBlocker
from inference import AIFirewallInference
import pandas as pd
from pathlib import Path

def test_with_real_data():
    """Test met real CICIDS2017 data"""
    
    print("\n" + "="*70)
    print("AI-FIREWALL AUTOMATIC BLOCKING TEST (Real Data)")
    print("="*70)
    
    # 1. Initialize
    print("\n[1] Initializing...")
    blocker = FirewallBlocker()
    
    # Force enable auto-block for testing
    blocker.auto_block_enabled = True
    print(f"    [FORCED] Auto-block enabled for testing")
    
    inference_engine = AIFirewallInference()
    inference_engine.load_models()
    
    print(f"    Auto-block: {blocker.auto_block_enabled}")
    print(f"    Threshold: {blocker.block_threshold}")
    
    # 2. Load real data
    print("\n[2] Loading CICIDS2017 data...")
    csv_file = Path("ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv")
    
    if not csv_file.exists():
        print(f"    ERROR: {csv_file} not found!")
        return
    
    # Load sample
    df = pd.read_csv(csv_file, nrows=50000)  # Load more to find malicious
    df.columns = df.columns.str.strip()  # Clean column names
    
    print(f"    Loaded {len(df)} flows")
    
    # Filter for malicious only
    malicious = df[df['Label'] != 'BENIGN'].head(5)
    benign = df[df['Label'] == 'BENIGN'].head(5)
    
    print(f"    Malicious samples: {len(malicious)}")
    print(f"    Benign samples: {len(benign)}")
    
    # 3. Test malicious flows
    print("\n[3] Testing Malicious Flows...")
    print("-" * 70)
    
    blocked_count = 0
    
    for idx, row in malicious.iterrows():
        # Convert to dict
        flow_data = row.to_dict()
        
        # Get actual label
        actual_label = flow_data.get('Label', 'Unknown')
        src_ip = flow_data.get('Source IP', 'Unknown')
        dst_ip = flow_data.get('Destination IP', 'Unknown')
        dst_port = flow_data.get('Destination Port', 0)
        
        # Predict
        result = inference_engine.predict_single_flow(flow_data)
        
        print(f"\nFlow {idx+1}:")
        print(f"  Source IP: {src_ip}")
        print(f"  Target: {dst_ip}:{dst_port}")
        print(f"  Actual: {actual_label}")
        print(f"  Predicted: {result['prediction']}")
        print(f"  Score: {result['ensemble_score']:.3f}")
        
        # Check if should block (case-insensitive check)
        is_malicious = result['prediction'].upper() == 'MALICIOUS'
        above_threshold = result['ensemble_score'] >= blocker.block_threshold
        
        if is_malicious and above_threshold:
            print(f"  [!] THREAT DETECTED!")
            
            # Add src_ip to flow_data for blocker
            flow_data['src_ip'] = src_ip
            
            if blocker.auto_block_enabled:
                blocked = blocker.process_prediction(flow_data, result)
                if blocked:
                    print(f"  [BLOCKED] IP: {src_ip}")
                    blocked_count += 1
                else:
                    print(f"  [FAILED] Could not block: {src_ip}")
            else:
                print(f"  [WARN] Would block: {src_ip} (auto-block disabled)")
        else:
            if is_malicious:
                print(f"  [INFO] Malicious but below threshold ({result['ensemble_score']:.3f} < {blocker.block_threshold})")
            else:
                print(f"  [OK] Benign traffic")
    
    # 4. Test benign flows
    print("\n" + "-" * 70)
    print("[4] Testing Benign Flows...")
    print("-" * 70)
    
    for idx, row in benign.iterrows():
        flow_data = row.to_dict()
        
        actual_label = flow_data.get('Label', 'Unknown')
        src_ip = flow_data.get('Source IP', 'Unknown')
        
        result = inference_engine.predict_single_flow(flow_data)
        
        print(f"\nFlow {idx+1}:")
        print(f"  Source IP: {src_ip}")
        print(f"  Actual: {actual_label}")
        print(f"  Predicted: {result['prediction']}")
        print(f"  Score: {result['ensemble_score']:.3f}")
        print(f"  Action: [OK] Allow")
    
    # 5. Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    stats = blocker.get_stats()
    
    print(f"\n[RESULTS]:")
    print(f"  Malicious detected: {len(malicious)}")
    print(f"  Benign allowed: {len(benign)}")
    
    if blocker.auto_block_enabled:
        print(f"  IPs blocked: {blocked_count}")
        print(f"  Total blocked: {stats['total_blocked']}")
    else:
        print(f"  Auto-block: DISABLED")
        print(f"  (Would have blocked malicious IPs)")
    
    print(f"\n[CONFIG]:")
    print(f"  Auto-block: {stats['auto_block_enabled']}")
    print(f"  Threshold: {stats['block_threshold']}")
    print(f"  Whitelist size: {stats['whitelist_size']}")
    
    print("\n[INFO] To enable automatic blocking:")
    print("   1. Edit config.json")
    print('   2. Set: "auto_block": true')
    print("   3. Re-run test")
    
    if blocker.blocked_ips:
        print(f"\n[BLOCKED] Currently Blocked IPs:")
        for ip in blocker.get_blocked_ips():
            print(f"   - {ip}")
    
    print("\n" + "="*70)
    print("[OK] Test Complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_with_real_data()
