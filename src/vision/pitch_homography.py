from typing import List, Tuple, Optional
import cv2
import numpy as np

class PitchHomography:
    """
    Transforms camera frame pixel coordinates to real-world pitch meters (105m x 68m).
    """

    def __init__(self, pitch_length_m: float = 105.0, pitch_width_m: float = 68.0):
        self.pitch_length_m = pitch_length_m
        self.pitch_width_m = pitch_width_m
        self.H: Optional[np.ndarray] = None
        self.H_inv: Optional[np.ndarray] = None

    def compute_homography(
        self,
        src_points: List[Tuple[float, float]],
        dst_points: Optional[List[Tuple[float, float]]] = None
    ) -> np.ndarray:
        """
        src_points: 4 or more (x, y) coordinates on the camera image.
        dst_points: corresponding (X, Y) coordinates on standard pitch in meters.
        Default dst_points assumes the 4 corners of standard pitch:
        [(0, 0), (pitch_length_m, 0), (pitch_length_m, pitch_width_m), (0, pitch_width_m)]
        """
        if dst_points is None:
            dst_points = [
                (0.0, 0.0),
                (self.pitch_length_m, 0.0),
                (self.pitch_length_m, self.pitch_width_m),
                (0.0, self.pitch_width_m),
            ]

        src = np.array(src_points, dtype=np.float32)
        dst = np.array(dst_points, dtype=np.float32)

        H, _ = cv2.findHomography(src, dst)
        self.H = H
        if H is not None:
            self.H_inv = np.linalg.pinv(H)
        return H

    def pixel_to_pitch(self, px: float, py: float) -> Optional[Tuple[float, float]]:
        """Transforms image pixel (px, py) to pitch coordinates (X, Y) in meters."""
        if self.H is None:
            return None

        pt = np.array([[[px, py]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(pt, self.H)
        x_m = float(transformed[0][0][0])
        y_m = float(transformed[0][0][1])

        # Clamp within pitch boundaries with slight margin
        x_m = max(0.0, min(self.pitch_length_m, x_m))
        y_m = max(0.0, min(self.pitch_width_m, y_m))
        return round(x_m, 2), round(y_m, 2)

    def pitch_to_pixel(self, x_m: float, y_m: float) -> Optional[Tuple[float, float]]:
        """Transforms pitch coordinates (X, Y) in meters back to camera image pixel."""
        if self.H_inv is None:
            return None

        pt = np.array([[[x_m, y_m]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(pt, self.H_inv)
        px = float(transformed[0][0][0])
        py = float(transformed[0][0][1])
        return round(px, 1), round(py, 1)
