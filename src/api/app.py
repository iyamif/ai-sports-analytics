from typing import Dict, Any, List
import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from ..config import config
from ..vision.video_processor import VideoMatchProcessor
from ..competition.schedule_engine import CompetitionScheduleEngine
from .models import (
    AnalyzeVideoRequest,
    ValidateScheduleRequest,
    ScheduleValidationResult
)

app = FastAPI(
    title="Garuda AI Sports Analytics & Competition API",
    description="Computer Vision Player Tracking, Spatial Homography, Redis Telemetry, and Competition Automation API.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Redis with fast socket probe & graceful fallback
redis_client = None
def is_redis_available(host: str, port: int) -> bool:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.05)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

if is_redis_available("127.0.0.1", config.redis_port):
    try:
        import redis
        r = redis.Redis(host="127.0.0.1", port=config.redis_port, db=config.redis_db, socket_timeout=0.2)
        r.ping()
        redis_client = r
        print(f"Connected to Redis at 127.0.0.1:{config.redis_port}")
    except Exception:
        redis_client = None
else:
    print("Redis service offline. Using high-performance in-memory stream buffer.")

processor = VideoMatchProcessor(
    model_name=config.model_name,
    redis_client=redis_client
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# Store last analysis result in memory for fast retrieval
last_analysis_result: Dict[str, Any] = {}

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Garuda AI Sports Analytics",
        "redis_connected": redis_client is not None,
        "vision_model": config.model_name
    }

@app.post("/api/v1/analyze")
async def analyze_video_endpoint(req: AnalyzeVideoRequest):
    global last_analysis_result
    if not os.path.exists(req.video_path):
        raise HTTPException(status_code=404, detail=f"File not found: {req.video_path}")

    # Callback to stream each frame to WebSockets in real time
    loop = asyncio.get_event_loop()
    def stream_callback(telemetry_frame):
        asyncio.run_coroutine_threadsafe(manager.broadcast(telemetry_frame), loop)

    try:
        # Run synchronous vision processor in a thread pool so it doesn't block FastAPI
        result = await asyncio.to_thread(
            processor.process_video,
            video_path=req.video_path,
            max_frames=req.max_frames,
            frame_callback=stream_callback
        )
        last_analysis_result = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/match/latest")
def get_latest_analysis():
    if not last_analysis_result:
        raise HTTPException(status_code=404, detail="No match analysis has been run yet.")
    return last_analysis_result

@app.get("/api/v1/telemetry/buffer")
def get_telemetry_buffer():
    return {
        "buffer_size": len(processor.latest_live_telemetry),
        "packets": processor.latest_live_telemetry[-50:]
    }

@app.post("/api/v1/competition/validate-schedule", response_model=ScheduleValidationResult)
def validate_competition_schedule(req: ValidateScheduleRequest):
    engine = CompetitionScheduleEngine(min_team_rest_hours=req.min_team_rest_hours)
    result = engine.validate_schedules(req.matches)
    return result

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open and receive any client ping
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Web Dashboard UI serving
web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(web_dir, "static")), name="static")

    @app.get("/")
    def serve_dashboard():
        index_file = os.path.join(web_dir, "index.html")
        return FileResponse(index_file)
