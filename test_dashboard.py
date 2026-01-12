"""
Test script om echte attacks en benign traffic te simuleren voor het dashboard.
Dit stuurt data naar de API en publiceert naar Redis zodat het dashboard het kan tonen.
"""

import requests
import pandas as pd
import time
import json
import redis
import random
from datetime import datetime

API_URL = "http://localhost:8000"
REDIS_URL = "redis://localhost:6379"

def load_test_data():
    """Laad echte DDoS en Benign data uit de CIC-IDS2017 dataset"""
    print("Loading test data from CIC-IDS2017 dataset...")
    
    # Load DDoS attacks
    ddos_file = "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
    df_ddos = pd.read_csv(ddos_file, nrows=50000)
    
    # Get actual DDoS attacks (not benign)
    df_attacks = df_ddos[df_ddos[' Label'].str.strip() != 'BENIGN']
    df_benign = df_ddos[df_ddos[' Label'].str.strip() == 'BENIGN']
    
    print(f"  Loaded {len(df_attacks)} DDoS attack samples")
    print(f"  Loaded {len(df_benign)} benign samples")
    
    return df_attacks, df_benign

def convert_row_to_api_format(row):
    """Convert een DataFrame row naar het API format"""
    # Strip column names en convert naar dict
    data = {}
    for col in row.index:
        if col.strip() == 'Label':
            continue
        clean_col = col.strip().lower().replace(' ', '_').replace('/', '_')
        value = row[col]
        # Handle NaN/Inf values
        if pd.isna(value) or value == float('inf') or value == float('-inf'):
            value = 0
        data[clean_col] = float(value)
    return data

def send_to_api(flow_data):
    """Stuur flow data naar de API"""
    try:
        response = requests.post(
            f"{API_URL}/predict",
            json=flow_data,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"API error: {e}")
        return None

def publish_to_redis(result, redis_client):
    """Publiceer resultaat naar Redis voor WebSocket dashboard"""
    try:
        event = {
            "prediction": result.get("prediction", "UNKNOWN").upper(),
            "ensemble_score": result.get("ensemble_score", 0),
            "xgb_score": result.get("xgb_score", 0),
            "timestamp": result.get("timestamp", datetime.now().isoformat()),
            "risk_level": result.get("risk_level", "UNKNOWN")
        }
        redis_client.publish('firewall_events', json.dumps(event))
        return True
    except Exception as e:
        print(f"Redis error: {e}")
        return False

def run_test(num_samples=50, attack_ratio=0.3):
    """
    Run de test met een mix van attacks en benign traffic
    
    Args:
        num_samples: Totaal aantal samples om te sturen
        attack_ratio: Fractie van samples die attacks moeten zijn (0-1)
    """
    print("=" * 60)
    print("AI-FIREWALL DASHBOARD TEST")
    print("=" * 60)
    
    # Load data
    df_attacks, df_benign = load_test_data()
    
    # Connect to Redis
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Dashboard won't receive real-time updates")
        r = None
    
    # Check API health
    try:
        resp = requests.get(f"{API_URL}/health")
        if resp.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"⚠️ API returned status {resp.status_code}")
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return
    
    print(f"\n📊 Sending {num_samples} samples ({int(attack_ratio*100)}% attacks)")
    print("   Watch the dashboard at http://localhost:80")
    print("-" * 60)
    
    stats = {"total": 0, "attacks": 0, "benign": 0, "detected": 0, "missed": 0}
    
    for i in range(num_samples):
        # Decide if this should be an attack or benign
        is_attack = random.random() < attack_ratio
        
        if is_attack and len(df_attacks) > 0:
            sample = df_attacks.sample(1).iloc[0]
            expected = "malicious"
            label = "DDoS"
        else:
            sample = df_benign.sample(1).iloc[0]
            expected = "benign"
            label = "BENIGN"
        
        # Convert to API format
        flow_data = convert_row_to_api_format(sample)
        
        # Send to API
        result = send_to_api(flow_data)
        
        if result:
            stats["total"] += 1
            prediction = result.get("prediction", "unknown")
            score = result.get("ensemble_score", 0)
            
            # Track accuracy
            if expected == "malicious":
                stats["attacks"] += 1
                if prediction == "malicious":
                    stats["detected"] += 1
                    status = "✅ DETECTED"
                else:
                    stats["missed"] += 1
                    status = "❌ MISSED"
            else:
                stats["benign"] += 1
                if prediction == "benign":
                    status = "✅ CORRECT"
                else:
                    status = "⚠️ FALSE POSITIVE"
            
            # Publish to Redis for dashboard
            if r:
                publish_to_redis(result, r)
            
            # Print progress
            if (i + 1) % 5 == 0 or is_attack:
                print(f"[{i+1:3d}/{num_samples}] {label:8s} → {prediction:9s} (score: {score:.3f}) {status}")
        
        # Small delay to not overwhelm the system
        time.sleep(0.2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total samples:     {stats['total']}")
    print(f"Attack samples:    {stats['attacks']}")
    print(f"Benign samples:    {stats['benign']}")
    print(f"Attacks detected:  {stats['detected']}/{stats['attacks']} ({100*stats['detected']/max(stats['attacks'],1):.1f}%)")
    print(f"Attacks missed:    {stats['missed']}/{stats['attacks']}")
    print("\n✅ Test complete! Check the dashboard at http://localhost:80")

if __name__ == "__main__":
    import sys
    
    # Parse arguments
    num_samples = 50
    attack_ratio = 0.3
    
    if len(sys.argv) > 1:
        num_samples = int(sys.argv[1])
    if len(sys.argv) > 2:
        attack_ratio = float(sys.argv[2])
    
    run_test(num_samples, attack_ratio)
