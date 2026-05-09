"""
main.py — Gun Detection Security System  |  Entry Point
========================================================
Run this file to start the security feed:
    python main.py

Keyboard shortcuts while the window is open
--------------------------------------------
  Q  — quit
  S  — save a manual screenshot
  R  — toggle manual video recording
  M  — toggle motion-box display
  P  — pause / unpause feed

Architecture
------------
Each responsibility lives in its own module:

  config.py        — all tunable settings
  gun_detector.py  — Haar cascade detection + drawing
  motion_detector  — MOG2 background subtraction
  alert_system.py  — screenshot, sound, video recording
  event_logger.py  — txt + csv session logs
  main.py          — orchestration (this file)
"""

import cv2
import numpy as np
import imutils
import datetime
import time

import config
from gun_detector   import GunDetector
from motion_detector import MotionDetector
from alert_system   import AlertSystem
from event_logger   import EventLogger


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER CLASSES
# ══════════════════════════════════════════════════════════════════════════════

class FPSCounter:
    """
    Computes a rolling frames-per-second value.

    Every time update() is called it increments a frame counter.
    Once at least 1 second has elapsed it calculates fps = frames / elapsed,
    resets the counter, and returns the new fps value.
    """
    def __init__(self):
        self._start      = time.time()
        self._frame_cnt  = 0
        self.fps         = 0.0

    def update(self):
        self._frame_cnt += 1
        elapsed = time.time() - self._start
        if elapsed >= 1.0:
            self.fps        = self._frame_cnt / elapsed
            self._frame_cnt = 0
            self._start     = time.time()
        return self.fps

    def draw(self, frame):
        cv2.putText(frame, f"FPS: {self.fps:.1f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 255), 2)
        return frame


# ══════════════════════════════════════════════════════════════════════════════
#  HUD (Heads-Up Display) helpers
# ══════════════════════════════════════════════════════════════════════════════

def draw_status_bar(frame, gun_detected, motion_detected,
                    total_detections, recording):
    """
    Semi-transparent dark bar at the bottom of the frame showing:
      • timestamp
      • gun-detection status
      • motion status
      • cumulative detection count
      • recording indicator
    """
    h, w        = frame.shape[:2]
    bar_height  = 55

    # Semi-transparent overlay using cv2.addWeighted
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - bar_height), (w, h), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Timestamp
    ts = datetime.datetime.now().strftime("%Y-%m-%d  %I:%M:%S %p")
    cv2.putText(frame, ts, (10, h - 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    # Gun status
    gun_col  = (0, 0, 255) if gun_detected  else (0, 200, 80)
    gun_txt  = "GUN: DETECTED" if gun_detected else "GUN: CLEAR"
    cv2.putText(frame, gun_txt, (10, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, gun_col, 2)

    # Motion status
    mot_col = (0, 220, 255) if motion_detected else (80, 80, 80)
    mot_txt = "MOTION: YES" if motion_detected else "MOTION: NO"
    cv2.putText(frame, mot_txt, (200, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, mot_col, 1)

    # Detection count
    cv2.putText(frame, f"Alerts: {total_detections}", (360, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 220, 60), 1)

    # Recording indicator
    if recording:
        cv2.circle(frame, (w - 20, h - 20), 8, (0, 0, 255), -1)
        cv2.putText(frame, "REC", (w - 55, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    return frame


def draw_corner_hud(frame):
    """
    Decorative corner bracket in the top-right to give a security-camera look.
    """
    h, w = frame.shape[:2]
    margin, length, thick = 10, 25, 2
    colour = (0, 200, 255)
    # Top-right bracket
    cv2.line(frame, (w-margin, margin), (w-margin-length, margin), colour, thick)
    cv2.line(frame, (w-margin, margin), (w-margin, margin+length), colour, thick)
    # Bottom-left bracket
    cv2.line(frame, (margin, h-margin), (margin+length, h-margin), colour, thick)
    cv2.line(frame, (margin, h-margin), (margin, h-margin-length), colour, thick)
    return frame


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # ── initialise all subsystems ──────────────────────────────────────────
    logger   = EventLogger()
    detector = GunDetector()
    motion   = MotionDetector()
    alerter  = AlertSystem()
    fps      = FPSCounter()

    logger.log(f"Opening camera index {config.CAMERA_INDEX}", "SYSTEM")
    camera = cv2.VideoCapture(config.CAMERA_INDEX)

    if not camera.isOpened():
        logger.log("ERROR: Cannot open camera. Check CAMERA_INDEX in config.py", "ERROR")
        return

    # ── session counters ───────────────────────────────────────────────────
    total_frames     = 0
    total_detections = 0
    paused           = False
    show_motion      = config.SHOW_MOTION

    logger.log("System ready. Press Q to quit, S=screenshot, R=record, M=toggle motion, P=pause")

    try:
        while True:
            ret, frame = camera.read()
            if not ret or frame is None:
                logger.log("Camera read failure — exiting.", "ERROR")
                break

            # ── pause support ──────────────────────────────────────────────
            if paused:
                cv2.putText(frame, "PAUSED — press P to resume",
                            (50, frame.shape[0] // 2),
                            cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 200, 255), 2)
                cv2.imshow("Gun Detection Security System", frame)
                if cv2.waitKey(1) & 0xFF == ord('p'):
                    paused = False
                continue

            total_frames += 1
            fps.update()

            # ── pre-processing ─────────────────────────────────────────────
            # Resize keeps processing fast regardless of camera resolution
            frame = imutils.resize(frame, width=config.FRAME_WIDTH)
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # GaussianBlur smooths out pixel-level noise before detection
            gray  = cv2.GaussianBlur(gray, (21, 21), 0)

            # ── motion detection ───────────────────────────────────────────
            motion_detected = False
            if config.MOTION_ENABLED:
                motion_detected, contours, motion_boxes = motion.update(gray)
                if show_motion and motion_detected:
                    frame = motion.draw_motion(frame, motion_boxes)

            # ── gun detection ──────────────────────────────────────────────
            detections    = detector.detect(gray)
            gun_detected  = len(detections) > 0

            if gun_detected:
                total_detections += 1
                frame = detector.draw_detections(frame, detections)
                logger.log_detection(len(detections), bboxes=detections)
                alerter.trigger(frame, logger)
                alerter.start_recording((frame.shape[1], frame.shape[0]))
            else:
                alerter.reset_alert()

            # ── overlays ───────────────────────────────────────────────────
            if config.SHOW_FPS:
                frame = fps.draw(frame)

            frame = alerter.draw_alert_overlay(frame)
            frame = draw_corner_hud(frame)
            frame = draw_status_bar(
                frame, gun_detected, motion_detected,
                total_detections, alerter._video_writer is not None
            )

            # ── write frame to recording if active ─────────────────────────
            alerter.write_frame(frame)

            # ── display ────────────────────────────────────────────────────
            if config.DISPLAY_FEED:
                cv2.imshow("Gun Detection Security System", frame)

            # ── keyboard controls ──────────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                logger.log("User quit.")
                break

            elif key == ord('s'):
                ts  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                fn  = f"manual_{ts}.jpg"
                cv2.imwrite(fn, frame)
                logger.log(f"Manual screenshot saved: {fn}")

            elif key == ord('r'):
                if alerter._video_writer is None:
                    alerter.start_recording((frame.shape[1], frame.shape[0]))
                    logger.log("Manual recording STARTED.")
                else:
                    alerter.stop_recording()
                    logger.log("Manual recording STOPPED.")

            elif key == ord('m'):
                show_motion = not show_motion
                logger.log(f"Motion display {'ON' if show_motion else 'OFF'}.")

            elif key == ord('p'):
                paused = True
                logger.log("Feed PAUSED.")

    except KeyboardInterrupt:
        logger.log("KeyboardInterrupt — shutting down.", "SYSTEM")

    finally:
        alerter.stop_recording()
        logger.log_session_end(total_frames, total_detections)
        camera.release()
        cv2.destroyAllWindows()
        print("\nSystem shut down cleanly.")


if __name__ == "__main__":
    main()
