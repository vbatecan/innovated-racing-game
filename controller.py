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
    """
    Webcam-based hand controller for steering, braking, boost, and shifting.

    This class owns the camera thread, runs MediaPipe hand landmark detection,
    derives control states from gestures, and exposes the latest annotated frame.
    """

    HAND_CONNECTIONS = (
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
        self.shift_up_requested = False
        self.shift_down_requested = False
        self.left_shift_active = False
        self.right_shift_active = False
        self._prev_left_shift_active = False
        self._prev_right_shift_active = False

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

    def _reset_controls(self) -> None:
        """
        Reset all derived control outputs to neutral defaults.

        This is used when two valid hands are not available so gameplay logic
        does not keep stale steering/gesture states.
        """
        self.steer = 0.0
        self.breaking = False
        self.shift_up_requested = False
        self.shift_down_requested = False
        self.left_shift_active = False
        self.right_shift_active = False
        self._prev_left_shift_active = False
        self._prev_right_shift_active = False

    def _resolve_left_right_hands(self):
        """
        Return landmarks ordered as `(left_hand, right_hand)`.

        Uses MediaPipe handedness labels when present; otherwise falls back to
        detector order.
        """
        hand_landmarks = self.latest_result.hand_landmarks
        handedness = getattr(self.latest_result, "handedness", None)
        left_idx = 0
        right_idx = 1
        if handedness and len(handedness) >= 2:
            for i, hand_class in enumerate(handedness):
                if not hand_class:
                    continue
                side = hand_class[0].category_name.lower()
                if side == "left":
                    left_idx = i
                elif side == "right":
                    right_idx = i
        return hand_landmarks[left_idx], hand_landmarks[right_idx]

    @staticmethod
    def _landmark_point(landmark) -> tuple[float, float]:
        """
        Convert a landmark object to `(x, y)` normalized coordinates.
        """
        return landmark.x, landmark.y

    def _is_palm_open(self, hand_landmarks) -> bool:
        """
        Detect an open-palm braking gesture.

        A palm is considered open if at least three finger tips are noticeably
        farther from the wrist than their corresponding PIP joints.
        """
        wrist = hand_landmarks[0]
        tip_indices = [8, 12, 16, 20]
        pip_indices = [6, 10, 14, 18]
        wrist_x, wrist_y = self._landmark_point(wrist)
        extended = 0
        for tip_i, pip_i in zip(tip_indices, pip_indices):
            tip = hand_landmarks[tip_i]
            pip = hand_landmarks[pip_i]
            tip_dist_sq = (tip.x - wrist_x) ** 2 + (tip.y - wrist_y) ** 2
            pip_dist_sq = (pip.x - wrist_x) ** 2 + (pip.y - wrist_y) ** 2
            if tip_dist_sq > pip_dist_sq * 1.05:
                extended += 1
        return extended >= 3

    @staticmethod
    def _is_index_only(hand_landmarks) -> bool:
        """
        Detect a "pointer finger" gesture for L1/R1 style shifting.

        The index finger must be extended while most other fingers stay curled.
        """
        index_tip = hand_landmarks[8]
        index_pip = hand_landmarks[6]
        index_mcp = hand_landmarks[5]
        index_extended = index_tip.y < index_pip.y and index_pip.y < index_mcp.y
        curled_count = 0
        for tip_i, pip_i in zip([12, 16, 20], [10, 14, 18]):
            if hand_landmarks[tip_i].y > hand_landmarks[pip_i].y:
                curled_count += 1
        return index_extended and curled_count >= 2

    @staticmethod
    def _is_thumb_up(hand_landmarks) -> bool:
        """
        Detect a thumbs-up gesture used to trigger boost.
        """
        thumb_tip = hand_landmarks[4]
        thumb_mcp = hand_landmarks[2]
        thumb_up = thumb_tip.y < thumb_mcp.y
        curled = 0
        for tip_i, pip_i in zip([8, 12, 16, 20], [6, 10, 14, 18]):
            if hand_landmarks[tip_i].y > hand_landmarks[pip_i].y:
                curled += 1
        return thumb_up and curled >= 3

    def _update_shift_state(self, left_hand, right_hand) -> None:
        """
        Update sustained shift poses and one-shot shift requests.

        Active poses (`left_shift_active`, `right_shift_active`) are continuous.
        Requests are rising-edge pulses consumed by the game loop.
        """
        self.left_shift_active = self._is_index_only(left_hand)
        self.right_shift_active = self._is_index_only(right_hand)
        self.shift_down_requested = (
            self.left_shift_active and not self._prev_left_shift_active
        )
        self.shift_up_requested = (
            self.right_shift_active and not self._prev_right_shift_active
        )
        self._prev_left_shift_active = self.left_shift_active
        self._prev_right_shift_active = self.right_shift_active

    @staticmethod
    def _compute_steer(left_wrist, right_wrist) -> float:
        """
        Compute clamped steering slope from wrist alignment.
        """
        slope = (right_wrist.y - left_wrist.y) / (right_wrist.x - left_wrist.x + 1e-6)
        return max(-5.0, min(5.0, slope))

    def _draw_status_overlays(self, image, normalized_slope: float) -> None:
        """
        Draw textual overlays for steer, throttle/brake, and shift feedback.
        """
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

        shift_status = "SHIFT L1-/R1+"
        if self.shift_down_requested and self.shift_up_requested:
            shift_status = "SHIFT: DOWN+UP"
        elif self.shift_down_requested:
            shift_status = "SHIFT: DOWN"
        elif self.shift_up_requested:
            shift_status = "SHIFT: UP"
        cv2.putText(
            image,
            shift_status,
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (180, 220, 255),
            2,
        )

        cv2.putText(
            image,
            f"Steer: {normalized_slope:.2f}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 0),
            2,
        )

    def _draw_hand_graphics(self, image, left_wrist, right_wrist) -> None:
        """
        Draw wrist connector plus full hand skeleton/landmark points.
        """
        h, w, _ = image.shape
        cv2.line(
            image,
            (int(left_wrist.x * w), int(left_wrist.y * h)),
            (int(right_wrist.x * w), int(right_wrist.y * h)),
            (0, 255, 0),
            2,
        )
        for hand_landmarks in self.latest_result.hand_landmarks:
            for a, b in self.HAND_CONNECTIONS:
                la = hand_landmarks[a]
                lb = hand_landmarks[b]
                ax, ay = int(la.x * w), int(la.y * h)
                bx, by = int(lb.x * w), int(lb.y * h)
                cv2.line(image, (ax, ay), (bx, by), (0, 255, 0), 2)
            for landmark in hand_landmarks:
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)

    def _process_two_hands(self, image) -> None:
        """
        Derive control states from two valid detected hands and annotate frame.
        """
        left_hand, right_hand = self._resolve_left_right_hands()
        left_wrist = left_hand[0]
        right_wrist = right_hand[0]

        self.breaking = self._is_palm_open(left_hand) or self._is_palm_open(right_hand)
        self._update_shift_state(left_hand, right_hand)
        self.boosting = self._is_thumb_up(left_hand)  # Left hand only for boost.

        normalized_slope = self._compute_steer(left_wrist, right_wrist)
        self.steer = 0.0 if self.breaking else normalized_slope

        self._draw_status_overlays(image, normalized_slope)
        self._draw_hand_graphics(image, left_wrist, right_wrist)

    def _draw_annotations_internal(self, image):
        """
        Process the latest detection result and return an annotated frame.

        Enforces the two-hand requirement, updates control state from gestures,
        and draws overlays used by the in-game camera preview.
        """
        if not (self.latest_result and self.latest_result.hand_landmarks):
            self._reset_controls()
            return image

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
            self._reset_controls()
            return image

        self._process_two_hands(image)

        return image

    def consume_shift_request(self) -> tuple[bool, bool]:
        """
        Return and clear edge-triggered shift requests.

        Returns:
            tuple[bool, bool]: (downshift_requested, upshift_requested)
        """
        down = self.shift_down_requested
        up = self.shift_up_requested
        self.shift_down_requested = False
        self.shift_up_requested = False
        return down, up

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
