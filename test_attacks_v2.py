"""
Test ML model met ECHTE ATTACK data uit de CIC-IDS2017 dataset
Specifiek zoeken naar DDoS attacks (niet de benign prefix)
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '.')

from inference import AIFirewallInference

def test_with_real_attacks():
    print("=" * 60)
    print("AI-FIREWALL ML MODEL - ATTACK DETECTION TEST")
    print("=" * 60)
    
    # Initialize
    inf = AIFirewallInference()
    
    # Load DDoS attacks file and find ACTUAL attacks
    ddos_file = "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
    df_ddos = pd.read_csv(ddos_file)
    
    # Filter for actual DDoS attacks
    df_attacks = df_ddos[df_ddos[' Label'].str.strip() != 'BENIGN'].head(20)
    df_benign = df_ddos[df_ddos[' Label'].str.strip() == 'BENIGN'].head(20)
    
    print(f"\nFound {len(df_attacks)} DDoS attack samples")
    print(f"Found {len(df_benign)} Benign samples")
    print(f"Attack types: {df_attacks[' Label'].unique()}")
    
    # Test DDoS detection
    print("\n" + "=" * 60)
    print("TEST 1: DDoS ATTACK DETECTION (Should be MALICIOUS)")
    print("=" * 60)
    
    attack_correct = 0
    attack_total = 0
    
    for idx, (_, row) in enumerate(df_attacks.iterrows()):
        if idx >= 15:
            break
            
        flow_dict = row.drop(' Label').to_dict()
        actual_label = row[' Label'].strip()
        
        try:
            result = inf.predict_single_flow(flow_dict)
            prediction = result['prediction']
            xgb_score = result['xgb_score']
            ensemble = result['ensemble_score']
            
            # Attack should be detected as malicious
            is_correct = prediction == 'malicious'
            if is_correct:
                attack_correct += 1
            attack_total += 1
            
            status = "✅" if is_correct else "❌"
            print(f"  {status} [{actual_label}] Pred={prediction}, XGB={xgb_score:.4f}, Ens={ensemble:.4f}")
            
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
    
    print(f"\n→ Attack Detection: {attack_correct}/{attack_total} ({100*attack_correct/max(attack_total,1):.1f}%)")
    
    # Test Benign detection
    print("\n" + "=" * 60)
    print("TEST 2: BENIGN TRAFFIC DETECTION (Should be BENIGN)")
    print("=" * 60)
    
    benign_correct = 0
    benign_total = 0
    
    for idx, (_, row) in enumerate(df_benign.iterrows()):
        if idx >= 15:
            break
            
        flow_dict = row.drop(' Label').to_dict()
        
        try:
            result = inf.predict_single_flow(flow_dict)
            prediction = result['prediction']
            xgb_score = result['xgb_score']
            ensemble = result['ensemble_score']
            
            is_correct = prediction == 'benign'
            if is_correct:
                benign_correct += 1
            benign_total += 1
            
            status = "✅" if is_correct else "❌"
            print(f"  {status} [BENIGN] Pred={prediction}, XGB={xgb_score:.4f}, Ens={ensemble:.4f}")
            
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
    
    print(f"\n→ Benign Detection: {benign_correct}/{benign_total} ({100*benign_correct/max(benign_total,1):.1f}%)")
    
    # Also test Port Scan attacks
    print("\n" + "=" * 60)
    print("TEST 3: PORT SCAN DETECTION")
    print("=" * 60)
    
    try:
        portscan_file = "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv"
        df_portscan = pd.read_csv(portscan_file)
        df_portscan_attacks = df_portscan[df_portscan[' Label'].str.strip() != 'BENIGN'].head(15)
        
        portscan_correct = 0
        portscan_total = 0
        
        for idx, (_, row) in enumerate(df_portscan_attacks.iterrows()):
            flow_dict = row.drop(' Label').to_dict()
            actual_label = row[' Label'].strip()
            
            try:
                result = inf.predict_single_flow(flow_dict)
                prediction = result['prediction']
                xgb_score = result['xgb_score']
                ensemble = result['ensemble_score']
                
                is_correct = prediction == 'malicious'
                if is_correct:
                    portscan_correct += 1
                portscan_total += 1
                
                status = "✅" if is_correct else "❌"
                print(f"  {status} [{actual_label}] Pred={prediction}, XGB={xgb_score:.4f}, Ens={ensemble:.4f}")
                
            except Exception as e:
                print(f"  ⚠️ Error: {e}")
        
        print(f"\n→ PortScan Detection: {portscan_correct}/{portscan_total} ({100*portscan_correct/max(portscan_total,1):.1f}%)")
        
    except Exception as e:
        print(f"  Could not load PortScan file: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    
    total_attacks = attack_correct + (portscan_correct if 'portscan_correct' in dir() else 0)
    total_attack_samples = attack_total + (portscan_total if 'portscan_total' in dir() else 0)
    
    print(f"Attack Detection Rate: {total_attacks}/{total_attack_samples} ({100*total_attacks/max(total_attack_samples,1):.1f}%)")
    print(f"Benign Detection Rate: {benign_correct}/{benign_total} ({100*benign_correct/max(benign_total,1):.1f}%)")
    
    if total_attacks / max(total_attack_samples, 1) > 0.7:
        print("\n✅ MODEL SUCCESSFULLY DETECTS WIRELESS/NETWORK ATTACKS!")
    else:
        print("\n⚠️ MODEL DETECTION NEEDS IMPROVEMENT")

if __name__ == "__main__":
    test_with_real_attacks()
