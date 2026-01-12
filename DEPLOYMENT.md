# 🚀 AI-Firewall Deployment Guide

Complete deployment guide voor productie omgeving.

## 📋 Inhoudsopgave

1. [Hardware Requirements](#hardware-requirements)
2. [Docker Deployment](#docker-deployment)
3. [Suricata Integration](#suricata-integration)
4. [Dashboard Setup](#dashboard-setup)
5. [Production Best Practices](#production-best-practices)

---

## 💻 Hardware Requirements

### Minimale Specificaties (Development/Testing)

```
CPU:     4 cores (Intel i5/AMD Ryzen 5 of hoger)
RAM:     8 GB minimum, 16 GB aanbevolen
Storage: 10 GB SSD (dataset + models + outputs)
GPU:     Optioneel (NVIDIA RTX 2060 of hoger)
Network: 100 Mbps
```

### Aanbevolen Specificaties (Production/Real-time)

```
CPU:     8+ cores (Intel i7/Xeon, AMD Ryzen 7/Threadripper)
RAM:     16-32 GB (voor multi-threading + caching)
Storage: 50-100 GB SSD (logs + historical data)
GPU:     Optioneel - NVIDIA RTX 3060 12GB of hoger
Network: 1 Gbps+ (voor packet capture)
```

### Huidige Systeem Check

```bash
# CPU & RAM info
python -c "import psutil; print(f'CPU: {psutil.cpu_count()} cores'); print(f'RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB')"

# Model sizes
ls -lh models/*.pkl
```

### Resource Usage

| Component | CPU Usage | RAM Usage | Disk I/O |
|-----------|-----------|-----------|----------|
| Model Loading | Low | 2-4 GB | One-time |
| Single Flow Inference | <1% | <100 MB | Minimal |
| Batch Processing (1000 flows) | 20-40% | 500 MB - 1 GB | Moderate |
| Real-time Monitoring | 10-30% | 1-2 GB | High (logs) |
| Dashboard | <5% | <200 MB | Low |

---

## 🐳 Docker Deployment

### 1. Build Docker Image

```bash
# Build image
docker build -t ai-firewall:latest .

# Verificatie
docker images | grep ai-firewall
```

### 2. Run met Docker Compose

```bash
# Start alle services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f ai-firewall

# Stop services
docker-compose down
```

### 3. Standalone Container

```bash
# Run alleen AI-Firewall API
docker run -d \
  --name ai-firewall \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models:ro \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/predictions:/app/predictions \
  -e MODEL_PATH=/app/models \
  -e LOG_LEVEL=INFO \
  ai-firewall:latest

# Test API
curl http://localhost:8000/health
```

### 4. Docker Compose Services

De `docker-compose.yml` bevat:

- **ai-firewall**: ML inference engine (FastAPI)
- **dashboard**: Web UI (Nginx)
- **redis**: Caching layer
- **postgres**: Logging database
- **suricata**: IDS/IPS packet capture

---

## 🔍 Suricata Integration

### 1. Installeer Suricata

**Ubuntu/Debian:**
```bash
sudo add-apt-repository ppa:oisf/suricata-stable
sudo apt-get update
sudo apt-get install suricata
```

**CentOS/RHEL:**
```bash
sudo yum install epel-release
sudo yum install suricata
```

**Docker:**
```bash
docker pull jasonish/suricata:latest
```

### 2. Configureer Suricata

Edit `/etc/suricata/suricata.yaml`:

```yaml
# EVE JSON logging (nodig voor AI-Firewall)
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - flow:
            enabled: yes
        - alert:
            enabled: yes
        - dns:
            enabled: yes
        - http:
            enabled: yes
```

### 3. Start Suricata

```bash
# Start Suricata op interface eth0
sudo suricata -c /etc/suricata/suricata.yaml -i eth0

# Of in daemon mode
sudo systemctl start suricata
sudo systemctl enable suricata
```

### 4. Integreer met AI-Firewall

```bash
# Start AI-Firewall Suricata integration
python suricata_integration.py --eve-log /var/log/suricata/eve.json

# Of met Docker
docker run -d \
  --name ai-firewall-suricata \
  -v /var/log/suricata:/logs:ro \
  ai-firewall:latest \
  python suricata_integration.py --eve-log /logs/eve.json
```

### 5. Zeek (Bro) Alternatief

```bash
# Installeer Zeek
sudo apt-get install zeek

# Start Zeek
zeek -i eth0

# Parse conn.log
python suricata_integration.py --zeek-log /var/log/zeek/current/conn.log
```

---

## 🎨 Dashboard Setup

### 1. Open Dashboard

```bash
# Start API server
python api_server.py

# Open dashboard in browser
# Navigeer naar: http://localhost:8000/dashboard

# Of gebruik standalone server
cd dashboard
python -m http.server 8080
# Open: http://localhost:8080
```

### 2. Dashboard Features

- **Real-time Monitoring**: Live flow classification via WebSocket
- **Statistics**: Total flows, benign/malicious counts, percentages
- **Charts**:
  - Flow classification pie chart
  - Threat timeline (time series)
  - Risk score distribution
  - Protocol distribution
- **Alerts**: Recent malicious detections
- **Control Panel**: Start/stop monitoring, reset stats, export data

### 3. Dashboard Configuration

Edit `dashboard/dashboard.js`:

```javascript
// API endpoint
const API_URL = 'http://your-server:8000';
const WS_URL = 'ws://your-server:8000/ws';

// Aanpassen refresh rate
const REFRESH_INTERVAL = 1000; // milliseconds
```

### 4. Production Deployment (Nginx)

```nginx
# /etc/nginx/sites-available/ai-firewall
server {
    listen 80;
    server_name firewall.example.com;
    
    # Dashboard
    location / {
        root /var/www/ai-firewall/dashboard;
        index index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🔒 Production Best Practices

### 1. Security

```bash
# Gebruik secrets voor passwords
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 32)" >> .env

# SSL/TLS certificaten
sudo certbot --nginx -d firewall.example.com

# Firewall rules
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Monitoring & Logging

```bash
# Prometheus metrics (add to api_server.py)
pip install prometheus-fastapi-instrumentator

# Grafana dashboard
docker run -d -p 3000:3000 grafana/grafana

# Log rotation
sudo nano /etc/logrotate.d/ai-firewall
# Add:
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### 3. Performance Tuning

```yaml
# docker-compose.yml - resource limits
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
    reservations:
      cpus: '2'
      memory: 4G
```

```python
# api_server.py - worker processes
uvicorn.run(
    "api_server:app",
    host="0.0.0.0",
    port=8000,
    workers=4,  # CPU cores
    worker_class="uvicorn.workers.UvicornWorker"
)
```

### 4. Backup & Recovery

```bash
# Backup models
tar -czf models-backup-$(date +%Y%m%d).tar.gz models/

# Backup database
docker exec ai-firewall-db pg_dump -U firewall ai_firewall > backup.sql

# Restore
docker exec -i ai-firewall-db psql -U firewall ai_firewall < backup.sql
```

### 5. High Availability

```yaml
# docker-compose.yml - replicas
services:
  ai-firewall:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```

### 6. Auto-Scaling (Kubernetes)

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-firewall
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-firewall
  template:
    metadata:
      labels:
        app: ai-firewall
    spec:
      containers:
      - name: ai-firewall
        image: ai-firewall:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-firewall-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-firewall
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 🧪 Testing Deployment

### 1. Health Check

```bash
# API health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","model_loaded":true,"timestamp":"..."}
```

### 2. Test Prediction

```bash
# Single flow prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "destination_port": 80,
    "flow_duration": 1000000,
    "total_fwd_packets": 10,
    "total_backward_packets": 8,
    "flow_bytes_s": 5000,
    "flow_packets_s": 100
  }'
```

### 3. Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Load test (1000 requests, 10 concurrent)
ab -n 1000 -c 10 -p flow.json -T application/json http://localhost:8000/predict
```

---

## 📊 Monitoring Dashboard

Access metrics:
- **Dashboard**: http://localhost:80
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

---

## 🆘 Troubleshooting

### Models Not Loading
```bash
# Check model files exist
ls -lh models/
# Should see: xgboost_model_latest.pkl, isolation_forest_model_latest.pkl, feature_transformers.pkl

# Check permissions
chmod -R 755 models/
```

### High Memory Usage
```bash
# Reduce batch size in config.yaml
batch_size: 500  # Instead of 1000

# Enable garbage collection
import gc
gc.collect()
```

### Suricata Not Logging
```bash
# Check Suricata is running
sudo systemctl status suricata

# Check EVE log
tail -f /var/log/suricata/eve.json

# Restart Suricata
sudo systemctl restart suricata
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Suricata User Guide](https://suricata.readthedocs.io/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [CICIDS2017 Dataset](https://www.unb.ca/cic/datasets/ids-2017.html)

---

**Deployment checklist:**
- [ ] Hardware requirements voldaan
- [ ] Docker images gebuild
- [ ] Models beschikbaar in `/models`
- [ ] Suricata/Zeek geïnstalleerd en geconfigureerd
- [ ] API server draait (port 8000)
- [ ] Dashboard toegankelijk (port 80)
- [ ] SSL certificaten geconfigureerd (productie)
- [ ] Logging & monitoring actief
- [ ] Backup strategie geïmplementeerd
