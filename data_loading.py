"""
Data Loading Module voor AI Firewall POC
Functies voor het laden, preprocessen en splitsen van netwerkflow data.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional, Union
from sklearn.model_selection import train_test_split
import logging

from utils import Config, Logger


class DataLoader:
    """Class voor het laden en preprocessen van netwerkflow data."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialiseert DataLoader.
        
        Args:
            config: Config object (optioneel)
        """
        self.config = config or Config()
        self.logger = Logger("DataLoader", self.config).get_logger()
        self.label_column = 'Label'  # Default label kolom naam
        
    def load_csv_files(self, 
                       data_dir: Optional[str] = None,
                       file_pattern: str = "*.csv") -> pd.DataFrame:
        """
        Laadt alle CSV bestanden uit een directory.
        
        Args:
            data_dir: Directory met CSV bestanden
            file_pattern: Patroon voor bestandsnamen
            
        Returns:
            Gecombineerde DataFrame
        """
        if data_dir is None:
            data_dir = self.config.get('data.input_dir')
        
        data_path = Path(data_dir)
        
        if not data_path.exists():
            raise FileNotFoundError(f"Data directory niet gevonden: {data_dir}")
        
        csv_files = list(data_path.glob(file_pattern))
        
        if not csv_files:
            raise FileNotFoundError(f"Geen CSV bestanden gevonden in {data_dir}")
        
        self.logger.info(f"Gevonden {len(csv_files)} CSV bestanden")
        
        dataframes = []
        for csv_file in csv_files:
            self.logger.info(f"Laden: {csv_file.name}")
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
                # Normaliseer kolomnamen (verwijder leading/trailing spaties)
                df.columns = df.columns.str.strip()
                dataframes.append(df)
                self.logger.info(f"  → {len(df)} rijen geladen")
            except Exception as e:
                self.logger.error(f"Fout bij laden {csv_file.name}: {e}")
                continue
        
        if not dataframes:
            raise ValueError("Geen data geladen uit CSV bestanden")
        
        # Combineer alle DataFrames
        combined_df = pd.concat(dataframes, ignore_index=True)
        self.logger.info(f"Totaal {len(combined_df)} rijen geladen uit {len(dataframes)} bestanden")
        
        return combined_df
    
    def load_parquet(self, filepath: str) -> pd.DataFrame:
        """
        Laadt Parquet bestand.
        
        Args:
            filepath: Pad naar Parquet bestand
            
        Returns:
            DataFrame
        """
        self.logger.info(f"Laden Parquet: {filepath}")
        df = pd.read_parquet(filepath)
        self.logger.info(f"  → {len(df)} rijen geladen")
        return df
    
    def preprocess_data(self, 
                       df: pd.DataFrame,
                       drop_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Voert basis preprocessing uit op data.
        
        Args:
            df: Input DataFrame
            drop_columns: Kolommen om te verwijderen
            
        Returns:
            Gepreprocessed DataFrame
        """
        self.logger.info("Start preprocessing...")
        df_clean = df.copy()
        
        # Verwijder duplicaten
        original_len = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        if len(df_clean) < original_len:
            self.logger.info(f"  → {original_len - len(df_clean)} duplicaten verwijderd")
        
        # Standaardiseer kolomnamen (strip whitespace)
        df_clean.columns = df_clean.columns.str.strip()
        
        # Drop specified columns
        if drop_columns is None:
            drop_columns = self.config.get('features.drop_columns', [])
        
        cols_to_drop = [col for col in drop_columns if col in df_clean.columns]
        if cols_to_drop:
            df_clean = df_clean.drop(columns=cols_to_drop)
            self.logger.info(f"  → {len(cols_to_drop)} kolommen verwijderd")
        
        # Vervang infinite values met NaN
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
        
        # Log missing values
        missing = df_clean.isnull().sum()
        if missing.sum() > 0:
            self.logger.warning(f"  → Missing values gevonden in {(missing > 0).sum()} kolommen")
            # Fill missing values met median voor numerieke kolommen
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df_clean[col].isnull().sum() > 0:
                    median_val = df_clean[col].median()
                    df_clean[col].fillna(median_val, inplace=True)
        
        self.logger.info(f"Preprocessing compleet. Shape: {df_clean.shape}")
        return df_clean
    
    def create_binary_labels(self, 
                            df: pd.DataFrame,
                            label_column: str = 'Label') -> pd.DataFrame:
        """
        Creëert binaire labels (0 = benign, 1 = malicious).
        
        Args:
            df: Input DataFrame
            label_column: Naam van de label kolom
            
        Returns:
            DataFrame met binaire labels
        """
        df_labeled = df.copy()
        self.label_column = label_column
        
        if label_column not in df_labeled.columns:
            self.logger.error(f"Label kolom '{label_column}' niet gevonden!")
            self.logger.info(f"Beschikbare kolommen: {df_labeled.columns.tolist()}")
            raise ValueError(f"Label kolom '{label_column}' niet gevonden")
        
        # Detecteer unieke labels
        unique_labels = df_labeled[label_column].unique()
        self.logger.info(f"Unieke labels gevonden: {unique_labels}")
        
        # Converteer naar binair (alles wat niet 'BENIGN' is, is malicious)
        df_labeled['BinaryLabel'] = df_labeled[label_column].apply(
            lambda x: 0 if str(x).upper() in ['BENIGN', 'NORMAL', '0'] else 1
        )
        
        # Log distributie
        label_counts = df_labeled['BinaryLabel'].value_counts()
        self.logger.info(f"Label distributie:")
        self.logger.info(f"  → Benign (0): {label_counts.get(0, 0)} ({label_counts.get(0, 0)/len(df_labeled)*100:.2f}%)")
        self.logger.info(f"  → Malicious (1): {label_counts.get(1, 0)} ({label_counts.get(1, 0)/len(df_labeled)*100:.2f}%)")
        
        return df_labeled
    
    def split_data(self, 
                   df: pd.DataFrame,
                   target_column: str = 'BinaryLabel',
                   test_size: Optional[float] = None,
                   random_state: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Splitst data in train en test sets.
        
        Args:
            df: Input DataFrame
            target_column: Naam van de target kolom
            test_size: Percentage voor test set
            random_state: Random seed
            
        Returns:
            Tuple van (X_train, X_test, y_train, y_test)
        """
        if test_size is None:
            test_size = self.config.get('training.test_size', 0.2)
        
        if random_state is None:
            random_state = self.config.get('training.random_state', 42)
        
        # Scheidt features en target
        if target_column not in df.columns:
            raise ValueError(f"Target kolom '{target_column}' niet gevonden")
        
        X = df.drop(columns=[target_column, self.label_column], errors='ignore')
        y = df[target_column]
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=test_size, 
            random_state=random_state,
            stratify=y  # Behoud label distributie
        )
        
        self.logger.info(f"Data gesplitst:")
        self.logger.info(f"  → Train set: {len(X_train)} samples")
        self.logger.info(f"  → Test set: {len(X_test)} samples")
        self.logger.info(f"  → Features: {X_train.shape[1]}")
        
        return X_train, X_test, y_train, y_test
    
    def save_processed_data(self, 
                           df: pd.DataFrame, 
                           filename: str,
                           format: str = 'parquet'):
        """
        Slaat gepreprocessed data op.
        
        Args:
            df: DataFrame om op te slaan
            filename: Bestandsnaam
            format: 'parquet' of 'csv'
        """
        output_dir = Path(self.config.get('data.output_dir'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        
        if format == 'parquet':
            df.to_parquet(filepath, index=False)
        elif format == 'csv':
            df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Onbekend formaat: {format}")
        
        self.logger.info(f"Data opgeslagen naar {filepath}")


def load_and_prepare_data(config: Optional[Config] = None) -> Tuple:
    """
    Convenience functie om data te laden en voor te bereiden.
    
    Args:
        config: Config object (optioneel)
        
    Returns:
        Tuple van (X_train, X_test, y_train, y_test, feature_names)
    """
    loader = DataLoader(config)
    
    # Laad data
    df = loader.load_csv_files()
    
    # Preprocess
    df = loader.preprocess_data(df)
    
    # Creëer binaire labels
    df = loader.create_binary_labels(df)
    
    # Split data
    X_train, X_test, y_train, y_test = loader.split_data(df)
    
    # Feature names
    feature_names = X_train.columns.tolist()
    
    return X_train, X_test, y_train, y_test, feature_names


if __name__ == "__main__":
    # Test data loading
    print("Testing Data Loading Module...")
    
    config = Config()
    loader = DataLoader(config)
    
    try:
        # Test laden van data
        df = loader.load_csv_files()
        print(f"✓ Data geladen: {df.shape}")
        print(f"  Kolommen: {list(df.columns[:5])}...")
        
        # Test preprocessing
        df_clean = loader.preprocess_data(df)
        print(f"✓ Preprocessing compleet: {df_clean.shape}")
        
        # Test label creation
        df_labeled = loader.create_binary_labels(df_clean)
        print(f"✓ Labels gecreëerd")
        
        # Test data split
        X_train, X_test, y_train, y_test = loader.split_data(df_labeled)
        print(f"✓ Data gesplitst: train={len(X_train)}, test={len(X_test)}")
        
        print("\n✅ Data loading module werkt correct!")
        
    except Exception as e:
        print(f"❌ Fout: {e}")
        import traceback
        traceback.print_exc()
