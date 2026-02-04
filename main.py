import time
import cv2
import logging
from controller import Controller

logging.basicConfig(level=logging.DEBUG)


def main():
    detector = Controller()
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    start_time = time.time()

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        frame_timestamp_ms = int((time.time() - start_time) * 1000)

        detector.detect(frame, frame_timestamp_ms)
        frame = detector.draw_annotations(frame)

        cv2.imshow("frame", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
