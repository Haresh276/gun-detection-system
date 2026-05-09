# Setup Guide — Step-by-Step Installation

---

## Prerequisites

- **Python 3.8 or newer**  
  Check with: `python --version` or `python3 --version`
- A working **webcam** (built-in or USB)
- `pip` package manager

---

## Step 1 — Get the Code

**Option A — Clone from GitHub**
```bash
git clone https://github.com/YOUR_USERNAME/gun-detection-system.git
cd gun-detection-system
```

**Option B — Download ZIP**  
Click *Code → Download ZIP* on GitHub, extract it, and open a terminal
in the extracted folder.

---

## Step 2 — (Recommended) Create a Virtual Environment

A virtual environment keeps these packages isolated from your system Python.

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate
```

You'll see `(venv)` at the start of your terminal prompt when it's active.

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package | Version | Why |
|---|---|---|
| `opencv-python` | ≥ 4.8 | Core computer-vision library (detection, drawing, video) |
| `numpy` | ≥ 1.24 | Every video frame is a NumPy ndarray under the hood |
| `imutils` | ≥ 0.5.4 | `imutils.resize()` resizes while preserving aspect ratio |

---

## Step 4 — Add the Cascade File

Copy your `cascade.xml` file into the **project root** (same folder as `main.py`).

```
gun-detection-system/
├── main.py
├── cascade.xml   ← place it here
├── config.py
└── ...
```

If your cascade file has a different name, update `CASCADE_PATH` in `config.py`:
```python
CASCADE_PATH = "my_cascade.xml"
```

---

## Step 5 — Run

```bash
python main.py
```

A window titled **"Gun Detection Security System"** should open showing
your webcam feed.

---

## Step 6 — Adjust Settings

Open `config.py` in any text editor.

**Common tweaks:**

```python
# Wrong camera / no image?
CAMERA_INDEX = 1   # Try 1, 2, 3 … for different cameras

# Too many false positives?
MIN_NEIGHBORS = 25   # Raise this (default 20)

# Missing real detections?
MIN_NEIGHBORS = 15   # Lower this

# Detection boxes too small?
MIN_SIZE = (80, 80)   # Lower the minimum size

# Want video clips of detections?
RECORD_ON_DETECTION = True

# Don't want the window (headless server)?
DISPLAY_FEED = False
```

---

## Troubleshooting

### Camera doesn't open
- Make sure no other app is using the camera.
- Try `CAMERA_INDEX = 1` or `2` in `config.py`.
- On Linux, check: `ls /dev/video*`

### `FileNotFoundError: cascade.xml`
- `cascade.xml` must be in the same folder as `main.py`.
- Check the path in `config.py` → `CASCADE_PATH`.

### `ModuleNotFoundError: No module named 'cv2'`
```bash
pip install opencv-python
```

### `ModuleNotFoundError: No module named 'imutils'`
```bash
pip install imutils
```

### Very low FPS
- Lower `FRAME_WIDTH` in `config.py` (e.g., `480` instead of `640`).
- Disable motion detection: `MOTION_ENABLED = False`.
- Disable video recording: `RECORD_ON_DETECTION = False`.

### Window opens but immediately closes
- Run from terminal, not by double-clicking — so you can see error messages.

---

## Platform Notes

### Windows
- `opencv-python` includes everything; no extra system packages needed.
- If you want the audio beep: it uses `winsound` (built into Python on Windows).

### macOS
```bash
brew install python   # if not installed
pip install -r requirements.txt
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3-pip python3-venv
pip install -r requirements.txt
```

---

## Verifying OpenCV Works

Run this in your terminal to confirm OpenCV is installed correctly:
```bash
python -c "import cv2; print('OpenCV version:', cv2.__version__)"
```

Expected output: `OpenCV version: 4.x.x`
