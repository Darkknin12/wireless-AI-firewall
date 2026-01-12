"""
Inference Module voor AI Firewall POC
Realtime classificatie van netwerkflows met ensemble scoring.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

from utils import Config, Logger, load_model, PredictionLogger
from feature_extraction import FeatureExtractor


class AIFirewallInference:
    """Inference engine voor realtime netwerkflow classificatie."""
    
    def __init__(self, 
                 models_dir: Optional[str] = None,
                 config: Optional[Config] = None):
        """
        Initialiseert inference engine.
        
        Args:
            models_dir: Directory met getrainde modellen
            config: Config object (optioneel)
        """
        self.config = config or Config()
        self.logger = Logger("AIFirewallInference", self.config).get_logger()
        
        if models_dir is None:
            models_dir = self.config.get('data.models_dir')
        
        self.models_dir = Path(models_dir)
        
        # Modellen en transformers
        self.xgb_model = None
        self.if_model = None
        self.feature_extractor = None
        
        # Ensemble configuratie
        self.xgb_weight = self.config.get('ensemble.xgboost_weight', 0.7)
        self.if_weight = self.config.get('ensemble.isolation_forest_weight', 0.3)
        self.threshold = self.config.get('ensemble.threshold', 0.5)
        self.alert_threshold = self.config.get('inference.alert_threshold', 0.7)
        
        # Prediction logger
        if self.config.get('inference.log_predictions', True):
            log_file = self.config.get('inference.prediction_log_file', 'logs/predictions.json')
            self.pred_logger = PredictionLogger(log_file)
        else:
            self.pred_logger = None
        
        # Load modellen
        self.load_models()
    
    def load_models(self):
        """Laadt getrainde modellen en feature transformers."""
        self.logger.info("Laden van modellen...")
        
        # Load feature extractor
        feature_transformer_path = self.models_dir / 'feature_transformers.pkl'
        if not feature_transformer_path.exists():
            raise FileNotFoundError(
                f"Feature transformers niet gevonden: {feature_transformer_path}"
            )
        
        self.feature_extractor = FeatureExtractor(self.config)
        self.feature_extractor.load_transformers(str(feature_transformer_path))
        self.logger.info("  ✓ Feature transformers geladen")
        
        # Load XGBoost model
        xgb_model_path = self.models_dir / 'xgboost_model_latest.pkl'
        if not xgb_model_path.exists():
            raise FileNotFoundError(f"XGBoost model niet gevonden: {xgb_model_path}")
        
        self.xgb_model, xgb_metadata = load_model(str(xgb_model_path))
        self.logger.info("  ✓ XGBoost model geladen")
        
        # Load Isolation Forest model
        if_model_path = self.models_dir / 'isolation_forest_model_latest.pkl'
        if not if_model_path.exists():
            raise FileNotFoundError(f"Isolation Forest model niet gevonden: {if_model_path}")
        
        self.if_model, if_metadata = load_model(str(if_model_path))
        self.logger.info("  ✓ Isolation Forest model geladen")
        
        self.logger.info("Alle modellen succesvol geladen!")
    
    def preprocess_flow(self, flow_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Preprocesst single flow voor inference.
        
        Args:
            flow_data: Dictionary met flow features
            
        Returns:
            Preprocessed DataFrame
        """
        # Converteer naar DataFrame
        df = pd.DataFrame([flow_data])
        
        # Transform met feature extractor
        df_transformed = self.feature_extractor.transform(df)
        
        return df_transformed
    
    def predict_single_flow(self, 
                          flow_data: Dict[str, Any],
                          return_details: bool = True) -> Dict[str, Any]:
        """
        Classificeert een enkele netwerkflow.
        
        Args:
            flow_data: Dictionary met flow features
            return_details: Of gedetailleerde scores teruggegeven moeten worden
            
        Returns:
            Dictionary met classificatie en scores
        """
        # Preprocess flow
        df = self.preprocess_flow(flow_data)
        
        # XGBoost prediction
        xgb_proba = self.xgb_model.predict_proba(df)[0, 1]
        
        # Isolation Forest prediction
        if_score = self.if_model.score_samples(df)[0]
        # Normaliseer (simpele normalisatie, in productie zou je min/max van training set gebruiken)
        # Voor nu: score < -0.5 is verdacht
        if_score_norm = 1.0 if if_score < -0.5 else 0.0
        if if_score >= -0.5 and if_score < 0:
            if_score_norm = (-if_score) / 0.5  # Scale [-0.5, 0] naar [0, 1]
        
        # Ensemble score
        ensemble_score = (self.xgb_weight * xgb_proba) + (self.if_weight * if_score_norm)
        
        # Classificatie
        prediction = 'malicious' if ensemble_score >= self.threshold else 'benign'
        is_alert = ensemble_score >= self.alert_threshold
        
        # Log prediction
        if self.pred_logger:
            self.pred_logger.log_prediction(
                flow_data=flow_data,
                prediction=prediction,
                score=ensemble_score,
                xgb_score=xgb_proba,
                if_score=if_score_norm,
                is_alert=is_alert
            )
        
        # Resultaat
        result = {
            'prediction': prediction,
            'ensemble_score': float(ensemble_score),
            'is_alert': is_alert,
            'confidence': float(abs(ensemble_score - 0.5) * 2),  # 0 = onzeker, 1 = zeer zeker
            'xgb_score': float(xgb_proba),
            'if_score': float(if_score_norm)
        }
        
        if return_details:
            result['details'] = {
                'xgboost_score': float(xgb_proba),
                'isolation_forest_score': float(if_score_norm),
                'raw_if_score': float(if_score),
                'threshold': self.threshold,
                'alert_threshold': self.alert_threshold
            }
        
        return result
    
    def predict_batch(self, 
                     flows: list[Dict[str, Any]],
                     return_details: bool = False) -> list[Dict[str, Any]]:
        """
        Classificeert meerdere flows in batch.
        
        Args:
            flows: List van flow dictionaries
            return_details: Of gedetailleerde scores teruggegeven moeten worden
            
        Returns:
            List van prediction dictionaries
        """
        self.logger.info(f"Batch prediction voor {len(flows)} flows...")
        
        results = []
        for flow in flows:
            result = self.predict_single_flow(flow, return_details=return_details)
            results.append(result)
        
        return results
    
    def predict_from_csv(self, 
                        csv_path: str,
                        output_path: Optional[str] = None) -> pd.DataFrame:
        """
        Classificeert flows van CSV bestand.
        
        Args:
            csv_path: Pad naar CSV bestand
            output_path: Pad om resultaten op te slaan (optioneel)
            
        Returns:
            DataFrame met originele data + predictions
        """
        self.logger.info(f"Laden van flows van {csv_path}...")
        
        # Laad CSV
        df = pd.read_csv(csv_path)
        # Normaliseer kolomnamen (verwijder leading/trailing spaties)
        df.columns = df.columns.str.strip()
        original_df = df.copy()
        
        self.logger.info(f"  → {len(df)} flows geladen")
        
        # Preprocess (zonder labels)
        df_transformed = self.feature_extractor.transform(df)
        
        # Predictions
        xgb_proba = self.xgb_model.predict_proba(df_transformed)[:, 1]
        if_scores = self.if_model.score_samples(df_transformed)
        
        # Normaliseer IF scores (simpel)
        if_scores_norm = np.zeros_like(if_scores)
        for i, score in enumerate(if_scores):
            if score < -0.5:
                if_scores_norm[i] = 1.0
            elif score >= -0.5 and score < 0:
                if_scores_norm[i] = (-score) / 0.5
            else:
                if_scores_norm[i] = 0.0
        
        # Ensemble
        ensemble_scores = (self.xgb_weight * xgb_proba) + (self.if_weight * if_scores_norm)
        predictions = (ensemble_scores >= self.threshold).astype(int)
        
        # Voeg toe aan originele DataFrame
        original_df['XGBoost_Score'] = xgb_proba
        original_df['IF_Score'] = if_scores_norm
        original_df['Ensemble_Score'] = ensemble_scores
        original_df['Prediction'] = predictions
        original_df['Prediction_Label'] = original_df['Prediction'].map({0: 'benign', 1: 'malicious'})
        
        # Save als gevraagd
        if output_path:
            original_df.to_csv(output_path, index=False)
            self.logger.info(f"Resultaten opgeslagen naar {output_path}")
        
        # Statistics
        n_malicious = (predictions == 1).sum()
        n_benign = (predictions == 0).sum()
        
        self.logger.info(f"Resultaten:")
        self.logger.info(f"  → Benign: {n_benign} ({n_benign/len(df)*100:.1f}%)")
        self.logger.info(f"  → Malicious: {n_malicious} ({n_malicious/len(df)*100:.1f}%)")
        
        return original_df


def create_example_flow() -> Dict[str, Any]:
    """
    Creëert een voorbeeld netwerkflow voor testing met ALLE vereiste CICIDS2017 features.
    """
    return {
        # Basic flow info
        'Destination Port': 80,
        'Flow Duration': 1500000,
        'Protocol': 6,
        
        # Packet counts
        'Total Fwd Packets': 10,
        'Total Backward Packets': 8,
        
        # Packet lengths
        'Total Length of Fwd Packets': 5000,
        'Total Length of Bwd Packets': 3000,
        'Fwd Packet Length Max': 1500,
        'Fwd Packet Length Min': 60,
        'Fwd Packet Length Mean': 500.0,
        'Fwd Packet Length Std': 200.0,
        'Bwd Packet Length Max': 1200,
        'Bwd Packet Length Min': 60,
        'Bwd Packet Length Mean': 375.0,
        'Bwd Packet Length Std': 150.0,
        
        # Flow rates
        'Flow Bytes/s': 5333.33,
        'Flow Packets/s': 12.0,
        'Fwd Packets/s': 6.67,
        'Bwd Packets/s': 5.33,
        
        # Inter-arrival times
        'Flow IAT Mean': 150000.0,
        'Flow IAT Std': 50000.0,
        'Flow IAT Max': 300000.0,
        'Flow IAT Min': 10000.0,
        'Fwd IAT Total': 1000000.0,
        'Fwd IAT Mean': 100000.0,
        'Fwd IAT Std': 30000.0,
        'Fwd IAT Max': 200000.0,
        'Fwd IAT Min': 5000.0,
        'Bwd IAT Total': 800000.0,
        'Bwd IAT Mean': 100000.0,
        'Bwd IAT Std': 25000.0,
        'Bwd IAT Max': 180000.0,
        'Bwd IAT Min': 8000.0,
        
        # Flags
        'Fwd PSH Flags': 1,
        'Bwd PSH Flags': 1,
        'Fwd URG Flags': 0,
        'Bwd URG Flags': 0,
        'FIN Flag Count': 1,
        'SYN Flag Count': 1,
        'RST Flag Count': 0,
        'PSH Flag Count': 2,
        'ACK Flag Count': 16,
        'URG Flag Count': 0,
        'CWE Flag Count': 0,
        'ECE Flag Count': 0,
        
        # Headers
        'Fwd Header Length': 200,
        'Bwd Header Length': 160,
        'Fwd Header Length.1': 200,
        
        # Packet sizes
        'Min Packet Length': 60,
        'Max Packet Length': 1500,
        'Packet Length Mean': 444.44,
        'Packet Length Std': 180.0,
        'Packet Length Variance': 32400.0,
        'Average Packet Size': 444.44,
        'Avg Fwd Segment Size': 500.0,
        'Avg Bwd Segment Size': 375.0,
        
        # Bulk
        'Fwd Avg Bytes/Bulk': 0,
        'Fwd Avg Packets/Bulk': 0,
        'Fwd Avg Bulk Rate': 0,
        'Bwd Avg Bytes/Bulk': 0,
        'Bwd Avg Packets/Bulk': 0,
        'Bwd Avg Bulk Rate': 0,
        
        # Subflows
        'Subflow Fwd Packets': 10,
        'Subflow Fwd Bytes': 5000,
        'Subflow Bwd Packets': 8,
        'Subflow Bwd Bytes': 3000,
        
        # Window sizes
        'Init_Win_bytes_forward': 8192,
        'Init_Win_bytes_backward': 8192,
        
        # Active/Idle times
        'Active Mean': 500000.0,
        'Active Std': 100000.0,
        'Active Max': 800000.0,
        'Active Min': 200000.0,
        'Idle Mean': 0.0,
        'Idle Std': 0.0,
        'Idle Max': 0.0,
        'Idle Min': 0.0,
        
        # Misc
        'Down/Up Ratio': 0,
        'act_data_pkt_fwd': 5,
        'min_seg_size_forward': 20,
    }


if __name__ == "__main__":
    """Test inference module."""
    print("\n🔥 AI FIREWALL POC - INFERENCE TEST 🔥\n")
    
    config = Config()
    
    try:
        # Initialiseer inference engine
        inference = AIFirewallInference(config=config)
        
        print("✅ Inference engine geladen!\n")
        
        # Test single flow prediction
        print("=" * 60)
        print("TEST: Single Flow Prediction")
        print("=" * 60)
        
        example_flow = create_example_flow()
        result = inference.predict_single_flow(example_flow)
        
        print(f"\nPrediction: {result['prediction'].upper()}")
        print(f"Ensemble Score: {result['ensemble_score']:.4f}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Alert: {'🚨 YES' if result['is_alert'] else '✓ NO'}")
        
        if 'details' in result:
            print(f"\nDetails:")
            print(f"  XGBoost Score: {result['details']['xgboost_score']:.4f}")
            print(f"  Isolation Forest Score: {result['details']['isolation_forest_score']:.4f}")
        
        print("\n✅ Inference test succesvol!")
        
    except Exception as e:
        print(f"\n❌ Fout: {e}")
        import traceback
        traceback.print_exc()
