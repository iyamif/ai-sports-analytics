from typing import List, Dict, Any, Optional
import os
import cv2
import numpy as np
from ultralytics import YOLO

class SportsDetector:
    """
    YOLOv8 + ByteTrack detector for players, referees, and the soccer ball.
    """

    def __init__(self, model_name: str = "yolov8n.pt", conf_thresh: float = 0.25):
        self.model_name = model_name
        self.conf_thresh = conf_thresh
        print(f"Loading YOLO model: {model_name}...")
        self.model = YOLO(model_name)
        # Class 0: person, Class 32: sports ball in standard COCO dataset
        self.person_class_id = 0
        self.ball_class_id = 32

    def detect_and_track(self, frame: np.ndarray, persist: bool = True) -> Dict[str, Any]:
        """
        Runs tracking on a single frame.
        Returns:
            {
                "players": [
                    {
                        "track_id": int,
                        "bbox": [x1, y1, x2, y2],
                        "foot_pixel": (x, y),
                        "confidence": float
                    }, ...
                ],
                "ball": {
                    "bbox": [x1, y1, x2, y2],
                    "center_pixel": (x, y),
                    "confidence": float
                } or None
            }
        """
        results = self.model.track(
            source=frame,
            persist=persist,
            conf=self.conf_thresh,
            classes=[self.person_class_id, self.ball_class_id],
            verbose=False,
            tracker="bytetrack.yaml"
        )

        players: List[Dict[str, Any]] = []
        ball: Optional[Dict[str, Any]] = None

        boxes = results[0].boxes if (results and len(results) > 0) else None

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                x1, y1, x2, y2 = xyxy

                if cls_id == self.person_class_id:
                    track_id = int(box.id[0].item()) if box.id is not None else -1
                    foot_x = (x1 + x2) / 2.0
                    foot_y = y2
                    players.append({
                        "track_id": track_id,
                        "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        "foot_pixel": (round(foot_x, 1), round(foot_y, 1)),
                        "confidence": round(conf, 3),
                    })

                elif cls_id == self.ball_class_id:
                    center_x = (x1 + x2) / 2.0
                    center_y = (y1 + y2) / 2.0
                    if ball is None or conf > ball["confidence"]:
                        ball = {
                            "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                            "center_pixel": (round(center_x, 1), round(center_y, 1)),
                            "confidence": round(conf, 3),
                        }

        # Fallback: Contour & Centroid tracking when YOLO finds no players
        if len(players) == 0:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            grass_mask = cv2.inRange(hsv, (45, 50, 40), (70, 255, 120))
            non_grass = cv2.bitwise_not(grass_mask)

            # Mask out scoreboards & margins
            h, w = frame.shape[:2]
            non_grass[:int(h * 0.08), :] = 0
            non_grass[int(h * 0.94):, :] = 0
            non_grass[:, :int(w * 0.05)] = 0
            non_grass[:, int(w * 0.95):] = 0

            # Filter white field lines
            white_mask = cv2.inRange(hsv, (0, 0, 180), (180, 40, 255))
            player_mask = cv2.bitwise_and(non_grass, cv2.bitwise_not(white_mask))
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            player_mask = cv2.morphologyEx(player_mask, cv2.MORPH_OPEN, kernel)

            contours, _ = cv2.findContours(player_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            detected_blobs = []

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 120:  # Player body area
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    foot_x = bx + bw / 2.0
                    foot_y = float(by + bh)
                    detected_blobs.append((bx, by, bw, bh, foot_x, foot_y))

            # Match blobs with previous tracks using nearest centroid
            current_tracks = {}
            used_blobs = set()

            for tid, (prev_x, prev_y) in list(getattr(self, "prev_tracks", {}).items()):
                best_idx = None
                min_dist = 80.0
                for idx, blob in enumerate(detected_blobs):
                    if idx in used_blobs:
                        continue
                    dist = float(np.hypot(blob[4] - prev_x, blob[5] - prev_y))
                    if dist < min_dist:
                        min_dist = dist
                        best_idx = idx

                if best_idx is not None:
                    used_blobs.add(best_idx)
                    b = detected_blobs[best_idx]
                    current_tracks[tid] = (b[4], b[5])
                    players.append({
                        "track_id": tid,
                        "bbox": [float(b[0]), float(b[1]), float(b[0] + b[2]), float(b[1] + b[3])],
                        "foot_pixel": (b[4], b[5]),
                        "confidence": 0.92
                    })

            if not hasattr(self, "next_track_id"):
                self.next_track_id = 1

            for idx, b in enumerate(detected_blobs):
                if idx not in used_blobs:
                    tid = self.next_track_id
                    self.next_track_id += 1
                    current_tracks[tid] = (b[4], b[5])
                    players.append({
                        "track_id": tid,
                        "bbox": [float(b[0]), float(b[1]), float(b[0] + b[2]), float(b[1] + b[3])],
                        "foot_pixel": (b[4], b[5]),
                        "confidence": 0.92
                    })

            self.prev_tracks = current_tracks

        return {"players": players, "ball": ball}
