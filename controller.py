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
    Webcam-based hand controller for steering, braking, and shifting.

    This class owns the camera thread, runs MediaPipe hand landmark detection,
    derives control states from gestures, and exposes the latest annotated frame.
    """

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
        self.shift_up_requested = False
        self.shift_down_requested = False
        self.left_shift_active = False
        self.right_shift_active = False
        self._prev_left_shift_active = False
        self._prev_right_shift_active = False
        self.swipe_up_detected = False
        self.swipe_down_detected = False
        self.question_select_requested = False
        self._prev_question_select_active = False
        self._question_select_hold_frames = 0
        self.question_select_required_frames = 3
        self._prev_right_hand_y = None
        self.swipe_threshold = 0.02
        self.require_two_hands = True
        self._last_timestamp_ms = -1

        self.lm = vision.HandLandmarker.create_from_options(
            HandLandmarkerOptions(
                base_options=BaseOptions(
                    model_asset_path="resources/hand_landmarker.task",
                ),
                num_hands=2,
                running_mode=vision.RunningMode.LIVE_STREAM,
                result_callback=self.callback,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        )

    def start_stream(self):
        """
        Start the camera capture and processing thread.

        Opens the default camera device, configures its resolution, and launches
        the background update loop that performs hand detection.
        """
        if self.thread is not None and self.thread.is_alive():
            logger.info("Camera thread already running.")
            return

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            logger.error("Failed to open camera device.")
            self.running = False
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_X_SIZE)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_Y_SIZE)
        self._reset_controls()
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
        self.running = False
        if self.thread is not None and self.thread.is_alive():
            self.thread.join()
        self.thread = None

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        with self.lock:
            self.current_frame = None
            self.annotated_frame = None
        self.latest_result = None
        self._reset_controls()
        logger.info("Camera thread stopped.")

    def restart_stream(self) -> None:
        """Restart camera capture and gesture processing state."""
        self.stop_stream()
        self.start_stream()

    def _update(self):
        """
        Capture frames and run asynchronous hand detection.

        Reads frames from the camera, flips them for a mirror view, and submits
        them to MediaPipe. The latest annotated frame is stored for rendering.
        """
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to read frame from camera.")
                continue

            frame = cv2.flip(frame, 1)

            # LIVE_STREAM mode requires timestamps to be monotonic across the
            # lifetime of the detector, including restarts.
            timestamp_ms = int(time.monotonic_ns() / 1_000_000)
            if timestamp_ms <= self._last_timestamp_ms:
                timestamp_ms = self._last_timestamp_ms + 1
            self._last_timestamp_ms = timestamp_ms

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            try:
                self.lm.detect_async(mp_image, timestamp_ms)
            except ValueError as e:
                logger.warning(f"MediaPipe detect_async error with timestamp {timestamp_ms}: {e}")

            annotated = self._draw_annotations_internal(frame)

            with self.lock:
                self.annotated_frame = annotated

    def callback(self, result, output_image, timestamp_ms):
        """
        Receive hand tracking results from MediaPipe.

        Stores the latest result for use by the annotation routine.
        """
        self.latest_result = result

    def set_require_two_hands(self, required: bool) -> None:
        """Set whether the controller should require two hands for processing."""
        self.require_two_hands = bool(required)

    def _reset_controls(self) -> None:
        """
        Reset all derived control outputs to neutral defaults.

        This is used when two valid hands are not available, so gameplay logic
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
        self.swipe_up_detected = False
        self.swipe_down_detected = False
        self.question_select_requested = False
        self._prev_question_select_active = False
        self._question_select_hold_frames = 0
        self._prev_right_hand_y = None

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
    def _is_wacky_gesture(hand_landmarks) -> bool:
        """Detect wacky gesture: index and middle fingers extended."""
        index_tip = hand_landmarks[8]
        index_pip = hand_landmarks[6]
        index_mcp = hand_landmarks[5]
        middle_tip = hand_landmarks[12]
        middle_pip = hand_landmarks[10]
        middle_mcp = hand_landmarks[9]

        index_extended = index_tip.y < index_pip.y < index_mcp.y
        middle_extended = middle_tip.y < middle_pip.y < middle_mcp.y

        ring_tip = hand_landmarks[16]
        ring_pip = hand_landmarks[14]
        pinky_tip = hand_landmarks[20]
        pinky_pip = hand_landmarks[18]
        ring_curled = ring_tip.y > ring_pip.y
        pinky_curled = pinky_tip.y > pinky_pip.y

        return index_extended and middle_extended and ring_curled and pinky_curled

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
            for a, b in config.HAND_CONNECTIONS:
                la = hand_landmarks[a]
                lb = hand_landmarks[b]
                ax, ay = int(la.x * w), int(la.y * h)
                bx, by = int(lb.x * w), int(lb.y * h)
                cv2.line(image, (ax, ay), (bx, by), (0, 255, 0), 2)
            for landmark in hand_landmarks:
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)

    def _detect_swipes(self, right_hand) -> None:
        """
        Detect swipe up/down gestures from right hand vertical movement.
        
        Compares current hand position to previous position. If hand moved up/down
        beyond the swipe threshold, trigger the appropriate gesture.
        """
        right_palm = right_hand[0]
        current_y = right_palm.y
        
        self.swipe_up_detected = False
        self.swipe_down_detected = False
        
        if self._prev_right_hand_y is not None:
            delta_y = self._prev_right_hand_y - current_y
            if delta_y > self.swipe_threshold:
                self.swipe_up_detected = True
            elif delta_y < -self.swipe_threshold:
                self.swipe_down_detected = True
        
        self._prev_right_hand_y = current_y

    def _process_two_hands(self, image) -> None:
        """
        Derive control states from two valid detected hands and annotate frame.
        """
        left_hand, right_hand = self._resolve_left_right_hands()
        left_wrist = left_hand[0]
        right_wrist = right_hand[0]

        self.breaking = not self.left_shift_active and not self.right_shift_active
        self._update_shift_state(left_hand, right_hand)
        self._detect_swipes(right_hand)

        normalized_slope = self._compute_steer(left_wrist, right_wrist)
        self.steer = 0.0 if self.breaking else normalized_slope

        self._draw_status_overlays(image, normalized_slope)
        self._draw_hand_graphics(image, left_wrist, right_wrist)

    def _process_question_hands(self, image) -> None:
        """Process gestures for question mode where one hand is sufficient."""
        hands = self.latest_result.hand_landmarks
        if not hands:
            self.swipe_up_detected = False
            self.swipe_down_detected = False
            self.question_select_requested = False
            self._prev_question_select_active = False
            self._question_select_hold_frames = 0
            self._prev_right_hand_y = None
            return

        primary_hand = hands[0]
        self._detect_swipes(primary_hand)
        wacky_gesture_active = any(self._is_wacky_gesture(hand) for hand in hands)

        if wacky_gesture_active:
            self._question_select_hold_frames += 1
        else:
            self._question_select_hold_frames = 0

        select_active = (
            self._question_select_hold_frames >= self.question_select_required_frames
        )
        self.question_select_requested = (
            select_active and not self._prev_question_select_active
        )
        self._prev_question_select_active = select_active

        self.steer = 0.0
        self.breaking = False
        self.shift_up_requested = False
        self.shift_down_requested = False
        self.left_shift_active = False
        self.right_shift_active = False

        h, w, _ = image.shape
        for hand_landmarks in hands:
            for a, b in config.HAND_CONNECTIONS:
                la = hand_landmarks[a]
                lb = hand_landmarks[b]
                ax, ay = int(la.x * w), int(la.y * h)
                bx, by = int(lb.x * w), int(lb.y * h)
                cv2.line(image, (ax, ay), (bx, by), (0, 255, 0), 2)
            for landmark in hand_landmarks:
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)

    def _draw_annotations_internal(self, image):
        """
        Process the latest detection result and return an annotated frame.

        Enforces the two-hand requirement, updates control state from gestures,
        and draws overlays used by the in-game camera preview.
        """
        if not (self.latest_result and self.latest_result.hand_landmarks):
            self._reset_controls()
            return image

        hand_count = len(self.latest_result.hand_landmarks)
        if self.require_two_hands and hand_count != 2:
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

        if self.require_two_hands:
            self._process_two_hands(image)
        else:
            self._process_question_hands(image)

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

    def consume_swipe_request(self) -> tuple[bool, bool]:
        """
        Return and clear edge-triggered swipe requests.

        Returns:
            tuple[bool, bool]: (swipe_up_detected, swipe_down_detected)
        """
        up = self.swipe_up_detected
        down = self.swipe_down_detected
        self.swipe_up_detected = False
        self.swipe_down_detected = False
        return up, down

    def consume_question_select_request(self) -> bool:
        """Return and clear edge-triggered question selection gesture."""
        requested = self.question_select_requested
        self.question_select_requested = False
        return requested

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
