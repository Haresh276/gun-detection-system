"""
config.py — Central Configuration for Gun Detection Security System
====================================================================
All tunable settings live here. Change values to adjust system behavior
without touching any other file.
"""

# ──────────────────────────────────────────────
#  CAMERA
# ──────────────────────────────────────────────
CAMERA_INDEX  = 0      # 0 = built-in webcam, 1 = first external camera
FRAME_WIDTH   = 640    # Width frames are resized to before processing
DISPLAY_FEED  = True   # Show the live video window

# ──────────────────────────────────────────────
#  GUN DETECTION (Haar Cascade)
# ──────────────────────────────────────────────
CASCADE_PATH   = "cascade.xml"   # Path to your trained cascade file
SCALE_FACTOR   = 1.3             # How much image shrinks each pass (>1.0)
MIN_NEIGHBORS  = 20              # Higher → fewer but more confident detections
MIN_SIZE       = (100, 100)      # Ignore detections smaller than this (px)

# ──────────────────────────────────────────────
#  MOTION DETECTION
# ──────────────────────────────────────────────
MOTION_ENABLED   = True   # Use background-subtraction motion detection
MOTION_THRESHOLD = 500    # Minimum contour area (px²) counted as motion
SHOW_MOTION      = True   # Draw green motion boxes on frame

# ──────────────────────────────────────────────
#  ALERTS
# ──────────────────────────────────────────────
ALERT_COOLDOWN   = 5      # Seconds between repeated alerts (prevents spam)
PLAY_SOUND       = False  # Beep on detection (platform-dependent)

# ──────────────────────────────────────────────
#  CAPTURES  (screenshots on detection)
# ──────────────────────────────────────────────
SAVE_CAPTURES = True
CAPTURES_DIR  = "captures"

# ──────────────────────────────────────────────
#  VIDEO RECORDING
# ──────────────────────────────────────────────
RECORD_ON_DETECTION = False   # Auto-record clip when gun detected
RECORD_DIR          = "recordings"
RECORD_DURATION     = 10      # Seconds to record after detection

# ──────────────────────────────────────────────
#  LOGGING
# ──────────────────────────────────────────────
SAVE_LOGS = True
LOGS_DIR  = "logs"

# ──────────────────────────────────────────────
#  DISPLAY
# ──────────────────────────────────────────────
SHOW_FPS = True   # Overlay frames-per-second counter on video
