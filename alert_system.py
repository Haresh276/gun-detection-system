"""
alert_system.py — Multi-Channel Alert System
=============================================
Fires when a gun is detected. Handles:
  • On-screen red-border overlay
  • Automatic screenshot capture
  • Optional audio beep (cross-platform)
  • Optional video clip recording
  • Cooldown timer so alerts don't spam every single frame
"""

import cv2
import os
import time
import datetime
import config


class AlertSystem:
    """
    Centralised alert manager. Decouple alert logic from detection logic
    so it's easy to add new channels (e.g., email, Telegram) later.
    """

    def __init__(self):
        self._last_alert_time = 0.0    # Unix timestamp of last alert
        self.alert_active     = False  # True while a gun is on-screen
        self._video_writer    = None   # OpenCV VideoWriter or None
        self._record_start    = None   # Time recording began

        # Create output directories
        if config.SAVE_CAPTURES:
            os.makedirs(config.CAPTURES_DIR, exist_ok=True)
        if config.RECORD_ON_DETECTION:
            os.makedirs(config.RECORD_DIR, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  TRIGGER
    # ------------------------------------------------------------------ #

    def trigger(self, frame, logger=None):
        """
        Call this every frame a gun is detected.
        Respects ALERT_COOLDOWN so side-effects (sound, file-save) don't
        fire every 30 ms.

        Parameters
        ----------
        frame  : np.ndarray — current BGR frame (used for screenshot)
        logger : EventLogger or None
        """
        now = time.time()
        self.alert_active = True

        if now - self._last_alert_time < config.ALERT_COOLDOWN:
            return   # Still cooling down — skip heavy side-effects

        self._last_alert_time = now
        ts = datetime.datetime.now()

        if config.SAVE_CAPTURES:
            filename = self._save_capture(frame, ts)
            if logger:
                logger.log(f"Screenshot saved → {filename}")

        if config.PLAY_SOUND:
            self._beep()

        print(f"\n{'='*50}")
        print(f"  ⚠  GUN DETECTED  —  {ts.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")

    # ------------------------------------------------------------------ #
    #  OVERLAY
    # ------------------------------------------------------------------ #

    def draw_alert_overlay(self, frame):
        """
        When alert_active is True, draw a pulsing red border and a
        centred warning banner at the top of the frame.
        """
        if not self.alert_active:
            return frame

        h, w = frame.shape[:2]

        # Red border — thickness 12px
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 0, 255), 12)

        # Banner background
        banner_text = "!! WEAPON DETECTED !!"
        (tw, th), _ = cv2.getTextSize(
            banner_text, cv2.FONT_HERSHEY_DUPLEX, 0.9, 2
        )
        bx = (w - tw) // 2
        cv2.rectangle(frame, (bx - 12, 8), (bx + tw + 12, th + 20),
                      (0, 0, 180), -1)
        cv2.rectangle(frame, (bx - 12, 8), (bx + tw + 12, th + 20),
                      (0, 0, 255), 2)
        cv2.putText(frame, banner_text, (bx, th + 12),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2)

        return frame

    def reset_alert(self):
        """Call this when no gun is detected to clear the overlay."""
        self.alert_active = False

    # ------------------------------------------------------------------ #
    #  RECORDING
    # ------------------------------------------------------------------ #

    def start_recording(self, frame_size, fps=20):
        """
        Begin writing frames to an AVI file.

        Parameters
        ----------
        frame_size : (width, height) tuple
        fps        : frames per second for output video
        """
        if not config.RECORD_ON_DETECTION:
            return
        if self._video_writer is not None:
            return   # Already recording

        ts       = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(config.RECORD_DIR, f"detection_{ts}.avi")
        fourcc   = cv2.VideoWriter_fourcc(*'XVID')
        self._video_writer = cv2.VideoWriter(filepath, fourcc, fps, frame_size)
        self._record_start = time.time()
        print(f"Recording started → {filepath}")

    def write_frame(self, frame):
        """Write frame to active recording, stop after RECORD_DURATION."""
        if self._video_writer is None:
            return
        self._video_writer.write(frame)
        if time.time() - self._record_start > config.RECORD_DURATION:
            self.stop_recording()

    def stop_recording(self):
        """Flush and close the video writer."""
        if self._video_writer:
            self._video_writer.release()
            self._video_writer = None
            print("Recording stopped.")

    # ------------------------------------------------------------------ #
    #  PRIVATE HELPERS
    # ------------------------------------------------------------------ #

    def _save_capture(self, frame, timestamp):
        """Save a JPEG screenshot and return its filename."""
        name = f"gun_detected_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(config.CAPTURES_DIR, name)
        cv2.imwrite(path, frame)
        return name

    def _beep(self):
        """
        Cross-platform terminal beep.
        Windows  → winsound.Beep
        Linux    → paplay (PulseAudio)
        Fallback → ASCII bell character
        """
        try:
            import winsound
            winsound.Beep(1000, 400)
        except ImportError:
            try:
                import subprocess
                subprocess.run(
                    ['paplay', '/usr/share/sounds/alsa/Front_Left.wav'],
                    capture_output=True
                )
            except Exception:
                print('\a', end='', flush=True)
