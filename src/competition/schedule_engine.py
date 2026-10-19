from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

class MatchScheduleItem(BaseModel):
    match_id: str
    tournament_name: str = "Piala Garuda / Liga Indonesia"
    team_home: str
    team_away: str
    venue_id: str
    venue_name: str
    start_time: str  # Format: "YYYY-MM-DDTHH:MM:SS"
    duration_minutes: int = 105  # 90 mins match + 15 mins half-time
    buffer_minutes: int = 30     # Warm-up / pitch maintenance buffer
    main_referee: str
    assistant_referees: List[str] = Field(default_factory=list)

class ScheduleConflict(BaseModel):
    conflict_type: str  # "VENUE_OVERLAP", "TEAM_REST_VIOLATION", "REFEREE_OVERLAP"
    match_id_a: str
    match_id_b: str
    description: str
    severity: str = "ERROR"  # "ERROR" or "WARNING"

class ScheduleValidationResult(BaseModel):
    is_valid: bool
    total_matches_checked: int
    conflicts: List[ScheduleConflict]
    recommendations: List[str]

class CompetitionScheduleEngine:
    """
    Automated competition and tournament management engine.
    Ensures zero scheduling conflicts across venues, team rest intervals, and match officials.
    """

    def __init__(self, min_team_rest_hours: int = 48):
        self.min_team_rest_hours = min_team_rest_hours

    def validate_schedules(self, matches: List[MatchScheduleItem]) -> ScheduleValidationResult:
        conflicts: List[ScheduleConflict] = []
        recommendations: List[str] = []

        # Parse match timings
        parsed_matches = []
        for m in matches:
            try:
                start_dt = datetime.fromisoformat(m.start_time)
            except Exception:
                start_dt = datetime.strptime(m.start_time, "%Y-%m-%d %H:%M:%S")

            end_dt = start_dt + timedelta(minutes=m.duration_minutes)
            venue_clear_dt = end_dt + timedelta(minutes=m.buffer_minutes)
            parsed_matches.append({
                "item": m,
                "start": start_dt,
                "end": end_dt,
                "venue_clear": venue_clear_dt,
                "teams": {m.team_home.lower().strip(), m.team_away.lower().strip()},
                "referees": {m.main_referee.lower().strip()}.union(
                    {r.lower().strip() for r in m.assistant_referees}
                )
            })

        n = len(parsed_matches)
        for i in range(n):
            for j in range(i + 1, n):
                m1 = parsed_matches[i]
                m2 = parsed_matches[j]
                item1 = m1["item"]
                item2 = m2["item"]

                # 1. Check Venue Overlap
                if item1.venue_id == item2.venue_id:
                    # Check if intervals [start, venue_clear] overlap
                    if max(m1["start"], m2["start"]) < min(m1["venue_clear"], m2["venue_clear"]):
                        conflicts.append(ScheduleConflict(
                            conflict_type="VENUE_OVERLAP",
                            match_id_a=item1.match_id,
                            match_id_b=item2.match_id,
                            description=f"Bentrok venue di '{item1.venue_name}': Laga {item1.team_home} vs {item1.team_away} tumpang tindih waktu dengan {item2.team_home} vs {item2.team_away}.",
                            severity="ERROR"
                        ))

                # 2. Check Team Rest Violation (< min_team_rest_hours)
                common_teams = m1["teams"].intersection(m2["teams"])
                if common_teams:
                    for team in common_teams:
                        rest_hours = abs((m2["start"] - m1["end"]).total_seconds()) / 3600.0
                        if rest_hours < self.min_team_rest_hours:
                            conflicts.append(ScheduleConflict(
                                conflict_type="TEAM_REST_VIOLATION",
                                match_id_a=item1.match_id,
                                match_id_b=item2.match_id,
                                description=f"Pelanggaran masa istirahat tim '{team.title()}': Jeda antara match {item1.match_id} dan {item2.match_id} hanya {rest_hours:.1f} jam (minimal {self.min_team_rest_hours} jam).",
                                severity="ERROR"
                            ))

                # 3. Check Referee Overlap
                common_refs = m1["referees"].intersection(m2["referees"])
                if common_refs:
                    for ref in common_refs:
                        # Referees need at least match duration + 2 hours buffer between matches
                        ref_buffer_hours = 2.0
                        ref_busy_end1 = m1["end"] + timedelta(hours=ref_buffer_hours)
                        ref_busy_end2 = m2["end"] + timedelta(hours=ref_buffer_hours)
                        if max(m1["start"], m2["start"]) < min(ref_busy_end1, ref_busy_end2):
                            conflicts.append(ScheduleConflict(
                                conflict_type="REFEREE_OVERLAP",
                                match_id_a=item1.match_id,
                                match_id_b=item2.match_id,
                                description=f"Bentrok penugasan wasit '{ref.title()}': Ditugaskan pada match {item1.match_id} dan {item2.match_id} tanpa jeda waktu istirahat/perjalanan yang cukup.",
                                severity="ERROR"
                            ))

        is_valid = len(conflicts) == 0

        if not is_valid:
            recommendations.append("Lakukan penyesuaian jam kick-off minimal 3 jam antar-laga pada stadion yang sama.")
            recommendations.append(f"Geser tanggal pertandingan tim terkait minimal {self.min_team_rest_hours} jam setelah pertandingan terakhir.")
            recommendations.append("Tugaskan perangkat wasit alternatif untuk pertandingan yang berlangsung berdekatan.")
        else:
            recommendations.append("Jadwal kompetisi valid! Tidak ditemukan bentrok stadion, pemulihan tim, maupun alokasi wasit.")

        return ScheduleValidationResult(
            is_valid=is_valid,
            total_matches_checked=len(matches),
            conflicts=conflicts,
            recommendations=recommendations
        )
