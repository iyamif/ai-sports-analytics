from typing import Dict, Any, Optional, Callable
import os
import time
import json
import cv2
import numpy as np

from .detector import SportsDetector
from .pitch_homography import PitchHomography
from ..analytics.metrics import PlayerMetricsTracker
from ..analytics.heatmap import HeatmapGenerator
from ..analytics.report_generator import ScoutingReportGenerator
from ..config import config

class VideoMatchProcessor:
    """
    End-to-end match video analysis pipeline:
    1. Video frame decoding
    2. Player & ball detection & multi-object tracking (YOLO + ByteTrack)
    3. Homography perspective mapping (pixels -> pitch meters)
    4. Physical metrics extraction (speed, distance, sprints)
    5. Real-time telemetry streaming to Redis / in-memory buffer
    6. Heatmap generation & NLP scouting report
    """

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        redis_client: Optional[Any] = None,
        telemetry_channel: str = "gsi_live_telemetry"
    ):
        self.detector = SportsDetector(model_name=model_name)
        self.homography = PitchHomography(
            pitch_length_m=config.pitch.length_m,
            pitch_width_m=config.pitch.width_m
        )
        self.redis_client = redis_client
        self.telemetry_channel = telemetry_channel
        self.latest_live_telemetry: list = []

    def calibrate_pitch(self, frame_w: int, frame_h: int):
        """
        Calibrate homography for the camera angle.
        Default standard camera view mapping 4 corners of the field.
        """
        # Standard broadcast camera perspective points on a 1280x720 or normalized frame
        src_corners = [
            (frame_w * 0.15, frame_h * 0.20),  # Top-left corner of pitch in frame
            (frame_w * 0.85, frame_h * 0.20),  # Top-right corner of pitch in frame
            (frame_w * 0.98, frame_h * 0.90),  # Bottom-right corner of pitch in frame
            (frame_w * 0.02, frame_h * 0.90),  # Bottom-left corner of pitch in frame
        ]
        self.homography.compute_homography(src_corners)

    def process_video(
        self,
        video_path: str,
        max_frames: Optional[int] = None,
        frame_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.calibrate_pitch(frame_w, frame_h)
        metrics_tracker = PlayerMetricsTracker(fps=fps)
        heatmap_gen = HeatmapGenerator(grid_x=50, grid_y=34)

        frame_idx = 0
        start_time = time.time()

        print(f"Starting video processing: {video_path} ({total_frames} frames, {fps:.1f} FPS)...")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            timestamp_sec = frame_idx / fps
            detections = self.detector.detect_and_track(frame, persist=True)

            live_players = []
            for player in detections["players"]:
                px, py = player["foot_pixel"]
                pitch_coord = self.homography.pixel_to_pitch(px, py)
                if pitch_coord:
                    x_m, y_m = pitch_coord
                    metric_update = metrics_tracker.update_player_position(
                        track_id=player["track_id"],
                        x_m=x_m,
                        y_m=y_m,
                        timestamp_sec=timestamp_sec
                    )
                    live_players.append({
                        "track_id": player["track_id"],
                        "bbox": player["bbox"],
                        "pixel": (px, py),
                        "pitch_m": (x_m, y_m),
                        "speed_kmh": metric_update["speed_kmh"]
                    })

            # Ball coordinates
            ball_pitch = None
            if detections["ball"]:
                bx, by = detections["ball"]["center_pixel"]
                ball_pitch = self.homography.pixel_to_pitch(bx, by)

            telemetry_packet = {
                "frame_idx": frame_idx,
                "timestamp_sec": round(timestamp_sec, 2),
                "players_count": len(live_players),
                "players": live_players,
                "ball": {
                    "pixel": detections["ball"]["center_pixel"] if detections["ball"] else None,
                    "pitch_m": ball_pitch
                } if detections["ball"] else None
            }

            self.latest_live_telemetry.append(telemetry_packet)
            if len(self.latest_live_telemetry) > 500:
                self.latest_live_telemetry.pop(0)

            # Broadcast to Redis if available
            if self.redis_client:
                try:
                    self.redis_client.publish(self.telemetry_channel, json.dumps(telemetry_packet))
                except Exception:
                    pass

            if frame_callback:
                frame_callback(telemetry_packet)

            frame_idx += 1
            if max_frames and frame_idx >= max_frames:
                break

        cap.release()
        elapsed = time.time() - start_time
        print(f"Processed {frame_idx} frames in {elapsed:.2f}s ({frame_idx / max(0.001, elapsed):.1f} FPS)")

        # Compile aggregates
        player_summaries = metrics_tracker.get_all_summaries()

        # Generate Heatmaps for each player
        heatmaps = {}
        for tid, traj in metrics_tracker.trajectories.items():
            pos_list = [{"x": p["x"], "y": p["y"]} for p in traj]
            heatmaps[str(tid)] = heatmap_gen.generate_heatmap_matrix(pos_list)

        # Generate NLP scouting reports
        scouting_reports = {}
        for summary in player_summaries:
            tid = summary["track_id"]
            scouting_reports[str(tid)] = ScoutingReportGenerator.generate_player_scouting_report(
                summary, player_name=f"Player #{tid}"
            )

        match_report = ScoutingReportGenerator.generate_match_summary(player_summaries)

        return {
            "status": "success",
            "video_metadata": {
                "width": frame_w,
                "height": frame_h,
                "fps": round(fps, 1),
                "frames_processed": frame_idx,
                "duration_seconds": round(frame_idx / fps, 2)
            },
            "player_summaries": player_summaries,
            "heatmaps": heatmaps,
            "scouting_reports": scouting_reports,
            "match_report": match_report
        }
