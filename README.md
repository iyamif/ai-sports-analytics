# Garuda AI Sports Analytics & Competition Platform (GSI)

Sistem analitik sepak bola terpadu berbasis **Computer Vision (YOLOv8 + ByteTrack)**, **Spatial Homography (2D Pitch Mapping)**, **Redis Live Telemetry**, **NLP Scouting Report Generation**, dan **Competition Schedule Conflict Engine**.

Dikembangkan oleh **Ilham Firmansyah** untuk portofolio posisi AI Engineer / Sports Analytics di **Garuda Sepak Bola Indonesia (GSI)**.

---

## 🌟 Fitur Utama

### 1. Computer Vision & Multi-Object Tracking
* **YOLOv8 + ByteTrack**: Deteksi otomatis pemain, wasit, dan bola pada setiap frame video pertandingan.
* **Foot-Contact Ground Mapping**: Mengambil titik kontak kaki pemain untuk diproyeksikan ke permukaan lapangan.
* **Spatial Homography Transform**: Mengonversi koordinat piksel kamera (*broadcast angle*) ke koordinat riil lapangan standar FIFA ($105\text{ m} \times 68\text{ m}$).

### 2. Physical & Tactical Analytics Engine
* **Jarak Tempuh (*Total Distance Covered*)**: Kalkulasi jarak akumulatif dalam meter dan kilometer.
* **Kecepatan & Top Speed**: Kalkulasi kecepatan seketika (*instantaneous speed*) dan kecepatan puncak (*top speed* dalam km/jam).
* **Sprint Bursts Counter**: Deteksi otomatis frekuensi akselerasi eksplosif ($> 20\text{ km/jam}$).
* **Speed Zone Breakdown**: Klasifikasi intensitas fisik (*Walking*, *Jogging*, *Running*, *Sprinting*).
* **Spatial Heatmaps**: Peta densitas 2D posisi pemain (*Kernel Density Estimation*) di atas lapangan.

### 3. Redis Streaming & Real-Time Telemetry
* Integrasi **Redis Pub/Sub** dan WebSocket untuk menyiarkan koordinat $22\text{ pemain} + \text{bola}$ per detik secara instan tanpa membebani database utama.
* Fallback *high-performance in-memory buffer* saat Redis offline.

### 4. Automated NLP Scouting Reports
* Menghasilkan laporan evaluasi taktik dan fisik otomatis dalam bahasa Indonesia yang siap dibaca oleh tim pelatih (*head coach*) dan manajemen kompetisi.
* Menganalisis *work-rate*, profil atletik, indikasi *fatigue*, serta rekomendasi porsi latihan spesifik.

### 5. Competition Schedule Conflict Engine
* **Venue Overlap Detection**: Mencegah dua pertandingan dijadwalkan pada stadion yang sama di waktu yang bertabrakan.
* **Team Rest Interval Protection**: Memastikan setiap tim memiliki waktu pemulihan minimal 48 jam antar-laga.
* **Referee & Official Allocation**: Mencegah penugasan wasit tumpang-tindih pada laga yang berdekatan.

---

## 🏗️ Struktur Proyek

```
ai-sports-analytics/
├── requirements.txt             # Dependensi Python (PyTorch, YOLOv8, OpenCV, FastAPI, Redis)
├── run.py                       # Launcher satu-klik server & dashboard
├── README.md                    # Dokumentasi lengkap
├── src/
│   ├── config.py                # Konfigurasi lapangan (105x68m) & ambang batas kecepatan
│   ├── vision/
│   │   ├── detector.py          # YOLOv8 + ByteTrack & centroid tracking
│   │   ├── pitch_homography.py  # Transformasi perspektif matriks homografi
│   │   └── video_processor.py   # Pipeline analisis video end-to-end
│   ├── analytics/
│   │   ├── metrics.py           # Kalkulasi jarak, top speed, sprint counter
│   │   ├── heatmap.py           # Generator matriks 2D heatmap
│   │   └── report_generator.py  # Engine pembuat laporan scouting NLP
│   ├── competition/
│   │   └── schedule_engine.py   # Engine deteksi konflik jadwal turnamen
│   └── api/
│       ├── app.py               # Server FastAPI (REST + WebSocket)
│       └── models.py            # Skema data Pydantic
├── web/
│   ├── index.html               # Web Dashboard interaktif
│   └── static/
│       ├── app.js               # Canvas 2D pitch radar & visualisasi live
│       └── style.css            # Dark mode sports UI styling
└── tests/
    ├── create_sample_match.py   # Generator video simulasi pertandingan
    └── test_pipeline.py         # Uji integrasi pipeline end-to-end (100% Pass)
```

---

## 🚀 Cara Menjalankan

### 1. Prasyarat
* Python 3.10+ (Sudah teruji di Windows)
* Koneksi internet (untuk mengunduh model YOLOv8n sekali saja di awal, ~6MB)

### 2. Jalankan Server & Web Dashboard
```bash
python run.py
```
Akses di browser:
* **Dashboard Interaktif**: [http://localhost:8000](http://localhost:8000)
* **Dokumentasi API (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Menjalankan Tes Integrasi
```bash
python tests/test_pipeline.py
```
Hasil uji integrasi memverifikasi:
* Ekstraksi frame video & tracking koordinat pemain.
* Kalkulasi metrik fisik (Distance, Speed, Sprints).
* Matriks 2D Heatmap & NLP Scouting Report.
* Deteksi 3 jenis konflik jadwal kompetisi.

---

## 📄 Lisensi & Kontributor
Dikembangkan secara mandiri oleh **Ilham Firmansyah** (Software & AI Engineer).
