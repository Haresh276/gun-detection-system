"""
event_logger.py — Structured Session Logging
=============================================
Writes all events to:
  • A human-readable .txt file  (session log)
  • A machine-readable .csv file (detection events, suitable for analysis)

Keeping these separate means you can later load the CSV into pandas,
plot detection frequency over time, etc.
"""

import os
import csv
import datetime
import config


class EventLogger:
    """
    Lightweight logger that writes to both a plain-text session log and a
    structured CSV so event data can be analysed after the session ends.
    """

    def __init__(self):
        self._txt_path = None
        self._csv_path = None

        if not config.SAVE_LOGS:
            return

        os.makedirs(config.LOGS_DIR, exist_ok=True)

        session_id   = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self._txt_path = os.path.join(config.LOGS_DIR, f"session_{session_id}.txt")
        self._csv_path = os.path.join(config.LOGS_DIR, f"events_{session_id}.csv")

        # Write CSV header
        self._write_csv_row(["Timestamp", "EventType", "Details"])

        self.log("Logger initialised — session started", "SYSTEM")

    # ------------------------------------------------------------------ #
    #  PUBLIC API
    # ------------------------------------------------------------------ #

    def log(self, message, event_type="INFO"):
        """
        Log an arbitrary message with a timestamp prefix.

        Parameters
        ----------
        message    : str  — human-readable description
        event_type : str  — tag such as INFO, ALERT, ERROR, SYSTEM
        """
        ts      = datetime.datetime.now()
        ts_str  = ts.strftime('%Y-%m-%d %H:%M:%S')
        line    = f"[{ts_str}] [{event_type:6s}] {message}"

        print(line)

        if self._txt_path:
            with open(self._txt_path, 'a', encoding='utf-8') as f:
                f.write(line + '\n')

    def log_detection(self, num_guns, bboxes=None):
        """
        Log a gun-detection event. Also writes a row to the CSV.

        Parameters
        ----------
        num_guns : int   — number of detections in this frame
        bboxes   : list  — list of (x,y,w,h) bounding boxes (optional)
        """
        details = f"guns={num_guns}"
        if bboxes:
            details += f" | boxes={bboxes}"

        self.log(f"GUN DETECTED — {details}", "ALERT")

        ts_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._write_csv_row([ts_str, "DETECTION", details])

    def log_session_end(self, total_frames, total_detections):
        """Write a summary line at the end of the session."""
        summary = (f"Session ended — frames={total_frames}, "
                   f"detections={total_detections}")
        self.log(summary, "SYSTEM")

        ts_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._write_csv_row([ts_str, "SESSION_END", summary])

    # ------------------------------------------------------------------ #
    #  PRIVATE HELPERS
    # ------------------------------------------------------------------ #

    def _write_csv_row(self, row):
        if not self._csv_path:
            return
        with open(self._csv_path, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(row)
