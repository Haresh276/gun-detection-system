"""
motion_detector.py — Background-Subtraction Motion Detection
=============================================================
Uses OpenCV's MOG2 (Mixture of Gaussians v2) algorithm to build a
statistical model of the background and flag moving foreground objects.

Why not simple frame-differencing?
-----------------------------------
Simple frame-diff (|frame_A - frame_B|) misses slow-moving objects and
creates double-edges. MOG2 maintains a per-pixel Gaussian mixture model
that adapts over time, handles illumination changes, and marks shadows
separately so we can ignore them.
"""

import cv2
import numpy as np
import config


class MotionDetector:
    """
    Wraps MOG2 background subtraction with morphological post-processing
    to produce clean, meaningful motion bounding boxes.
    """

    def __init__(self):
        # MOG2 params:
        #   history     – how many past frames contribute to the background model
        #   varThreshold – Mahalanobis distance threshold (higher → less sensitive)
        #   detectShadows – mark shadows as gray (127) instead of white (255)
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=50,
            detectShadows=True
        )

        # Structuring element for morphological cleanup
        self._kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        self.motion_detected = False

    # ------------------------------------------------------------------ #
    #  UPDATE — call once per frame
    # ------------------------------------------------------------------ #

    def update(self, gray_frame):
        """
        Feed a new grayscale frame into the background model and detect motion.

        Pipeline
        --------
        1. Apply MOG2  →  raw foreground mask (0/127/255)
        2. Threshold   →  remove shadow pixels (127), keep foreground (255)
        3. Morphological OPEN  →  erase small noise blobs
        4. Dilate      →  connect nearby blobs into one region
        5. findContours →  get outlines of moving regions
        6. Filter small contours below MOTION_THRESHOLD

        Returns
        -------
        motion_detected : bool
        contours        : list of numpy contour arrays
        bounding_boxes  : list of (x, y, w, h) tuples
        """
        # Step 1 – raw mask
        fg_mask = self.bg_subtractor.apply(gray_frame)

        # Step 2 – remove shadows (shadow pixels = 127)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # Step 3 – morphological OPEN removes tiny noise specs
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self._kernel)

        # Step 4 – dilate to merge nearby motion regions
        fg_mask = cv2.dilate(fg_mask, self._kernel, iterations=2)

        # Step 5 – find contours of moving blobs
        contours, _ = cv2.findContours(
            fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Step 6 – drop tiny contours (dust, camera noise)
        significant = [c for c in contours
                       if cv2.contourArea(c) > config.MOTION_THRESHOLD]

        self.motion_detected = len(significant) > 0
        bounding_boxes = [cv2.boundingRect(c) for c in significant]

        return self.motion_detected, significant, bounding_boxes

    # ------------------------------------------------------------------ #
    #  VISUALISATION
    # ------------------------------------------------------------------ #

    def draw_motion(self, frame, bounding_boxes):
        """
        Draw thin green boxes around each motion region.
        These are intentionally lighter than the gun-detection boxes
        so they don't clutter the view.
        """
        for (x, y, w, h) in bounding_boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 220, 0), 1)

        if bounding_boxes:
            cv2.putText(frame, "Motion", (bounding_boxes[0][0],
                        bounding_boxes[0][1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 0), 1)

        return frame
