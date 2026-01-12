# AI Firewall Proof of Concept 🔥🛡️

Een complete Python-oplossing voor **realtime netwerkflow classificatie** met Machine Learning. Dit project combineert XGBoost en Isolation Forest in een ensemble model voor het detecteren van malicious netwerkverkeer.

## 📋 Overzicht

Dit project biedt een end-to-end machine learning pipeline voor:
- **Training** van classificatiemodellen op netwerkflow data
- **Realtime inference** voor flow-by-flow classificatie
- **Anomaly detection** met Isolation Forest
- **Ensemble scoring** voor robuuste detectie
- **Visualisaties** van model performance en feature importances

## 🏗️ Projectstructuur

```
ML/
├── config.yaml                  # Configuratie bestand
├── requirements.txt             # Python dependencies
├── utils.py                     # Utilities (logging, config, etc.)
├── data_loading.py              # Data laden en preprocessing
├── feature_extraction.py        # Feature engineering
├── train_model.py              # Model training script
├── inference.py                # Realtime inference
├── visualize.py                # Extra visualisaties
├── ml_data/                    # Data directory
│   └── MachineLearningCVE/     # CSV bestanden
├── models/                     # Getrainde modellen (gegenereerd)
├── output/                     # Visualisaties (gegenereerd)
└── logs/                       # Prediction logs (gegenereerd)
```

## 🚀 Quick Start

### 1. Installatie

```powershell
# Installeer dependencies
pip install -r requirements.txt
```

**Voor GPU support (NVIDIA RTX 3060):**
```powershell
# Installeer XGBoost met CUDA support
pip install xgboost[gpu]
```

### 2. Configuratie

Bewerk `config.yaml` naar wens:
```yaml
training:
  use_gpu: true  # Zet op true voor GPU training
  test_size: 0.2
  
ensemble:
  xgboost_weight: 0.7
  isolation_forest_weight: 0.3
  threshold: 0.5
```

### 3. Model Training

```powershell
# Train modellen
python train_model.py
```

Dit voert de volledige pipeline uit:
- ✅ Laadt data van `ml_data/MachineLearningCVE/`
- ✅ Preprocessing en feature engineering
- ✅ Traint XGBoost en Isolation Forest
- ✅ Evalueert modellen (confusion matrix, ROC-AUC, etc.)
- ✅ Slaat modellen op naar `models/`
- ✅ Genereert visualisaties in `output/`

**Output:**
```
models/
  ├── xgboost_model_latest.pkl
  ├── isolation_forest_model_latest.pkl
  └── feature_transformers.pkl

output/
  ├── confusion_matrices.png
  ├── feature_importance.png
  └── anomaly_score_distribution.png
```

### 4. Realtime Inference

#### Single Flow Classificatie

```python
from inference import AIFirewallInference

# Initialiseer inference engine
firewall = AIFirewallInference()

# Classificeer een flow
flow_data = {
    'Destination Port': 80,
    'Flow Duration': 1500000,
    'Total Fwd Packets': 10,
    'Total Backward Packets': 8,
    # ... andere features
}

result = firewall.predict_single_flow(flow_data)

print(f"Prediction: {result['prediction']}")
print(f"Score: {result['ensemble_score']:.4f}")
print(f"Alert: {result['is_alert']}")
```

#### Batch Prediction

```python
# Meerdere flows classificeren
flows = [flow1, flow2, flow3]
results = firewall.predict_batch(flows)
```

#### CSV Classificatie

```python
# Classificeer flows van CSV
df_results = firewall.predict_from_csv(
    'ml_data/test_flows.csv',
    output_path='output/predictions.csv'
)
```

### 5. Test Inference

```powershell
# Test inference met voorbeeld flow
python inference.py
```

## 📊 Features

### Data Processing
- **Automatische CSV loading** van meerdere bestanden
- **Missing value handling** en outlier filtering
- **Feature engineering**: packet size ratios, bytes/sec, flags
- **Categorical encoding** (Protocol, etc.)
- **Feature scaling** (RobustScaler voor outlier resistance)

### Modellen

#### XGBoost Classifier
- **Primary model** voor classificatie
- GPU acceleration support (RTX 3060)
- Feature importance tracking
- Configureerbare hyperparameters

#### Isolation Forest
- **Anomaly detector** voor unseen attack patterns
- Complementeert XGBoost voor zero-day threats
- Unsupervised learning approach

#### Ensemble
- **Weighted combination** (default: 70% XGBoost, 30% IF)
- **Adaptive threshold** voor precision/recall tuning
- **Alert system** voor high-confidence threats

### Evaluatie Metrics
- Accuracy, F1-Score, ROC-AUC
- Precision-Recall curves
- Confusion matrices
- Feature importance visualization
- Anomaly score distributions

## ⚙️ Configuratie Opties

### GPU Training
```yaml
training:
  use_gpu: true
  xgboost:
    tree_method: 'gpu_hist'  # Automatisch gezet bij use_gpu: true
```

### Model Hyperparameters

**XGBoost:**
```yaml
training:
  xgboost:
    max_depth: 8
    learning_rate: 0.1
    n_estimators: 200
    subsample: 0.8
    colsample_bytree: 0.8
```

**Isolation Forest:**
```yaml
training:
  isolation_forest:
    n_estimators: 100
    max_samples: 256
    contamination: 0.1
```

### Ensemble Tuning
```yaml
ensemble:
  xgboost_weight: 0.7        # XGBoost invloed
  isolation_forest_weight: 0.3  # IF invloed
  threshold: 0.5             # Classificatie drempel
```

## 📈 Visualisaties

Het training script genereert automatisch:

1. **Confusion Matrices** - XGBoost en Ensemble performance
2. **Feature Importance** - Top 20 belangrijkste features
3. **Anomaly Score Distribution** - IF score verdeling per class

Extra visualisaties via `visualize.py`:
```powershell
python visualize.py
```

## 🔍 Logging

### Prediction Logging
Alle predictions worden automatisch gelogd naar `logs/predictions.json`:

```json
{
  "timestamp": "2025-11-06T10:30:45",
  "prediction": "malicious",
  "ensemble_score": 0.8234,
  "xgboost_score": 0.7891,
  "isolation_forest_score": 0.9200,
  "is_alert": true,
  "flow_summary": {
    "Protocol": 6,
    "Flow Duration": 1500000,
    "Destination Port": 443
  }
}
```

## 🛠️ Modules Overzicht

### `utils.py`
- **Config**: YAML configuratie management
- **Logger**: Custom logging setup
- **PredictionLogger**: JSON logging voor predictions
- **Model I/O**: save/load helpers met metadata

### `data_loading.py`
- **DataLoader**: CSV/Parquet data loading
- **Preprocessing**: Duplicates, missing values, outliers
- **Label creation**: Binary en multi-class labels
- **Train/test split**: Stratified splitting

### `feature_extraction.py`
- **FeatureExtractor**: Feature engineering pipeline
- **Engineering**: Ratio's, per-second metrics, flag counts
- **Encoding**: Categorical → numerical
- **Scaling**: StandardScaler of RobustScaler
- **Persistence**: Save/load transformers

### `train_model.py`
- **AIFirewallTrainer**: Complete training pipeline
- **Model training**: XGBoost + Isolation Forest
- **Evaluation**: Comprehensive metrics
- **Visualization**: Auto-generate plots
- **Model saving**: Timestamped + latest versions

### `inference.py`
- **AIFirewallInference**: Realtime inference engine
- **Single flow**: Dict input → classification
- **Batch prediction**: Multiple flows at once
- **CSV prediction**: Bulk file processing
- **Logging**: Automatic prediction logging

### `visualize.py`
- **Advanced plots**: ROC curves, PR curves
- **Performance analysis**: Model comparison
- **Data exploration**: Feature distributions

## 🎯 Use Cases

### 1. Home Network Protection
```python
# Monitor netwerkverkeer en blokkeer verdachte flows
firewall = AIFirewallInference()

for flow in network_monitor.get_flows():
    result = firewall.predict_single_flow(flow)
    
    if result['is_alert']:
        print(f"🚨 ALERT: {flow['Source IP']} → {flow['Destination IP']}")
        firewall_rules.block(flow['Source IP'])
```

### 2. Small Office Firewall
```python
# Batch analysis van netwerkverkeer logs
df = firewall.predict_from_csv('daily_network_logs.csv')

# Filter high-risk connections
alerts = df[df['Ensemble_Score'] > 0.7]
admin.send_alert_email(alerts)
```

### 3. Model Retraining
```python
# Periodiek retrainen met nieuwe data
trainer = AIFirewallTrainer()
trainer.train_full_pipeline()

# Deploy nieuwe modellen automatisch
deploy_models('models/')
```

## 📊 Dataset

Het project gebruikt de **CICIDS2017** dataset structuur:
- Netwerkflows met 80+ features
- Labels: BENIGN, DDoS, PortScan, Infiltration, Web Attacks
- CSV formaat met kolom headers

**Data locatie:** `ml_data/MachineLearningCVE/`

## 🔧 Troubleshooting

### GPU niet gedetecteerd
```powershell
# Controleer CUDA installatie
python -c "import xgboost as xgb; print(xgb.__version__)"

# Installeer GPU versie
pip uninstall xgboost
pip install xgboost --upgrade
```

### Memory errors bij grote datasets
Pas `config.yaml` aan:
```yaml
training:
  xgboost:
    max_samples: 100000  # Limiteer training samples
```

### Import errors
```powershell
# Herinstalleer dependencies
pip install -r requirements.txt --upgrade
```

## 📝 To-Do / Toekomstige Features

- [ ] **Real-time integration** met Suricata/Zeek
- [ ] **Web dashboard** voor monitoring
- [ ] **Automatic retraining** pipeline
- [ ] **Multi-class classification** (specifieke attack types)
- [ ] **Deep learning models** (LSTM voor sequential flows)
- [ ] **Explainable AI** (SHAP values voor predictions)

## 📄 Licentie

Dit is een proof-of-concept project voor educatieve doeleinden.

## 👨‍💻 Auteur

AI Firewall POC - Ontwikkeld voor thuisnetwerk en small office bescherming.

---

**🔥 Stay Safe! 🛡️**
