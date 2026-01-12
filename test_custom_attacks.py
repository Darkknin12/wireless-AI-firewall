#!/usr/bin/env python3
"""
Test with custom crafted attacks - NO CSV data!
Creates simulated network flows that should trigger detection
"""

import requests
import time
import random
import json

API_URL = "http://localhost:8000"

# Attack patterns - manually crafted to test detection
CUSTOM_ATTACKS = {
    "DDoS Attack": {
        " Destination Port": 80,
        " Flow Duration": 1000,  # Very short
        " Total Fwd Packets": 50000,  # Many packets
        " Total Backward Packets": 100,
        " Total Length of Fwd Packets": 5000000,
        " Total Length of Bwd Packets": 1000,
        " Fwd Packet Length Max": 100,
        " Fwd Packet Length Min": 60,
        " Fwd Packet Length Mean": 80,
        " Fwd Packet Length Std": 10,
        " Bwd Packet Length Max": 60,
        " Bwd Packet Length Min": 40,
        " Bwd Packet Length Mean": 50,
        " Bwd Packet Length Std": 5,
        " Flow Bytes/s": 5000000000,  # Very high
        " Flow Packets/s": 50000000,  # Very high
        " Flow IAT Mean": 0.02,  # Very low IAT
        " Flow IAT Std": 0.01,
        " Flow IAT Max": 0.1,
        " Flow IAT Min": 0.001,
        " Fwd IAT Total": 1000,
        " Fwd IAT Mean": 0.02,
        " Fwd IAT Std": 0.01,
        " Fwd IAT Max": 0.1,
        " Fwd IAT Min": 0.001,
        " Bwd IAT Total": 500,
        " Bwd IAT Mean": 5,
        " Bwd IAT Std": 2,
        " Bwd IAT Max": 10,
        " Bwd IAT Min": 1,
        " Fwd PSH Flags": 1,
        " Bwd PSH Flags": 0,
        " Fwd URG Flags": 0,
        " Bwd URG Flags": 0,
        " Fwd Header Length": 1000000,
        " Bwd Header Length": 2000,
        " Fwd Packets/s": 50000,  # High packet rate
        " Bwd Packets/s": 100,
        " Min Packet Length": 40,
        " Max Packet Length": 100,
        " Packet Length Mean": 70,
        " Packet Length Std": 20,
        " Packet Length Variance": 400,
        " FIN Flag Count": 0,
        " SYN Flag Count": 50000,  # Many SYN (DDoS pattern)
        " RST Flag Count": 0,
        " PSH Flag Count": 1,
        " ACK Flag Count": 100,
        " URG Flag Count": 0,
        " CWE Flag Count": 0,
        " ECE Flag Count": 0,
        " Down/Up Ratio": 0.002,
        " Average Packet Size": 70,
        " Avg Fwd Segment Size": 80,
        " Avg Bwd Segment Size": 50,
        " Fwd Header Length.1": 1000000,
        " Fwd Avg Bytes/Bulk": 0,
        " Fwd Avg Packets/Bulk": 0,
        " Fwd Avg Bulk Rate": 0,
        " Bwd Avg Bytes/Bulk": 0,
        " Bwd Avg Packets/Bulk": 0,
        " Bwd Avg Bulk Rate": 0,
        " Subflow Fwd Packets": 50000,
        " Subflow Fwd Bytes": 5000000,
        " Subflow Bwd Packets": 100,
        " Subflow Bwd Bytes": 1000,
        " Init_Win_bytes_forward": 8192,
        " Init_Win_bytes_backward": 0,
        " act_data_pkt_fwd": 50000,
        " min_seg_size_forward": 20,
        " Active Mean": 100,
        " Active Std": 50,
        " Active Max": 200,
        " Active Min": 10,
        " Idle Mean": 10,
        " Idle Std": 5,
        " Idle Max": 20,
        " Idle Min": 1,
    },
    "Port Scan": {
        " Destination Port": 22,  # SSH
        " Flow Duration": 100,  # Very short probes
        " Total Fwd Packets": 2,  # Few packets per probe
        " Total Backward Packets": 0,  # No response (closed ports)
        " Total Length of Fwd Packets": 120,
        " Total Length of Bwd Packets": 0,
        " Fwd Packet Length Max": 60,
        " Fwd Packet Length Min": 60,
        " Fwd Packet Length Mean": 60,
        " Fwd Packet Length Std": 0,
        " Bwd Packet Length Max": 0,
        " Bwd Packet Length Min": 0,
        " Bwd Packet Length Mean": 0,
        " Bwd Packet Length Std": 0,
        " Flow Bytes/s": 1200000,
        " Flow Packets/s": 20000,
        " Flow IAT Mean": 50,
        " Flow IAT Std": 10,
        " Flow IAT Max": 100,
        " Flow IAT Min": 1,
        " Fwd IAT Total": 100,
        " Fwd IAT Mean": 50,
        " Fwd IAT Std": 10,
        " Fwd IAT Max": 100,
        " Fwd IAT Min": 1,
        " Bwd IAT Total": 0,
        " Bwd IAT Mean": 0,
        " Bwd IAT Std": 0,
        " Bwd IAT Max": 0,
        " Bwd IAT Min": 0,
        " Fwd PSH Flags": 0,
        " Bwd PSH Flags": 0,
        " Fwd URG Flags": 0,
        " Bwd URG Flags": 0,
        " Fwd Header Length": 40,
        " Bwd Header Length": 0,
        " Fwd Packets/s": 20000,
        " Bwd Packets/s": 0,
        " Min Packet Length": 60,
        " Max Packet Length": 60,
        " Packet Length Mean": 60,
        " Packet Length Std": 0,
        " Packet Length Variance": 0,
        " FIN Flag Count": 0,
        " SYN Flag Count": 2,  # SYN scan
        " RST Flag Count": 0,
        " PSH Flag Count": 0,
        " ACK Flag Count": 0,
        " URG Flag Count": 0,
        " CWE Flag Count": 0,
        " ECE Flag Count": 0,
        " Down/Up Ratio": 0,
        " Average Packet Size": 60,
        " Avg Fwd Segment Size": 60,
        " Avg Bwd Segment Size": 0,
        " Fwd Header Length.1": 40,
        " Fwd Avg Bytes/Bulk": 0,
        " Fwd Avg Packets/Bulk": 0,
        " Fwd Avg Bulk Rate": 0,
        " Bwd Avg Bytes/Bulk": 0,
        " Bwd Avg Packets/Bulk": 0,
        " Bwd Avg Bulk Rate": 0,
        " Subflow Fwd Packets": 2,
        " Subflow Fwd Bytes": 120,
        " Subflow Bwd Packets": 0,
        " Subflow Bwd Bytes": 0,
        " Init_Win_bytes_forward": 1024,
        " Init_Win_bytes_backward": 0,
        " act_data_pkt_fwd": 0,
        " min_seg_size_forward": 20,
        " Active Mean": 0,
        " Active Std": 0,
        " Active Max": 0,
        " Active Min": 0,
        " Idle Mean": 0,
        " Idle Std": 0,
        " Idle Max": 0,
        " Idle Min": 0,
    },
    "Brute Force SSH": {
        " Destination Port": 22,
        " Flow Duration": 5000000,  # Longer session
        " Total Fwd Packets": 100,  # Multiple login attempts
        " Total Backward Packets": 100,
        " Total Length of Fwd Packets": 15000,
        " Total Length of Bwd Packets": 20000,
        " Fwd Packet Length Max": 500,
        " Fwd Packet Length Min": 40,
        " Fwd Packet Length Mean": 150,
        " Fwd Packet Length Std": 100,
        " Bwd Packet Length Max": 600,
        " Bwd Packet Length Min": 40,
        " Bwd Packet Length Mean": 200,
        " Bwd Packet Length Std": 150,
        " Flow Bytes/s": 7000,
        " Flow Packets/s": 40,
        " Flow IAT Mean": 50000,
        " Flow IAT Std": 20000,
        " Flow IAT Max": 100000,
        " Flow IAT Min": 1000,
        " Fwd IAT Total": 2500000,
        " Fwd IAT Mean": 25000,
        " Fwd IAT Std": 10000,
        " Fwd IAT Max": 50000,
        " Fwd IAT Min": 500,
        " Bwd IAT Total": 2500000,
        " Bwd IAT Mean": 25000,
        " Bwd IAT Std": 10000,
        " Bwd IAT Max": 50000,
        " Bwd IAT Min": 500,
        " Fwd PSH Flags": 1,
        " Bwd PSH Flags": 1,
        " Fwd URG Flags": 0,
        " Bwd URG Flags": 0,
        " Fwd Header Length": 4000,
        " Bwd Header Length": 4000,
        " Fwd Packets/s": 20,
        " Bwd Packets/s": 20,
        " Min Packet Length": 40,
        " Max Packet Length": 600,
        " Packet Length Mean": 175,
        " Packet Length Std": 125,
        " Packet Length Variance": 15625,
        " FIN Flag Count": 2,
        " SYN Flag Count": 2,
        " RST Flag Count": 0,
        " PSH Flag Count": 80,
        " ACK Flag Count": 100,
        " URG Flag Count": 0,
        " CWE Flag Count": 0,
        " ECE Flag Count": 0,
        " Down/Up Ratio": 1,
        " Average Packet Size": 175,
        " Avg Fwd Segment Size": 150,
        " Avg Bwd Segment Size": 200,
        " Fwd Header Length.1": 4000,
        " Fwd Avg Bytes/Bulk": 0,
        " Fwd Avg Packets/Bulk": 0,
        " Fwd Avg Bulk Rate": 0,
        " Bwd Avg Bytes/Bulk": 0,
        " Bwd Avg Packets/Bulk": 0,
        " Bwd Avg Bulk Rate": 0,
        " Subflow Fwd Packets": 100,
        " Subflow Fwd Bytes": 15000,
        " Subflow Bwd Packets": 100,
        " Subflow Bwd Bytes": 20000,
        " Init_Win_bytes_forward": 65535,
        " Init_Win_bytes_backward": 65535,
        " act_data_pkt_fwd": 50,
        " min_seg_size_forward": 20,
        " Active Mean": 100000,
        " Active Std": 50000,
        " Active Max": 200000,
        " Active Min": 10000,
        " Idle Mean": 500000,
        " Idle Std": 200000,
        " Idle Max": 1000000,
        " Idle Min": 100000,
    },
    "SQL Injection": {
        " Destination Port": 3306,  # MySQL
        " Flow Duration": 100000,
        " Total Fwd Packets": 10,
        " Total Backward Packets": 15,
        " Total Length of Fwd Packets": 5000,  # Larger payloads (SQL queries)
        " Total Length of Bwd Packets": 50000,  # Large data exfiltration
        " Fwd Packet Length Max": 1500,
        " Fwd Packet Length Min": 100,
        " Fwd Packet Length Mean": 500,
        " Fwd Packet Length Std": 400,
        " Bwd Packet Length Max": 15000,
        " Bwd Packet Length Min": 100,
        " Bwd Packet Length Mean": 3333,
        " Bwd Packet Length Std": 4000,
        " Flow Bytes/s": 550000,
        " Flow Packets/s": 250,
        " Flow IAT Mean": 4000,
        " Flow IAT Std": 2000,
        " Flow IAT Max": 10000,
        " Flow IAT Min": 500,
        " Fwd IAT Total": 50000,
        " Fwd IAT Mean": 5000,
        " Fwd IAT Std": 2000,
        " Fwd IAT Max": 10000,
        " Fwd IAT Min": 500,
        " Bwd IAT Total": 50000,
        " Bwd IAT Mean": 3333,
        " Bwd IAT Std": 1500,
        " Bwd IAT Max": 7000,
        " Bwd IAT Min": 300,
        " Fwd PSH Flags": 1,
        " Bwd PSH Flags": 1,
        " Fwd URG Flags": 0,
        " Bwd URG Flags": 0,
        " Fwd Header Length": 400,
        " Bwd Header Length": 600,
        " Fwd Packets/s": 100,
        " Bwd Packets/s": 150,
        " Min Packet Length": 100,
        " Max Packet Length": 15000,
        " Packet Length Mean": 2200,
        " Packet Length Std": 3500,
        " Packet Length Variance": 12250000,
        " FIN Flag Count": 2,
        " SYN Flag Count": 2,
        " RST Flag Count": 0,
        " PSH Flag Count": 20,
        " ACK Flag Count": 25,
        " URG Flag Count": 0,
        " CWE Flag Count": 0,
        " ECE Flag Count": 0,
        " Down/Up Ratio": 10,  # Much more data coming back
        " Average Packet Size": 2200,
        " Avg Fwd Segment Size": 500,
        " Avg Bwd Segment Size": 3333,
        " Fwd Header Length.1": 400,
        " Fwd Avg Bytes/Bulk": 0,
        " Fwd Avg Packets/Bulk": 0,
        " Fwd Avg Bulk Rate": 0,
        " Bwd Avg Bytes/Bulk": 0,
        " Bwd Avg Packets/Bulk": 0,
        " Bwd Avg Bulk Rate": 0,
        " Subflow Fwd Packets": 10,
        " Subflow Fwd Bytes": 5000,
        " Subflow Bwd Packets": 15,
        " Subflow Bwd Bytes": 50000,
        " Init_Win_bytes_forward": 65535,
        " Init_Win_bytes_backward": 65535,
        " act_data_pkt_fwd": 10,
        " min_seg_size_forward": 20,
        " Active Mean": 50000,
        " Active Std": 20000,
        " Active Max": 100000,
        " Active Min": 10000,
        " Idle Mean": 0,
        " Idle Std": 0,
        " Idle Max": 0,
        " Idle Min": 0,
    }
}

# Benign traffic patterns
BENIGN_PATTERNS = {
    "Web Browsing": {
        " Destination Port": 443,
        " Flow Duration": 300000,
        " Total Fwd Packets": 20,
        " Total Backward Packets": 30,
        " Total Length of Fwd Packets": 3000,
        " Total Length of Bwd Packets": 150000,
        " Fwd Packet Length Max": 500,
        " Fwd Packet Length Min": 40,
        " Fwd Packet Length Mean": 150,
        " Fwd Packet Length Std": 100,
        " Bwd Packet Length Max": 15000,
        " Bwd Packet Length Min": 40,
        " Bwd Packet Length Mean": 5000,
        " Bwd Packet Length Std": 4000,
        " Flow Bytes/s": 510000,
        " Flow Packets/s": 166,
        " Flow IAT Mean": 6000,
        " Flow IAT Std": 5000,
        " Flow IAT Max": 50000,
        " Flow IAT Min": 100,
        " Fwd IAT Total": 150000,
        " Fwd IAT Mean": 7500,
        " Fwd IAT Std": 5000,
        " Fwd IAT Max": 30000,
        " Fwd IAT Min": 500,
        " Bwd IAT Total": 150000,
        " Bwd IAT Mean": 5000,
        " Bwd IAT Std": 3000,
        " Bwd IAT Max": 20000,
        " Bwd IAT Min": 200,
        " Fwd PSH Flags": 1,
        " Bwd PSH Flags": 1,
        " Fwd URG Flags": 0,
        " Bwd URG Flags": 0,
        " Fwd Header Length": 800,
        " Bwd Header Length": 1200,
        " Fwd Packets/s": 66,
        " Bwd Packets/s": 100,
        " Min Packet Length": 40,
        " Max Packet Length": 15000,
        " Packet Length Mean": 3060,
        " Packet Length Std": 4500,
        " Packet Length Variance": 20250000,
        " FIN Flag Count": 2,
        " SYN Flag Count": 2,
        " RST Flag Count": 0,
        " PSH Flag Count": 30,
        " ACK Flag Count": 50,
        " URG Flag Count": 0,
        " CWE Flag Count": 0,
        " ECE Flag Count": 0,
        " Down/Up Ratio": 50,
        " Average Packet Size": 3060,
        " Avg Fwd Segment Size": 150,
        " Avg Bwd Segment Size": 5000,
        " Fwd Header Length.1": 800,
        " Fwd Avg Bytes/Bulk": 0,
        " Fwd Avg Packets/Bulk": 0,
        " Fwd Avg Bulk Rate": 0,
        " Bwd Avg Bytes/Bulk": 0,
        " Bwd Avg Packets/Bulk": 0,
        " Bwd Avg Bulk Rate": 0,
        " Subflow Fwd Packets": 20,
        " Subflow Fwd Bytes": 3000,
        " Subflow Bwd Packets": 30,
        " Subflow Bwd Bytes": 150000,
        " Init_Win_bytes_forward": 65535,
        " Init_Win_bytes_backward": 65535,
        " act_data_pkt_fwd": 15,
        " min_seg_size_forward": 20,
        " Active Mean": 100000,
        " Active Std": 50000,
        " Active Max": 200000,
        " Active Min": 20000,
        " Idle Mean": 100000,
        " Idle Std": 50000,
        " Idle Max": 200000,
        " Idle Min": 20000,
    },
    "DNS Query": {
        " Destination Port": 53,
        " Flow Duration": 50000,
        " Total Fwd Packets": 2,
        " Total Backward Packets": 2,
        " Total Length of Fwd Packets": 80,
        " Total Length of Bwd Packets": 200,
        " Fwd Packet Length Max": 60,
        " Fwd Packet Length Min": 40,
        " Fwd Packet Length Mean": 40,
        " Fwd Packet Length Std": 10,
        " Bwd Packet Length Max": 150,
        " Bwd Packet Length Min": 50,
        " Bwd Packet Length Mean": 100,
        " Bwd Packet Length Std": 50,
        " Flow Bytes/s": 5600,
        " Flow Packets/s": 80,
        " Flow IAT Mean": 12500,
        " Flow IAT Std": 5000,
        " Flow IAT Max": 25000,
        " Flow IAT Min": 1000,
        " Fwd IAT Total": 25000,
        " Fwd IAT Mean": 12500,
        " Fwd IAT Std": 5000,
        " Fwd IAT Max": 25000,
        " Fwd IAT Min": 1000,
        " Bwd IAT Total": 25000,
        " Bwd IAT Mean": 12500,
        " Bwd IAT Std": 5000,
        " Bwd IAT Max": 25000,
        " Bwd IAT Min": 1000,
        " Fwd PSH Flags": 0,
        " Bwd PSH Flags": 0,
        " Fwd URG Flags": 0,
        " Bwd URG Flags": 0,
        " Fwd Header Length": 80,
        " Bwd Header Length": 80,
        " Fwd Packets/s": 40,
        " Bwd Packets/s": 40,
        " Min Packet Length": 40,
        " Max Packet Length": 150,
        " Packet Length Mean": 70,
        " Packet Length Std": 40,
        " Packet Length Variance": 1600,
        " FIN Flag Count": 0,
        " SYN Flag Count": 0,
        " RST Flag Count": 0,
        " PSH Flag Count": 0,
        " ACK Flag Count": 0,
        " URG Flag Count": 0,
        " CWE Flag Count": 0,
        " ECE Flag Count": 0,
        " Down/Up Ratio": 2.5,
        " Average Packet Size": 70,
        " Avg Fwd Segment Size": 40,
        " Avg Bwd Segment Size": 100,
        " Fwd Header Length.1": 80,
        " Fwd Avg Bytes/Bulk": 0,
        " Fwd Avg Packets/Bulk": 0,
        " Fwd Avg Bulk Rate": 0,
        " Bwd Avg Bytes/Bulk": 0,
        " Bwd Avg Packets/Bulk": 0,
        " Bwd Avg Bulk Rate": 0,
        " Subflow Fwd Packets": 2,
        " Subflow Fwd Bytes": 80,
        " Subflow Bwd Packets": 2,
        " Subflow Bwd Bytes": 200,
        " Init_Win_bytes_forward": 65535,
        " Init_Win_bytes_backward": 65535,
        " act_data_pkt_fwd": 1,
        " min_seg_size_forward": 20,
        " Active Mean": 25000,
        " Active Std": 10000,
        " Active Max": 50000,
        " Active Min": 5000,
        " Idle Mean": 0,
        " Idle Std": 0,
        " Idle Max": 0,
        " Idle Min": 0,
    }
}


def generate_random_ip():
    """Generate random IP address"""
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def send_flow(flow_data, attack_type, src_ip, dst_ip, is_attack=True):
    """Send a flow to the API"""
    try:
        # Add IP info to the flow
        flow_data["src_ip"] = src_ip
        flow_data["dst_ip"] = dst_ip
        flow_data["attack_type"] = attack_type if is_attack else "BENIGN"
        
        # Use /predict/raw endpoint for full flow data
        response = requests.post(
            f"{API_URL}/predict/raw",
            json=flow_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"  ❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return None


def main():
    print("=" * 60)
    print("AI-FIREWALL CUSTOM ATTACK TEST")
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
    
    # Send attacks
    print("\n🔴 SENDING ATTACK TRAFFIC:")
    for attack_name, attack_data in CUSTOM_ATTACKS.items():
        # Send 3 instances of each attack
        for i in range(3):
            src_ip = generate_random_ip()
            dst_ip = "192.168.1.100"  # Target
            
            # Add some variation
            variation = attack_data.copy()
            for key in variation:
                if isinstance(variation[key], (int, float)) and key != " Destination Port":
                    variation[key] *= random.uniform(0.8, 1.2)
            
            result = send_flow(variation, attack_name, src_ip, dst_ip, is_attack=True)
            total_attacks += 1
            
            if result:
                pred = result.get("prediction", "UNKNOWN")
                score = result.get("ensemble_score", 0)
                
                if pred == "MALICIOUS":
                    detected += 1
                    print(f"  ✅ {attack_name} [{i+1}/3] → DETECTED (score: {score:.3f})")
                else:
                    print(f"  ❌ {attack_name} [{i+1}/3] → MISSED (score: {score:.3f})")
            
            time.sleep(0.3)
    
    # Send benign traffic
    print("\n🟢 SENDING BENIGN TRAFFIC:")
    for benign_name, benign_data in BENIGN_PATTERNS.items():
        for i in range(3):
            src_ip = "192.168.1." + str(random.randint(10, 50))
            dst_ip = generate_random_ip()
            
            variation = benign_data.copy()
            for key in variation:
                if isinstance(variation[key], (int, float)) and key != " Destination Port":
                    variation[key] *= random.uniform(0.8, 1.2)
            
            result = send_flow(variation, benign_name, src_ip, dst_ip, is_attack=False)
            total_benign += 1
            
            if result:
                pred = result.get("prediction", "UNKNOWN")
                score = result.get("ensemble_score", 0)
                
                if pred == "BENIGN":
                    correct_benign += 1
                    print(f"  ✅ {benign_name} [{i+1}/3] → BENIGN (score: {score:.3f})")
                else:
                    print(f"  ⚠️ {benign_name} [{i+1}/3] → False Positive (score: {score:.3f})")
            
            time.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Attacks:  {detected}/{total_attacks} detected ({100*detected/total_attacks:.1f}%)")
    print(f"Benign:   {correct_benign}/{total_benign} correct ({100*correct_benign/total_benign:.1f}%)")
    print("\n✅ Check the dashboard for attack types!")


if __name__ == "__main__":
    main()
