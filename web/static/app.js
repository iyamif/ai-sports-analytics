// Garuda AI Sports Analytics Dashboard JS
let canvas, ctx;
let showHeatmap = false;
let currentMatchData = null;
let liveTelemetry = [];
let animInterval = null;

const PITCH_L = 105.0; // meters
const PITCH_W = 68.0;  // meters

document.addEventListener("DOMContentLoaded", () => {
  canvas = document.getElementById("pitchCanvas");
  ctx = canvas.getContext("2d");
  drawPitch();

  // Load sample schedule initially
  loadSampleSchedule("conflict");

  // Fetch match analysis data if available
  fetchLatestMatch();

  // Connect WebSocket for live streaming
  connectWebSocket();
});

// Tab Switcher
function switchTab(tabId) {
  document.querySelectorAll(".tab-pane").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));

  document.getElementById(tabId).classList.add("active");
  event.target.classList.add("active");

  if (tabId === "visionTab") {
    drawPitch();
  }
}

// 2D Pitch Drawing
function drawPitch() {
  const w = canvas.width;
  const h = canvas.height;

  // Clear grass
  ctx.fillStyle = "#1e3a24";
  ctx.fillRect(0, 0, w, h);

  // Pitch lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.6)";
  ctx.lineWidth = 2;

  const pad = 20;
  const pw = w - pad * 2;
  const ph = h - pad * 2;

  // Boundary
  ctx.strokeRect(pad, pad, pw, ph);

  // Half-way line
  ctx.beginPath();
  ctx.moveTo(pad + pw / 2, pad);
  ctx.lineTo(pad + pw / 2, pad + ph);
  ctx.stroke();

  // Center circle (radius 9.15m scaled)
  const centerR = (9.15 / PITCH_L) * pw;
  ctx.beginPath();
  ctx.arc(pad + pw / 2, pad + ph / 2, centerR, 0, Math.PI * 2);
  ctx.stroke();

  // Center spot
  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(pad + pw / 2, pad + ph / 2, 3, 0, Math.PI * 2);
  ctx.fill();

  // Penalty areas (16.5m length, 40.3m width)
  const penL = (16.5 / PITCH_L) * pw;
  const penW = (40.3 / PITCH_W) * ph;
  const penY = pad + (ph - penW) / 2;

  // Left penalty box
  ctx.strokeRect(pad, penY, penL, penW);
  // Right penalty box
  ctx.strokeRect(pad + pw - penL, penY, penL, penW);

  // Goal areas (5.5m length, 18.32m width)
  const goalL = (5.5 / PITCH_L) * pw;
  const goalW = (18.32 / PITCH_W) * ph;
  const goalY = pad + (ph - goalW) / 2;

  ctx.strokeRect(pad, goalY, goalL, goalW);
  ctx.strokeRect(pad + pw - goalL, goalY, goalL, goalW);

  // Goals
  ctx.strokeRect(pad - 8, pad + (ph - 30) / 2, 8, 30);
  ctx.strokeRect(pad + pw, pad + (ph - 30) / 2, 8, 30);
}

// Convert meter coords (0..105, 0..68) to canvas pixels
function pitchToCanvas(xm, ym) {
  const pad = 20;
  const pw = canvas.width - pad * 2;
  const ph = canvas.height - pad * 2;
  const cx = pad + (xm / PITCH_L) * pw;
  const cy = pad + (ym / PITCH_W) * ph;
  return { x: cx, y: cy };
}

// Draw a player dot
function drawPlayer(x_m, y_m, trackId, speedKmh = 0) {
  const pt = pitchToCanvas(x_m, y_m);
  const isTeamA = trackId <= 11;
  const isSprint = speedKmh >= 20.0;

  ctx.beginPath();
  ctx.arc(pt.x, pt.y, 7, 0, Math.PI * 2);

  if (isSprint) {
    ctx.fillStyle = "#ec4899"; // Pink for sprinting
    ctx.shadowColor = "#ec4899";
    ctx.shadowBlur = 10;
  } else if (isTeamA) {
    ctx.fillStyle = "#3b82f6"; // Blue team
    ctx.shadowColor = "#3b82f6";
    ctx.shadowBlur = 4;
  } else {
    ctx.fillStyle = "#ef4444"; // Red team
    ctx.shadowColor = "#ef4444";
    ctx.shadowBlur = 4;
  }
  ctx.fill();
  ctx.shadowBlur = 0; // reset

  // Border
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Label track ID
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 9px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(trackId, pt.x, pt.y - 10);
}

// Draw soccer ball
function drawBall(x_m, y_m) {
  const pt = pitchToCanvas(x_m, y_m);
  ctx.beginPath();
  ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
  ctx.fillStyle = "#facc15";
  ctx.shadowColor = "#facc15";
  ctx.shadowBlur = 8;
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.strokeStyle = "#000000";
  ctx.lineWidth = 1;
  ctx.stroke();
}

// Render 2D Heatmap Overlay
function renderHeatmapMatrix(matrixData) {
  if (!matrixData || !matrixData.matrix) return;
  const pad = 20;
  const pw = canvas.width - pad * 2;
  const ph = canvas.height - pad * 2;
  const gridX = matrixData.grid_x;
  const gridY = matrixData.grid_y;
  const cellW = pw / gridX;
  const cellH = ph / gridY;

  for (let gy = 0; gy < gridY; gy++) {
    for (let gx = 0; gx < gridX; gx++) {
      const val = matrixData.matrix[gy][gx];
      if (val > 0.05) {
        const px = pad + gx * cellW;
        const py = pad + gy * cellH;
        // RGBA color map: transparent to yellow to red
        const alpha = Math.min(0.75, val * 0.9);
        const r = Math.min(255, Math.floor(val * 350));
        const g = Math.max(0, Math.min(255, Math.floor((1 - val) * 200)));
        ctx.fillStyle = `rgba(${r}, ${g}, 0, ${alpha})`;
        ctx.fillRect(px, py, cellW + 1, cellH + 1);
      }
    }
  }
}

function toggleHeatmap() {
  showHeatmap = !showHeatmap;
  const btn = document.getElementById("btnToggleHeatmap");
  btn.innerText = showHeatmap ? "Hide Heatmap" : "Toggle Heatmap";
  btn.classList.toggle("btn-primary", showHeatmap);
  redrawCurrentFrame();
}

function redrawCurrentFrame() {
  drawPitch();
  if (showHeatmap && currentMatchData && currentMatchData.heatmaps) {
    // Render first player or aggregate heatmap
    const firstKey = Object.keys(currentMatchData.heatmaps)[0];
    if (firstKey) renderHeatmapMatrix(currentMatchData.heatmaps[firstKey]);
  }
}

// WebSocket Connection
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    document.getElementById("systemStatus").innerText = "Live Connected";
  };

  ws.onmessage = (event) => {
    try {
      const packet = JSON.parse(event.data);
      handleLivePacket(packet);
    } catch (e) {
      console.error(e);
    }
  };

  ws.onclose = () => {
    setTimeout(connectWebSocket, 3000);
  };
}

function handleLivePacket(packet) {
  drawPitch();
  if (showHeatmap && currentMatchData && currentMatchData.heatmaps) {
    const firstKey = Object.keys(currentMatchData.heatmaps)[0];
    if (firstKey) renderHeatmapMatrix(currentMatchData.heatmaps[firstKey]);
  }

  if (packet.players) {
    packet.players.forEach(p => {
      if (p.pitch_m) {
        drawPlayer(p.pitch_m[0], p.pitch_m[1], p.track_id, p.speed_kmh);
      }
    });
  }

  if (packet.ball && packet.ball.pitch_m) {
    drawBall(packet.ball.pitch_m[0], packet.ball.pitch_m[1]);
  }
}

// Fetch Latest Analysis
async function fetchLatestMatch() {
  try {
    const res = await fetch("/api/v1/match/latest");
    if (res.ok) {
      currentMatchData = await res.json();
      updateDashboardData(currentMatchData);
    } else {
      // Auto trigger initial analysis if none exists
      triggerAnalysis();
    }
  } catch (err) {
    console.log("No previous match found, generating initial analysis...");
    triggerAnalysis();
  }
}

async function triggerAnalysis() {
  const btn = document.getElementById("btnRunAnalysis");
  btn.innerText = "Analyzing Video (AI)...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/v1/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_path: "tests/sample_match.mp4",
        max_frames: 120
      })
    });
    if (res.ok) {
      currentMatchData = await res.json();
      updateDashboardData(currentMatchData);
      btn.innerText = "Analysis Complete ✓";
    } else {
      btn.innerText = "Run Sample Match Analysis";
    }
  } catch (err) {
    console.error(err);
    btn.innerText = "Run Sample Match Analysis";
  } finally {
    btn.disabled = false;
  }
}

function updateDashboardData(data) {
  // Update Metrics Table
  const tbody = document.getElementById("metricsTableBody");
  tbody.innerHTML = "";

  const select = document.getElementById("playerReportSelect");
  select.innerHTML = '<option value="match">Ringkasan Pertandingan Keseluruhan</option>';

  if (data.player_summaries && data.player_summaries.length > 0) {
    data.player_summaries.forEach(p => {
      const tr = document.createElement("tr");
      const z = p.speed_zones || { walking_pct: 30, jogging_pct: 40, running_pct: 20, sprinting_pct: 10 };

      tr.innerHTML = `
        <td><strong>#${p.track_id}</strong></td>
        <td>${p.total_distance_km} km</td>
        <td><span style="color:#f87171;font-weight:600;">${p.top_speed_kmh}</span> km/h</td>
        <td>${p.avg_speed_kmh} km/h</td>
        <td>${p.sprint_count}x</td>
        <td>
          <div class="progress-bar-container" title="Walk: ${z.walking_pct}%, Jog: ${z.jogging_pct}%, Run: ${z.running_pct}%, Sprint: ${z.sprinting_pct}%">
            <div class="prog-walk" style="width: ${z.walking_pct}%"></div>
            <div class="prog-jog" style="width: ${z.jogging_pct}%"></div>
            <div class="prog-run" style="width: ${z.running_pct}%"></div>
            <div class="prog-sprint" style="width: ${z.sprinting_pct}%"></div>
          </div>
        </td>
      `;
      tbody.appendChild(tr);

      const opt = document.createElement("option");
      opt.value = p.track_id;
      opt.innerText = `Pemain #${p.track_id} (${p.top_speed_kmh} km/h • ${p.total_distance_km} km)`;
      select.appendChild(opt);
    });
  }

  displaySelectedPlayerReport();
  redrawCurrentFrame();
}

function displaySelectedPlayerReport() {
  const select = document.getElementById("playerReportSelect");
  const box = document.getElementById("reportContent");
  if (!currentMatchData) return;

  const val = select.value;
  if (val === "match") {
    box.innerText = currentMatchData.match_report || "Belum ada laporan pertandingan.";
  } else {
    const r = currentMatchData.scouting_reports[val];
    box.innerText = r || "Laporan pemain tidak ditemukan.";
  }
}

// COMPETITION ENGINE SAMPLES & VALIDATION
const sampleConflictMatches = [
  {
    match_id: "M01",
    tournament_name: "Piala Garuda 2026",
    team_home: "Persija",
    team_away: "Persib",
    venue_id: "GBK",
    venue_name: "Stadion Utama Gelora Bung Karno",
    start_time: "2026-11-01T15:30:00",
    duration_minutes: 105,
    buffer_minutes: 30,
    main_referee: "Thoriq Alkatiri",
    assistant_referees: ["Bambang S", "Agus P"]
  },
  {
    match_id: "M02",
    tournament_name: "Piala Garuda 2026",
    team_home: "Arema FC",
    team_away: "Persebaya",
    venue_id: "GBK", // VENUE OVERLAP (Same stadium only 1 hour later)
    venue_name: "Stadion Utama Gelora Bung Karno",
    start_time: "2026-11-01T16:30:00",
    duration_minutes: 105,
    buffer_minutes: 30,
    main_referee: "Thoriq Alkatiri", // REFEREE OVERLAP (Same referee)
    assistant_referees: ["Fajar K", "Rian D"]
  },
  {
    match_id: "M03",
    tournament_name: "Piala Garuda 2026",
    team_home: "Persija", // TEAM REST VIOLATION (Persija plays again 24 hours later)
    team_away: "Bali United",
    venue_id: "STIS",
    venue_name: "Stadion Patriot Candrabhaga",
    start_time: "2026-11-02T15:30:00",
    duration_minutes: 105,
    buffer_minutes: 30,
    main_referee: "Yudi Prasojo",
    assistant_referees: ["Iwan S", "Dedi T"]
  }
];

const sampleValidMatches = [
  {
    match_id: "M01",
    tournament_name: "Piala Garuda 2026",
    team_home: "Persija",
    team_away: "Persib",
    venue_id: "GBK",
    venue_name: "Stadion Utama Gelora Bung Karno",
    start_time: "2026-11-01T15:30:00",
    duration_minutes: 105,
    buffer_minutes: 30,
    main_referee: "Thoriq Alkatiri",
    assistant_referees: ["Bambang S", "Agus P"]
  },
  {
    match_id: "M02",
    tournament_name: "Piala Garuda 2026",
    team_home: "Arema FC",
    team_away: "Persebaya",
    venue_id: "GBLA",
    venue_name: "Stadion Gelora Bandung Lautan Api",
    start_time: "2026-11-01T19:00:00",
    duration_minutes: 105,
    buffer_minutes: 30,
    main_referee: "Fariq Hitaba",
    assistant_referees: ["Fajar K", "Rian D"]
  },
  {
    match_id: "M03",
    tournament_name: "Piala Garuda 2026",
    team_home: "Persija",
    team_away: "Bali United",
    venue_id: "GBK",
    venue_name: "Stadion Utama Gelora Bung Karno",
    start_time: "2026-11-04T19:00:00", // 72 hours later -> Safe rest
    duration_minutes: 105,
    buffer_minutes: 30,
    main_referee: "Yudi Prasojo",
    assistant_referees: ["Iwan S", "Dedi T"]
  }
];

let currentSchedules = sampleConflictMatches;

function loadSampleSchedule(type) {
  currentSchedules = (type === "valid") ? sampleValidMatches : sampleConflictMatches;
  renderScheduleTable();
  const box = document.getElementById("diagnosticContent");
  box.className = "text-muted";
  box.innerText = `Jadwal sampel "${type === 'valid' ? 'Ideal (Bebas Bentrok)' : 'Simulasi Bentrok'}" dimuat. Klik "Validasi Jadwal" untuk memeriksa.`;
}

function renderScheduleTable() {
  const tbody = document.getElementById("scheduleTableBody");
  tbody.innerHTML = "";

  currentSchedules.forEach(m => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${m.match_id}</strong></td>
      <td>${m.tournament_name}</td>
      <td><strong>${m.team_home}</strong> vs <strong>${m.team_away}</strong></td>
      <td>${m.venue_name}</td>
      <td>${m.start_time.replace("T", " ")}</td>
      <td>${m.main_referee}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function validateSchedule() {
  const box = document.getElementById("diagnosticContent");
  box.innerHTML = "Memeriksa bentrok jadwal turnamen...";

  try {
    const res = await fetch("/api/v1/competition/validate-schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        matches: currentSchedules,
        min_team_rest_hours: 48
      })
    });

    const result = await res.json();
    if (result.is_valid) {
      box.innerHTML = `
        <div class="valid-item">
          <strong>✓ JADWAL VALID & LAYAK KOMPETISI</strong><br>
          Semua ${result.total_matches_checked} pertandingan bebas dari bentrok venue, jadwal istirahat tim terpenuhi minimal 48 jam, dan tidak ada tumpang tindih wasit.
        </div>
      `;
    } else {
      let html = `<div style="margin-bottom:0.5rem;font-weight:600;color:#f87171;">Ditemukan ${result.conflicts.length} Konflik Jadwal:</div>`;
      result.conflicts.forEach(c => {
        html += `
          <div class="conflict-item">
            <strong>[${c.conflict_type}] Match ${c.match_id_a} & ${c.match_id_b}</strong><br>
            ${c.description}
          </div>
        `;
      });
      if (result.recommendations && result.recommendations.length > 0) {
        html += `<div style="margin-top:0.5rem;font-size:0.8rem;color:#94a3b8;"><strong>Rekomendasi AI:</strong><br>• ${result.recommendations.join('<br>• ')}</div>`;
      }
      box.innerHTML = html;
    }
  } catch (err) {
    box.innerHTML = `<div class="conflict-item">Gagal memvalidasi: ${err.message}</div>`;
  }
}
