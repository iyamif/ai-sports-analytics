import os
import cv2
import numpy as np

def generate_soccer_match_video(output_path: str = "tests/sample_match.mp4", duration_sec: int = 4, fps: int = 30):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    w, h = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    total_frames = duration_sec * fps

    # Define 6 players moving across the pitch
    # Format: [base_x, base_y, vx, vy, color_jersey, team_id]
    players = [
        {"x": 300, "y": 300, "vx": 4.5, "vy": 1.2, "color": (220, 50, 50)},    # Striker Blue
        {"x": 450, "y": 420, "vx": 3.0, "vy": -2.0, "color": (220, 50, 50)},   # Midfield Blue
        {"x": 250, "y": 500, "vx": 2.0, "vy": 0.5, "color": (220, 50, 50)},    # Defender Blue
        {"x": 750, "y": 320, "vx": -3.5, "vy": 1.0, "color": (50, 50, 220)},   # Defender Red
        {"x": 850, "y": 450, "vx": -2.8, "vy": -1.5, "color": (50, 50, 220)},  # Midfield Red
        {"x": 600, "y": 250, "vx": 5.8, "vy": 2.5, "color": (20, 200, 200)},   # Sprinting Winger (Yellow/Cyan)
    ]

    ball = {"x": 320, "y": 310, "vx": 6.5, "vy": 1.8}

    print(f"Generating realistic soccer video: {output_path} ({total_frames} frames)...")

    for f in range(total_frames):
        # 1. Draw green pitch with perspective grass bands
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (35, 75, 40) # Deep turf green

        # Alternating pitch grass stripes
        stripe_w = 80
        for s in range(0, w, stripe_w * 2):
            cv2.rectangle(frame, (s, 0), (s + stripe_w, h), (40, 85, 45), -1)

        # 2. Draw Pitch Lines
        # Outer boundary
        cv2.rectangle(frame, (80, 60), (1200, 660), (255, 255, 255), 3)
        # Half-way line
        cv2.line(frame, (640, 60), (640, 660), (255, 255, 255), 3)
        # Center circle
        cv2.circle(frame, (640, 360), 85, (255, 255, 255), 3)
        cv2.circle(frame, (640, 360), 5, (255, 255, 255), -1)

        # Penalty boxes
        cv2.rectangle(frame, (80, 210), (260, 510), (255, 255, 255), 3)
        cv2.rectangle(frame, (1020, 210), (1200, 510), (255, 255, 255), 3)

        # 3. Draw Players (Realistic human figure silhouette: head, body, legs)
        for p in players:
            p["x"] += p["vx"]
            p["y"] += p["vy"]

            # Bounce off boundary
            if p["x"] < 120 or p["x"] > 1160: p["vx"] *= -1
            if p["y"] < 100 or p["y"] > 620: p["vy"] *= -1

            cx, cy = int(p["x"]), int(p["y"])

            # Head
            cv2.circle(frame, (cx, cy - 28), 8, (200, 180, 160), -1)
            # Torso (Jersey)
            cv2.rectangle(frame, (cx - 10, cy - 20), (cx + 10, cy), p["color"], -1)
            # Shorts (White)
            cv2.rectangle(frame, (cx - 9, cy), (cx + 9, cy + 12), (240, 240, 240), -1)
            # Legs
            cv2.line(frame, (cx - 5, cy + 12), (cx - 5, cy + 28), (200, 180, 160), 3)
            cv2.line(frame, (cx + 5, cy + 12), (cx + 5, cy + 28), (200, 180, 160), 3)
            # Cleats / Shoes
            cv2.circle(frame, (cx - 5, cy + 28), 3, (20, 20, 20), -1)
            cv2.circle(frame, (cx + 5, cy + 28), 3, (20, 20, 20), -1)

        # 4. Draw Ball
        ball["x"] += ball["vx"]
        ball["y"] += ball["vy"]
        if ball["x"] < 100 or ball["x"] > 1180: ball["vx"] *= -1
        if ball["y"] < 80 or ball["y"] > 640: ball["vy"] *= -1

        bx, by = int(ball["x"]), int(ball["y"])
        cv2.circle(frame, (bx, by), 7, (255, 255, 255), -1)
        cv2.circle(frame, (bx, by), 7, (0, 0, 0), 1)

        # Add camera timecode
        cv2.putText(frame, f"REC 00:0{f // fps:02d}:{f % fps:02d} - FIFA GSI CAM 1",
                    (90, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        out.write(frame)

    out.release()
    print(f"Sample video successfully created: {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    generate_soccer_match_video()
