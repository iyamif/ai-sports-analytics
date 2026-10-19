from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..competition.schedule_engine import MatchScheduleItem, ScheduleValidationResult

class AnalyzeVideoRequest(BaseModel):
    video_path: str
    max_frames: Optional[int] = Field(default=150, description="Limit frames to process for fast analysis")

class PlayerSpeedZones(BaseModel):
    walking_pct: float
    jogging_pct: float
    running_pct: float
    sprinting_pct: float

class PlayerSummaryModel(BaseModel):
    track_id: int
    samples_count: int
    total_distance_m: float
    total_distance_km: float
    top_speed_kmh: float
    avg_speed_kmh: float
    sprint_count: int
    speed_zones: PlayerSpeedZones

class MatchAnalysisResponse(BaseModel):
    status: str
    video_metadata: Dict[str, Any]
    player_summaries: List[PlayerSummaryModel]
    heatmaps: Dict[str, Any]
    scouting_reports: Dict[str, str]
    match_report: str

class ValidateScheduleRequest(BaseModel):
    matches: List[MatchScheduleItem]
    min_team_rest_hours: int = 48
