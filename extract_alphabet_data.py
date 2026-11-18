import cv2
import csv
import math
import mediapipe as mp
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "ISL custom Data"
MODEL_PATH = BASE_DIR / "models" / "hand_landmarker.task"
OUTPUT_FILE = BASE_DIR / "dataset" / "isl_alphabet_candidate.csv"

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# MediaPipe setup
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=1,
    min_hand_detection_confidence=0.20,
    min_hand_presence_confidence=0.20
)


def extract_features(hand):
    wrist = hand[0]

    distances = []
    for point in hand:
        distance = math.sqrt(
            (point.x - wrist.x) ** 2 +
            (point.y - wrist.y) ** 2
        )
        distances.append(distance)

    scale = max(distances)

    if scale == 0:
        return None

    features = []

    for point in hand:
        features.extend([
            (point.x - wrist.x) / scale,
            (point.y - wrist.y) / scale,
            (point.z - wrist.z) / scale
        ])

    return features


def make_variants(image):
    # Original image
    yield image

    # Enlarged image
    enlarged = cv2.resize(
        image, None, fx=2, fy=2,
        interpolation=cv2.INTER_CUBIC
    )
    yield enlarged

    # Contrast-enhanced enlarged image
    lab = cv2.cvtColor(enlarged, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    l = clahe.apply(l)
    enhanced = cv2.merge((l, a, b))
    enhanced = cv2.cvtColor(
        enhanced, cv2.COLOR_LAB2BGR
    )

    yield enhanced


def detect_hand(detector, image):
    for variant in make_variants(image):
        rgb = cv2.cvtColor(
            variant, cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = detector.detect(mp_image)

        if result.hand_landmarks:
            features = extract_features(
                result.hand_landmarks[0]
            )

            if features is not None:
                return features

    return None


def main():
    if not DATASET_DIR.exists():
        print("ERROR: ISL custom Data folder not found.")
        return

    if not MODEL_PATH.exists():
        print("ERROR: hand_landmarker.task not found.")
        return

    OUTPUT_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )

    headers = ["label"] + [
        f"f{i}" for i in range(63)
    ]

    saved = 0
    failed = 0

    with HandLandmarker.create_from_options(options) as detector:
        with open(
            OUTPUT_FILE, "w", newline=""
        ) as file:

            writer = csv.writer(file)
            writer.writerow(headers)

            for letter in LETTERS:
                folder = DATASET_DIR / letter

                if not folder.exists():
                    print(f"Missing folder: {letter}")
                    continue

                images = sorted([
                    p for p in folder.iterdir()
                    if p.is_file()
                    and p.suffix.lower() in [".jpg", ".jpeg"]
                ])

                letter_saved = 0

                print(
                    f"\nProcessing {letter}: "
                    f"{len(images)} images"
                )

                for image_path in images:
                    image = cv2.imread(str(image_path))

                    if image is None:
                        failed += 1
                        continue

                    features = detect_hand(
                        detector, image
                    )

                    if features is None:
                        failed += 1
                        continue

                    writer.writerow(
                        [letter] + features
                    )

                    saved += 1
                    letter_saved += 1

                print(
                    f"Completed {letter}: "
                    f"{letter_saved} detected"
                )

    print("\nALPHABET DATA EXTRACTION FINISHED")
    print("Images successfully processed:", saved)
    print("Images skipped:", failed)
    print("CSV saved at:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
