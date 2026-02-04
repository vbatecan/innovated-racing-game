import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarkerOptions
import cv2


class Controller:
    def __init__(self):
        self.latest_result = None

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
        self.steer = 0.0

    # This runs in a separate thread!
    def callback(self, result, output_image, timestamp_ms):
        # Just store the result. Don't draw here.
        self.latest_result = result

    def detect(self, frame, timestamp_ms):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        self.lm.detect_async(mp_image, timestamp_ms)

    def draw_annotations(self, image):
        # Check if we have results to draw
        if self.latest_result and self.latest_result.hand_landmarks:
            # Must be two hands
            if len(self.latest_result.hand_landmarks) != 2:
                cv2.putText(
                    image,
                    "Must be 2 hands detected",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )
                return image

            # Magddraw tayo ng line between the left hand wrist and right hand wrist and
            # we will use that to measure yung steering [-1.0 < 0 < 1.0]
            left_hand_wrist = self.latest_result.hand_landmarks[0][0]
            right_hand_wrist = self.latest_result.hand_landmarks[1][0]

            # Gamitin natin yung slope formula
            slope = (right_hand_wrist.y - left_hand_wrist.y) / (
                right_hand_wrist.x - left_hand_wrist.x
            )

            # Normalize the slope to be between -5.0 and 5.0
            normalized_slope = max(-5.0, min(5.0, slope))
            cv2.putText(
                image,
                f"Steering: {normalized_slope:.2f}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 0),
                2,
            )

            cv2.line(
                image,
                (
                    int(left_hand_wrist.x * image.shape[1]),
                    int(left_hand_wrist.y * image.shape[0]),
                ),
                (
                    int(right_hand_wrist.x * image.shape[1]),
                    int(right_hand_wrist.y * image.shape[0]),
                ),
                (0, 255, 0),
                2,
            )

            for hand_landmarks in self.latest_result.hand_landmarks:
                h, w, _ = image.shape
                for landmark in hand_landmarks:
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)
            self.steer = normalized_slope

        return image
