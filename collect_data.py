import cv2
import mediapipe as mp
import csv
import math
from pathlib import Path
from gesture_catalog import GESTURE_MESSAGES

# ==========================================
# SIGNBRIDGE - DATA COLLECTION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_DIR = BASE_DIR / "dataset"
CSV_FILE = DATASET_DIR / "hand_signs.csv"
TASK_FILE = BASE_DIR / "models" / "hand_landmarker.task"

DATASET_DIR.mkdir(exist_ok=True)

SAMPLES_PER_CLASS = 100

# ==========================================
# GESTURE LABELS
# ==========================================

COLLECTION_KEYS = "123456789asdfghjklzx"
labels = {
    ord(key): label
    for key, label in zip(COLLECTION_KEYS, GESTURE_MESSAGES)
}

gesture_names = list(labels.values())

# ==========================================
# CREATE CSV IF NEEDED
# ==========================================

headers = ["label"]

for i in range(21):
    headers.extend([
        f"x{i}", f"y{i}", f"z{i}"
    ])

if not TASK_FILE.exists():
    raise FileNotFoundError(
        f"Hand landmarker not found: {TASK_FILE}"
    )

if not CSV_FILE.exists():
    with open(CSV_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

# ==========================================
# LOAD EXISTING SAMPLE COUNTS
# ==========================================

counts = {name: 0 for name in gesture_names}

with open(CSV_FILE, "r", newline="") as file:
    reader = csv.DictReader(file)

    if reader.fieldnames != headers:
        raise ValueError(
            "Existing CSV columns do not match the expected format. "
            "Keep a backup before changing the dataset."
        )

    for row in reader:
        label = row.get("label")

        if label in counts:
            counts[label] += 1

print("\nSIGNBRIDGE DATA COLLECTION")
print("--------------------------------")

for key, name in labels.items():
    print(f"Press {chr(key)} = {name}")

print("Press 0 = Pause collection")
print("Press Q = Quit")
print("--------------------------------")

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
# CAMERA SETUP
# ==========================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    detector.close()
    raise RuntimeError("Camera could not be opened.")

selected_label = None
frame_count = 0
timestamp = 0

# ==========================================
# HAND CONNECTIONS
# ==========================================

connections = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17)
]

# ==========================================
# DATA COLLECTION
# ==========================================

try:

    with open(CSV_FILE, "a", newline="") as file:

        writer = csv.writer(file)

        while True:

            success, frame = camera.read()

            if not success:
                print("Unable to read camera frame.")
                break

            frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb
            )

            result = detector.detect_for_video(
                mp_image,
                timestamp
            )

            timestamp += 33
            frame_count += 1

            hand_detected = False

            if result.hand_landmarks:

                hand_detected = True
                hand = result.hand_landmarks[0]

                points = [
                    (
                        int(p.x * frame.shape[1]),
                        int(p.y * frame.shape[0])
                    )
                    for p in hand
                ]

                for a, b in connections:

                    cv2.line(
                        frame,
                        points[a],
                        points[b],
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
                # FEATURE EXTRACTION
                # ==================================

                if (
                    selected_label is not None
                    and counts[selected_label] < SAMPLES_PER_CLASS
                    and frame_count % 5 == 0
                ):

                    wrist = hand[0]

                    scale = max(
                        math.sqrt(
                            (p.x - wrist.x) ** 2
                            + (p.y - wrist.y) ** 2
                        )
                        for p in hand
                    )

                    if scale > 0:

                        coords = []

                        for p in hand:

                            coords.extend([
                                (p.x - wrist.x) / scale,
                                (p.y - wrist.y) / scale,
                                (p.z - wrist.z) / scale
                            ])

                        writer.writerow(
                            [selected_label] + coords
                        )

                        file.flush()

                        counts[selected_label] += 1

                        if counts[selected_label] >= SAMPLES_PER_CLASS:
                            print(
                                selected_label,
                                "collection completed!"
                            )
                            selected_label = None

            # ==================================
            # DISPLAY STATUS
            # ==================================

            cv2.putText(
                frame,
                f"Selected: {selected_label or 'NONE'}",
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

            for index, name in enumerate(gesture_names):

                column_x = 15 if index < 10 else frame.shape[1] // 2
                row_y = 75 + (index % 10) * 27

                cv2.putText(
                    frame,
                    f"{name}: {counts[name]}/{SAMPLES_PER_CLASS}",
                    (column_x, row_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.48,
                    (0, 255, 0),
                    1
                )

            if selected_label and not hand_detected:

                cv2.putText(
                    frame,
                    "Show your hand!",
                    (15, frame.shape[0] - 55),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

            cv2.imshow(
                "SignBridge - Data Collection",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("0"):
                selected_label = None
                print("Collection paused.")

            elif key in labels:

                new_label = labels[key]

                if counts[new_label] < SAMPLES_PER_CLASS:

                    selected_label = new_label

                    print(
                        "Collecting:",
                        selected_label
                    )

                else:

                    selected_label = None

                    print(
                        new_label,
                        "already has 100 samples."
                    )

            if all(
                count >= SAMPLES_PER_CLASS
                for count in counts.values()
            ):

                print(
                    f"\nAll {len(gesture_names) * SAMPLES_PER_CLASS} "
                    "samples collected!"
                )
                break

finally:

    camera.release()
    detector.close()
    cv2.destroyAllWindows()

    print("\nCamera closed.")

print("\nFINAL SAMPLE COUNTS")

for name, count in counts.items():
    print(name, ":", count)

print("\nDataset saved at:", CSV_FILE)
