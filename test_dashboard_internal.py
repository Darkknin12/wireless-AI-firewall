"""
Test script voor het dashboard - runt IN de container
Stuurt echte attacks en benign traffic naar de API en publiceert naar Redis
"""

import pandas as pd
import json
import time
import sys
sys.path.insert(0, '.')

from inference import AIFirewallInference
import redis
from datetime import datetime
import random

def run_test(num_samples=30, attack_ratio=0.3):
    print("=" * 60)
    print("AI-FIREWALL DASHBOARD TEST (Internal)")
    print("=" * 60)
    
    # Initialize inference engine
    inf = AIFirewallInference()
    
    # Connect to Redis
    try:
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        r.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        r = None
    
    # Load DDoS attacks and benign data
    print("\nLoading test data...")
    ddos_file = "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
    df = pd.read_csv(ddos_file, nrows=50000)
    
    df_attacks = df[df[' Label'].str.strip() != 'BENIGN']
    df_benign = df[df[' Label'].str.strip() == 'BENIGN']
    
    print(f"  Loaded {len(df_attacks)} attack samples")
    print(f"  Loaded {len(df_benign)} benign samples")
    
    print(f"\n📊 Sending {num_samples} samples ({int(attack_ratio*100)}% attacks)")
    print("   Watch the dashboard at http://localhost:80")
    print("-" * 60)
    
    stats = {"total": 0, "attacks": 0, "benign": 0, "detected": 0}
    
    for i in range(num_samples):
        # Decide if attack or benign
        is_attack = random.random() < attack_ratio
        
        if is_attack and len(df_attacks) > 0:
            sample = df_attacks.sample(1).iloc[0]
            expected = "malicious"
            label = "DDoS"
        else:
            sample = df_benign.sample(1).iloc[0]
            expected = "benign"
            label = "BENIGN"
        
        # Convert to dict and run prediction
        flow_dict = sample.drop(' Label').to_dict()
        
        try:
            result = inf.predict_single_flow(flow_dict)
            
            prediction = result['prediction']
            score = result['ensemble_score']
            
            stats["total"] += 1
            
            if expected == "malicious":
                stats["attacks"] += 1
                if prediction == "malicious":
                    stats["detected"] += 1
                    status = "✅ DETECTED"
                else:
                    status = "❌ MISSED"
            else:
                stats["benign"] += 1
                status = "✅ CORRECT" if prediction == "benign" else "⚠️ FP"
            
            # Publish to Redis for dashboard
            if r:
                event = {
                    "prediction": prediction.upper(),
                    "ensemble_score": score,
                    "xgb_score": result['xgb_score'],
                    "timestamp": datetime.now().isoformat(),
                    "risk_level": "HIGH" if score > 0.7 else "MEDIUM" if score > 0.4 else "LOW"
                }
                r.publish('firewall_events', json.dumps(event))
            
            # Print every attack or every 5th benign
            if is_attack or (i + 1) % 5 == 0:
                print(f"[{i+1:3d}/{num_samples}] {label:8s} → {prediction:9s} (score: {score:.3f}) {status}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        # Small delay
        time.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total:     {stats['total']}")
    print(f"Attacks:   {stats['attacks']}")
    print(f"Benign:    {stats['benign']}")
    print(f"Detected:  {stats['detected']}/{stats['attacks']} ({100*stats['detected']/max(stats['attacks'],1):.1f}%)")
    print("\n✅ Test complete! Check the dashboard.")

if __name__ == "__main__":
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    ratio = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
    run_test(num, ratio)
