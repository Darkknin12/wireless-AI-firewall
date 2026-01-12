"""
Visualisatie Module voor AI Firewall POC
Extra visualisaties en analytics voor model performance.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import roc_curve, precision_recall_curve, auc
import json
from typing import Optional
import warnings
warnings.filterwarnings('ignore')

from utils import Config, Logger, load_model
from data_loading import DataLoader
from feature_extraction import FeatureExtractor


class FirewallVisualizer:
    """Class voor het genereren van visualisaties."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialiseert visualizer.
        
        Args:
            config: Config object (optioneel)
        """
        self.config = config or Config()
        self.logger = Logger("FirewallVisualizer", self.config).get_logger()
        
        self.output_dir = Path(self.config.get('data.output_dir'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Styling
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
    
    def plot_roc_curves(self, 
                       y_test: pd.Series,
                       xgb_scores: np.ndarray,
                       if_scores: np.ndarray,
                       ensemble_scores: np.ndarray):
        """
        Plot ROC curves voor alle modellen.
        
        Args:
            y_test: True labels
            xgb_scores: XGBoost probability scores
            if_scores: Isolation Forest scores
            ensemble_scores: Ensemble scores
        """
        plt.figure(figsize=(10, 8))
        
        # XGBoost ROC
        fpr_xgb, tpr_xgb, _ = roc_curve(y_test, xgb_scores)
        roc_auc_xgb = auc(fpr_xgb, tpr_xgb)
        
        # Isolation Forest ROC
        fpr_if, tpr_if, _ = roc_curve(y_test, if_scores)
        roc_auc_if = auc(fpr_if, tpr_if)
        
        # Ensemble ROC
        fpr_ens, tpr_ens, _ = roc_curve(y_test, ensemble_scores)
        roc_auc_ens = auc(fpr_ens, tpr_ens)
        
        # Plot
        plt.plot(fpr_xgb, tpr_xgb, 'b-', linewidth=2,
                label=f'XGBoost (AUC = {roc_auc_xgb:.4f})')
        plt.plot(fpr_if, tpr_if, 'g-', linewidth=2,
                label=f'Isolation Forest (AUC = {roc_auc_if:.4f})')
        plt.plot(fpr_ens, tpr_ens, 'r-', linewidth=2,
                label=f'Ensemble (AUC = {roc_auc_ens:.4f})')
        
        # Diagonal line
        plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
        
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title('ROC Curves - Model Comparison', fontsize=14, fontweight='bold')
        plt.legend(loc="lower right", fontsize=11)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'roc_curves.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"ROC curves opgeslagen: {self.output_dir / 'roc_curves.png'}")
    
    def plot_precision_recall_curves(self,
                                     y_test: pd.Series,
                                     xgb_scores: np.ndarray,
                                     if_scores: np.ndarray,
                                     ensemble_scores: np.ndarray):
        """
        Plot Precision-Recall curves voor alle modellen.
        
        Args:
            y_test: True labels
            xgb_scores: XGBoost probability scores
            if_scores: Isolation Forest scores
            ensemble_scores: Ensemble scores
        """
        plt.figure(figsize=(10, 8))
        
        # XGBoost PR
        prec_xgb, rec_xgb, _ = precision_recall_curve(y_test, xgb_scores)
        pr_auc_xgb = auc(rec_xgb, prec_xgb)
        
        # Isolation Forest PR
        prec_if, rec_if, _ = precision_recall_curve(y_test, if_scores)
        pr_auc_if = auc(rec_if, prec_if)
        
        # Ensemble PR
        prec_ens, rec_ens, _ = precision_recall_curve(y_test, ensemble_scores)
        pr_auc_ens = auc(rec_ens, prec_ens)
        
        # Plot
        plt.plot(rec_xgb, prec_xgb, 'b-', linewidth=2,
                label=f'XGBoost (AUC = {pr_auc_xgb:.4f})')
        plt.plot(rec_if, prec_if, 'g-', linewidth=2,
                label=f'Isolation Forest (AUC = {pr_auc_if:.4f})')
        plt.plot(rec_ens, prec_ens, 'r-', linewidth=2,
                label=f'Ensemble (AUC = {pr_auc_ens:.4f})')
        
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('Recall', fontsize=12)
        plt.ylabel('Precision', fontsize=12)
        plt.title('Precision-Recall Curves - Model Comparison', fontsize=14, fontweight='bold')
        plt.legend(loc="lower left", fontsize=11)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'precision_recall_curves.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"PR curves opgeslagen: {self.output_dir / 'precision_recall_curves.png'}")
    
    def plot_score_distributions(self,
                                y_test: pd.Series,
                                ensemble_scores: np.ndarray):
        """
        Plot ensemble score distributie per class.
        
        Args:
            y_test: True labels
            ensemble_scores: Ensemble scores
        """
        plt.figure(figsize=(12, 6))
        
        # Separate scores per class
        benign_scores = ensemble_scores[y_test == 0]
        malicious_scores = ensemble_scores[y_test == 1]
        
        # Plot histograms
        plt.hist(benign_scores, bins=50, alpha=0.6, label='Benign', color='green', edgecolor='black')
        plt.hist(malicious_scores, bins=50, alpha=0.6, label='Malicious', color='red', edgecolor='black')
        
        # Threshold line
        threshold = self.config.get('ensemble.threshold', 0.5)
        plt.axvline(x=threshold, color='blue', linestyle='--', linewidth=2, 
                   label=f'Threshold ({threshold})')
        
        plt.xlabel('Ensemble Score', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.title('Ensemble Score Distribution by Class', fontsize=14, fontweight='bold')
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'score_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Score distribution opgeslagen: {self.output_dir / 'score_distribution.png'}")
    
    def plot_feature_correlations(self, X: pd.DataFrame, top_n: int = 20):
        """
        Plot correlatie heatmap van top features.
        
        Args:
            X: Feature DataFrame
            top_n: Aantal features om te tonen
        """
        # Selecteer subset van features (te veel maakt plot onleesbaar)
        if len(X.columns) > top_n:
            # Bereken variance en selecteer top features
            variances = X.var().sort_values(ascending=False)
            top_features = variances.head(top_n).index
            X_subset = X[top_features]
        else:
            X_subset = X
        
        plt.figure(figsize=(14, 12))
        
        # Bereken correlatie
        corr = X_subset.corr()
        
        # Plot heatmap
        sns.heatmap(corr, cmap='coolwarm', center=0, 
                   square=True, linewidths=0.5,
                   cbar_kws={"shrink": 0.8},
                   annot=False)  # annot=True voor waarden (druk bij veel features)
        
        plt.title(f'Feature Correlation Heatmap (Top {len(X_subset.columns)})', 
                 fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'feature_correlations.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Correlation heatmap opgeslagen: {self.output_dir / 'feature_correlations.png'}")
    
    def plot_prediction_timeline(self, log_file: Optional[str] = None):
        """
        Plot prediction timeline van prediction logs.
        
        Args:
            log_file: Pad naar prediction log JSON
        """
        if log_file is None:
            log_file = self.config.get('inference.prediction_log_file', 'logs/predictions.json')
        
        log_path = Path(log_file)
        
        if not log_path.exists():
            self.logger.warning(f"Prediction log niet gevonden: {log_file}")
            return
        
        # Laad logs
        with open(log_path, 'r') as f:
            logs = json.load(f)
        
        if not logs:
            self.logger.warning("Geen prediction logs gevonden")
            return
        
        # Converteer naar DataFrame
        df = pd.DataFrame(logs)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # 1. Score timeline
        ax1.plot(df['timestamp'], df['ensemble_score'], 'o-', alpha=0.6, markersize=3)
        ax1.axhline(y=self.config.get('ensemble.threshold', 0.5), 
                   color='orange', linestyle='--', label='Threshold')
        ax1.axhline(y=self.config.get('inference.alert_threshold', 0.7), 
                   color='red', linestyle='--', label='Alert Threshold')
        ax1.set_ylabel('Ensemble Score', fontsize=11)
        ax1.set_title('Prediction Timeline', fontsize=13, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Prediction counts
        df['hour'] = df['timestamp'].dt.floor('H')
        hourly_counts = df.groupby(['hour', 'prediction']).size().unstack(fill_value=0)
        
        if 'benign' in hourly_counts.columns:
            ax2.bar(hourly_counts.index, hourly_counts['benign'], 
                   alpha=0.6, label='Benign', color='green')
        if 'malicious' in hourly_counts.columns:
            ax2.bar(hourly_counts.index, hourly_counts['malicious'], 
                   alpha=0.6, label='Malicious', color='red', bottom=hourly_counts.get('benign', 0))
        
        ax2.set_xlabel('Time', fontsize=11)
        ax2.set_ylabel('Prediction Count', fontsize=11)
        ax2.set_title('Hourly Prediction Distribution', fontsize=13, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'prediction_timeline.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Prediction timeline opgeslagen: {self.output_dir / 'prediction_timeline.png'}")
    
    def generate_all_visualizations(self):
        """Genereert alle visualisaties met test data."""
        self.logger.info("=" * 60)
        self.logger.info("GENEREREN VAN VISUALISATIES")
        self.logger.info("=" * 60)
        
        # Laad data en modellen
        from data_loading import load_and_prepare_data
        
        X_train, X_test, y_train, y_test, _ = load_and_prepare_data(self.config)
        
        # Feature extraction
        extractor = FeatureExtractor(self.config)
        models_dir = Path(self.config.get('data.models_dir'))
        extractor.load_transformers(str(models_dir / 'feature_transformers.pkl'))
        
        X_test_transformed = extractor.transform(X_test)
        
        # Load modellen
        xgb_model, _ = load_model(str(models_dir / 'xgboost_model_latest.pkl'))
        if_model, _ = load_model(str(models_dir / 'isolation_forest_model_latest.pkl'))
        
        # Predictions
        xgb_scores = xgb_model.predict_proba(X_test_transformed)[:, 1]
        if_scores = if_model.score_samples(X_test_transformed)
        
        # Normaliseer IF scores
        if_scores_norm = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min())
        if_scores_norm = 1 - if_scores_norm
        
        # Ensemble
        xgb_weight = self.config.get('ensemble.xgboost_weight', 0.7)
        if_weight = self.config.get('ensemble.isolation_forest_weight', 0.3)
        ensemble_scores = (xgb_weight * xgb_scores) + (if_weight * if_scores_norm)
        
        # Generate plots
        self.plot_roc_curves(y_test, xgb_scores, if_scores_norm, ensemble_scores)
        self.plot_precision_recall_curves(y_test, xgb_scores, if_scores_norm, ensemble_scores)
        self.plot_score_distributions(y_test, ensemble_scores)
        self.plot_feature_correlations(X_test_transformed, top_n=20)
        self.plot_prediction_timeline()
        
        self.logger.info("=" * 60)
        self.logger.info("VISUALISATIES COMPLEET")
        self.logger.info("=" * 60)


if __name__ == "__main__":
    """Generate visualizations."""
    print("\n📊 AI FIREWALL POC - VISUALISATIES 📊\n")
    
    config = Config()
    visualizer = FirewallVisualizer(config)
    
    try:
        visualizer.generate_all_visualizations()
        
        print(f"\n✅ Visualisaties gegenereerd in: {config.get('data.output_dir')}")
        
    except Exception as e:
        print(f"\n❌ Fout: {e}")
        import traceback
        traceback.print_exc()
