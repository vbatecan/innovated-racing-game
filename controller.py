import logging
import os
import threading
import time
from threading import Thread

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarkerOptions

import config

os.makedirs("logs", exist_ok=True)
logger = logging.getLogger(__name__)


class Controller:
    def __init__(self):
        """
        Initialize camera control and hand tracking state.

        Sets defaults for steering/braking, creates the MediaPipe hand landmarker,
        and prepares synchronization primitives for the capture thread.
        """
        self.cap: cv2.VideoCapture | None = None
        self.running = False
        self.latest_result = None
        self.steer = 0.0
        self.breaking = False
        self.brake_threshold = 0.02
        self.current_frame = None
        self.annotated_frame = None
        self.lock = threading.Lock()
        self.thread: Thread | None = None
        self.boosting = False  # Ensure boosting attribute always exists

        self.lm = vision.HandLandmarker.create_from_options(
            HandLandmarkerOptions(
                base_options=BaseOptions(
                    model_asset_path="resources/hand_landmarker.task",
                ),
                num_hands=2,
                running_mode=vision.RunningMode.LIVE_STREAM,
                result_callback=self.callback,
                min_hand_detection_confidence=0.4,
                min_hand_presence_confidence=0.4,
                min_tracking_confidence=0.4,
            )
        )

    def start_stream(self):
        """
        Start the camera capture and processing thread.

        Opens the default camera device, configures its resolution, and launches
        the background update loop that performs hand detection.
        """
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_X_SIZE)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_Y_SIZE)
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        logger.info("Camera thread started.")

    def stop_stream(self):
        """
        Stop the camera capture and clean up resources.

        Signals the update loop to exit, joins the thread, and releases the
        camera handle if it is open.
        """
        if self.thread is None or not self.thread.is_alive():
            return
        self.running = False
        if self.thread.is_alive():
            self.thread.join()

        if self.cap is not None:
            self.cap.release()
        logger.info("Camera thread stopped.")

    def _update(self):
        """
        Capture frames and run asynchronous hand detection.

        Reads frames from the camera, flips them for a mirror view, and submits
        them to MediaPipe. The latest annotated frame is stored for rendering.
        """
        start_time = time.time()
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to read frame from camera.")
                continue

            frame = cv2.flip(frame, 1)

            timestamp_ms = int((time.time() - start_time) * 1000)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            self.lm.detect_async(mp_image, timestamp_ms)

            annotated = self._draw_annotations_internal(frame)

            with self.lock:
                self.annotated_frame = annotated

    def callback(self, result, output_image, timestamp_ms):
        """
        Receive hand tracking results from MediaPipe.

        Stores the latest result for use by the annotation routine.
        """
        self.latest_result = result

    def _draw_annotations_internal(self, image):
        """
        Annotate a frame and compute steering/braking state.

        Draws hand landmarks and a steering line when two hands are detected,
        updates the current steer value, and overlays status text.
        """
        # Standard MediaPipe hand landmark connections (21 landmarks).
        # Index mapping: 0 wrist; thumb 1-4; index 5-8; middle 9-12; ring 13-16; pinky 17-20.
        connections = (
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),
            (0, 5),
            (5, 6),
            (6, 7),
            (7, 8),
            (0, 9),
            (9, 10),
            (10, 11),
            (11, 12),
            (0, 13),
            (13, 14),
            (14, 15),
            (15, 16),
            (0, 17),
            (17, 18),
            (18, 19),
            (19, 20),
            (5, 9),
            (9, 13),
            (13, 17),
        )

        if self.latest_result and self.latest_result.hand_landmarks:
            if len(self.latest_result.hand_landmarks) != 2:
                cv2.putText(
                    image,
                    "Must be 2 hands",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )
                self.steer = 0.0
                self.breaking = False
                return image

            left_hand_wrist = self.latest_result.hand_landmarks[0][0]
            right_hand_wrist = self.latest_result.hand_landmarks[1][0]

            # Reliable braking: Open Palms gesture
            def landmark_point(landmark):
                return landmark.x, landmark.y

            def is_palm_open(hand_landmarks):
                wrist = hand_landmarks[0]
                tip_indices = [8, 12, 16, 20]
                pip_indices = [6, 10, 14, 18]
                wrist_x, wrist_y = landmark_point(wrist)
                extended = 0
                for tip_i, pip_i in zip(tip_indices, pip_indices):
                    tip = hand_landmarks[tip_i]
                    pip = hand_landmarks[pip_i]
                    tip_dist_sq = (tip.x - wrist_x) ** 2 + (tip.y - wrist_y) ** 2
                    pip_dist_sq = (pip.x - wrist_x) ** 2 + (pip.y - wrist_y) ** 2
                    if tip_dist_sq > pip_dist_sq * 1.05:
                        extended += 1
                return extended >= 3


            left_hand = self.latest_result.hand_landmarks[0]
            right_hand = self.latest_result.hand_landmarks[1]
            left_open = is_palm_open(left_hand)
            right_open = is_palm_open(right_hand)
            self.breaking = left_open or right_open

            # --- Thumbs Up Detection ---
            def is_thumb_up(hand_landmarks):
                # Thumb tip (4) above MCP (2) and other fingers curled
                thumb_tip = hand_landmarks[4]
                thumb_mcp = hand_landmarks[2]
                # Y axis: top is smaller value
                thumb_up = thumb_tip.y < thumb_mcp.y
                # Other fingers curled: tip below pip
                curled = 0
                for tip_i, pip_i in zip([8, 12, 16, 20], [6, 10, 14, 18]):
                    if hand_landmarks[tip_i].y > hand_landmarks[pip_i].y:
                        curled += 1
                return thumb_up and curled >= 3

            left_thumb = is_thumb_up(left_hand)
            # Only left thumb up triggers boost
            self.boosting = left_thumb

            brake_color = (0, 0, 255) if self.breaking else (0, 255, 0)
            status_text = "BRAKING!" if self.breaking else "THROTTLE ON"
            cv2.putText(
                image,
                status_text,
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                brake_color,
                2,
            )

            slope = (right_hand_wrist.y - left_hand_wrist.y) / (
                right_hand_wrist.x - left_hand_wrist.x + 1e-6
            )

            normalized_slope = max(-5.0, min(5.0, slope))
            # Prevent steering while braking
            if self.breaking:
                self.steer = 0.0
            else:
                self.steer = normalized_slope

            cv2.putText(
                image,
                f"Steer: {normalized_slope:.2f}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 0),
                2,
            )

            h, w, _ = image.shape
            cv2.line(
                image,
                (int(left_hand_wrist.x * w), int(left_hand_wrist.y * h)),
                (int(right_hand_wrist.x * w), int(right_hand_wrist.y * h)),
                (0, 255, 0),
                2,
            )

            for hand_landmarks in self.latest_result.hand_landmarks:
                # Draw skeleton (connections) first, then landmark points.
                for a, b in connections:
                    la = hand_landmarks[a]
                    lb = hand_landmarks[b]
                    ax, ay = int(la.x * w), int(la.y * h)
                    bx, by = int(lb.x * w), int(lb.y * h)
                    cv2.line(image, (ax, ay), (bx, by), (0, 255, 0), 2)
                for landmark in hand_landmarks:
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)
        else:
            self.steer = 0.0
            self.breaking = False

        return image

    def get_frame(self):
        """
        Return the most recent annotated frame.

        Provides a copy of the latest frame to avoid threading issues. Returns
        None if no frame is available yet.
        """
        with self.lock:
            if self.annotated_frame is not None:
                return self.annotated_frame.copy()
            return None
