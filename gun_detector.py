"""
gun_detector.py — Haar Cascade Gun Detection Module
====================================================
Wraps OpenCV's CascadeClassifier with a clean class interface.
Adds bounding-box drawing and Region-of-Interest extraction.
"""

import cv2
import config


class GunDetector:
    """
    Detects guns in a grayscale frame using a pre-trained Haar Cascade.

    How it works
    ------------
    A Haar Cascade is a sliding-window classifier trained with thousands of
    positive (gun) and negative (non-gun) images. At each window position the
    classifier votes YES/NO through a series of 'stages'. Only windows that
    pass ALL stages are kept as detections.

    detectMultiScale scans the image at multiple scales (controlled by
    scaleFactor) so the detector catches guns that appear at different sizes.
    minNeighbors filters out false positives: a rectangle is only kept if at
    least that many nearby rectangles also fired.
    """

    def __init__(self):
        self.cascade = cv2.CascadeClassifier(config.CASCADE_PATH)
        if self.cascade.empty():
            raise FileNotFoundError(
                f"Cascade file not found or invalid: '{config.CASCADE_PATH}'\n"
                "Make sure cascade.xml is in the project root folder."
            )
        self.total_detections = 0    # Cumulative counter across all frames

    # ------------------------------------------------------------------ #
    #  CORE DETECTION
    # ------------------------------------------------------------------ #

    def detect(self, gray_frame):
        """
        Run the cascade classifier on a grayscale frame.

        Parameters
        ----------
        gray_frame : np.ndarray
            Single-channel (grayscale) image, already blurred to reduce noise.

        Returns
        -------
        list of (x, y, w, h) tuples, empty list if nothing found.
        """
        detections = self.cascade.detectMultiScale(
            gray_frame,
            scaleFactor  = config.SCALE_FACTOR,
            minNeighbors = config.MIN_NEIGHBORS,
            minSize      = config.MIN_SIZE
        )

        # detectMultiScale returns a numpy array or an empty tuple
        if len(detections) > 0:
            self.total_detections += 1
            return list(detections)

        return []

    # ------------------------------------------------------------------ #
    #  VISUALISATION
    # ------------------------------------------------------------------ #

    def draw_detections(self, frame, detections, color=(0, 0, 255)):
        """
        Draw bounding boxes and labels on the BGR frame for every detection.

        Parameters
        ----------
        frame      : np.ndarray  — BGR colour frame
        detections : list        — output of detect()
        color      : BGR tuple   — box colour (default red)

        Returns
        -------
        Annotated frame (modifies in-place and also returns it).
        """
        for (x, y, w, h) in detections:
            # --- Bounding rectangle ---
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)

            # --- Label background pill ---
            label      = "GUN DETECTED"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x, y - lh - 12), (x + lw + 8, y), color, -1)
            cv2.putText(frame, label, (x + 4, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # --- Corner accents (decorative — common in security UIs) ---
            thickness = 3
            length    = 20
            # Top-left
            cv2.line(frame, (x, y), (x + length, y), (255, 255, 255), thickness)
            cv2.line(frame, (x, y), (x, y + length), (255, 255, 255), thickness)
            # Top-right
            cv2.line(frame, (x + w, y), (x + w - length, y), (255, 255, 255), thickness)
            cv2.line(frame, (x + w, y), (x + w, y + length), (255, 255, 255), thickness)
            # Bottom-left
            cv2.line(frame, (x, y + h), (x + length, y + h), (255, 255, 255), thickness)
            cv2.line(frame, (x, y + h), (x, y + h - length), (255, 255, 255), thickness)
            # Bottom-right
            cv2.line(frame, (x + w, y + h), (x + w - length, y + h), (255, 255, 255), thickness)
            cv2.line(frame, (x + w, y + h), (x + w, y + h - length), (255, 255, 255), thickness)

        return frame

    # ------------------------------------------------------------------ #
    #  ROI EXTRACTION
    # ------------------------------------------------------------------ #

    def get_rois(self, frame, gray_frame, detections):
        """
        Extract the Region of Interest (the area inside each bounding box).

        Useful if you want to pass the cropped gun region to a second
        classifier for confirmation (e.g., a deep-learning model).

        Returns list of dicts with 'color', 'gray', and 'bbox' keys.
        """
        rois = []
        for (x, y, w, h) in detections:
            rois.append({
                "color" : frame[y:y+h, x:x+w],
                "gray"  : gray_frame[y:y+h, x:x+w],
                "bbox"  : (x, y, w, h),
            })
        return rois
