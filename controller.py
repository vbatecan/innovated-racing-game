import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarkerOptions
import cv2
import threading
import time


class Controller:
    def __init__(self):
        self.latest_result = None
        self.steer = 0.0
        self.breaking = False
        self.running = False
        self.current_frame = None
        self.annotated_frame = None
        self.lock = threading.Lock()

        self.lm = vision.HandLandmarker.create_from_options(
            HandLandmarkerOptions(
                base_options=BaseOptions(
                    model_asset_path="resources/hand_landmarker.task",
                ),
                num_hands=2,
                running_mode=vision.RunningMode.LIVE_STREAM,
                result_callback=self.callback,
                min_hand_detection_confidence=0.1,
                min_hand_presence_confidence=0.1,
                min_tracking_confidence=0.3,
            )
        )

    def start_stream(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        print("Camera thread started.")

    def stop_stream(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
        self.cap.release()
        print("Camera thread stopped.")

    def _update(self):
        start_time = time.time()
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)

            timestamp_ms = int((time.time() - start_time) * 1000)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            self.lm.detect_async(mp_image, timestamp_ms)

            # Draw annotations on the frame immediately
            # Note: detection is async, so latest_result might trail behind slightly.
            annotated = self._draw_annotations_internal(frame)

            with self.lock:
                self.annotated_frame = annotated

            # Optional: tiny sleep to yield if CPU usage is too high,
            # but cap.read() is blocking so it shouldn't spin.

    def callback(self, result, output_image, timestamp_ms):
        self.latest_result = result

    def _draw_annotations_internal(self, image):
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

            # Check for braking (Thumb Up) on EITHER hand
            self.breaking = False
            for hand_landmarks in self.latest_result.hand_landmarks:
                # Thumb Tip (4) < Thumb IP (3) < Thumb MCP (2) (y-coordinate, lower is higher on screen)
                # And basic check that thumb is actually pointing up relative to wrist
                thumb_tip = hand_landmarks[4]
                thumb_ip = hand_landmarks[3]

                # Simple check: Thumb tip is significantly above the IP joint
                if thumb_tip.y < thumb_ip.y - 0.02:
                    self.breaking = True

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
                for landmark in hand_landmarks:
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)
        else:
            self.steer = 0.0
            self.breaking = False

        return image

    def get_frame(self):
        with self.lock:
            if self.annotated_frame is not None:
                return self.annotated_frame.copy()
            return None
