import cv2
import mediapipe as mp
import csv
import math
from pathlib import Path

# ==========================================
# SIGNBRIDGE - DYNAMIC GESTURE COLLECTION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_DIR = BASE_DIR / "dataset"
TASK_FILE = BASE_DIR / "models" / "hand_landmarker.task"
CSV_FILE = DATASET_DIR / "dynamic_gestures.csv"

DATASET_DIR.mkdir(exist_ok=True)

# ==========================================
# COLLECTION SETTINGS
# ==========================================

SEQUENCE_LENGTH = 30
FRAME_INTERVAL = 2

FEATURES_PER_FRAME = 65
TOTAL_FEATURES = SEQUENCE_LENGTH * FEATURES_PER_FRAME

# ==========================================
# DYNAMIC GESTURE LABELS
# ==========================================

labels = {
    ord("1"): "WATER",
    ord("2"): "FOOD",
    ord("3"): "DRINK",
    ord("4"): "TOILET",
    ord("5"): "HUNGRY",
    ord("6"): "THIRSTY",
    ord("7"): "PAIN",
    ord("8"): "DOCTOR",
    ord("9"): "HOME",
    ord("a"): "WHERE",
    ord("b"): "WHAT",
    ord("c"): "GOODBYE"
}

# ==========================================
# CSV HEADERS
# ==========================================

headers = (
    ["label"] +
    [f"f{i}" for i in range(TOTAL_FEATURES)]
)

# ==========================================
# CHECK REQUIRED MODEL FILE
# ==========================================

if not TASK_FILE.exists():
    raise FileNotFoundError(
        f"Hand landmarker not found: {TASK_FILE}"
    )

# ==========================================
# CREATE OR VALIDATE DATASET
# ==========================================

if not CSV_FILE.exists():

    with open(CSV_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

else:

    with open(CSV_FILE, "r", newline="") as file:
        existing_headers = next(csv.reader(file), [])

    if existing_headers != headers:
        raise ValueError(
            "Dynamic dataset format mismatch. "
            "Do not overwrite the existing dataset."
        )

# ==========================================
# MEDIAPIPE SETUP
# ==========================================

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=str(TASK_FILE)
    ),
    running_mode=RunningMode.VIDEO,
    num_hands=1
)

detector = HandLandmarker.create_from_options(options)

# ==========================================
# FEATURE EXTRACTION
# ==========================================

def extract_features(hand):

    wrist = hand[0]

    scale = max(
        math.sqrt(
            (point.x - wrist.x) ** 2 +
            (point.y - wrist.y) ** 2
        )
        for point in hand
    )

    if scale <= 0:
        return None

    features = []

    # Normalised hand landmarks
    for point in hand:

        features.extend([
            (point.x - wrist.x) / scale,
            (point.y - wrist.y) / scale,
            (point.z - wrist.z) / scale
        ])

    # Preserve wrist screen position for movement tracking
    return [wrist.x, wrist.y] + features

# ==========================================
# CAMERA SETUP
# ==========================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():

    detector.close()

    raise RuntimeError(
        "Camera could not be opened. "
        "Close other camera applications and try again."
    )

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# ==========================================
# COLLECTION VARIABLES
# ==========================================

selected_label = None

sequence = []

frame_number = 0
timestamp = 0

# ==========================================
# START MESSAGE
# ==========================================

print("\n====================================")
print("SIGNBRIDGE DYNAMIC DATA COLLECTION")
print("====================================")

for key, name in labels.items():
    print(f"Press {chr(key)} = {name}")

print("------------------------------------")
print("Press 0 = Cancel current sequence")
print("Press Q = Quit")
print("------------------------------------")

print("Dataset:", CSV_FILE)

# ==========================================
# MAIN COLLECTION LOOP
# ==========================================

try:

    with open(CSV_FILE, "a", newline="") as file:

        writer = csv.writer(file)

        while True:

            success, frame = camera.read()

            if not success:

                print("Unable to read camera frame.")
                break

            # Mirror camera
            frame = cv2.flip(frame, 1)

            # Convert BGR to RGB
            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb
            )

            # Detect hand
            result = detector.detect_for_video(
                mp_image,
                timestamp
            )

            timestamp += 33
            frame_number += 1

            hand_detected = False

            # ==================================
            # HAND DETECTION
            # ==================================

            if result.hand_landmarks:

                hand_detected = True
                hand = result.hand_landmarks[0]

                # Draw hand landmarks
                points = [
                    (
                        int(point.x * frame.shape[1]),
                        int(point.y * frame.shape[0])
                    )
                    for point in hand
                ]

                connections = [
                    (0, 1), (1, 2), (2, 3), (3, 4),
                    (0, 5), (5, 6), (6, 7), (7, 8),
                    (5, 9), (9, 10), (10, 11), (11, 12),
                    (9, 13), (13, 14), (14, 15), (15, 16),
                    (13, 17), (17, 18), (18, 19), (19, 20),
                    (0, 17)
                ]

                for start, end in connections:

                    cv2.line(
                        frame,
                        points[start],
                        points[end],
                        (255, 0, 0),
                        2
                    )

                for x, y in points:

                    cv2.circle(
                        frame,
                        (x, y),
                        5,
                        (0, 255, 0),
                        -1
                    )

                # ==================================
                # COLLECT MOVEMENT SEQUENCE
                # ==================================

                if (
                    selected_label is not None
                    and frame_number % FRAME_INTERVAL == 0
                    and len(sequence) < SEQUENCE_LENGTH
                ):

                    features = extract_features(hand)

                    if features is not None:
                        sequence.append(features)

                # ==================================
                # SAVE COMPLETED SEQUENCE
                # ==================================

                if (
                    selected_label is not None
                    and len(sequence) >= SEQUENCE_LENGTH
                ):

                    flattened_sequence = [
                        value
                        for frame_features in sequence
                        for value in frame_features
                    ]

                    if len(flattened_sequence) == TOTAL_FEATURES:

                        writer.writerow(
                            [selected_label] + flattened_sequence
                        )

                        file.flush()

                        print(
                            "Sequence saved successfully:",
                            selected_label
                        )

                    selected_label = None
                    sequence = []

            else:

                # Restart sequence if hand disappears
                if selected_label is not None:
                    sequence = []

            # ==================================
            # DISPLAY STATUS
            # ==================================

            cv2.putText(
                frame,
                f"Gesture: {selected_label or 'NONE'}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Frames: {len(sequence)}/{SEQUENCE_LENGTH}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            if selected_label and not hand_detected:

                cv2.putText(
                    frame,
                    "Show your hand!",
                    (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

            cv2.putText(
                frame,
                "Press Q to Exit",
                (20, frame.shape[0] - 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                "SignBridge - Dynamic Collection",
                frame
            )

            # ==================================
            # KEYBOARD CONTROLS
            # ==================================

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("0"):

                selected_label = None
                sequence = []

                print("Current sequence cancelled.")

            elif key in labels:

                selected_label = labels[key]
                sequence = []

                print(
                    "\nRecording:",
                    selected_label
                )

                print(
                    "Perform the complete hand movement."
                )

finally:

    camera.release()
    detector.close()
    cv2.destroyAllWindows()

    print("\n====================================")
    print("DYNAMIC COLLECTION STOPPED")
    print("====================================")

    print("Dataset saved at:", CSV_FILE)