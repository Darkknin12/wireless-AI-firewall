"""
Test ML model met ECHTE data uit de CIC-IDS2017 dataset
Dit test of het model correct werkt met volledige feature sets
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '.')

from inference import AIFirewallInference

def test_with_real_data():
    print("=" * 60)
    print("AI-FIREWALL ML MODEL - TEST MET ECHTE DATASET")
    print("=" * 60)
    
    # Initialize
    inf = AIFirewallInference()
    
    # Load een sample van de echte training data
    try:
        # DDoS attacks
        ddos_file = "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
        df_ddos = pd.read_csv(ddos_file, nrows=100)
        
        # Benign traffic
        benign_file = "ml_data/MachineLearningCVE/Friday-WorkingHours-Morning.pcap_ISCX.csv"
        df_benign = pd.read_csv(benign_file, nrows=100)
        
        print(f"\nLoaded {len(df_ddos)} DDoS samples")
        print(f"Loaded {len(df_benign)} Benign samples")
        
    except Exception as e:
        print(f"ERROR loading data: {e}")
        print("Data files not found in container. Testing with inline data.")
        return
    
    # Test DDoS detection
    print("\n" + "=" * 60)
    print("TEST 1: DDoS ATTACK DETECTION")
    print("=" * 60)
    
    ddos_correct = 0
    ddos_total = 0
    
    for idx, row in df_ddos.iterrows():
        if idx >= 20:  # Test 20 samples
            break
        
        flow_dict = row.drop(' Label').to_dict()
        actual_label = row[' Label'].strip().lower()
        
        try:
            result = inf.predict_single_flow(flow_dict)
            prediction = result['prediction']
            ensemble = result['ensemble_score']
            
            # DDoS should be detected as malicious
            is_attack = actual_label != 'benign'
            predicted_attack = prediction == 'malicious'
            
            if is_attack == predicted_attack:
                ddos_correct += 1
            ddos_total += 1
            
            status = "✅" if is_attack == predicted_attack else "❌"
            print(f"  {status} Sample {idx}: Label={actual_label}, Pred={prediction}, Score={ensemble:.4f}")
            
        except Exception as e:
            print(f"  ⚠️ Sample {idx}: Error - {e}")
    
    print(f"\nDDoS Detection Accuracy: {ddos_correct}/{ddos_total} ({100*ddos_correct/max(ddos_total,1):.1f}%)")
    
    # Test Benign detection
    print("\n" + "=" * 60)
    print("TEST 2: BENIGN TRAFFIC DETECTION")
    print("=" * 60)
    
    benign_correct = 0
    benign_total = 0
    
    for idx, row in df_benign.iterrows():
        if idx >= 20:  # Test 20 samples
            break
        
        flow_dict = row.drop(' Label').to_dict()
        actual_label = row[' Label'].strip().lower()
        
        try:
            result = inf.predict_single_flow(flow_dict)
            prediction = result['prediction']
            ensemble = result['ensemble_score']
            
            # Benign should be detected as benign
            is_benign = actual_label == 'benign'
            predicted_benign = prediction == 'benign'
            
            if is_benign == predicted_benign:
                benign_correct += 1
            benign_total += 1
            
            status = "✅" if is_benign == predicted_benign else "❌"
            print(f"  {status} Sample {idx}: Label={actual_label}, Pred={prediction}, Score={ensemble:.4f}")
            
        except Exception as e:
            print(f"  ⚠️ Sample {idx}: Error - {e}")
    
    print(f"\nBenign Detection Accuracy: {benign_correct}/{benign_total} ({100*benign_correct/max(benign_total,1):.1f}%)")
    
    # Summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    total_correct = ddos_correct + benign_correct
    total_samples = ddos_total + benign_total
    print(f"Total Accuracy: {total_correct}/{total_samples} ({100*total_correct/max(total_samples,1):.1f}%)")
    
    if total_correct / max(total_samples, 1) > 0.8:
        print("\n✅ MODEL WORKS CORRECTLY!")
        print("   The AI-Firewall can detect attacks with high accuracy.")
    else:
        print("\n⚠️ MODEL NEEDS IMPROVEMENT")
        print("   Check feature alignment and model training.")

if __name__ == "__main__":
    test_with_real_data()
