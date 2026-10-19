import os
import sys

# Ensure project root is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from src.vision.video_processor import VideoMatchProcessor
from src.competition.schedule_engine import CompetitionScheduleEngine, MatchScheduleItem

def run_integration_tests():
    print("==================================================")
    print("   RUNNING AI SPORTS ANALYTICS INTEGRATION TEST   ")
    print("==================================================")

    # 1. Vision & Analytics Pipeline Test
    video_path = os.path.join(ROOT_DIR, "tests", "sample_match.mp4")
    assert os.path.exists(video_path), f"Video missing: {video_path}"

    processor = VideoMatchProcessor(model_name="yolov8n.pt")
    result = processor.process_video(video_path=video_path, max_frames=60)

    print("\n[✓] Vision Processing Finished:")
    print(f"    - Frames processed: {result['video_metadata']['frames_processed']}")
    print(f"    - Resolution: {result['video_metadata']['width']}x{result['video_metadata']['height']}")
    print(f"    - Total players tracked: {len(result['player_summaries'])}")

    assert result["status"] == "success"
    assert "player_summaries" in result
    assert "heatmaps" in result
    assert "scouting_reports" in result
    assert len(result["match_report"]) > 50

    if result["player_summaries"]:
        top_p = result["player_summaries"][0]
        print(f"\n[✓] Sample Player #{top_p['track_id']} Metrics:")
        print(f"    - Distance: {top_p['total_distance_m']} m ({top_p['total_distance_km']} km)")
        print(f"    - Top Speed: {top_p['top_speed_kmh']} km/h")
        print(f"    - Avg Speed: {top_p['avg_speed_kmh']} km/h")
        print(f"    - Sprint count: {top_p['sprint_count']}")

    print("\n[✓] Sample Scouting Report Preview:")
    print("--------------------------------------------------")
    print(result["match_report"])
    print("--------------------------------------------------")

    # 2. Competition Schedule Conflict Engine Test
    print("\n[✓] Testing Competition Conflict Validation Engine:")
    engine = CompetitionScheduleEngine(min_team_rest_hours=48)

    conflict_items = [
        MatchScheduleItem(
            match_id="M01",
            tournament_name="Liga 1 Indonesia",
            team_home="Persija",
            team_away="Persib",
            venue_id="GBK",
            venue_name="Stadion GBK",
            start_time="2026-11-01T15:30:00",
            duration_minutes=105,
            buffer_minutes=30,
            main_referee="Thoriq Alkatiri"
        ),
        MatchScheduleItem(
            match_id="M02",
            tournament_name="Liga 1 Indonesia",
            team_home="Arema FC",
            team_away="Persebaya",
            venue_id="GBK",
            venue_name="Stadion GBK",
            start_time="2026-11-01T16:30:00",
            duration_minutes=105,
            buffer_minutes=30,
            main_referee="Thoriq Alkatiri"
        ),
        MatchScheduleItem(
            match_id="M03",
            tournament_name="Liga 1 Indonesia",
            team_home="Persija",
            team_away="Bali United",
            venue_id="Patriot",
            venue_name="Stadion Patriot",
            start_time="2026-11-02T15:30:00",
            duration_minutes=105,
            buffer_minutes=30,
            main_referee="Yudi P"
        )
    ]

    validation = engine.validate_schedules(conflict_items)
    print(f"    - Valid: {validation.is_valid}")
    print(f"    - Total conflicts detected: {len(validation.conflicts)}")
    for c in validation.conflicts:
        print(f"      * [{c.conflict_type}] {c.description}")

    assert not validation.is_valid
    assert len(validation.conflicts) >= 3

    print("\n==================================================")
    print("   ALL INTEGRATION TESTS PASSED PERFECTLY! (100%)  ")
    print("==================================================")

if __name__ == "__main__":
    run_integration_tests()
