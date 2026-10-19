import os
from pydantic import BaseModel

class PitchConfig(BaseModel):
    length_m: float = 105.0  # Standard FIFA pitch length (meters)
    width_m: float = 68.0    # Standard FIFA pitch width (meters)

class SpeedThresholds(BaseModel):
    walk_max: float = 7.0     # 0 - 7 km/h: Walking
    jog_max: float = 14.0     # 7 - 14 km/h: Jogging
    run_max: float = 20.0     # 14 - 20 km/h: High intensity run
    sprint_min: float = 20.0  # > 20 km/h: Sprint

class AppConfig(BaseModel):
    pitch: PitchConfig = PitchConfig()
    speed_thresholds: SpeedThresholds = SpeedThresholds()
    model_name: str = "yolov8n.pt"
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    sample_fps: float = 30.0

config = AppConfig()
