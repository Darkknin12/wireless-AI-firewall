# 🗑️ Unused Files - Mogelijk te Verwijderen

Dit bestand bevat een lijst van bestanden die waarschijnlijk **niet meer nodig** zijn voor het project. Deze kunnen worden verwijderd om de repository schoon te houden.

> ⚠️ **Let op**: Controleer elk bestand voordat je het verwijdert!

---

## 📄 Documentatie Files (Mogelijk Redundant)

Deze documentatie bestanden overlappen met PRESENTATIE.md en README.md:

| Bestand | Reden | Actie |
|---------|-------|-------|
| `ATTACK_TYPES.md` | Info staat in PRESENTATIE.md | ❓ Review |
| `AUTOMATIC_BLOCKING.md` | Feature niet geïmplementeerd | ✅ Delete |
| `COMMANDS.md` | Basis commands, niet nodig | ✅ Delete |
| `COMPLETE_SUMMARY.md` | Oude samenvatting | ✅ Delete |
| `DEPLOYMENT.md` | Info staat in README.md | ❓ Review |
| `FIREWALL_SETUP.md` | Suricata niet meer gebruikt | ✅ Delete |
| `GAMING_IMPACT.md` | Niet relevant | ✅ Delete |
| `IMPLEMENTATION_SUMMARY.md` | Oude samenvatting | ✅ Delete |
| `MANUFACTURING.md` | Niet relevant | ✅ Delete |
| `PLUG_AND_PLAY.md` | Concept niet uitgewerkt | ✅ Delete |
| `PROJECT_ANALYSIS.md` | Oude analyse | ✅ Delete |
| `QUICKSTART.md` | Info in README.md | ❓ Review |
| `QUICKSTART_RPI.md` | Raspberry Pi niet getest | ✅ Delete |
| `RASPBERRY_PI_SETUP.md` | Raspberry Pi niet getest | ✅ Delete |
| `RPI_OVERVIEW.md` | Raspberry Pi niet getest | ✅ Delete |
| `USER_MANUAL.md` | Info in README/PRESENTATIE | ❓ Review |
| `logboek.md` | Vervangen door LOGBOEK_FINAL.md | ✅ Delete |
| `logboek_week2.md` | Vervangen door LOGBOEK_FINAL.md | ✅ Delete |

---

## 🐍 Python Scripts (Niet Meer Nodig)

Oude test scripts en diagnose tools:

| Bestand | Reden | Actie |
|---------|-------|-------|
| `diagnose_model.py` | Debug script, niet nodig | ✅ Delete |
| `diagnose_v2.py` | Debug script, niet nodig | ✅ Delete |
| `patch_fix.py` | One-time fix, niet nodig | ✅ Delete |
| `PROJECT_SUMMARY.py` | Oude summary generator | ✅ Delete |
| `example_realtime.py` | Example code | ❓ Review |
| `demo_blocking.py` | Blocking niet geïmplementeerd | ✅ Delete |
| `benchmark_latency.py` | Benchmarking | ❓ Review |

### Test Scripts (Veel Overlap)

| Bestand | Reden | Actie |
|---------|-------|-------|
| `test_attacks_v2.py` | Vervangen door test_wireless_attacks.py | ✅ Delete |
| `test_blocking.py` | Blocking niet geïmplementeerd | ✅ Delete |
| `test_blocking_simple.py` | Blocking niet geïmplementeerd | ✅ Delete |
| `test_custom_attacks.py` | Oude versie | ✅ Delete |
| `test_dashboard.py` | Dashboard handmatig getest | ✅ Delete |
| `test_dashboard_internal.py` | Oude dashboard test | ✅ Delete |
| `test_live_blocking.py` | Blocking niet geïmplementeerd | ✅ Delete |
| `test_ml_attacks.py` | Vervangen door test_wireless_attacks.py | ✅ Delete |
| `test_real_attacks.py` | Vervangen door test_wireless_attacks.py | ✅ Delete |
| `test_real_data.py` | Oude data test | ✅ Delete |
| `test_system.py` | System test | ❓ Review |

---

## 🐳 Docker Files (Raspberry Pi Specifiek)

Niet getest/gebruikt:

| Bestand | Reden | Actie |
|---------|-------|-------|
| `docker-compose-rpi.yml` | Raspberry Pi niet getest | ✅ Delete |
| `docker-compose-full.yml` | Alternatieve compose | ❓ Review |
| `docker-compose-test.yml` | Test compose | ✅ Delete |
| `Dockerfile.rpi` | Raspberry Pi niet getest | ✅ Delete |
| `Dockerfile.firewall` | Niet gebruikt | ✅ Delete |
| `nginx-rpi.conf` | Raspberry Pi niet getest | ✅ Delete |
| `nginx-blocking.conf` | Blocking niet geïmplementeerd | ✅ Delete |

---

## 📜 Setup/Config Files (Niet Gebruikt)

| Bestand | Reden | Actie |
|---------|-------|-------|
| `ai-firewall.service` | Systemd service, niet Docker | ✅ Delete |
| `factory_setup.sh` | Manufacturing setup | ✅ Delete |
| `install.sh` | Manual install, we use Docker | ✅ Delete |
| `start.sh` | Start script, docker-compose volstaat | ❓ Review |
| `setup_windows_firewall.ps1` | Windows blocking niet getest | ✅ Delete |
| `suricata_integration.py` | Suricata verwijderd | ✅ Delete |
| `suricata_ml_blocker.py` | Suricata verwijderd | ✅ Delete |
| `config.yaml` | Mogelijk duplicate van config.json | ❓ Review |
| `init-db.sql` | Database niet gebruikt (Redis wel) | ✅ Delete |

---

## 📁 Folders (Mogelijk Leeg of Ongebruikt)

| Folder | Reden | Actie |
|--------|-------|-------|
| `init.sql/` | Database niet gebruikt | ✅ Delete |
| `ssl/` | SSL niet geconfigureerd | ❓ Review |
| `grafana/` | Grafana niet geïmplementeerd | ✅ Delete |
| `logs/` | Mogelijk leeg, check eerst | ❓ Review |
| `output/` | Check inhoud | ❓ Review |
| `predictions/` | Check inhoud | ❓ Review |

---

## 🗑️ Dashboard Files (Duplicaten)

| Bestand | Reden | Actie |
|---------|-------|-------|
| `dashboard.js` (root) | Duplicate van dashboard/dashboard.js | ✅ Delete |
| `dashboard/index-blocking.html` | Blocking niet geïmplementeerd | ✅ Delete |
| `dashboard/dashboard-blocking.js` | Blocking niet geïmplementeerd | ✅ Delete |
| `dashboard/setup-wizard.html` | Wizard niet geïmplementeerd | ✅ Delete |
| `dashboard/dist/` | Build output, check inhoud | ❓ Review |

---

## ✅ Bestanden om te BEHOUDEN

Deze zijn **essentieel** voor het project:

### Core Files
- `api_server.py` - FastAPI server
- `inference.py` - ML inference
- `feature_extraction.py` - Feature extraction
- `train_model.py` - Model training
- `data_loading.py` - Data loading
- `main.py` - Entry point
- `utils.py` - Utilities

### Config
- `docker-compose.yml` - Main Docker setup
- `Dockerfile` - Main container
- `nginx.conf` - Nginx config
- `config.json` - App config
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore

### Dashboard
- `dashboard/index.html` - Main dashboard
- `dashboard/dashboard.js` - Dashboard JS
- `dashboard/style.css` - Dashboard CSS

### Documentation
- `README.md` - Project readme
- `PRESENTATIE.md` - Presentation
- `LOGBOEK_FINAL.md` - Final logbook

### Testing
- `test_wireless_attacks.py` - Attack simulator
- `create_presentation.py` - PowerPoint generator

### Data & Models
- `ml_data/` - Training data
- `models/` - Trained models
- `data/` - Additional data

---

## 🧹 Quick Cleanup Commands

```powershell
# Verwijder redundante documentatie
Remove-Item ATTACK_TYPES.md, AUTOMATIC_BLOCKING.md, COMMANDS.md, COMPLETE_SUMMARY.md -Force
Remove-Item FIREWALL_SETUP.md, GAMING_IMPACT.md, IMPLEMENTATION_SUMMARY.md -Force
Remove-Item MANUFACTURING.md, PLUG_AND_PLAY.md, PROJECT_ANALYSIS.md -Force
Remove-Item QUICKSTART_RPI.md, RASPBERRY_PI_SETUP.md, RPI_OVERVIEW.md -Force
Remove-Item logboek.md, logboek_week2.md -Force

# Verwijder oude test scripts
Remove-Item diagnose_model.py, diagnose_v2.py, patch_fix.py, PROJECT_SUMMARY.py -Force
Remove-Item demo_blocking.py -Force
Remove-Item test_attacks_v2.py, test_blocking.py, test_blocking_simple.py -Force
Remove-Item test_custom_attacks.py, test_dashboard.py, test_dashboard_internal.py -Force
Remove-Item test_live_blocking.py, test_ml_attacks.py, test_real_attacks.py, test_real_data.py -Force

# Verwijder RPi/blocking files
Remove-Item docker-compose-rpi.yml, docker-compose-test.yml -Force
Remove-Item Dockerfile.rpi, Dockerfile.firewall -Force
Remove-Item nginx-rpi.conf, nginx-blocking.conf -Force

# Verwijder setup scripts
Remove-Item ai-firewall.service, factory_setup.sh, install.sh -Force
Remove-Item setup_windows_firewall.ps1 -Force
Remove-Item suricata_integration.py, suricata_ml_blocker.py -Force
Remove-Item init-db.sql -Force

# Verwijder duplicate dashboard files
Remove-Item dashboard.js -Force
Remove-Item dashboard/index-blocking.html, dashboard/dashboard-blocking.js -Force
Remove-Item dashboard/setup-wizard.html -Force

# Verwijder folders
Remove-Item -Recurse -Force init.sql, grafana -ErrorAction SilentlyContinue
```

---

## 📊 Samenvatting

| Categorie | Te Verwijderen | Te Reviewen | Te Behouden |
|-----------|----------------|-------------|-------------|
| Documentatie | 15 | 4 | 3 |
| Python Scripts | 14 | 3 | 8 |
| Docker Files | 6 | 1 | 2 |
| Config Files | 8 | 2 | 6 |
| Dashboard | 4 | 1 | 3 |
| **Totaal** | **47** | **11** | **22** |

Na cleanup blijven er **~22 essentiële bestanden** over, wat het project veel overzichtelijker maakt.

---

*Gegenereerd op: Januari 12, 2026*
