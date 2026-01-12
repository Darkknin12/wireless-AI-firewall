"""
Feature Extraction Module voor AI Firewall POC
Feature engineering, normalisatie en encoding voor netwerkflow data.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
import joblib
from pathlib import Path
import logging

from utils import Config, Logger


class FeatureExtractor:
    """Class voor feature engineering en transformatie."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialiseert FeatureExtractor.
        
        Args:
            config: Config object (optioneel)
        """
        self.config = config or Config()
        self.logger = Logger("FeatureExtractor", self.config).get_logger()
        
        self.scaler = None
        self.label_encoders = {}
        self.feature_names = None
        self.categorical_columns = []
        self.numeric_columns_for_scaling = []  # Bewaar welke kolommen geschaald werden
        
    def identify_feature_types(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Identificeert numerieke en categorische features.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dict met 'numeric' en 'categorical' kolommen
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Check config voor expliciet gedefinieerde categorische kolommen
        config_categorical = self.config.get('features.categorical_columns', [])
        for col in config_categorical:
            if col in numeric_cols:
                numeric_cols.remove(col)
                if col not in categorical_cols:
                    categorical_cols.append(col)
        
        self.logger.info(f"Feature types geïdentificeerd:")
        self.logger.info(f"  → Numeriek: {len(numeric_cols)} kolommen")
        self.logger.info(f"  → Categorisch: {len(categorical_cols)} kolommen")
        
        return {
            'numeric': numeric_cols,
            'categorical': categorical_cols
        }
    
    def encode_categorical_features(self, 
                                    df: pd.DataFrame,
                                    categorical_cols: Optional[List[str]] = None,
                                    fit: bool = True) -> pd.DataFrame:
        """
        Encodeert categorische features naar numerieke waarden.
        
        Args:
            df: Input DataFrame
            categorical_cols: Lijst van categorische kolommen
            fit: Of encoders gefitted moeten worden (True voor training)
            
        Returns:
            DataFrame met geëncodeerde features
        """
        df_encoded = df.copy()
        
        if categorical_cols is None:
            categorical_cols = df_encoded.select_dtypes(
                include=['object', 'category']
            ).columns.tolist()
        
        # Update categorical_columns alleen bij fit
        if fit:
            self.categorical_columns = categorical_cols
        
        if not categorical_cols:
            self.logger.info("Geen categorische kolommen om te encoden")
            return df_encoded
        
        self.logger.info(f"Encoden van {len(categorical_cols)} categorische kolommen...")
        
        for col in categorical_cols:
            if col not in df_encoded.columns:
                continue
                
            if fit:
                # Maak nieuwe encoder
                le = LabelEncoder()
                # Converteer naar string en handle missing values
                df_encoded[col] = df_encoded[col].astype(str).fillna('unknown')
                df_encoded[col] = le.fit_transform(df_encoded[col])
                self.label_encoders[col] = le
                self.logger.info(f"  → {col}: {len(le.classes_)} unieke waarden")
            else:
                # Gebruik bestaande encoder
                if col not in self.label_encoders:
                    self.logger.warning(f"Geen encoder gevonden voor {col}, skip...")
                    continue
                
                le = self.label_encoders[col]
                df_encoded[col] = df_encoded[col].astype(str).fillna('unknown')
                
                # Handle unseen labels
                df_encoded[col] = df_encoded[col].apply(
                    lambda x: x if x in le.classes_ else 'unknown'
                )
                df_encoded[col] = le.transform(df_encoded[col])
        
        return df_encoded
    
    def create_engineered_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Creëert extra engineered features voor netwerkflows.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame met extra features
        """
        df_eng = df.copy()
        self.logger.info("Creëren van engineered features...")
        
        new_features = 0
        
        # Packet size statistieken
        if 'Total Fwd Packets' in df_eng.columns and 'Total Length of Fwd Packets' in df_eng.columns:
            df_eng['Avg_Fwd_Packet_Size'] = df_eng['Total Length of Fwd Packets'] / (
                df_eng['Total Fwd Packets'] + 1  # +1 om delen door 0 te voorkomen
            )
            new_features += 1
        
        if 'Total Backward Packets' in df_eng.columns and 'Total Length of Bwd Packets' in df_eng.columns:
            df_eng['Avg_Bwd_Packet_Size'] = df_eng['Total Length of Bwd Packets'] / (
                df_eng['Total Backward Packets'] + 1
            )
            new_features += 1
        
        # Flow ratio's
        if 'Total Fwd Packets' in df_eng.columns and 'Total Backward Packets' in df_eng.columns:
            total_packets = df_eng['Total Fwd Packets'] + df_eng['Total Backward Packets']
            df_eng['Fwd_Bwd_Packet_Ratio'] = df_eng['Total Fwd Packets'] / (total_packets + 1)
            new_features += 1
        
        # Bytes per second
        if 'Flow Duration' in df_eng.columns:
            duration_sec = df_eng['Flow Duration'] / 1000000  # Microseconden naar seconden
            duration_sec = duration_sec.replace(0, 0.001)  # Voorkom delen door 0
            
            if 'Total Length of Fwd Packets' in df_eng.columns:
                df_eng['Fwd_Bytes_Per_Sec'] = df_eng['Total Length of Fwd Packets'] / duration_sec
                new_features += 1
            
            if 'Total Length of Bwd Packets' in df_eng.columns:
                df_eng['Bwd_Bytes_Per_Sec'] = df_eng['Total Length of Bwd Packets'] / duration_sec
                new_features += 1
        
        # Flags ratio (als beschikbaar)
        flag_columns = [col for col in df_eng.columns if 'Flag' in col or 'flag' in col]
        if len(flag_columns) > 0:
            df_eng['Total_Flags'] = df_eng[flag_columns].sum(axis=1)
            new_features += 1
        
        # Vervang infinite values
        df_eng = df_eng.replace([np.inf, -np.inf], np.nan)
        
        # Fill NaN met 0 voor nieuwe features
        df_eng.fillna(0, inplace=True)
        
        self.logger.info(f"  → {new_features} nieuwe features gecreëerd")
        
        return df_eng
    
    def scale_features(self, 
                      df: pd.DataFrame,
                      fit: bool = True,
                      method: str = 'robust') -> pd.DataFrame:
        """
        Schaalt numerieke features.
        
        Args:
            df: Input DataFrame
            fit: Of scaler gefitted moet worden (True voor training)
            method: 'standard' of 'robust' scaling
            
        Returns:
            DataFrame met geschaalde features
        """
        if not self.config.get('features.scale_features', True):
            self.logger.info("Feature scaling uitgeschakeld in config")
            return df
        
        df_scaled = df.copy()
        
        # Selecteer alleen numerieke kolommen
        numeric_cols = df_scaled.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            self.logger.warning("Geen numerieke kolommen om te schalen")
            return df_scaled
        
        if fit:
            # Maak nieuwe scaler
            if method == 'robust':
                self.scaler = RobustScaler()
                self.logger.info("RobustScaler gebruikt (robuust tegen outliers)")
            else:
                self.scaler = StandardScaler()
                self.logger.info("StandardScaler gebruikt")
            
            # Bewaar welke kolommen geschaald worden
            self.numeric_columns_for_scaling = numeric_cols
            df_scaled[numeric_cols] = self.scaler.fit_transform(df_scaled[numeric_cols])
        else:
            # Gebruik bestaande scaler en alleen de kolommen die tijdens fit geschaald werden
            if self.scaler is None:
                raise ValueError("Scaler niet gefit! Roep eerst aan met fit=True")
            
            # Gebruik alleen kolommen die tijdens fit aanwezig waren
            cols_to_scale = [col for col in self.numeric_columns_for_scaling if col in df_scaled.columns]
            
            if cols_to_scale:
                df_scaled[cols_to_scale] = self.scaler.transform(df_scaled[cols_to_scale])
        
        self.logger.info(f"  → {len(numeric_cols)} features geschaald")
        
        return df_scaled
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit en transform features (voor training data).
        
        Args:
            df: Training DataFrame
            
        Returns:
            Getransformeerde DataFrame
        """
        self.logger.info("Fitting en transforming features...")
        
        # Engineer features
        df_transformed = self.create_engineered_features(df)
        
        # Encode categoricals
        feature_types = self.identify_feature_types(df_transformed)
        df_transformed = self.encode_categorical_features(
            df_transformed, 
            feature_types['categorical'],
            fit=True
        )
        
        # Scale features
        df_transformed = self.scale_features(df_transformed, fit=True)
        
        # Bewaar feature names
        self.feature_names = df_transformed.columns.tolist()
        
        self.logger.info(f"Feature transformation compleet. Features: {len(self.feature_names)}")
        
        return df_transformed
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform features (voor test/inference data).
        
        Args:
            df: DataFrame om te transformeren
            
        Returns:
            Getransformeerde DataFrame
        """
        # Engineer features
        df_transformed = self.create_engineered_features(df)
        
        # EERST: Voeg ontbrekende features toe met waarde 0
        if self.feature_names:
            for feature in self.feature_names:
                if feature not in df_transformed.columns:
                    df_transformed[feature] = 0
        
        # Encode categoricals (gebruik opgeslagen categorical_columns lijst)
        if self.categorical_columns:
            self.logger.info(f"Transforming met {len(self.categorical_columns)} categorische kolommen: {self.categorical_columns}")
            # Converteer categorische kolommen naar juiste types indien nodig
            for col in self.categorical_columns:
                if col in df_transformed.columns:
                    # Zorg dat kolom als object/string behandeld wordt voor encoding
                    if col in self.label_encoders:
                        df_transformed[col] = df_transformed[col].astype(str)
            
            df_transformed = self.encode_categorical_features(
                df_transformed,
                self.categorical_columns,
                fit=False
            )
        else:
            self.logger.info("Geen categorical_columns opgeslagen")
        
        # Scale features
        df_transformed = self.scale_features(df_transformed, fit=False)
        
        # Selecteer alleen bekende features in de juiste volgorde
        if self.feature_names:
            df_transformed = df_transformed[self.feature_names]
        
        return df_transformed
    
    def save_transformers(self, filepath: str):
        """
        Slaat feature transformers op.
        
        Args:
            filepath: Pad om transformers op te slaan
        """
        transformers = {
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'categorical_columns': self.categorical_columns,
            'numeric_columns_for_scaling': self.numeric_columns_for_scaling
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(transformers, filepath)
        self.logger.info(f"Transformers opgeslagen naar {filepath}")
    
    def load_transformers(self, filepath: str):
        """
        Laadt feature transformers.
        
        Args:
            filepath: Pad naar transformers bestand
        """
        transformers = joblib.load(filepath)
        
        self.scaler = transformers['scaler']
        self.label_encoders = transformers['label_encoders']
        self.feature_names = transformers['feature_names']
        self.categorical_columns = transformers['categorical_columns']
        self.numeric_columns_for_scaling = transformers.get('numeric_columns_for_scaling', [])
        
        self.logger.info(f"Transformers geladen van {filepath}")
        self.logger.info(f"  → {len(self.feature_names)} features")


if __name__ == "__main__":
    # Test feature extraction
    print("Testing Feature Extraction Module...")
    
    from data_loading import DataLoader
    
    config = Config()
    loader = DataLoader(config)
    extractor = FeatureExtractor(config)
    
    try:
        # Laad sample data
        df = loader.load_csv_files()
        df = loader.preprocess_data(df)
        df = loader.create_binary_labels(df)
        
        # Split data
        X_train, X_test, y_train, y_test = loader.split_data(df)
        
        print(f"✓ Data geladen: {X_train.shape}")
        
        # Fit transform op training data
        X_train_transformed = extractor.fit_transform(X_train)
        print(f"✓ Training features getransformeerd: {X_train_transformed.shape}")
        
        # Transform test data
        X_test_transformed = extractor.transform(X_test)
        print(f"✓ Test features getransformeerd: {X_test_transformed.shape}")
        
        # Test save/load
        extractor.save_transformers("models/feature_transformers.pkl")
        print(f"✓ Transformers opgeslagen")
        
        print("\n✅ Feature extraction module werkt correct!")
        
    except Exception as e:
        print(f"❌ Fout: {e}")
        import traceback
        traceback.print_exc()
