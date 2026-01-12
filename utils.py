"""
Utility Module voor AI Firewall POC
Bevat helper functies voor logging, configuratie, en algemene utilities.
"""

import os
import yaml
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np


class Config:
    """Configuration loader en manager."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Laadt configuratie van YAML bestand.
        
        Args:
            config_path: Pad naar config.yaml bestand
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._create_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """Laadt YAML configuratie."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.warning(f"Config file {self.config_path} niet gevonden. Gebruik defaults.")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Geeft default configuratie terug."""
        return {
            'data': {
                'input_dir': 'ml_data/MachineLearningCVE',
                'output_dir': 'output',
                'models_dir': 'models',
                'logs_dir': 'logs'
            },
            'training': {
                'test_size': 0.2,
                'random_state': 42,
                'use_gpu': False
            },
            'ensemble': {
                'xgboost_weight': 0.7,
                'isolation_forest_weight': 0.3,
                'threshold': 0.5
            }
        }
    
    def _create_directories(self):
        """Maakt benodigde directories aan."""
        dirs = [
            self.config['data']['output_dir'],
            self.config['data']['models_dir'],
            self.config['data']['logs_dir']
        ]
        for directory in dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Haalt waarde op uit configuratie met dot-notation.
        
        Args:
            key_path: Pad naar config waarde, bijv. 'training.test_size'
            default: Default waarde als key niet bestaat
            
        Returns:
            Config waarde of default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value


class Logger:
    """Custom logger voor AI Firewall."""
    
    def __init__(self, name: str, config: Optional[Config] = None):
        """
        Initialiseert logger.
        
        Args:
            name: Naam van de logger
            config: Config object (optioneel)
        """
        self.logger = logging.getLogger(name)
        
        if config:
            level = config.get('logging.level', 'INFO')
            log_format = config.get('logging.format', 
                                   '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        else:
            level = 'INFO'
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        self.logger.setLevel(getattr(logging, level))
        
        # Console handler
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, level))
            formatter = logging.Formatter(log_format)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """Geeft logger instance terug."""
        return self.logger


class PredictionLogger:
    """Logger voor model predictions en alerts."""
    
    def __init__(self, log_file: str):
        """
        Initialiseert prediction logger.
        
        Args:
            log_file: Pad naar JSON log bestand
        """
        self.log_file = log_file
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialiseer log bestand als het niet bestaat
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                json.dump([], f)
    
    def log_prediction(self, 
                      flow_data: Dict[str, Any], 
                      prediction: str,
                      score: float,
                      xgb_score: float,
                      if_score: float,
                      is_alert: bool = False):
        """
        Logt een prediction naar JSON bestand.
        
        Args:
            flow_data: Flow features/data
            prediction: Classificatie ('benign' of 'malicious')
            score: Ensemble score
            xgb_score: XGBoost score
            if_score: Isolation Forest score
            is_alert: Of het een alert is
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'prediction': str(prediction),
            'ensemble_score': float(score),
            'xgboost_score': float(xgb_score),
            'isolation_forest_score': float(if_score),
            'is_alert': bool(is_alert),
            'flow_summary': self._summarize_flow(flow_data)
        }
        
        # Lees bestaande logs
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logs = []
        
        # Voeg nieuwe log toe
        logs.append(log_entry)
        
        # Schrijf terug (limiteer tot laatste 10000 entries)
        with open(self.log_file, 'w') as f:
            json.dump(logs[-10000:], f, indent=2)
    
    def _summarize_flow(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creëert samenvatting van flow data voor logging."""
        summary = {}
        
        # Neem alleen relevante/interessante velden
        important_fields = [
            'Protocol', 'Flow Duration', 'Total Fwd Packets', 
            'Total Backward Packets', 'Flow Bytes/s', 'Flow Packets/s',
            'Destination Port'
        ]
        
        for field in important_fields:
            if field in flow_data:
                value = flow_data[field]
                # Convert numpy types en bool naar Python types
                if isinstance(value, (np.integer, np.floating)):
                    value = value.item()
                elif isinstance(value, (np.bool_, bool)):
                    value = bool(value)
                elif isinstance(value, np.ndarray):
                    value = value.tolist()
                summary[field] = value
        
        return summary


def save_model(model: Any, filepath: str, metadata: Optional[Dict] = None):
    """
    Slaat model op naar bestand met optionele metadata.
    
    Args:
        model: Model object om op te slaan
        filepath: Pad waar model opgeslagen moet worden
        metadata: Extra metadata om mee op te slaan
    """
    import joblib
    
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    save_obj = {
        'model': model,
        'metadata': metadata or {},
        'saved_at': datetime.now().isoformat()
    }
    
    joblib.dump(save_obj, filepath)
    logging.info(f"Model opgeslagen naar {filepath}")


def load_model(filepath: str) -> tuple:
    """
    Laadt model van bestand.
    
    Args:
        filepath: Pad naar model bestand
        
    Returns:
        Tuple van (model, metadata)
    """
    import joblib
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model bestand niet gevonden: {filepath}")
    
    save_obj = joblib.load(filepath)
    
    if isinstance(save_obj, dict) and 'model' in save_obj:
        return save_obj['model'], save_obj.get('metadata', {})
    else:
        # Backwards compatibility: alleen model object
        return save_obj, {}


def format_bytes(num_bytes: float) -> str:
    """
    Formatteert bytes naar leesbaar formaat.
    
    Args:
        num_bytes: Aantal bytes
        
    Returns:
        Geformatteerde string (bijv. '1.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def get_timestamp() -> str:
    """Geeft huidige timestamp als string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


if __name__ == "__main__":
    # Test utilities
    print("Testing AI Firewall Utilities...")
    
    # Test Config
    config = Config()
    print(f"✓ Config geladen: {config.get('training.test_size')}")
    
    # Test Logger
    logger = Logger("test", config)
    logger.get_logger().info("Test log bericht")
    print("✓ Logger werkt")
    
    # Test PredictionLogger
    pred_logger = PredictionLogger("logs/test_predictions.json")
    pred_logger.log_prediction(
        flow_data={'Protocol': 6, 'Flow Duration': 1000},
        prediction='benign',
        score=0.3,
        xgb_score=0.25,
        if_score=0.35
    )
    print("✓ PredictionLogger werkt")
    
    print("\n✅ Alle utilities werken correct!")
