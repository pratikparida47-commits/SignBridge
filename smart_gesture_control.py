import cv2
import mediapipe as mp
import joblib
import numpy as np
import pandas as pd
import math
import pyautogui
import time
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="SignBridge 8-class gesture control")
parser.add_argument("--confidence-limit", type=float, default=65.0)
parser.add_argument("--cooldown", type=float, default=1.5)
parser.add_argument("--camera-index", type=int, default=0)
parser.add_argument("--permission-granted", action="store_true")
parser.add_argument(
    "--open-palm-click-only",
    action="store_true",
    help="Allow only Open Palm mouse clicks; ignore every other action gesture.",
)
args, _unknown_args = parser.parse_known_args()

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "signbridge_model.pkl"
TASK_PATH = BASE_DIR / "models" / "hand_landmarker.task"

if not MODEL_PATH.is_file():
    raise FileNotFoundError(f"Gesture model not found: {MODEL_PATH}")
if not TASK_PATH.is_file():
    raise FileNotFoundError(f"Hand landmarker task not found: {TASK_PATH}")

model = joblib.load(MODEL_PATH)

CONFIDENCE_LIMIT = min(95.0, max(40.0, args.confidence_limit))
STABLE_FRAME_LIMIT = 5
COOLDOWN = max(0.5, args.cooldown)
ACTION_GESTURES = {
    "OPEN_PALM",
    "FIST",
    "POINT_UP",
    "CROSSED_FINGERS",
    "VICTORY",
    "THUMBS_UP",
    "THUMBS_DOWN",
}
if args.open_palm_click_only:
    ACTION_GESTURES = {"OPEN_PALM"}

candidate = ""
stable_frames = 0
last_action_time = 0
gesture_used = False
timestamp = 0
last_debug_time = 0
last_open_palm_status_time = 0

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


def extract_features(hand):
    wrist = hand[0]

    scale = max(
        math.sqrt(
            (p.x - wrist.x) ** 2 +
            (p.y - wrist.y) ** 2
        )
        for p in hand
    )

    if scale <= 0:
        return None

    features = []

    for p in hand:
        features.extend([
            (p.x - wrist.x) / scale,
            (p.y - wrist.y) / scale,
            (p.z - wrist.z) / scale
        ])

    if hasattr(model, "feature_names_in_"):
        return pd.DataFrame(
            [features],
            columns=model.feature_names_in_
        )

    return np.array(features).reshape(1, -1)


def perform_action(gesture):
    try:
        if gesture == "FIST":
            print("EMERGENCY STOP GESTURE: controller stopping.", flush=True)
            return False

        if gesture == "POINT_UP":
            pyautogui.press("pageup")
            print("ACTION SENT: Page Up", flush=True)

        elif gesture == "CROSSED_FINGERS":
            pyautogui.press("pagedown")
            print("ACTION SENT: Page Down", flush=True)

        elif gesture == "VICTORY":
            pyautogui.hotkey("alt", "tab")
            print("ACTION SENT: Alt + Tab", flush=True)

        elif gesture == "THUMBS_UP":
            pyautogui.press("enter")
            print("ACTION SENT: Enter", flush=True)

        elif gesture == "THUMBS_DOWN":
            pyautogui.press("esc")
            print("ACTION SENT: Escape", flush=True)

        elif gesture == "OPEN_PALM":
            pyautogui.click()
            print("ACTION SENT: Click", flush=True)

    except Exception as error:
        print("CONTROL ERROR:", error, flush=True)
    return True


options = mp.tasks.vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(
        model_asset_path=str(TASK_PATH)
    ),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_hands=1
)

detector = mp.tasks.vision.HandLandmarker.create_from_options(options)

camera = cv2.VideoCapture(args.camera_index)

if not camera.isOpened():
    detector.close()
    raise RuntimeError(f"Unable to open camera index {args.camera_index}.")

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if args.open_palm_click_only:
    preview_window = "SignBridge Smart Gesture Control"
    cv2.namedWindow(preview_window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(preview_window, 480, 360)
    cv2.moveWindow(preview_window, 0, 0)

print("\nSIGNBRIDGE SMART GESTURE CONTROL", flush=True)
print(f"Permission: {'GRANTED' if args.permission_granted else 'NOT GRANTED'}", flush=True)
if args.open_palm_click_only:
    print("Safety mode: OPEN PALM CLICK ONLY (all other actions disabled)", flush=True)
print("Webcam started. Keep Chrome active for testing.", flush=True)
print("Press Ctrl+C in this terminal to stop.\n", flush=True)

try:
    while True:
        success, frame = camera.read()

        if not success:
            print("CAMERA ERROR: Cannot read frame.", flush=True)
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = detector.detect_for_video(mp_image, timestamp)
        timestamp += 33

        prediction = "NO HAND"
        confidence = 0.0

        if result.hand_landmarks:
            features = extract_features(result.hand_landmarks[0])

            if features is not None:
                prediction = model.predict(features)[0]

                if hasattr(model, "predict_proba"):
                    probabilities = model.predict_proba(features)[0]
                    confidence = float(np.max(probabilities) * 100)

                if confidence >= CONFIDENCE_LIMIT and prediction in ACTION_GESTURES:
                    if prediction == candidate:
                        stable_frames += 1
                    else:
                        candidate = prediction
                        stable_frames = 1
                        gesture_used = False

                    if (
                        stable_frames >= STABLE_FRAME_LIMIT
                        and not gesture_used
                        and time.time() - last_action_time >= COOLDOWN
                    ):
                        print(
                            f"\nRECOGNISED: {prediction} ({confidence:.1f}%)",
                            flush=True
                        )

                        if not args.permission_granted:
                            print("ACTION BLOCKED: permission was not passed to the controller.", flush=True)
                            gesture_used = True
                        else:
                            should_continue = perform_action(prediction)
                            if not should_continue:
                                break

                            last_action_time = time.time()
                            gesture_used = True
                else:
                    candidate = ""
                    stable_frames = 0
                    gesture_used = False
        else:
            candidate = ""
            stable_frames = 0
            gesture_used = False

        if time.time() - last_open_palm_status_time >= 1.0:
            now = time.time()
            cooldown_left = max(0.0, COOLDOWN - (now - last_action_time))
            open_palm_stable = stable_frames if candidate == "OPEN_PALM" else 0
            status_reason = "ready"
            if prediction != "OPEN_PALM":
                status_reason = "classifier did not predict OPEN_PALM"
            elif confidence < CONFIDENCE_LIMIT:
                status_reason = "confidence below threshold"
            elif open_palm_stable < STABLE_FRAME_LIMIT:
                status_reason = "waiting for stable prediction"
            elif not args.permission_granted:
                status_reason = "permission missing"
            elif cooldown_left > 0:
                status_reason = "cooldown active"
            elif gesture_used:
                status_reason = "already acted; release and repeat the gesture"
            print(
                "OPEN_PALM DIAGNOSTIC: "
                f"detected={'yes' if prediction == 'OPEN_PALM' else 'no'} "
                f"confidence={confidence:.1f}%/{CONFIDENCE_LIMIT:.1f}% "
                f"stability={open_palm_stable}/{STABLE_FRAME_LIMIT} "
                f"permission={'granted' if args.permission_granted else 'missing'} "
                f"cooldown_remaining={cooldown_left:.1f}s "
                f"gesture_used={'yes' if gesture_used else 'no'} status={status_reason}",
                flush=True,
            )
            last_open_palm_status_time = now

        # Print camera and recognition status once per second
        if time.time() - last_debug_time >= 1:
            print(
                f"Status: {prediction} | Confidence: {confidence:.1f}%",
                flush=True
            )
            last_debug_time = time.time()

        cv2.putText(
            frame,
            f"Gesture: {prediction} | Confidence: {confidence:.1f}%",
            (12, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            "Q: quit | Open Palm: click",
            (12, frame.shape[0] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        cv2.imshow("SignBridge Smart Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    print("\nStopping...", flush=True)

finally:
    camera.release()
    detector.close()
    cv2.destroyAllWindows()
    print("Smart Gesture Control stopped.", flush=True)
