# AI-Firewall Docker Container
FROM python:3.12-slim

# Metadata
LABEL maintainer="AI-Firewall"
LABEL description="Network Flow Classification with XGBoost + Isolation Forest"

# Installeer system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Werkdirectory
WORKDIR /app

# Copy requirements eerst (voor Docker cache optimization)
COPY requirements.txt .

# Installeer Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy applicatie code
COPY *.py ./
COPY config.yaml ./
COPY models/ ./models/
COPY output/ ./output/

# Maak directories voor logs en data
RUN mkdir -p /app/logs /app/data /app/predictions

# Environment variabelen
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/app/models
ENV LOG_PATH=/app/logs
ENV PREDICTION_PATH=/app/predictions

# Expose poort voor API (Flask/FastAPI)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: Start API server
CMD ["python", "api_server.py"]
