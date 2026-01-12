# 🚀 QUICK START GUIDE

## ⚡ Snelle Installatie en Start

### Stap 1: Installeer Dependencies

```powershell
# Installeer alle requirements
pip install -r requirements.txt

# Voor GPU support (NVIDIA RTX 3060):
pip install xgboost --upgrade
```

### Stap 2: Controleer Data

Zorg dat je CSV bestanden in de `ml_data/MachineLearningCVE/` directory staan:

```
ml_data/
└── MachineLearningCVE/
    ├── Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
    ├── Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
    ├── Monday-WorkingHours.pcap_ISCX.csv
    └── ... (andere CSV bestanden)
```

### Stap 3: Configuratie (Optioneel)

Edit `config.yaml` voor GPU support:

```yaml
training:
  use_gpu: true  # Zet op true voor RTX 3060
```

### Stap 4: Train Modellen

```powershell
# Via main script (AANBEVOLEN)
python main.py train

# Of direct:
python train_model.py
```

Dit duurt 5-15 minuten afhankelijk van je hardware.

### Stap 5: Test Inference

```powershell
# Test met voorbeeld flow
python main.py inference

# Of direct:
python inference.py
```

### Stap 6: Genereer Visualisaties

```powershell
python main.py visualize
```

Check `output/` directory voor plots!

---

## 📊 Gebruik in Code

### Single Flow Classificatie

```python
from inference import AIFirewallInference

# Load firewall
firewall = AIFirewallInference()

# Classificeer een flow
flow = {
    'Destination Port': 443,
    'Flow Duration': 1500000,
    'Total Fwd Packets': 10,
    # ... andere features
}

result = firewall.predict_single_flow(flow)

if result['is_alert']:
    print(f"🚨 MALICIOUS! Score: {result['ensemble_score']:.2f}")
else:
    print(f"✓ Benign. Score: {result['ensemble_score']:.2f}")
```

### CSV Classificatie

```python
from inference import AIFirewallInference

firewall = AIFirewallInference()

# Classificeer hele CSV
df = firewall.predict_from_csv(
    'network_logs.csv',
    output_path='predictions_output.csv'
)

# Filter alerts
alerts = df[df['Prediction_Label'] == 'malicious']
print(f"Found {len(alerts)} malicious flows!")
```

---

## 🎯 CLI Commands

```powershell
# Status check
python main.py status

# Train modellen
python main.py train

# Test inference
python main.py inference

# Genereer visualisaties
python main.py visualize

# Classificeer CSV
python main.py classify data.csv -o results.csv
```

---

## 🔧 Troubleshooting

### "FileNotFoundError: Data directory not found"
→ Check dat CSV bestanden in `ml_data/MachineLearningCVE/` staan

### "Module not found: xgboost"
→ Run: `pip install -r requirements.txt`

### "GPU not detected"
→ Check CUDA installatie of zet `use_gpu: false` in config.yaml

### "Memory Error"
→ Limiteer data in config.yaml:
```yaml
training:
  max_samples: 100000
```

---

## 📁 Project Structuur

```
ML/
├── main.py              ← START HIER
├── train_model.py       ← Model training
├── inference.py         ← Realtime classificatie
├── visualize.py         ← Extra plots
├── config.yaml          ← Configuratie
├── requirements.txt     ← Dependencies
├── utils.py            
├── data_loading.py     
├── feature_extraction.py
├── ml_data/             ← Je data hier
│   └── MachineLearningCVE/
├── models/              ← Getrainde modellen (auto-generated)
├── output/              ← Visualisaties (auto-generated)
└── logs/                ← Prediction logs (auto-generated)
```

---

## ✅ Checklist

- [ ] Python 3.8+ geïnstalleerd
- [ ] Dependencies geïnstalleerd (`pip install -r requirements.txt`)
- [ ] CSV data in `ml_data/MachineLearningCVE/`
- [ ] Config aangepast (GPU enabled?)
- [ ] Modellen getraind (`python main.py train`)
- [ ] Inference getest (`python main.py inference`)
- [ ] Visualisaties gegenereerd (`python main.py visualize`)

---

## 🎓 Next Steps

1. **Integreer met netwerkmonitor** (Suricata/Zeek)
2. **Deploy als service** (Flask API)
3. **Automatisch retrainen** met nieuwe data
4. **Dashboard bouwen** voor real-time monitoring
5. **Alert systeem** naar email/Slack

---

**🔥 Veel succes met je AI Firewall! 🛡️**
