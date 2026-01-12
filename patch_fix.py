"""
Patch de feature_extraction.py transform() functie om kolomnamen te strippen
"""

# Dit is de nieuwe transform functie met fix voor spaties in kolomnamen

NEW_TRANSFORM_CODE = '''
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform features (voor test/inference data).

        Args:
            df: DataFrame om te transformeren

        Returns:
            Getransformeerde DataFrame
        """
        # STRIP COLUMN NAMES - Fix voor spaties in CSV kolomnamen
        df.columns = [col.strip() for col in df.columns]
        
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
'''

print("Run dit commando om de fix toe te passen:")
print("De transform() functie moet beginnen met: df.columns = [col.strip() for col in df.columns]")
