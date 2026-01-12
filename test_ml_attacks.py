"""
Test script voor ML Model Attack Detection
Test of de AI-Firewall correct malicious traffic detecteert
"""

import pandas as pd
import sys
sys.path.insert(0, '.')

from inference import AIFirewallInference

def test_attacks():
    print("=" * 60)
    print("AI-FIREWALL ML MODEL - ATTACK DETECTION TEST")
    print("=" * 60)
    
    # Initialize
    inf = AIFirewallInference()
    
    # Test cases met originele column names (zoals in training data)
    test_cases = [
        {
            "name": "Normal HTTPS Browsing (Should be BENIGN)",
            "flow": {
                " Destination Port": 443,
                " Flow Duration": 5000000,
                " Total Fwd Packets": 10,
                " Total Backward Packets": 8,
                "Flow Bytes/s": 1000.0,
                " Flow Packets/s": 3.0,
            },
            "expected": "benign"
        },
        {
            "name": "DDoS Attack - High Packet Flood (Should be MALICIOUS)",
            "flow": {
                " Destination Port": 80,
                " Flow Duration": 1000,
                " Total Fwd Packets": 100000,
                " Total Backward Packets": 10,
                "Flow Bytes/s": 100000000.0,
                " Flow Packets/s": 100000.0,
            },
            "expected": "malicious"
        },
        {
            "name": "Port Scan - Many Different Ports (Should be MALICIOUS)",
            "flow": {
                " Destination Port": 22,
                " Flow Duration": 100,
                " Total Fwd Packets": 1,
                " Total Backward Packets": 0,
                "Flow Bytes/s": 5000.0,
                " Flow Packets/s": 100.0,
            },
            "expected": "malicious"
        },
        {
            "name": "SSH Brute Force - Many Failed Logins (Should be MALICIOUS)",
            "flow": {
                " Destination Port": 22,
                " Flow Duration": 500000,
                " Total Fwd Packets": 1000,
                " Total Backward Packets": 1000,
                "Flow Bytes/s": 50000.0,
                " Flow Packets/s": 2000.0,
            },
            "expected": "malicious"
        },
        {
            "name": "Wireless Deauth Flood Pattern (Should be MALICIOUS)",
            "flow": {
                " Destination Port": 0,
                " Flow Duration": 100,
                " Total Fwd Packets": 50000,
                " Total Backward Packets": 0,
                "Flow Bytes/s": 1000000.0,
                " Flow Packets/s": 50000.0,
            },
            "expected": "malicious"
        },
        {
            "name": "IoT Botnet C&C Communication (Should be MALICIOUS)",
            "flow": {
                " Destination Port": 4444,
                " Flow Duration": 10000000,
                " Total Fwd Packets": 50,
                " Total Backward Packets": 100,
                "Flow Bytes/s": 500.0,
                " Flow Packets/s": 0.015,
            },
            "expected": "malicious"
        },
        {
            "name": "Normal Video Streaming (Should be BENIGN)",
            "flow": {
                " Destination Port": 443,
                " Flow Duration": 60000000,
                " Total Fwd Packets": 100,
                " Total Backward Packets": 5000,
                "Flow Bytes/s": 5000000.0,
                " Flow Packets/s": 85.0,
            },
            "expected": "benign"
        },
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test['name']} ---")
        
        try:
            result = inf.predict_single_flow(test["flow"])
            
            prediction = result["prediction"]
            xgb_score = result["xgb_score"]
            if_score = result["if_score"]
            ensemble = result["ensemble_score"]
            
            correct = prediction == test["expected"]
            status = "✅ CORRECT" if correct else "❌ WRONG"
            
            print(f"  Prediction: {prediction.upper()}")
            print(f"  Expected:   {test['expected'].upper()}")
            print(f"  XGB Score:  {xgb_score:.4f}")
            print(f"  IF Score:   {if_score:.4f}")
            print(f"  Ensemble:   {ensemble:.4f}")
            print(f"  Result:     {status}")
            
            results.append({
                "name": test["name"],
                "expected": test["expected"],
                "prediction": prediction,
                "correct": correct,
                "ensemble": ensemble
            })
            
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "name": test["name"],
                "expected": test["expected"],
                "prediction": "error",
                "correct": False,
                "ensemble": 0
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    correct_count = sum(1 for r in results if r["correct"])
    total = len(results)
    
    print(f"Correct: {correct_count}/{total} ({100*correct_count/total:.1f}%)")
    
    for r in results:
        status = "✅" if r["correct"] else "❌"
        print(f"  {status} {r['name'][:40]}... -> {r['prediction']}")
    
    return results

if __name__ == "__main__":
    test_attacks()
