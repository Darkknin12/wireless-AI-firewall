"""
Diagnose waarom het model DDoS attacks niet detecteert
"""

import pandas as pd
import numpy as np
import pickle
import sys
sys.path.insert(0, '.')

from feature_extraction import FeatureExtractor
from inference import AIFirewallInference

def diagnose_model():
    print("=" * 60)
    print("MODEL DIAGNOSE - Waarom detecteert het model attacks niet?")
    print("=" * 60)
    
    # 1. Laad de training feature list
    print("\n1. Controleer feature extractors...")
    fe = FeatureExtractor()
    print(f"   Feature names: {len(fe.feature_names)} features")
    print(f"   Eerste 10: {fe.feature_names[:10]}")
    
    # 2. Laad XGBoost model en check feature importances
    print("\n2. Controleer XGBoost model feature importances...")
    import xgboost as xgb
    xgb_model = xgb.Booster()
    xgb_model.load_model('models/xgb_model.json')
    
    # Get feature importance
    importance = xgb_model.get_score(importance_type='gain')
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:15]
    print(f"   Top 15 belangrijkste features:")
    for feat, imp in sorted_imp:
        print(f"   - {feat}: {imp:.2f}")
    
    # 3. Test met raw data vs transformed
    print("\n3. Vergelijk raw features met transformed features...")
    ddos_file = "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
    df = pd.read_csv(ddos_file)
    
    # Get a DDoS sample
    df_attacks = df[df[' Label'].str.strip() != 'BENIGN']
    sample = df_attacks.iloc[0]
    
    print(f"\n   Sample label: {sample[' Label']}")
    print(f"\n   Raw belangrijke features uit de sample:")
    
    # Check de belangrijkste features in de raw data
    important_raw = [' Fwd Packet Length Max', ' Fwd Packet Length Mean', ' Flow Bytes/s', 
                     ' Flow Packets/s', ' Total Length of Fwd Packets', ' Packet Length Mean']
    for feat in important_raw:
        if feat in sample.index:
            print(f"   {feat}: {sample[feat]}")
    
    # 4. Transform en check de output
    print("\n4. Na feature extraction en transformatie:")
    flow_dict = sample.drop(' Label').to_dict()
    
    # Clean column names like in transform()
    cleaned_dict = {}
    for k, v in flow_dict.items():
        clean_key = k.strip()
        cleaned_dict[clean_key] = v
    
    # Check of de feature columns matchen
    print(f"\n   Features in input dict: {len(cleaned_dict)}")
    print(f"   Features die het model verwacht: {len(fe.feature_columns)}")
    
    # Check of de kolomnamen matchen
    mismatched = []
    for fc in fe.feature_names[:20]:
        if fc.strip() not in [k.strip() for k in cleaned_dict.keys()]:
            mismatched.append(fc)
    
    if mismatched:
        print(f"\n   ⚠️ Mismatched feature names:")
        for m in mismatched[:10]:
            print(f"      - '{m}'")
    
    # 5. Bekijk de daadwerkelijke transformed output
    print("\n5. Transformeer de sample en bekijk output...")
    try:
        X_transformed = fe.transform(pd.DataFrame([cleaned_dict]))
        print(f"   Transformed shape: {X_transformed.shape}")
        print(f"   Non-zero values: {np.count_nonzero(X_transformed)}")
        print(f"   Mean: {np.mean(X_transformed):.4f}")
        print(f"   Max: {np.max(X_transformed):.4f}")
        print(f"   Min: {np.min(X_transformed):.4f}")
        
        # Check welke features hoge waarden hebben
        if X_transformed.shape[1] == len(fe.feature_names):
            feature_vals = list(zip(fe.feature_names, X_transformed[0]))
            sorted_vals = sorted(feature_vals, key=lambda x: abs(x[1]), reverse=True)[:10]
            print(f"\n   Top 10 features met hoogste absolute waarden:")
            for feat, val in sorted_vals:
                print(f"      {feat}: {val:.4f}")
                
    except Exception as e:
        print(f"   Error bij transform: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Direct predict met XGBoost
    print("\n6. Direct XGBoost predictie...")
    import xgboost as xgb
    dmatrix = xgb.DMatrix(X_transformed, feature_names=fe.feature_names)
    proba = xgb_model.predict(dmatrix)
    print(f"   XGBoost prediction probability: {proba[0]:.6f}")
    print(f"   (> 0.5 = malicious, < 0.5 = benign)")

if __name__ == "__main__":
    diagnose_model()
