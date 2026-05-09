# 🔫 Gun Detection Security System

A real-time computer-vision security application built with Python and OpenCV.  
Detects firearms in a live camera feed using a trained **Haar Cascade classifier**,
overlays a HUD (heads-up display), saves screenshots, records video clips, and
logs every event to structured files.

---

## 📸 Features

| Feature | Description |
|---|---|
| **Gun Detection** | Haar Cascade classifier scans every frame |
| **Motion Detection** | MOG2 background subtraction flags moving objects |
| **Alert Overlay** | Red border + banner when a weapon is detected |
| **Auto Screenshot** | JPEG saved to `captures/` on each detection |
| **Video Recording** | AVI clip saved to `recordings/` (optional) |
| **Event Logging** | Human-readable `.txt` + analysis-ready `.csv` in `logs/` |
| **FPS Counter** | Live frames-per-second display |
| **HUD Status Bar** | Timestamp, detection state, motion state, alert count |
| **Keyboard Controls** | Q quit · S screenshot · R record · M motion toggle · P pause |

---

## 📁 Project Structure

```
gun-detection-system/
│
├── main.py               ← Entry point — run this
├── config.py             ← All settings (camera, thresholds, paths…)
├── gun_detector.py       ← Haar Cascade detection + drawing
├── motion_detector.py    ← MOG2 background-subtraction motion detection
├── alert_system.py       ← Screenshot, overlay, sound, video recording
├── event_logger.py       ← .txt + .csv session logging
│
├── cascade.xml           ← Pre-trained gun Haar Cascade  ← ADD THIS FILE
├── requirements.txt      ← pip dependencies
│
├── captures/             ← Auto-created; holds detection screenshots
├── logs/                 ← Auto-created; holds session logs
├── recordings/           ← Auto-created; holds video clips
│
└── docs/
    ├── HOW_IT_WORKS.md         ← Technical deep-dive
    ├── MODULES_EXPLAINED.md    ← Every function documented
    └── SETUP_GUIDE.md          ← Step-by-step installation
```

---

## ⚡ Quick Start

### 1 — Clone / download
```bash
git clone https://github.com/YOUR_USERNAME/gun-detection-system.git
cd gun-detection-system
```

### 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### 3 — Add your cascade file
Copy your `cascade.xml` into the project root (same folder as `main.py`).

### 4 — Run
```bash
python main.py
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `Q` | Quit the program |
| `S` | Save a manual screenshot |
| `R` | Toggle manual video recording on/off |
| `M` | Toggle motion-box display |
| `P` | Pause / resume the feed |

---

## ⚙️ Configuration

Open **`config.py`** to change any setting without touching other code:

```python
CAMERA_INDEX   = 0       # Change to 1 for an external webcam
FRAME_WIDTH    = 640     # Wider = more detail, slower FPS
MIN_NEIGHBORS  = 20      # Raise to reduce false positives
ALERT_COOLDOWN = 5       # Seconds between repeated file-saves
RECORD_ON_DETECTION = True   # Enable auto video recording
```

---

## 📖 Documentation

| Doc | Contents |
|---|---|
| [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md) | Haar Cascades, MOG2, image pipeline explained |
| [`docs/MODULES_EXPLAINED.md`](docs/MODULES_EXPLAINED.md) | Every class and function in detail |
| [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) | Detailed installation on Windows / macOS / Linux |

---

## 🛠 Tech Stack

- **Python 3.8+**
- **OpenCV** (`opencv-python`) — core CV library
- **NumPy** — array math underneath every frame
- **imutils** — convenience wrappers for resizing

---

## 📊 Log Files

Each session creates two files in `logs/`:

- `session_YYYYMMDD_HHMMSS.txt` — readable event log
- `events_YYYYMMDD_HHMMSS.csv`  — structured CSV with timestamp, event type, details

The CSV can be loaded directly into pandas for analysis:
```python
import pandas as pd
df = pd.read_csv("logs/events_20240915_143000.csv")
print(df[df["EventType"] == "DETECTION"])
```

---

## ⚠️ Disclaimer

This project is for **educational purposes only**.  
It demonstrates classical computer-vision techniques (Haar Cascades, background
subtraction) on a publicly available trained model.  
Always use security technology responsibly and in compliance with local laws.
