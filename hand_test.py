import cv2
import mediapipe as mp

# Load MediaPipe Hand Landmarker
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="models/hand_landmarker.task"
    ),
    running_mode=RunningMode.VIDEO,
    num_hands=2
)

detector = HandLandmarker.create_from_options(options)

# Open laptop camera
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Camera could not be opened!")
    detector.close()
    exit()

connections = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

frame_timestamp = 0

print("Hand detection started! Press Q to quit.")

while True:
    success, frame = camera.read()

    if not success:
        print("Could not read camera frame.")
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    result = detector.detect_for_video(
        mp_image,
        frame_timestamp
    )

    frame_timestamp += 33

    if result.hand_landmarks:
        for hand_landmarks in result.hand_landmarks:

            points = []

            for landmark in hand_landmarks:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                points.append((x, y))

                cv2.circle(
                    frame, (x, y), 5,
                    (0, 255, 0), -1
                )

            for start, end in connections:
                cv2.line(
                    frame,
                    points[start],
                    points[end],
                    (255, 0, 0),
                    2
                )

        cv2.putText(
            frame,
            "HAND DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    else:
        cv2.putText(
            frame,
            "Show your hand to camera",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    cv2.imshow("SignBridge - AI Hand Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
detector.close()
cv2.destroyAllWindows()