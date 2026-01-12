"""
Model Training Script voor AI Firewall POC
Training van XGBoost en Isolation Forest modellen met evaluatie.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    roc_auc_score, roc_curve, precision_recall_curve,
    average_precision_score, accuracy_score, f1_score
)
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import time
from typing import Tuple, Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

from utils import Config, Logger, save_model, get_timestamp
from data_loading import load_and_prepare_data
from feature_extraction import FeatureExtractor


class AIFirewallTrainer:
    """Trainer voor AI Firewall modellen."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialiseert trainer.
        
        Args:
            config: Config object (optioneel)
        """
        self.config = config or Config()
        self.logger = Logger("AIFirewallTrainer", self.config).get_logger()
        
        self.xgb_model = None
        self.if_model = None
        self.feature_extractor = None
        
        self.metrics = {}
        
    def prepare_data(self) -> Tuple:
        """
        Laadt en bereidt data voor.
        
        Returns:
            Tuple van (X_train, X_test, y_train, y_test, feature_names)
        """
        self.logger.info("=" * 60)
        self.logger.info("DATA VOORBEREIDING")
        self.logger.info("=" * 60)
        
        # Laad data
        X_train, X_test, y_train, y_test, feature_names = load_and_prepare_data(self.config)
        
        # Feature extraction
        self.feature_extractor = FeatureExtractor(self.config)
        
        X_train_transformed = self.feature_extractor.fit_transform(X_train)
        X_test_transformed = self.feature_extractor.transform(X_test)
        
        # Save feature extractor
        models_dir = Path(self.config.get('data.models_dir'))
        self.feature_extractor.save_transformers(
            str(models_dir / 'feature_transformers.pkl')
        )
        
        return X_train_transformed, X_test_transformed, y_train, y_test
    
    def train_xgboost(self, X_train: pd.DataFrame, y_train: pd.Series) -> xgb.XGBClassifier:
        """
        Traint XGBoost classifier.
        
        Args:
            X_train: Training features
            y_train: Training labels
            
        Returns:
            Getraind XGBoost model
        """
        self.logger.info("=" * 60)
        self.logger.info("XGBOOST TRAINING")
        self.logger.info("=" * 60)
        
        # Haal parameters uit config
        xgb_params = self.config.get('training.xgboost', {}).copy()
        use_gpu = self.config.get('training.use_gpu', False)
        
        # Update tree_method voor GPU (met fallback naar CPU)
        if use_gpu:
            try:
                # Probeer GPU training
                xgb_params['tree_method'] = 'hist'  # Basis method
                xgb_params['device'] = 'cuda:0'
                
                # Test of GPU beschikbaar is
                test_model = xgb.XGBClassifier(n_estimators=1, device='cuda:0')
                test_model.fit(X_train.head(100), y_train.head(100), verbose=False)
                
                self.logger.info("GPU training ingeschakeld (device=cuda:0)")
            except Exception as e:
                # Fallback naar CPU
                self.logger.warning(f"GPU niet beschikbaar ({e}), val terug naar CPU")
                xgb_params['tree_method'] = 'hist'
                xgb_params['device'] = 'cpu'
                use_gpu = False
        else:
            xgb_params['tree_method'] = 'hist'
            xgb_params['device'] = 'cpu'
            self.logger.info("CPU training (device=cpu)")
        
        self.logger.info(f"Parameters: {xgb_params}")
        
        # Maak model
        model = xgb.XGBClassifier(**xgb_params)
        
        # Train model
        start_time = time.time()
        
        try:
            model.fit(
                X_train, y_train,
                eval_set=[(X_train, y_train)],
                verbose=False
            )
        except Exception as e:
            # Als training faalt, probeer zonder device parameter (oudere XGBoost versies)
            self.logger.warning(f"Training error met device parameter: {e}")
            self.logger.info("Probeer training zonder device parameter...")
            
            xgb_params_fallback = xgb_params.copy()
            xgb_params_fallback.pop('device', None)
            
            model = xgb.XGBClassifier(**xgb_params_fallback)
            model.fit(
                X_train, y_train,
                eval_set=[(X_train, y_train)],
                verbose=False
            )
        
        training_time = time.time() - start_time
        self.logger.info(f"Training compleet in {training_time:.2f} seconden")
        
        self.xgb_model = model
        return model
    
    def train_isolation_forest(self, X_train: pd.DataFrame) -> IsolationForest:
        """
        Traint Isolation Forest voor anomaly detection.
        
        Args:
            X_train: Training features
            
        Returns:
            Getraind Isolation Forest model
        """
        self.logger.info("=" * 60)
        self.logger.info("ISOLATION FOREST TRAINING")
        self.logger.info("=" * 60)
        
        # Haal parameters uit config
        if_params = self.config.get('training.isolation_forest', {})
        
        self.logger.info(f"Parameters: {if_params}")
        
        # Maak model
        model = IsolationForest(**if_params)
        
        # Train model
        start_time = time.time()
        
        model.fit(X_train)
        
        training_time = time.time() - start_time
        self.logger.info(f"Training compleet in {training_time:.2f} seconden")
        
        self.if_model = model
        return model
    
    def evaluate_models(self, 
                       X_test: pd.DataFrame, 
                       y_test: pd.Series) -> Dict[str, Any]:
        """
        Evalueert beide modellen en ensemble.
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary met evaluatie metrics
        """
        self.logger.info("=" * 60)
        self.logger.info("MODEL EVALUATIE")
        self.logger.info("=" * 60)
        
        # XGBoost predictions
        xgb_proba = self.xgb_model.predict_proba(X_test)[:, 1]
        xgb_pred = (xgb_proba >= 0.5).astype(int)
        
        # Isolation Forest predictions (scores)
        if_scores = self.if_model.score_samples(X_test)
        # Normaliseer IF scores naar [0, 1] (lagere score = meer anomalous)
        if_scores_norm = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min())
        if_scores_norm = 1 - if_scores_norm  # Invert zodat hoog = malicious
        
        # Ensemble predictions
        xgb_weight = self.config.get('ensemble.xgboost_weight', 0.7)
        if_weight = self.config.get('ensemble.isolation_forest_weight', 0.3)
        threshold = self.config.get('ensemble.threshold', 0.5)
        
        ensemble_scores = (xgb_weight * xgb_proba) + (if_weight * if_scores_norm)
        ensemble_pred = (ensemble_scores >= threshold).astype(int)
        
        # Bereken metrics
        metrics = {
            'xgboost': self._calculate_metrics(y_test, xgb_pred, xgb_proba),
            'isolation_forest': self._calculate_metrics(y_test, (if_scores_norm >= 0.5).astype(int), if_scores_norm),
            'ensemble': self._calculate_metrics(y_test, ensemble_pred, ensemble_scores)
        }
        
        # Log resultaten
        self.logger.info("\nXGBoost Metrics:")
        self._log_metrics(metrics['xgboost'])
        
        self.logger.info("\nIsolation Forest Metrics:")
        self._log_metrics(metrics['isolation_forest'])
        
        self.logger.info("\nEnsemble Metrics:")
        self._log_metrics(metrics['ensemble'])
        
        # Confusion matrices
        metrics['xgboost']['confusion_matrix'] = confusion_matrix(y_test, xgb_pred)
        metrics['ensemble']['confusion_matrix'] = confusion_matrix(y_test, ensemble_pred)
        
        self.metrics = metrics
        return metrics
    
    def _calculate_metrics(self, y_true, y_pred, y_scores) -> Dict[str, float]:
        """Berekent classificatie metrics."""
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'f1_score': f1_score(y_true, y_pred),
            'roc_auc': roc_auc_score(y_true, y_scores),
            'avg_precision': average_precision_score(y_true, y_scores)
        }
    
    def _log_metrics(self, metrics: Dict[str, float]):
        """Logt metrics naar console."""
        self.logger.info(f"  Accuracy: {metrics['accuracy']:.4f}")
        self.logger.info(f"  F1 Score: {metrics['f1_score']:.4f}")
        self.logger.info(f"  ROC AUC: {metrics['roc_auc']:.4f}")
        self.logger.info(f"  Avg Precision: {metrics['avg_precision']:.4f}")
    
    def save_models(self):
        """Slaat getrainde modellen op."""
        self.logger.info("=" * 60)
        self.logger.info("MODELLEN OPSLAAN")
        self.logger.info("=" * 60)
        
        models_dir = Path(self.config.get('data.models_dir'))
        timestamp = get_timestamp()
        
        # XGBoost model
        xgb_path = models_dir / f'xgboost_model_{timestamp}.pkl'
        save_model(
            self.xgb_model, 
            str(xgb_path),
            metadata={
                'type': 'xgboost',
                'metrics': self.metrics.get('xgboost', {}),
                'feature_count': len(self.feature_extractor.feature_names)
            }
        )
        
        # Isolation Forest model
        if_path = models_dir / f'isolation_forest_model_{timestamp}.pkl'
        save_model(
            self.if_model,
            str(if_path),
            metadata={
                'type': 'isolation_forest',
                'metrics': self.metrics.get('isolation_forest', {}),
                'feature_count': len(self.feature_extractor.feature_names)
            }
        )
        
        # Ook save zonder timestamp voor easy loading
        save_model(self.xgb_model, str(models_dir / 'xgboost_model_latest.pkl'))
        save_model(self.if_model, str(models_dir / 'isolation_forest_model_latest.pkl'))
        
        self.logger.info(f"Modellen opgeslagen in {models_dir}")
    
    def plot_results(self, X_test: pd.DataFrame, y_test: pd.Series):
        """
        Creëert visualisaties van resultaten.
        
        Args:
            X_test: Test features
            y_test: Test labels
        """
        self.logger.info("Genereren van visualisaties...")
        
        output_dir = Path(self.config.get('data.output_dir'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Confusion Matrix
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # XGBoost confusion matrix
        sns.heatmap(
            self.metrics['xgboost']['confusion_matrix'],
            annot=True, fmt='d', cmap='Blues',
            xticklabels=['Benign', 'Malicious'],
            yticklabels=['Benign', 'Malicious'],
            ax=axes[0]
        )
        axes[0].set_title('XGBoost Confusion Matrix')
        axes[0].set_ylabel('True Label')
        axes[0].set_xlabel('Predicted Label')
        
        # Ensemble confusion matrix
        sns.heatmap(
            self.metrics['ensemble']['confusion_matrix'],
            annot=True, fmt='d', cmap='Greens',
            xticklabels=['Benign', 'Malicious'],
            yticklabels=['Benign', 'Malicious'],
            ax=axes[1]
        )
        axes[1].set_title('Ensemble Confusion Matrix')
        axes[1].set_ylabel('True Label')
        axes[1].set_xlabel('Predicted Label')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'confusion_matrices.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Feature Importance (XGBoost)
        if hasattr(self.xgb_model, 'feature_importances_'):
            plt.figure(figsize=(10, 8))
            
            feature_importance = pd.DataFrame({
                'feature': self.feature_extractor.feature_names,
                'importance': self.xgb_model.feature_importances_
            }).sort_values('importance', ascending=False).head(20)
            
            sns.barplot(data=feature_importance, x='importance', y='feature')
            plt.title('Top 20 Feature Importances (XGBoost)')
            plt.xlabel('Importance')
            plt.tight_layout()
            plt.savefig(output_dir / 'feature_importance.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Score Distribution (Isolation Forest)
        if_scores = self.if_model.score_samples(X_test)
        
        plt.figure(figsize=(10, 6))
        plt.hist(if_scores[y_test == 0], bins=50, alpha=0.5, label='Benign', color='green')
        plt.hist(if_scores[y_test == 1], bins=50, alpha=0.5, label='Malicious', color='red')
        plt.xlabel('Anomaly Score')
        plt.ylabel('Frequency')
        plt.title('Isolation Forest Score Distribution')
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / 'anomaly_score_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Visualisaties opgeslagen in {output_dir}")
    
    def train_full_pipeline(self):
        """Voert volledige training pipeline uit."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("START AI FIREWALL TRAINING PIPELINE")
        self.logger.info("=" * 60 + "\n")
        
        start_time = time.time()
        
        # 1. Data voorbereiding
        X_train, X_test, y_train, y_test = self.prepare_data()
        
        # 2. Train modellen
        self.train_xgboost(X_train, y_train)
        self.train_isolation_forest(X_train)
        
        # 3. Evalueer modellen
        self.evaluate_models(X_test, y_test)
        
        # 4. Save modellen
        self.save_models()
        
        # 5. Visualisaties
        self.plot_results(X_test, y_test)
        
        total_time = time.time() - start_time
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"TRAINING COMPLEET in {total_time:.2f} seconden")
        self.logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    """Main training script."""
    from typing import Optional
    
    print("\n🔥 AI FIREWALL POC - MODEL TRAINING 🔥\n")
    
    # Laad configuratie
    config = Config()
    
    # Initialiseer trainer
    trainer = AIFirewallTrainer(config)
    
    try:
        # Start training
        trainer.train_full_pipeline()
        
        print("\n✅ Training succesvol afgerond!")
        print(f"\nModellen opgeslagen in: {config.get('data.models_dir')}")
        print(f"Visualisaties opgeslagen in: {config.get('data.output_dir')}")
        
    except Exception as e:
        print(f"\n❌ Fout tijdens training: {e}")
        import traceback
        traceback.print_exc()
