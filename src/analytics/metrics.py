from typing import List, Dict, Any, Tuple
import math
from ..config import config

class PlayerMetricsTracker:
    """
    Computes distance, speed (instantaneous, average, top speed), sprint bursts,
    and work-rate distribution for each tracked player.
    """

    def __init__(self, fps: float = 30.0):
        self.fps = fps
        self.dt = 1.0 / max(1.0, fps)
        # Store history per player: track_id -> list of (timestamp_sec, x_m, y_m, speed_kmh)
        self.trajectories: Dict[int, List[Dict[str, float]]] = {}
        # Sprints tracking state
        self.in_sprint: Dict[int, bool] = {}

    def update_player_position(self, track_id: int, x_m: float, y_m: float, timestamp_sec: float) -> Dict[str, Any]:
        """
        Record a new position (in pitch meters) for a player and compute real-time metrics.
        """
        if track_id not in self.trajectories:
            self.trajectories[track_id] = []
            self.in_sprint[track_id] = False

        history = self.trajectories[track_id]
        speed_kmh = 0.0

        if len(history) > 0:
            last = history[-1]
            time_delta = timestamp_sec - last["timestamp"]
            if time_delta > 0:
                dist_m = math.sqrt((x_m - last["x"]) ** 2 + (y_m - last["y"]) ** 2)
                # Filter out impossible teleportation noise (> 40 km/h is unrealistic for footballers)
                speed_mps = dist_m / time_delta
                instant_speed_kmh = speed_mps * 3.6
                if instant_speed_kmh <= 38.0:
                    speed_kmh = instant_speed_kmh
                else:
                    speed_kmh = last.get("speed_kmh", 0.0)

        entry = {
            "timestamp": timestamp_sec,
            "x": round(x_m, 2),
            "y": round(y_m, 2),
            "speed_kmh": round(speed_kmh, 2)
        }
        history.append(entry)

        # Check sprint status
        if speed_kmh >= config.speed_thresholds.sprint_min:
            if not self.in_sprint[track_id]:
                self.in_sprint[track_id] = True
        else:
            self.in_sprint[track_id] = False

        return entry

    def get_player_summary(self, track_id: int) -> Dict[str, Any]:
        """
        Calculates aggregate statistics for a given player.
        """
        history = self.trajectories.get(track_id, [])
        if not history:
            return {
                "track_id": track_id,
                "total_distance_m": 0.0,
                "top_speed_kmh": 0.0,
                "avg_speed_kmh": 0.0,
                "sprint_count": 0,
                "speed_zones": {"walking_pct": 0, "jogging_pct": 0, "running_pct": 0, "sprinting_pct": 0}
            }

        total_dist_m = 0.0
        speeds: List[float] = []
        sprint_count = 0
        currently_sprinting = False

        walk_pts, jog_pts, run_pts, sprint_pts = 0, 0, 0, 0

        for i in range(1, len(history)):
            prev, curr = history[i - 1], history[i]
            d = math.sqrt((curr["x"] - prev["x"]) ** 2 + (curr["y"] - prev["y"]) ** 2)
            total_dist_m += d

            spd = curr["speed_kmh"]
            speeds.append(spd)

            # Categorize speed zones
            if spd < config.speed_thresholds.walk_max:
                walk_pts += 1
            elif spd < config.speed_thresholds.jog_max:
                jog_pts += 1
            elif spd < config.speed_thresholds.run_max:
                run_pts += 1
            else:
                sprint_pts += 1

            # Count distinct sprint bursts
            if spd >= config.speed_thresholds.sprint_min:
                if not currently_sprinting:
                    sprint_count += 1
                    currently_sprinting = True
            else:
                currently_sprinting = False

        top_speed = max(speeds) if speeds else 0.0
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
        total_pts = max(1, len(history) - 1)

        return {
            "track_id": track_id,
            "samples_count": len(history),
            "total_distance_m": round(total_dist_m, 1),
            "total_distance_km": round(total_dist_m / 1000.0, 3),
            "top_speed_kmh": round(top_speed, 2),
            "avg_speed_kmh": round(avg_speed, 2),
            "sprint_count": sprint_count,
            "speed_zones": {
                "walking_pct": round((walk_pts / total_pts) * 100, 1),
                "jogging_pct": round((jog_pts / total_pts) * 100, 1),
                "running_pct": round((run_pts / total_pts) * 100, 1),
                "sprinting_pct": round((sprint_pts / total_pts) * 100, 1)
            }
        }

    def get_all_summaries(self) -> List[Dict[str, Any]]:
        """Returns statistics for all tracked players."""
        return [self.get_player_summary(tid) for tid in sorted(self.trajectories.keys())]
