# SignBridge laptop repair diagnostic

Date: 2026-11-17

## Summary

This is an isolated repaired copy made from `C:\Projects\SignBridge-repaired\SignBridge-repaired`. The user's source folder and existing ZIPs were not modified. A source snapshot ZIP is preserved alongside the deliverables. This copy includes code fixes and safer training/capture behavior, but it is not certified as fully functional for live recognition. The initial camera/MediaPipe failures were rechecked successfully in the project environment on 2026-11-18; see the Step 5 follow-up below for the current launch result and remaining recognition-quality limitations.

## Phase results

### Phase 1 — Backup, dependencies, model verification

- Created a complete source snapshot archive and verified its ZIP entries (`testzip()` returned no corrupt member); it contains 51,680 entries and 1,170,275,013 uncompressed bytes.
- Created a separate editable project copy; original source and original backup archives were left unchanged.
- Supplied virtual environment: Python 3.13.2. `pip check`: no broken requirements.
- Static model and data structurally match: model expects 63 features and contains the original 8 classes; static CSV contains 800 rows, 100 per class.
- Correct manual bundle remains separate: sequence model has 40 outputs, scaler expects 1,662 features, and manual_labels.json has 40 labels. Do not mix this with `signbridge_40_words.keras` or its separate labels/scaler bundle.
- `word_model/test_scaler.py` passes when run from project root: StandardScaler loads and expects 1,662 features.

### Phase 2 — 40-word model and data

- Model, scaler, and labels load together; a synthetic zero-sequence inference produced a finite 1×40 output. This verifies wiring/shapes only, not accuracy.
- The manual trainer was run. It safely refused to train because all 900 `afternoon` frames have no hand landmarks (only 37 pose frames). It did not save a reduced-class model. The other 39 class directories meet the trainer's minimum hand-frame threshold.
- At the initial Phase 2 check, MediaPipe 0.10.35 no longer exposed `mp.solutions.holistic`, and an attempted download of a separate Tasks asset failed. This was a historical blocker; the later Step 5 recheck initialized the existing Holistic task asset and completed a short camera-loop smoke test. The later result supersedes the initial launch finding, but neither result establishes gesture accuracy.
- Use a Python 3.11 environment with the pinned legacy MediaPipe for matching the existing dataset, or if using Python 3.13's Tasks pipeline, recapture all 40 labels consistently before retraining. Recapture procedure is in README.

### Phase 3 — Both recognition modes

- Static 8-class and manual 40-word modes remain distinct in the app, use their respective model pipelines, and their mode-selection UI rendered in Streamlit testing.
- The original `OPEN_PALM` click mapping remains in Smart Gesture Control. Other actions require explicit opt-in; FIST stops the controller. Action mappings were checked with mocked inputs only; no real desktop action was sent.
- Manual sequence model output count is verified. The initial camera/MediaPipe limitation is superseded by the successful short loop smoke test in the Step 5 follow-up below; real gesture prediction quality remains unverified for live use.

### Phase 4 — Remaining application features

Code repairs include speech language/voice controls and save-to-history, duplicate microphone component key handling, history deletion/clear, Text-to-Sign sentence fallback for unsupported words, SOS contact/message preparation with explicit confirmation and no automatic send, bilingual Quick Communication Board/custom text, Smart Gesture consent/confidence/cooldown/stop behavior, and clearer recognition subprocess diagnostics. Existing app features were retained.

Streamlit AppTest rendered all 9 pages without app exceptions: Home, Sign to Text & Voice, Conversation History, Speech to Text, Text to Sign, About Project, Emergency SOS, Quick Communication Board, and Smart Gesture Control. Tested SOS link preparation (no SMS sent), history operations (original CSV restored byte-for-byte), contact save/reload (test JSON removed), English/Hindi quick board text, unsupported text-to-sign fallback, and mode selection. These are UI/logic checks, not browser microphone, speaker, or sensor tests.

### Phase 5 — Testing and delivery

- Dependency check passed; imports and the Streamlit app were checked earlier under the supplied virtual environment.
- `run_signbridge.bat` and direct Streamlit startup previously returned a healthy HTTP response in this environment.
- Dynamic training is blocked by the actual data: only 10 rows for WATER exist, while 11 other expected classes are absent. The guarded trainer refuses to write a reduced-class model.
- Raw alphabet image folders contain 26 labels, but an extracted alphabet CSV contains only 17 labels; guarded training writes candidates and refuses incomplete class sets.
- An earlier physical camera attempt returned `camera_opened=False`; the later Step 5 recheck opened camera index 0 and read frames. Microphone permissions, real speech capture, audible TTS, geolocation sensor access, and hardware sign recognition were not tested remotely.

## Files changed

Changes are limited to the delivered copy: `app.py`, `recognition.py`, `smart_gesture_control.py`, `requirements.txt`, `README.md`, `FEST_DEMO_NOTES.md`, collection/training/extraction utilities, manual live-test/view tools, and the added `word_model/holistic_compat.py` and `word_model/download_holistic_model.py`. Model/data assets were preserved; key hashes matched the source snapshot after test runs.

## Remaining limitations and laptop acceptance checklist

1. Install dependencies using the exact commands in README, then run `pip check`.
2. Confirm Windows camera privacy permissions and correct camera; run `word_model/test_holistic_webcam.py`.
3. For the existing manual dataset, use Python 3.11 with the specified MediaPipe version; recapture `afternoon` with visible hands and face for all 30 sequences. Do not overwrite its old data; collector makes a dated backup.
4. Capture a held-out evaluation set for every word, train, and report per-class precision/recall/confusion matrix before calling the 40-word model reliable.
5. Run actual browser microphone, TTS playback, and geolocation checks on the laptop.
6. Dynamic gesture model cannot be repaired by code alone; gather representative examples for all expected labels.
7. Text-to-Sign only has limited image references. Unsupported words correctly show a fallback rather than fabricated signs.

This report separates verified software checks from hardware and recognition-quality claims. The project camera opened in the Step 5 recheck, but the presentation laptop and live gesture accuracy are not certified. Microphone, geolocation, and audible output still require manual testing.

## Step 5 follow-up — 2026-11-18

- The recognition log showed earlier 40-word launches failing before camera access because the Python interpreter used by Streamlit could not import `cv2` and later `joblib`.
- The project `.venv` is Python 3.13.2; imports for Streamlit, OpenCV, Joblib, MediaPipe, TensorFlow, scikit-learn, and NumPy pass, and `pip check` reports no broken requirements. No packages were installed.
- With that interpreter, the active model/scaler/label bundle loaded with input shape `(30, 1662)`, 40 outputs, and 40 labels; the active label, scaler, and model hashes still match the recorded bundle/evaluation. The Holistic tracker initialized using the existing task asset, camera index 0 opened, and the complete recognizer loop processed three frames and cleaned up without exception.
- `run_signbridge.bat` now reports and preflights its selected interpreter. The app checks 40-word dependencies before launching and records the same `sys.executable` used for its child process.
- **Camera launch checks pass, but prediction quality does not:** the saved same-signer test session scored 4.5% accuracy for both the active model and the unpromoted candidate. No model, scaler, labels, or dataset were changed; retraining/replacement remains out of scope without approval and better validated data.
- Still unverified on this machine: recognition of intended signs in a live demo; microphone input, geolocation, audible output from all voices, and real Smart Gesture actions. The 40-word local reference gallery also lacks verified per-word images. The project recommends the 8-class static demo path, but it still needs a brief live recognition check before claiming a successful gesture result.

## Step 5 subsystem audit — 2026-11-18

- Static model inspection confirmed a RandomForest classifier with 63 inputs and these output classes in model order: `CROSSED_FINGERS`, `FIST`, `I_LOVE_YOU`, `OPEN_PALM`, `POINT_UP`, `THUMBS_DOWN`, `THUMBS_UP`, `VICTORY`. The active gesture catalog and model feature extraction remain unchanged. The runtime previously passed a NumPy array to a model fitted with named columns; it now supplies the same ordered `x0`…`z20` columns. Startup also rejects an unexpected feature count or class order rather than continuing with a mismatched model.
- The static model and collector both use wrist-relative, hand-scale-normalized 21-point XYZ landmarks. OpenCV BGR frames are converted to RGB for MediaPipe. The existing 50% threshold and two-frame stability requirement remain unchanged. Live gesture accuracy has not been tested.
- Location values are now checked for numeric, finite latitude/longitude values and valid geographic ranges before maps/SMS links are built. Missing or invalid location leaves the emergency message available without fabricated coordinates.
- Speech-to-text still uses the browser-selected microphone and Google's online recognizer. The page now explains browser/OS input selection and WO Mic setup. Physical microphone, service connectivity, and speaker output remain manual tests.
- Current `.venv` imports and `pip check` passed before manifest editing. The environment has both `opencv-python` 4.14.0.94 and `opencv-contrib-python` 5.0.0.93; `cv2` 5.0.0 works in the tested environment. The manifest now selects the contrib package required by MediaPipe and records the tested Hindi-voice helper dependencies. No package was installed, upgraded, or removed; do not clean the duplicate distributions without approval.
- `dataset/dynamic_gestures.csv` contains 10 valid 1,950-feature sequences, all labelled `WATER`; the other 11 required labels are absent. Training was not run. The separate alphabet image/CSV mismatch and absent 40-word reference images remain documented above.
