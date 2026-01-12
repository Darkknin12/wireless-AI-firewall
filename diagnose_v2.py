"""
Diagnose waarom het model DDoS attacks niet detecteert - v2
"""

import pandas as pd
import numpy as np
import pickle
import joblib
import sys
sys.path.insert(0, '.')

def diagnose_model():
    print("=" * 60)
    print("MODEL DIAGNOSE - Waarom detecteert het model attacks niet?")
    print("=" * 60)
    
    # 1. Laad de feature transformers direct
    print("\n1. Laad feature transformers...")
    transformers = joblib.load('models/feature_transformers.pkl')
    
    print(f"   Keys in transformers: {transformers.keys()}")
    print(f"   Feature names: {len(transformers['feature_names']) if transformers['feature_names'] else 'None'}")
    print(f"   Categorical columns: {transformers['categorical_columns']}")
    print(f"   Numeric columns for scaling: {len(transformers['numeric_columns_for_scaling'])}")
    
    if transformers['feature_names']:
        print(f"\n   Eerste 20 feature names:")
        for i, fn in enumerate(transformers['feature_names'][:20]):
            print(f"      {i}: '{fn}'")
    
    # 2. Laad een DDoS sample
    print("\n2. Laad DDoS sample...")
    ddos_file = "ml_data/MachineLearningCVE/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
    df = pd.read_csv(ddos_file, nrows=10000)
    
    df_attacks = df[df[' Label'].str.strip() != 'BENIGN']
    print(f"   Found {len(df_attacks)} attack samples in first 10000 rows")
    
    if len(df_attacks) == 0:
        # Laad meer data
        df = pd.read_csv(ddos_file, nrows=100000)
        df_attacks = df[df[' Label'].str.strip() != 'BENIGN']
        print(f"   Found {len(df_attacks)} attack samples in first 100000 rows")
    
    sample = df_attacks.iloc[0]
    print(f"\n   Sample label: {sample[' Label']}")
    print(f"   Sample columns: {len(sample)}")
    
    # 3. Check column name matching
    print("\n3. Vergelijk kolomnamen...")
    csv_cols = [c.strip() for c in sample.index.tolist() if c.strip() != 'Label']
    model_cols = [c.strip() for c in transformers['feature_names']] if transformers['feature_names'] else []
    
    print(f"   CSV kolommen (stripped): {len(csv_cols)}")
    print(f"   Model features (stripped): {len(model_cols)}")
    
    # Find mismatches
    csv_set = set(csv_cols)
    model_set = set(model_cols)
    
    in_model_not_csv = model_set - csv_set
    in_csv_not_model = csv_set - model_set
    
    print(f"\n   In model maar niet in CSV ({len(in_model_not_csv)}):")
    for col in list(in_model_not_csv)[:15]:
        print(f"      '{col}'")
    
    print(f"\n   In CSV maar niet in model ({len(in_csv_not_model)}):")
    for col in list(in_csv_not_model)[:15]:
        print(f"      '{col}'")
    
    # 4. Check of de kolomnamen EXACT matchen (inclusief spaties)
    print("\n4. Check EXACT column name matching (met spaties)...")
    raw_csv_cols = sample.index.tolist()
    raw_model_cols = transformers['feature_names'] if transformers['feature_names'] else []
    
    print(f"   Eerste 10 RAW CSV kolommen:")
    for c in raw_csv_cols[:10]:
        print(f"      '{c}' (len={len(c)})")
    
    print(f"\n   Eerste 10 RAW model features:")
    for c in raw_model_cols[:10]:
        print(f"      '{c}' (len={len(c)})")
    
    # 5. Direct XGBoost test met correct prepared data
    print("\n5. Direct XGBoost test...")
    import xgboost as xgb
    
    xgb_model = xgb.Booster()
    xgb_model.load_model('models/xgb_model.json')
    
    # Check het aantal features dat XGBoost verwacht
    config = xgb_model.save_config()
    print(f"   XGBoost config (eerste 200 chars): {config[:200]}")

if __name__ == "__main__":
    diagnose_model()
