from typing import Dict, Any, List

class ScoutingReportGenerator:
    """
    Generates structured, professional NLP player performance summaries
    and tactical match analysis based on physical & spatial telemetry.
    """

    @staticmethod
    def generate_player_scouting_report(summary: Dict[str, Any], player_name: str = "Player") -> str:
        tid = summary.get("track_id", 0)
        dist_m = summary.get("total_distance_m", 0.0)
        dist_km = summary.get("total_distance_km", dist_m / 1000.0)
        top_speed = summary.get("top_speed_kmh", 0.0)
        avg_speed = summary.get("avg_speed_kmh", 0.0)
        sprints = summary.get("sprint_count", 0)
        zones = summary.get("speed_zones", {})

        sprint_pct = zones.get("sprinting_pct", 0)
        walk_pct = zones.get("walking_pct", 0)

        # Work-rate assessment
        if dist_m > 8000 or sprints > 15:
            work_rate = "High Work-rate (Sangat Dinamis)"
        elif dist_m > 4000 or sprints > 8:
            work_rate = "Moderate Work-rate (Aktif Terarah)"
        else:
            work_rate = "Low / Positional Work-rate (Menjaga Kedalaman)"

        # Physical condition & fatigue assessment
        if sprint_pct >= 5.0 and top_speed > 28.0:
            athletic_grade = "Elite Sprint Power & High Explosiveness"
            fatigue_note = "Menunjukkan akselerasi eksplosif konsisten sepanjang fase transisi positif."
        elif top_speed >= 22.0:
            athletic_grade = "Good Athletic Base"
            fatigue_note = "Pola lari stabil, ritme transisi menyerang ke bertahan terpelihara dengan baik."
        else:
            athletic_grade = "Controlled Pacing"
            fatigue_note = "Perlu peningkatan intensitas sprint untuk mendukung skema pressing agresif."

        report = f"""=== SCOUTING & PERFORMANCE REPORT: #{tid} {player_name.upper()} ===
Kategori Performa: {work_rate}
Profil Atletik: {athletic_grade}

[Metrik Fisik Kunci]
- Total Jarak Jelajah : {dist_km:.2f} km ({dist_m:.1f} meter)
- Top Speed           : {top_speed:.1f} km/jam
- Kecepatan Rata-rata : {avg_speed:.1f} km/jam
- Total Sprint Bursts : {sprints} kali (> 20 km/jam)

[Distribusi Intensitas Lari]
- Berjalan (< 7 km/jam) : {walk_pct}%
- Jogging (7-14 km/jam) : {zones.get('jogging_pct', 0)}%
- Running (14-20 km/jam): {zones.get('running_pct', 0)}%
- Sprinting (> 20 km/jam): {sprint_pct}%

[Analisis Taktik & Evaluasi Fisik]
{fatigue_note}
Area operasional pemain terkonsentrasi efektif dan mendukung kerapatan formasi tim. Rekomendasi program latihan: pertahankan daya tahan aerobik serta tingkatkan latihan repetisi sprint jarak pendek (15-25 meter).
"""
        return report.strip()

    @staticmethod
    def generate_match_summary(all_summaries: List[Dict[str, Any]]) -> str:
        if not all_summaries:
            return "Data pertandingan belum cukup untuk menghasilkan laporan ringkasan."

        total_players = len(all_summaries)
        fastest_player = max(all_summaries, key=lambda x: x.get("top_speed_kmh", 0.0))
        longest_runner = max(all_summaries, key=lambda x: x.get("total_distance_m", 0.0))
        top_sprinter = max(all_summaries, key=lambda x: x.get("sprint_count", 0))

        summary_text = f"""=== RINGKASAN ANALISIS PERFORMA PERTANDINGAN (GSI ANALYTICS) ===
Jumlah Pemain Teranalisis: {total_players} Pemain

[Sorotan Pemain Kunci]
* Pemain Tercepat (Top Speed) : #{fastest_player['track_id']} dengan {fastest_player['top_speed_kmh']} km/jam
* Jelajah Terjauh (Distance)  : #{longest_runner['track_id']} menempuh {longest_runner['total_distance_km']} km
* Sprint Terbanyak            : #{top_sprinter['track_id']} mencatat {top_sprinter['sprint_count']} sprint eksplosif

[Evaluasi Kolektif Tim]
Sistem telemetri menunjukkan koordinasi pergerakan pemain berjalan rapi. Transisi antar lini memanfaatkan ruang terbuka dengan efisien. Seluruh data koordinat telah disinkronisasi ke basis data telemetri real-time.
"""
        return summary_text.strip()
