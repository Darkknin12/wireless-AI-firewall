"""
FastAPI Web Server voor AI-Firewall
Real-time inference API + WebSocket streaming
"""

from fastapi import FastAPI, File, UploadFile, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import json
import uuid
import os
import pandas as pd
from datetime import datetime
from pathlib import Path

from inference import AIFirewallInference
from utils import Config, Logger

# Initialisatie
app = FastAPI(
    title="AI-Firewall API",
    description="Network Flow Classification API",
    version="1.0.0"
)

# CORS voor dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In productie: specificeer domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globals
config = Config()
logger = Logger(__name__).logger  # Get actual logger instance
firewall = None

# In-memory storage for recent predictions (for dashboard polling)
recent_predictions = []
MAX_RECENT_PREDICTIONS = 100

# Pydantic models
class FlowInput(BaseModel):
    """Single network flow input"""
    destination_port: int
    flow_duration: float
    total_fwd_packets: int
    total_backward_packets: int
    flow_bytes_s: float
    flow_packets_s: float
    protocol: int = 6  # TCP default
    # ... Voeg alle 79+ features toe voor productie

class PredictionResponse(BaseModel):
    """Prediction output"""
    prediction: str
    confidence: float
    xgb_score: float
    if_score: float
    ensemble_score: float
    timestamp: str
    risk_level: str

class BatchPredictionResponse(BaseModel):
    """Batch prediction output"""
    total_flows: int
    benign_count: int
    malicious_count: int
    predictions: List[PredictionResponse]

class StatsResponse(BaseModel):
    """System statistics"""
    model_loaded: bool
    total_predictions: int
    uptime_seconds: float
    cpu_percent: float
    memory_percent: float

# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    """Laad modellen bij startup"""
    global firewall
    logger.info("🚀 Starting AI-Firewall API...")
    
    try:
        firewall = AIFirewallInference()
        logger.info("✓ Models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup bij shutdown"""
    logger.info("Shutting down AI-Firewall API...")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint voor Docker"""
    return {
        "status": "healthy",
        "model_loaded": firewall is not None,
        "timestamp": datetime.now().isoformat()
    }

# API Endpoints
@app.get("/")
async def root():
    """API root"""
    return {
        "name": "AI-Firewall API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "predict_batch": "/predict/batch",
            "predict_csv": "/predict/csv",
            "stats": "/stats",
            "websocket": "/ws"
        }
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_single_flow(flow: FlowInput):
    """
    Classificeer single network flow
    
    Args:
        flow: Network flow features
        
    Returns:
        Prediction met confidence scores
    """
    global recent_predictions
    
    if firewall is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Converteer naar dictionary
        flow_dict = flow.dict()
        
        # Voer inferentie uit
        result = firewall.predict_single_flow(flow_dict)
        
        # Bepaal risk level
        risk_level = "HIGH" if result['ensemble_score'] > 0.7 else \
                     "MEDIUM" if result['ensemble_score'] > 0.4 else "LOW"
        
        response = PredictionResponse(
            prediction=result['prediction'],
            confidence=result['confidence'],
            xgb_score=result['xgb_score'],
            if_score=result['if_score'],
            ensemble_score=result['ensemble_score'],
            timestamp=datetime.now().isoformat(),
            risk_level=risk_level
        )
        
        # Store in recent predictions for dashboard polling
        recent_predictions.append({
            "prediction": result['prediction'].upper(),
            "ensemble_score": result['ensemble_score'],
            "timestamp": response.timestamp,
            "risk_level": risk_level
        })
        
        # Keep only last N predictions
        if len(recent_predictions) > MAX_RECENT_PREDICTIONS:
            recent_predictions = recent_predictions[-MAX_RECENT_PREDICTIONS:]
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/raw")
async def predict_raw_flow(flow: Dict):
    """
    Classificeer raw network flow met alle features
    Accepteert elke JSON dictionary met network flow features
    
    Args:
        flow: Raw network flow dictionary (79+ features)
        
    Returns:
        Prediction met confidence scores
    """
    global recent_predictions
    
    if firewall is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Extract metadata for dashboard
        attack_type = flow.pop("attack_type", "Unknown Attack") if "attack_type" in flow else "Unknown Attack"
        src_ip = flow.pop("src_ip", None) if "src_ip" in flow else None
        dst_ip = flow.pop("dst_ip", None) if "dst_ip" in flow else None
        src_port = flow.get(" Source Port", flow.get("Source Port", None))
        dst_port = flow.get(" Destination Port", flow.get("Destination Port", None))
        
        # Voer inferentie uit
        result = firewall.predict_single_flow(flow)
        
        # Bepaal risk level
        risk_level = "HIGH" if result['ensemble_score'] > 0.7 else \
                     "MEDIUM" if result['ensemble_score'] > 0.4 else "LOW"
        
        timestamp = datetime.now().isoformat()
        
        # Store in recent predictions for dashboard polling (with attack type!)
        recent_predictions.append({
            "prediction": result['prediction'].upper(),
            "ensemble_score": result['ensemble_score'],
            "timestamp": timestamp,
            "risk_level": risk_level,
            "attack_type": attack_type if result['prediction'].upper() == "MALICIOUS" else "BENIGN",
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port
        })
        
        # Keep only last N predictions
        if len(recent_predictions) > MAX_RECENT_PREDICTIONS:
            recent_predictions = recent_predictions[-MAX_RECENT_PREDICTIONS:]
        
        return {
            "prediction": result['prediction'],
            "confidence": result['confidence'],
            "xgb_score": result['xgb_score'],
            "if_score": result['if_score'],
            "ensemble_score": result['ensemble_score'],
            "timestamp": timestamp,
            "risk_level": risk_level,
            "attack_type": attack_type
        }
        
    except Exception as e:
        logger.error(f"Raw prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch")
async def predict_batch(flows: List[FlowInput]):
    """
    Classificeer batch van flows
    
    Args:
        flows: List van network flows
        
    Returns:
        Batch prediction results
    """
    if firewall is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Converteer naar DataFrame
        df = pd.DataFrame([f.dict() for f in flows])
        
        # Batch inferentie
        results_df = firewall.predict_batch(df)
        
        # Converteer naar response format
        predictions = []
        for _, row in results_df.iterrows():
            risk_level = "HIGH" if row['ensemble_score'] > 0.7 else \
                         "MEDIUM" if row['ensemble_score'] > 0.4 else "LOW"
            
            predictions.append(PredictionResponse(
                prediction=row['prediction'],
                confidence=row['confidence'],
                xgb_score=row['xgb_score'],
                if_score=row['if_score'],
                ensemble_score=row['ensemble_score'],
                timestamp=datetime.now().isoformat(),
                risk_level=risk_level
            ))
        
        malicious_count = sum(1 for p in predictions if p.prediction == "MALICIOUS")
        
        return BatchPredictionResponse(
            total_flows=len(predictions),
            benign_count=len(predictions) - malicious_count,
            malicious_count=malicious_count,
            predictions=predictions
        )
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/csv")
async def predict_csv_file(file: UploadFile = File(...)):
    """
    Classificeer flows van uploaded CSV
    
    Args:
        file: CSV bestand met network flows
        
    Returns:
        CSV bestand met predictions
    """
    if firewall is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Save uploaded file
        temp_path = Path("data") / f"upload_{datetime.now().timestamp()}.csv"
        temp_path.parent.mkdir(exist_ok=True)
        
        with temp_path.open("wb") as f:
            f.write(await file.read())
        
        # Predict
        output_path = Path("predictions") / f"prediction_{datetime.now().timestamp()}.csv"
        output_path.parent.mkdir(exist_ok=True)
        
        firewall.predict_from_csv(str(temp_path), str(output_path))
        
        # Return file
        return FileResponse(
            path=output_path,
            filename=output_path.name,
            media_type="text/csv"
        )
        
    except Exception as e:
        logger.error(f"CSV prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Systeem statistieken
    """
    import psutil
    process = psutil.Process()
    
    return StatsResponse(
        model_loaded=firewall is not None,
        total_predictions=len(recent_predictions),
        uptime_seconds=process.create_time(),
        cpu_percent=process.cpu_percent(),
        memory_percent=process.memory_percent()
    )

@app.get("/predictions/recent")
async def get_recent_predictions(since: int = 0, initial: bool = False):
    """
    Get recent predictions for dashboard polling
    
    Args:
        since: Only return predictions after this index
        initial: If True, return last 20 for initial load
        
    Returns:
        List of recent predictions
    """
    global recent_predictions
    
    # Initial load - return last 20
    if initial:
        return {
            "predictions": recent_predictions[-20:] if recent_predictions else [],
            "total": len(recent_predictions),
            "next_index": len(recent_predictions)
        }
    
    # Polling - only return NEW predictions after since index
    if since >= len(recent_predictions):
        # No new predictions
        return {
            "predictions": [],
            "total": len(recent_predictions),
            "next_index": len(recent_predictions)
        }
    
    return {
        "predictions": recent_predictions[since:],
        "total": len(recent_predictions),
        "next_index": len(recent_predictions)
    }

# WebSocket voor real-time streaming
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint voor real-time flow streaming
    
    Connects to Redis channel 'firewall_events' and pushes updates to client
    """
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    import redis.asyncio as redis
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    r = redis.from_url(redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe('firewall_events')
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_text(message['data'])
            await asyncio.sleep(0.01)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await pubsub.unsubscribe('firewall_events')
        await r.close()
        logger.info("WebSocket client disconnected")

# === FIREWALL BLOCKING ENDPOINTS ===

@app.get("/firewall/stats")
async def get_firewall_stats():
    """Get firewall blocking statistics"""
    try:
        from firewall_blocker import FirewallBlocker
        blocker = FirewallBlocker(reload_config=False)
        
        stats = blocker.get_stats()
        blocked_ips = blocker.get_blocked_ips()
        
        return {
            "status": "success",
            "stats": stats,
            "blocked_ips": blocked_ips,
            "block_count": len(blocked_ips),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting firewall stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blocked-ips")
async def get_blocked_ips():
    """Get list of all blocked IPs with details"""
    try:
        from firewall_blocker import FirewallBlocker
        blocker = FirewallBlocker(reload_config=False)
        
        # Get blocked IPs
        blocked_ips = []
        for ip in blocker.get_blocked_ips():
            # Find in history
            ip_history = [h for h in blocker.block_history if h['ip'] == ip]
            
            if ip_history:
                latest = ip_history[-1]
                blocked_ips.append({
                    "ip": ip,
                    "blocked_at": latest['timestamp'],
                    "reason": latest['reason'],
                    "method": latest['method'],
                    "duration_hours": blocker.block_duration_hours
                })
            else:
                blocked_ips.append({
                    "ip": ip,
                    "blocked_at": datetime.now().isoformat(),
                    "reason": "Unknown",
                    "method": "manual",
                    "duration_hours": blocker.block_duration_hours
                })
        
        return {
            "status": "success",
            "blocked_ips": blocked_ips,
            "total": len(blocked_ips),
            "auto_block_enabled": blocker.auto_block_enabled,
            "threshold": blocker.block_threshold
        }
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/unblock/{ip}")
async def unblock_ip(ip: str):
    """Manually unblock an IP address"""
    try:
        from firewall_blocker import FirewallBlocker
        blocker = FirewallBlocker(reload_config=False)
        
        # Unblock
        success = blocker.unblock_ip(ip)
        
        if success:
            return {
                "status": "success",
                "message": f"IP {ip} unblocked successfully",
                "ip": ip,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "failed",
                "message": f"Failed to unblock IP {ip} (may not be blocked)",
                "ip": ip
            }
    except Exception as e:
        logger.error(f"Error unblocking IP {ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/block/{ip}")
async def manual_block_ip(ip: str, reason: str = "Manual block"):
    """Manually block an IP address"""
    try:
        from firewall_blocker import FirewallBlocker
        blocker = FirewallBlocker(reload_config=False)
        
        # Block
        success = blocker.block_ip(ip, reason)
        
        if success:
            return {
                "status": "success",
                "message": f"IP {ip} blocked successfully",
                "ip": ip,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "failed",
                "message": f"Failed to block IP {ip} (may be whitelisted or already blocked)",
                "ip": ip
            }
    except Exception as e:
        logger.error(f"Error blocking IP {ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/blocked")
async def get_block_logs(limit: int = 100):
    """Get recent blocking history from logs"""
    try:
        log_file = Path("logs/blocked_ips.json")
        
        if not log_file.exists():
            return {
                "status": "success",
                "logs": [],
                "total": 0
            }
        
        # Read last N lines
        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except:
                    pass
        
        # Return most recent first
        logs = logs[-limit:][::-1]
        
        return {
            "status": "success",
            "logs": logs,
            "total": len(logs)
        }
    except Exception as e:
        logger.error(f"Error reading block logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/device-info")
async def get_device_info():
    """Get device information"""
    # Generate or read device ID
    config_file = Path("config.json")
    device_id = "AF-2025-UNKNOWN"
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                cfg = json.load(f)
                if "device_id" in cfg:
                    device_id = cfg["device_id"]
                else:
                    # Generate new ID
                    device_id = f"AF-2025-{uuid.uuid4().hex[:6].upper()}"
                    cfg["device_id"] = device_id
                    with open(config_file, 'w') as f_out:
                        json.dump(cfg, f_out, indent=4)
        except Exception as e:
            logger.error(f"Error reading config: {e}")
    
    return {
        "device_id": device_id,
        "status": "online",
        "version": "1.0.0"
    }

class ActivationRequest(BaseModel):
    auto_block: bool
    block_threshold: float
    device_id: str

@app.post("/activate")
async def activate_device(request: ActivationRequest):
    """Activate protection"""
    try:
        config_file = Path("config.json")
        cfg = {}
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                cfg = json.load(f)
        
        # Update config
        cfg["firewall"] = cfg.get("firewall", {})
        cfg["firewall"]["auto_block"] = request.auto_block
        cfg["firewall"]["threshold"] = request.block_threshold
        cfg["device_id"] = request.device_id
        cfg["activated"] = True
        cfg["activation_date"] = datetime.now().isoformat()
        
        with open(config_file, 'w') as f:
            json.dump(cfg, f, indent=4)
            
        return {"status": "success", "message": "Protection activated"}
    except Exception as e:
        logger.error(f"Activation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Run server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable in productie
        workers=4,  # Multi-process
        log_level="info"
    )
