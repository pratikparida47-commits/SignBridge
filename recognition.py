import cv2
import mediapipe as mp
import joblib
import numpy as np
import pandas as pd
import math
import subprocess
import sys
import csv
import argparse

from pathlib import Path
from datetime import datetime
from collections import deque
from gesture_catalog import GESTURE_MESSAGES, TRAINED_STATIC_GESTURES

# ==========================================
# SIGNBRIDGE - AI GESTURE RECOGNITION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "signbridge_model.pkl"
TASK_PATH = BASE_DIR / "models" / "hand_landmarker.task"
FEATURE_COUNT = 63
argument_parser = argparse.ArgumentParser(description="SignBridge static gesture recognition")
argument_parser.add_argument("--camera-index", type=int, default=0)
args, _unknown_args = argument_parser.parse_known_args()

HISTORY_FILE = BASE_DIR / "conversation_history.csv"

# ==========================================
# CHECK REQUIRED FILES
# ==========================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

if not TASK_PATH.exists():
    raise FileNotFoundError(f"Hand landmarker file not found: {TASK_PATH}")

# ==========================================
# LOAD TRAINED MODEL
# ==========================================

model = joblib.load(MODEL_PATH)
voice_process = None
model_classes = tuple(model.classes_)
expected_model_classes = tuple(sorted(TRAINED_STATIC_GESTURES))
expected_feature_names = tuple(
    f"{axis}{index}"
    for index in range(21)
    for axis in ("x", "y", "z")
)

if model_classes != expected_model_classes:
    raise ValueError(
        "Static model classes do not match the expected 8-class vocabulary. "
        f"Expected {expected_model_classes}; found {model_classes}."
    )

if getattr(model, "n_features_in_", None) != FEATURE_COUNT:
    raise ValueError(
        f"Static model must accept {FEATURE_COUNT} features; "
        f"found {getattr(model, 'n_features_in_', None)}."
    )

if (
    hasattr(model, "feature_names_in_")
    and tuple(model.feature_names_in_) != expected_feature_names
):
    raise ValueError(
        "Static model feature names/order do not match the 21-point XYZ extractor."
    )

if not callable(getattr(model, "predict_proba", None)):
    raise ValueError("Static model must support predict_proba for confidence display.")

missing_catalog_labels = set(TRAINED_STATIC_GESTURES) - set(GESTURE_MESSAGES)
if missing_catalog_labels:
    raise ValueError(
        f"Trained model labels are missing from gesture_catalog.py: "
        f"{sorted(missing_catalog_labels)}"
    )

# ==========================================
# MEDIAPIPE SETUP
# ==========================================

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=str(TASK_PATH)),
    running_mode=RunningMode.VIDEO,
    num_hands=1
)

detector = HandLandmarker.create_from_options(options)

# ==========================================
# VOICE OUTPUT FUNCTION
# ==========================================

def speak_message(message):
    global voice_process

    speech_code = """
import sys
import os
import pyttsx3

engine = pyttsx3.init('sapi5') if os.name == 'nt' else pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

engine.say(sys.argv[1])
engine.runAndWait()
"""

    try:
        if voice_process is not None and voice_process.poll() is None:
            return

        voice_process = subprocess.Popen(
            [sys.executable, "-c", speech_code, message],
        )

        print("Voice started:", message)

    except Exception as error:
        print("Voice error:", error)

# ==========================================
# ALL 8 GESTURE MEANINGS
# ==========================================

messages = {
    label: GESTURE_MESSAGES[label]
    for label in model_classes
}

# ==========================================
# HAND CONNECTIONS
# ==========================================

connections = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

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

    for point in hand:

        features.extend([
            (point.x - wrist.x) / scale,
            (point.y - wrist.y) / scale,
            (point.z - wrist.z) / scale
        ])

    return np.array(features).reshape(1, -1)

# ==========================================
# PERMANENT CONVERSATION HISTORY
# ==========================================

def save_conversation(gesture, message, confidence, current_time):

    file_exists = HISTORY_FILE.exists()

    try:
        with open(
            HISTORY_FILE,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            if not file_exists:
                writer.writerow([
                    "Date",
                    "Time",
                    "Gesture",
                    "Message",
                    "Confidence"
                ])

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                current_time,
                gesture,
                message,
                f"{confidence:.1f}%"
            ])

        print("Conversation saved successfully!")
    except OSError as error:
        print(f"Could not save conversation history: {error}", flush=True)

# ==========================================
# CAMERA SETUP
# ==========================================

camera = cv2.VideoCapture(args.camera_index)

if not camera.isOpened():

    detector.close()

    raise RuntimeError(
        f"Camera index {args.camera_index} could not be opened. "
        "Choose another camera or close other camera applications."
    )

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# ==========================================
# RECOGNITION SETTINGS
# ==========================================

timestamp = 0

CONFIDENCE_LIMIT = 50.0
STABLE_FRAME_LIMIT = 2

candidate_prediction = ""
stable_frames = 0
last_spoken = ""

# Latest 5 messages for camera display
history = deque(maxlen=5)
recognized_sentence = deque(maxlen=8)

# ==========================================
# START MESSAGE
# ==========================================

print("------------------------------------")
print("SIGNBRIDGE AI RECOGNITION STARTED")
print("------------------------------------")

for gesture, message in messages.items():
    print(f"{gesture} = {message}")

print("------------------------------------")
print("Press Q to stop | C to clear sentence | R to repeat latest speech.")
print("------------------------------------")

print("Conversation file:", HISTORY_FILE)

# ==========================================
# MAIN RECOGNITION LOOP
# ==========================================

try:

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

        prediction = "SHOW YOUR HAND"
        confidence = 0.0

        # ==================================
        # HAND DETECTION
        # ==================================

        if result.hand_landmarks:

            hand = result.hand_landmarks[0]

            features = extract_features(hand)

            if features is not None:

                prediction_features = (
                    pd.DataFrame(features, columns=model.feature_names_in_)
                    if hasattr(model, "feature_names_in_")
                    else features
                )
                prediction = model.predict(prediction_features)[0]

                # Calculate confidence
                probabilities = model.predict_proba(prediction_features)[0]
                confidence = float(np.max(probabilities) * 100)

                # ==================================
                # STABLE GESTURE DETECTION
                # ==================================

                if (
                    confidence >= CONFIDENCE_LIMIT
                    and prediction in messages
                ):

                    if prediction == candidate_prediction:

                        stable_frames += 1

                    else:

                        candidate_prediction = prediction
                        stable_frames = 1

                    if (
                        stable_frames >= STABLE_FRAME_LIMIT
                        and prediction != last_spoken
                    ):

                        message = messages[prediction]

                        current_time = datetime.now().strftime(
                            "%H:%M:%S"
                        )

                        print("\nRecognised:", prediction)
                        print(
                            "Confidence:",
                            f"{confidence:.1f}%"
                        )
                        print("Message:", message)
                        print("Time:", current_time)
                        recognized_sentence.append(message)

                        # Add to live history
                        history.appendleft({
                            "gesture": prediction,
                            "message": message,
                            "time": current_time
                        })

                        # Save permanently to CSV
                        save_conversation(
                            prediction,
                            message,
                            confidence,
                            current_time
                        )

                        # Speak message
                        last_spoken = prediction

                        speak_message(message)

                else:

                    candidate_prediction = ""
                    stable_frames = 0

            else:

                candidate_prediction = ""
                stable_frames = 0

            # ==================================
            # DRAW HAND LANDMARKS
            # ==================================

            points = []

            for point in hand:

                x = int(point.x * frame.shape[1])
                y = int(point.y * frame.shape[0])

                points.append((x, y))

            # Draw connections
            for start, end in connections:

                cv2.line(
                    frame,
                    points[start],
                    points[end],
                    (255, 0, 0),
                    2
                )

            # Draw landmark points
            for x, y in points:

                cv2.circle(
                    frame,
                    (x, y),
                    5,
                    (0, 255, 0),
                    -1
                )

        else:

            candidate_prediction = ""
            stable_frames = 0

        # ==================================
        # DISPLAY RECOGNITION INFORMATION
        # ==================================

        cv2.putText(
            frame,
            f"Gesture: {prediction}",
            (20, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Confidence: {confidence:.1f}%",
            (20, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Stable Frames: {stable_frames}/{STABLE_FRAME_LIMIT}",
            (20, 125),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        sentence_text = " ".join(recognized_sentence)
        cv2.putText(
            frame,
            f"Sentence: {sentence_text[:100]}",
            (20, 165),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        # ==================================
        # RECOGNITION HISTORY PANEL
        # ==================================

        panel_x = 20
        panel_y = 165
        panel_width = 480
        panel_height = 245

        overlay = frame.copy()

        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (20, 20, 20),
            -1
        )

        cv2.addWeighted(
            overlay,
            0.75,
            frame,
            0.25,
            0,
            frame
        )

        cv2.putText(
            frame,
            "RECOGNITION HISTORY",
            (panel_x + 15, panel_y + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        if not history:

            cv2.putText(
                frame,
                "No messages recognised yet",
                (panel_x + 15, panel_y + 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (220, 220, 220),
                1
            )

        else:

            for index, item in enumerate(history):

                y_position = panel_y + 70 + index * 34

                history_text = (
                    f"{item['time']}  {item['gesture']}: "
                    f"{item['message']}"
                )

                cv2.putText(
                    frame,
                    history_text,
                    (panel_x + 15, y_position),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.48,
                    (255, 255, 255),
                    1
                )

        # ==================================
        # EXIT INSTRUCTION
        # ==================================

        cv2.putText(
            frame,
            "Q: Exit | C: Clear sentence | R: Repeat speech",
            (20, frame.shape[0] - 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # ==================================
        # SHOW CAMERA WINDOW
        # ==================================

        cv2.imshow(
            "SignBridge - AI Gesture Recognition",
            frame
        )

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("c"):
            recognized_sentence.clear()
        elif key == ord("r") and last_spoken in messages:
            speak_message(messages[last_spoken])

finally:

    # ==================================
    # RELEASE RESOURCES
    # ==================================

    camera.release()
    detector.close()
    cv2.destroyAllWindows()

    print("SignBridge recognition stopped.")
