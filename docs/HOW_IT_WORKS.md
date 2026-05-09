# How It Works — Technical Deep-Dive

This document explains the computer-vision concepts and engineering decisions
behind every part of the Gun Detection Security System.

---

## 1. What Is a Haar Cascade Classifier?

A Haar Cascade is a **machine-learning based object detector** introduced by
Viola and Jones in 2001. It remains one of the fastest face/object detectors
available without a GPU.

### 1.1 Haar Features

The classifier looks for rectangular patterns of light and dark regions,
called **Haar-like features**. For example:

```
■ ■ □ □      ■ = dark pixel region
■ ■ □ □      □ = bright pixel region
```

For a face this might correspond to "eyes are darker than cheeks".
For a gun it might correspond to the barrel-to-grip ratio or trigger-guard shape.

### 1.2 Integral Images (Why It's Fast)

Computing the sum of pixels inside any rectangle takes O(1) time if you
pre-compute an **integral image** (also called a summed-area table).  
OpenCV builds this once per frame, so thousands of feature evaluations
cost almost nothing.

### 1.3 AdaBoost Training

During training, thousands of Haar features are evaluated. **AdaBoost**
selects the small subset that together discriminate guns from non-guns.
It combines many "weak classifiers" (each barely better than random)
into one strong classifier.

### 1.4 Cascade of Classifiers

The strong classifier is arranged as a **cascade of stages**.  
Each stage is a quick gate: windows that definitely aren't guns are rejected
immediately. Only windows that pass all stages are reported as detections.
This means most of the image is discarded after stage 1 or 2, making the
algorithm very fast.

```
Window enters → Stage 0 → reject? → discard
                         → pass?   → Stage 1 → reject? → discard
                                              → pass?   → Stage 2 → ...
                                                                   → DETECTION
```

### 1.5 detectMultiScale Parameters

| Parameter | What it does |
|---|---|
| `scaleFactor` | How much the image shrinks between passes. `1.3` means each pass is 30 % smaller. Lower value = more scales checked = slower but catches more sizes. |
| `minNeighbors` | A rectangle is only kept if at least this many neighbouring rectangles also fired. Higher = fewer false positives, but may miss real guns. |
| `minSize` | Ignore detections smaller than this. Prevents tiny false positives. |

---

## 2. Frame Pre-Processing Pipeline

Before the cascade runs, every frame goes through:

```
Camera frame (BGR)
       │
       ▼
  imutils.resize(width=640)         ← standardise size; keep aspect ratio
       │
       ▼
  cv2.cvtColor(BGR → GRAY)          ← cascade needs single-channel input
       │
       ▼
  cv2.GaussianBlur(kernel=21×21)    ← smooth pixel noise
       │
       ▼
  CascadeClassifier.detectMultiScale(...)
```

**Why grayscale?**  
Colour information is not needed for shape-based detection and dropping it
halves the data volume, cutting processing time.

**Why Gaussian blur?**  
High-frequency noise (individual bright/dark pixels) creates false Haar features.
A 21×21 Gaussian kernel averages each pixel with its neighbours, suppressing
noise without smearing edges too much.

---

## 3. Motion Detection — MOG2 Background Subtraction

The system runs a parallel motion-detection pipeline using **MOG2
(Mixture of Gaussians v2)**, an adaptive background model.

### 3.1 The Idea

The algorithm maintains a per-pixel statistical model of what the
**background** looks like. Pixels that deviate significantly from their
background model are classified as **foreground** (motion).

### 3.2 Mixture of Gaussians

For each pixel, MOG2 maintains a small set of Gaussian distributions
(mean + variance) representing different lighting conditions or
background states it has seen. When a new pixel value arrives:

- If it fits one of the existing Gaussians → background → black in mask
- If it doesn't fit any → foreground (motion) → white in mask
- Shadows get a special gray (127) value so we can ignore them

### 3.3 Post-Processing the Mask

Raw MOG2 output is noisy. We clean it up with:

```
Raw mask (0/127/255)
       │
       ▼
  Threshold at 200                ← removes shadow pixels (127), keeps 255
       │
       ▼
  Morphological OPEN              ← erodes then dilates; removes small noise blobs
       │
       ▼
  Dilate (iterations=2)           ← grows remaining blobs to merge nearby motion
       │
       ▼
  findContours                    ← get outlines of moving regions
       │
       ▼
  Filter: area > MOTION_THRESHOLD ← ignore tiny specks (dust, camera noise)
```

**Morphological OPEN = Erosion then Dilation.**  
Erosion shrinks bright regions, removing tiny specs.  
Dilation then expands them back to original size.  
Net effect: small blobs disappear, large blobs survive.

---

## 4. The HUD Overlay System

The HUD is drawn in layers, from background to foreground:

```
Layer 1: Raw video frame
Layer 2: Motion boxes (green, thin)
Layer 3: Gun bounding boxes + corner accents (red, thick)
Layer 4: Alert overlay (red border + banner, only on detection)
Layer 5: FPS counter (top-left)
Layer 6: Corner decorative brackets (top-right / bottom-left)
Layer 7: Status bar (semi-transparent dark bar at bottom)
```

**Semi-transparency** is achieved with `cv2.addWeighted`:
```python
overlay = frame.copy()
cv2.rectangle(overlay, ...)           # draw solid rectangle on copy
cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
# result = 75% overlay + 25% original = semi-transparent
```

---

## 5. Alert System Design

The AlertSystem uses a **cooldown timer** pattern to avoid firing side-effects
(file saves, beeps) on every frame during a sustained detection.

```
Gun detected in frame N
       │
       ▼
  self.alert_active = True        ← overlay fires immediately (every frame)
       │
       ▼
  (now - last_alert_time) > COOLDOWN?
       │ YES                    │ NO
       ▼                        ▼
  Save screenshot            Skip file-save
  Play sound                 (overlay still shown)
  Update last_alert_time
```

This means the visual alert responds instantly, but screenshots are only
saved once every `ALERT_COOLDOWN` seconds.

---

## 6. Video Recording — OpenCV VideoWriter

When recording is triggered:

```python
fourcc = cv2.VideoWriter_fourcc(*'XVID')
writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
```

- **FOURCC** (Four Character Code) identifies the codec. `XVID` is a
  widely supported MPEG-4 codec that produces small `.avi` files.
- Each frame is passed to `writer.write(frame)`.
- After `RECORD_DURATION` seconds, `writer.release()` flushes and closes the file.

---

## 7. Logging Architecture

Two complementary log files per session:

| File | Format | Best for |
|---|---|---|
| `session_*.txt` | Plain text | Reading in a terminal, quick inspection |
| `events_*.csv` | CSV | Loading into pandas, Excel, plotting |

The CSV has columns: `Timestamp, EventType, Details`.  
`EventType` is one of: `DETECTION`, `SESSION_END`, `SYSTEM`.

---

## 8. Why These Libraries?

| Library | Role | Why this one? |
|---|---|---|
| `opencv-python` | All CV operations | Industry standard; wraps optimised C++ |
| `numpy` | Array math | Every frame *is* a numpy ndarray |
| `imutils` | Convenience utilities | `resize()` that preserves aspect ratio |
