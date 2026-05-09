# Modules & Functions — Complete Reference

Every file, class, and function explained.

---

## `config.py`

A plain Python file of constants. No classes, no functions — just variables.

**Why a separate config file?**  
All tunable values live in one place. If you want to change the camera,
the detection sensitivity, or where files are saved, you edit `config.py`
and nowhere else.

| Variable | Type | Purpose |
|---|---|---|
| `CAMERA_INDEX` | int | Which camera to open (0 = built-in) |
| `FRAME_WIDTH` | int | Width frames are resized to before processing |
| `DISPLAY_FEED` | bool | Whether to show the OpenCV window |
| `CASCADE_PATH` | str | Path to `cascade.xml` |
| `SCALE_FACTOR` | float | Image pyramid step (Haar cascade parameter) |
| `MIN_NEIGHBORS` | int | Detection confidence filter (Haar parameter) |
| `MIN_SIZE` | tuple | Minimum detection size in pixels |
| `MOTION_ENABLED` | bool | Enable/disable MOG2 motion detection |
| `MOTION_THRESHOLD` | int | Minimum contour area counted as motion |
| `SHOW_MOTION` | bool | Draw motion boxes on screen |
| `ALERT_COOLDOWN` | int | Seconds between repeated alert side-effects |
| `PLAY_SOUND` | bool | Beep on detection |
| `SAVE_CAPTURES` | bool | Save screenshots on detection |
| `CAPTURES_DIR` | str | Folder for screenshots |
| `RECORD_ON_DETECTION` | bool | Auto-record video clips |
| `RECORD_DIR` | str | Folder for video clips |
| `RECORD_DURATION` | int | Seconds to record per clip |
| `SAVE_LOGS` | bool | Write log files |
| `LOGS_DIR` | str | Folder for log files |
| `SHOW_FPS` | bool | Overlay FPS counter |

---

## `gun_detector.py` — class `GunDetector`

Wraps `cv2.CascadeClassifier` with drawing and ROI utilities.

### `__init__(self)`
Loads `cascade.xml` using `cv2.CascadeClassifier()`.  
Raises `FileNotFoundError` immediately if the file is missing or corrupt,
rather than failing silently later.

### `detect(self, gray_frame) → list`
Calls `cascade.detectMultiScale()` on the blurred grayscale frame.  
Returns a list of `(x, y, w, h)` tuples — one per detected gun.  
Returns an empty list `[]` if nothing is found.

**Why list and not numpy array?**  
The raw return from `detectMultiScale` is a numpy array *or* an empty tuple
(not an empty array). Normalising to a list means the rest of the code can
always do `if len(detections) > 0` without type errors.

### `draw_detections(self, frame, detections, color) → frame`
For each `(x, y, w, h)`:
- Draws a thick rectangle around the detection
- Adds a coloured label box with "GUN DETECTED" text
- Draws corner accent marks (4 L-shapes at the corners) — this is a
  common UI pattern in security / military HUDs

### `get_rois(self, frame, gray_frame, detections) → list`
Crops the area inside each bounding box from both the colour and
grayscale frames. Returns a list of dicts.  
Use case: pass `roi["gray"]` to a second, more accurate classifier for
verification (reduces false positives).

---

## `motion_detector.py` — class `MotionDetector`

### `__init__(self)`
Creates a **MOG2** background subtractor via `cv2.createBackgroundSubtractorMOG2()`.

`history=500` — the model averages over the last 500 frames. On a 30 fps
camera that's ~17 seconds of background learning.

`varThreshold=50` — how different a pixel must be from its background
model to count as foreground. Lower = more sensitive.

`detectShadows=True` — shadows are marked 127 (not 255) so the threshold
step at 200 strips them out.

Creates `self._kernel`, a 5×5 elliptical structuring element reused in
morphological operations (created once for efficiency).

### `update(self, gray_frame) → (bool, contours, bboxes)`

1. `bg_subtractor.apply(gray_frame)` — updates the background model and
   returns a foreground mask.
2. `cv2.threshold(mask, 200, 255, THRESH_BINARY)` — binarise; removes shadows.
3. `cv2.morphologyEx(MORPH_OPEN)` — erode then dilate to kill tiny noise.
4. `cv2.dilate(iterations=2)` — expand surviving blobs to connect nearby regions.
5. `cv2.findContours(RETR_EXTERNAL)` — only outer contours (no nested).
6. Filter by `cv2.contourArea(c) > MOTION_THRESHOLD`.
7. `cv2.boundingRect(c)` — axis-aligned bounding box for each contour.

### `draw_motion(self, frame, bounding_boxes) → frame`
Draws thin green rectangles. Kept visually lighter than the gun boxes
so the HUD stays readable.

---

## `alert_system.py` — class `AlertSystem`

### `__init__(self)`
Initialises timing variables and creates output directories
(`os.makedirs(..., exist_ok=True)` — no error if folder already exists).

### `trigger(self, frame, logger=None)`
The main alert entry point. Called every frame a gun is detected.

**Cooldown logic:**
```python
if (time.time() - self._last_alert_time) < config.ALERT_COOLDOWN:
    return   # skip heavy side-effects
```
This prevents saving a screenshot 30 times per second.

After the cooldown, it:
1. Saves a JPEG via `_save_capture()`
2. Optionally beeps via `_beep()`
3. Prints a console banner

### `draw_alert_overlay(self, frame) → frame`
Only draws when `self.alert_active is True`.  
Uses `cv2.getTextSize()` to compute the text width so the banner can be
centred regardless of frame width.  
`cv2.FONT_HERSHEY_DUPLEX` is a bolder font than SIMPLEX — more visible.

### `reset_alert(self)`
Sets `alert_active = False`. Called when no gun is in the current frame
so the overlay disappears.

### `start_recording(self, frame_size, fps=20)`
Creates a `cv2.VideoWriter` only if one isn't already active
(`if self._video_writer is not None: return`).

`cv2.VideoWriter_fourcc(*'XVID')` — XVID is MPEG-4 video.
The `*` unpacks the string `'XVID'` into four separate character arguments.

### `write_frame(self, frame)`
Passes the frame to the writer and checks if `RECORD_DURATION` has elapsed.

### `stop_recording(self)`
Calls `release()` which flushes the buffer to disk and frees the file handle.

### `_save_capture(self, frame, timestamp) → filename`
`cv2.imwrite(path, frame)` — writes a JPEG. OpenCV infers the format from
the file extension.

### `_beep(self)`
Tries `winsound` (Windows only), then `paplay` (Linux PulseAudio),
then falls back to `print('\a')` which sends the ASCII bell character
to the terminal.

---

## `event_logger.py` — class `EventLogger`

### `__init__(self)`
Creates two log files whose names embed the session timestamp:
- `session_20240915_143000.txt`
- `events_20240915_143000.csv`

Writes the CSV header row immediately.

### `log(self, message, event_type="INFO")`
Formats a line: `[2024-09-15 14:30:00] [INFO  ] Message here`

Prints to console AND appends to the `.txt` file.  
Using `'a'` mode (append) means the file grows line by line and
is never overwritten mid-session.

### `log_detection(self, num_guns, bboxes=None)`
Calls `log()` with `event_type="ALERT"` and also appends a row to the CSV.  
Having both ensures the readable log and the structured CSV stay in sync.

### `log_session_end(self, total_frames, total_detections)`
Writes a summary. Called in `main.py`'s `finally` block so it always
executes even if the program crashes.

---

## `main.py`

### class `FPSCounter`
Tracks elapsed time and frame count. When 1 second passes, divides
frames by elapsed time to get fps, then resets both counters.
This gives a rolling 1-second average rather than an instantaneous value.

### `draw_status_bar(frame, ...)`
Uses `cv2.addWeighted` to blend a solid dark rectangle with the original
frame, creating a semi-transparent bar.  
All text is drawn on this blended result.

### `draw_corner_hud(frame)`
Four short `cv2.line()` calls in the top-right and bottom-left corners.
Pure cosmetic detail — signals "security camera interface".

### `main()`
The application's event loop.

**Initialisation** — creates one instance of each subsystem.

**Per-frame pipeline:**
```
read frame → resize → grayscale → blur
    → motion detection (every frame)
    → gun detection (every frame)
    → draw overlays (every frame)
    → write to recording (if active)
    → show window (if DISPLAY_FEED)
    → handle keyboard
```

**`finally` block** — `camera.release()` and `cv2.destroyAllWindows()`
run even if an exception occurs, preventing zombie processes or locked cameras.
