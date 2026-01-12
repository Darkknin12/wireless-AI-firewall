#!/usr/bin/env python3
"""
Test with REAL CIC-IDS2017 data - shows attack types on dashboard
Uses actual attack samples from the dataset with labeled attack types
"""

import requests
import time
import random
import pandas as pd
import os

API_URL = "http://localhost:8000"

# Mapping van CSV files naar attack types
# Use Windows paths for local execution
ATTACK_FILES = {
    "DDoS Attack": "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
    "Port Scan": "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
    "Web Attack (XSS/SQL)": "ml_data/MachineLearningCVE/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    "Infiltration": "ml_data/MachineLearningCVE/Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
}

BENIGN_FILE = "ml_data/MachineLearningCVE/Monday-WorkingHours.pcap_ISCX.csv"


def generate_random_ip():
    """Generate random IP address"""
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def load_samples(file_path, label_filter=None, n_samples=5):
    """Load samples from CSV"""
    try:
        df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
        
        # Strip column names
        df.columns = [col.strip() for col in df.columns]
        
        # Filter by label if specified
        if label_filter:
            if label_filter == "attack":
                df = df[df['Label'] != 'BENIGN']
            else:
                df = df[df['Label'] == 'BENIGN']
        
        if len(df) == 0:
            return []
        
        # Sample random rows
        samples = df.sample(n=min(n_samples, len(df)))
        return samples.to_dict('records')
    except Exception as e:
        print(f"  Error loading {file_path}: {e}")
        return []


def send_flow(flow_data, attack_type, is_attack=True):
    """Send a flow to the API"""
    try:
        # Extract source/dest info from the data
        src_ip = flow_data.get('Source IP', generate_random_ip())
        dst_ip = flow_data.get('Destination IP', generate_random_ip())
        src_port = flow_data.get('Source Port', 0)
        dst_port = flow_data.get('Destination Port', 0)
        
        # Remove non-feature columns
        for col in ['Label', 'Source IP', 'Destination IP', 'Flow ID', 'Timestamp']:
            if col in flow_data:
                del flow_data[col]
        
        # Add metadata for dashboard
        flow_data["src_ip"] = str(src_ip)
        flow_data["dst_ip"] = str(dst_ip)
        flow_data["attack_type"] = attack_type if is_attack else "BENIGN"
        
        # Use /predict/raw endpoint
        response = requests.post(
            f"{API_URL}/predict/raw",
            json=flow_data,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ❌ Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return None


def main():
    print("=" * 60)
    print("AI-FIREWALL REAL ATTACK TEST")
    print("Uses actual CIC-IDS2017 data with attack type labels")
    print("=" * 60)
    
    # Check API health
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is online")
        else:
            print("❌ API not healthy")
            return
    except:
        print("❌ Cannot connect to API")
        return
    
    print("\n📡 Watch the dashboard at http://localhost:80")
    print("-" * 60)
    
    detected = 0
    total_attacks = 0
    correct_benign = 0
    total_benign = 0
    
    samples_per_type = 5
    
    # Send attacks from different files
    print("\n🔴 SENDING ATTACK TRAFFIC (REAL DATA):")
    for attack_type, file_path in ATTACK_FILES.items():
        print(f"\n  Loading {attack_type}...")
        samples = load_samples(file_path, label_filter="attack", n_samples=samples_per_type)
        
        if not samples:
            print(f"    ⚠️ No samples found")
            continue
        
        for i, sample in enumerate(samples):
            result = send_flow(sample.copy(), attack_type, is_attack=True)
            total_attacks += 1
            
            if result:
                pred = result.get("prediction", "UNKNOWN").upper()
                score = result.get("ensemble_score", 0)
                
                if pred == "MALICIOUS":
                    detected += 1
                    print(f"    ✅ {attack_type} [{i+1}/{len(samples)}] → DETECTED (score: {score:.3f})")
                else:
                    print(f"    ❌ {attack_type} [{i+1}/{len(samples)}] → MISSED (score: {score:.3f})")
            
            time.sleep(0.3)
    
    # Send benign traffic
    print("\n🟢 SENDING BENIGN TRAFFIC (REAL DATA):")
    samples = load_samples(BENIGN_FILE, label_filter="benign", n_samples=10)
    
    for i, sample in enumerate(samples):
        result = send_flow(sample.copy(), "Normal Traffic", is_attack=False)
        total_benign += 1
        
        if result:
            pred = result.get("prediction", "UNKNOWN").upper()
            score = result.get("ensemble_score", 0)
            
            if pred == "BENIGN":
                correct_benign += 1
                print(f"  ✅ Normal Traffic [{i+1}/{len(samples)}] → BENIGN (score: {score:.3f})")
            else:
                print(f"  ⚠️ Normal Traffic [{i+1}/{len(samples)}] → False Positive (score: {score:.3f})")
        
        time.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    if total_attacks > 0:
        print(f"Attacks:  {detected}/{total_attacks} detected ({100*detected/total_attacks:.1f}%)")
    if total_benign > 0:
        print(f"Benign:   {correct_benign}/{total_benign} correct ({100*correct_benign/total_benign:.1f}%)")
    print("\n✅ Check the dashboard for attack types!")


if __name__ == "__main__":
    main()
