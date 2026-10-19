from typing import List, Dict, Tuple, Any
import numpy as np
from ..config import config

class HeatmapGenerator:
    """
    Generates 2D pitch density matrices (heatmaps) from player trajectories.
    Standard pitch is 105m x 68m.
    """

    def __init__(self, grid_x: int = 50, grid_y: int = 34):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.pitch_length = config.pitch.length_m
        self.pitch_width = config.pitch.width_m

    def generate_heatmap_matrix(self, positions: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Takes a list of positions [{'x': float, 'y': float}, ...]
        Returns a normalized 2D grid matrix [grid_y, grid_x] with values 0.0 - 1.0.
        """
        matrix = np.zeros((self.grid_y, self.grid_x), dtype=np.float32)

        if not positions:
            return {
                "grid_x": self.grid_x,
                "grid_y": self.grid_y,
                "matrix": matrix.tolist()
            }

        for pt in positions:
            x, y = pt["x"], pt["y"]
            # Map x (0..105) -> (0..grid_x - 1)
            gx = int((x / self.pitch_length) * (self.grid_x - 1))
            # Map y (0..68) -> (0..grid_y - 1)
            gy = int((y / self.pitch_width) * (self.grid_y - 1))

            gx = max(0, min(self.grid_x - 1, gx))
            gy = max(0, min(self.grid_y - 1, gy))

            # Apply Gaussian-like spread around the point
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nx, ny = gx + dx, gy + dy
                    if 0 <= nx < self.grid_x and 0 <= ny < self.grid_y:
                        dist_sq = dx * dx + dy * dy
                        weight = np.exp(-dist_sq / 2.0)
                        matrix[ny, nx] += weight

        # Normalize matrix between 0.0 and 1.0
        max_val = np.max(matrix)
        if max_val > 0:
            matrix = matrix / max_val

        return {
            "grid_x": self.grid_x,
            "grid_y": self.grid_y,
            "matrix": np.round(matrix, 3).tolist()
        }
