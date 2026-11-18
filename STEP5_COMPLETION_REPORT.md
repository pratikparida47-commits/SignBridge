# SignBridge Step 5 Completion Report

Date: 2026-11-18

## Result

The existing project was continued in place. The 40-word camera launch/interpreter issue is resolved when started with the project launcher, but the saved 40-word evaluation is poor. The static model is structurally compatible, but live gesture accuracy has not been validated. SignBridge is **not fully validated for live sign recognition**.

No datasets, trained models, label files, reference images, or verified backup folders were changed. No package was installed, upgraded, or removed, and no model was retrained or replaced.

## A. Fixed and tested

- The static recognizer now checks its saved model's exact eight-class order and 63-feature input before starting. The former missing-label check could not detect a reduced model because it derived its expected labels from the model itself.
- Static inference now passes a DataFrame with the saved model's fitted feature names/order (`x0` through `z20`) instead of an unnamed NumPy array. A smoke inference returned the expected `(1, 8)` probability shape without the previous scikit-learn feature-name warning. This is a structure check, not an accuracy result.
- Static feature extraction remains wrist-relative and hand-scale-normalized over 21 XYZ landmarks; the collector uses the same formula. The existing 50% confidence threshold and two-consecutive-frame stability rule were preserved.
- Geolocation values are checked for numeric, finite latitude/longitude values and legal ranges before links or SMS text are prepared. Offline cases passed for valid boundaries, missing values, booleans, malformed strings, NaN/infinity, and out-of-range coordinates.
- Speech-to-text instructions now explain that the browser-selected microphone is used and how to select WO Mic in browser/OS settings.
- The launcher uses one selected Python interpreter for Streamlit and child recognition scripts (`sys.executable`), reports that interpreter, and checks required imports. The word-mode app preflight reports missing modules before launching a child process.
- The existing active 40-word model/scaler/labels loaded together with 40 outputs and the required 1,662-feature input. The exact final labels/order remain unchanged:
  `aboard, afternoon, bad, beside, book, byebye, camera, car, computer, correct, deaf, evening, family, food, friend, good, happy, house, lunch, man, marry, middle, morning, namaste, night, pen, place, practice, prisoner, sad, sorry, strong, sweet, teacher, time, understand, water, week, woman, you`.
- The 40-word feature order is pose (132), face (1,404), left hand (63), right hand (63), totalling 1,662. Runtime collects 30 hand-present frames, clears a partial sequence when a hand is missing, predicts every five frames, and requires at least 70% confidence plus three matching votes in its five-prediction window. The active 40-word label/model/scaler hashes were unchanged in the earlier Step 5 recheck.
- Requirements syntax and Python-version markers parsed successfully. The selected OpenCV dependency is now `opencv-contrib-python` (MediaPipe's distribution); `edge-tts==7.3.1` and `pygame==2.6.1` are declared for the included Hindi voice helper. The current environment's `pip check` passed and all inspected application, recognition, audio, and component imports loaded.
- All nine Streamlit pages passed AppTest: Home, Sign to Text & Voice, Conversation History, Speech to Text, Text to Sign, About Project, Emergency SOS, Quick Communication Board, and Smart Gesture Control.
- Smart Gesture action dispatch passed a mocked-action check for the configured keys/click and FIST stop behavior. No real mouse or keyboard event was sent.
- Smart Gesture code inspection confirmed a 65% default confidence threshold, five stable frames, a 1.5-second default cooldown, one action for a sustained pose, PyAutoGUI failsafe, and stop paths through FIST, Q, Ctrl+C, and the app stop button. The app's explicit permission checkbox enables all listed actions; the restricted Open-Palm-only mode is available through the controller flag used in the safe manual procedure.
- An in-memory WAV parsed through SpeechRecognition, and the Windows SAPI5 engine initialized and enumerated voices. No microphone, online transcription, or audible playback was tested.

## B. Fixed but not hardware-tested

- Geolocation now safely handles missing/invalid component values, but real browser permission, sensor readings, and browser-service failures need manual testing.
- The microphone guidance is corrected, but physical microphone selection, WO Mic, browser permission, and Google's online transcription service were not live-tested.
- SAPI5 enumerated two installed voices, both English (US); no Hindi SAPI5 voice was found. The engine was not asked to speak. `test_hindi_voice.py` was not run because it uses online audio generation and playback.
- Static webcam loop smoke testing used a real camera frame and a no-hand detector stub so no recognition, speech, or history write could occur. It does not validate hand detection or gesture predictions.

## C. Live-tested successfully

- `run_signbridge.bat` started Streamlit and `http://localhost:8501/_stcore/health` returned HTTP 200. The test server was stopped afterward and no longer responded.
- In the inspected project environment, camera index 0 opened and returned frames. The 40-word Holistic tracker initialized and its recognition loop processed three frames and cleaned up.
- The static camera loop processed a real camera frame in the controlled no-hand smoke test described above.

These are launcher/camera-pipeline checks only. They are **not** evidence of successful live gesture recognition.

## D. Still failing or unvalidated

- The saved same-signer held-out 40-word evaluation scored **4.5%**. In the five recorded `sorry` sequences, one was predicted as `night`, three as `strong`, and one as `sorry`. Model/scaler/label compatibility was checked; this is not explained by a bundle-order mismatch. The current evidence does not establish a single confirmed software cause, and the held-out test set was not used for tuning.
- Static-model live accuracy has not been measured. Structural compatibility and camera startup do not establish that the eight poses are predicted correctly.
- The installed environment contains both `opencv-python` 4.14.0.94 and `opencv-contrib-python` 5.0.0.93. The tested `cv2` runtime works, but the duplicate distributions remain. No uninstall/cleanup was performed. A clean Python 3.11 dependency installation was not run; its manifest branch was parsed but is not hardware/runtime-certified here.
- No `Air Switch` implementation was found in the app, Smart Gesture controller, or README. It is not available to test and was not invented.

## E. Blocked by missing data or references

- `dataset/dynamic_gestures.csv` contains 10 correctly shaped, finite 1,950-feature sequences, all labelled `WATER`. The other 11 required labels (`FOOD`, `DRINK`, `TOILET`, `HUNGRY`, `THIRSTY`, `PAIN`, `DOCTOR`, `HOME`, `WHERE`, `WHAT`, `GOODBYE`) are absent. Dynamic training was not run; no incomplete-class model was created.
- All 900 current `afternoon` frames lack hand landmarks. The existing guarded trainer requires at least three usable sequences for every one of the 40 labels. Preserve the old recordings and collect valid `afternoon` sequences plus a separate held-out evaluation set before any retraining is considered.
- The static catalogue has 20 custom pose labels, but only the original eight are trained. The other 12 require real labelled recordings and evaluation before being described as recognisable.
- The gallery has only `hello.png`, `stop.png`, and `thank_you.png`. The 40-word reference folder contains no word-reference images (only its README). No sign images were fabricated or presented as verified ISL references.
- The alphabet image/CSV mismatch and the missing 40-word references remain as documented in the existing diagnostic reports.

## F. Requires manual confirmation

1. **Eight static gestures:** On the demo laptop, use the same signer and webcam intended for the presentation. In good lighting, show one pose at a time for 2–3 seconds, return to neutral between poses, and repeat each at least three times. Check both the displayed label and mapped message:
   - `OPEN_PALM` → Hello
   - `FIST` → Stop
   - `THUMBS_UP` → Thank you
   - `THUMBS_DOWN` → No
   - `POINT_UP` → Help
   - `VICTORY` → Yes
   - `CROSSED_FINGERS` → Please
   - `I_LOVE_YOU` → I love you
   
   Record mismatches; do not claim reliable recognition if any pose is unstable. Do not present the 40-word mode as reliable given its saved evaluation.
2. **Smart Gesture:** The app's permission checkbox enables the listed real mouse/keyboard actions. For a restricted safe test, save work, open a blank Notepad document, place the pointer in its empty text area, then run from the project folder:
   ```powershell
   .\.venv\Scripts\python.exe .\smart_gesture_control.py --open-palm-click-only --permission-granted --confidence-limit 80 --cooldown 3
   ```
   This controller mode allows only Open Palm clicks. Test only if a click at the pointer location is harmless. Press `Q` in the camera window or Ctrl+C in the terminal to stop. Do not test keyboard actions on unsaved or important work. No real action was run in this audit.
3. **Speech:** Select the intended browser input (WO Mic if used), allow microphone access, make a short English/Hindi recording with internet available, then separately confirm English and Hindi audio output with the actual speakers. Hindi SAPI5 voice is currently absent; do not claim Hindi SAPI playback until a suitable voice is installed and heard.
4. **Geolocation/SOS:** Allow location in the browser, confirm the displayed coordinates are the browser's real coordinates, and review the contact, message, and location before opening the SMS app. No SMS was sent and no location was invented.
5. **Package cleanup:** Ask before installing packages or removing either OpenCV distribution. The current project environment launches without package changes.

## Test record

| Check | Result |
|---|---|
| Pylance syntax checks: `app.py`, `recognition.py`, `gesture_catalog.py` | Passed |
| Project `.venv` imports; `pip check` | Passed |
| Requirements parsing and Python 3.11/3.13 marker selection | Passed; no clean install attempted |
| Static model class order, 63 inputs, probability shape, feature-name warning | Passed (structural smoke only) |
| Static normalized feature extraction shape and finite values | Passed (synthetic landmarks only) |
| Geolocation input validation cases | Passed (offline synthetic values only) |
| Streamlit AppTest, nine pages | Passed with increased timeout; the initial default 3-second cold-start timeout was insufficient |
| `run_signbridge.bat` health endpoint | Passed, HTTP 200; server stopped afterward |
| Static camera loop | Passed for a real frame with no-hand detector stub; no prediction/history write |
| 40-word bundle and three-frame recognition-loop smoke test | Passed in prior Step 5 recheck; not an accuracy test |
| Smart Gesture mappings | Passed with mocked `pyautogui`; no real input |
| Speech WAV parsing / SAPI5 initialization | Passed; no mic, network transcription, or audio playback |
| Live gesture accuracy, browser microphone/location, audible output | Not tested |
| Dynamic model training | Not run; incomplete classes block training |

## Changed files

- `app.py`
- `recognition.py`
- `gesture_catalog.py`
- `requirements.txt`
- `run_signbridge.bat` (launcher/interpreter preflight from the earlier Step 5 pass)
- `README.md`
- `FEST_DEMO_NOTES.md`
- `DIAGNOSTIC_REPORT.md`
- `GESTURE_EXPANSION_STATUS.md`
- `STEP5_COMPLETION_REPORT.md` (this report)

Timestamped pre-change copies are under `reports/step5_prechange_20261118_063719/` and `reports/step5_prechange_fest_demo_20261118_064226/`. The verified backup folder was not modified.

## Start the demo

From PowerShell:

```powershell
Set-Location 'C:\Projects\SignBridge-laptop-repaired-final\SignBridge-laptop-repaired'
.\run_signbridge.bat
```

Use the local URL printed by Streamlit, usually `http://localhost:8501`. For the webcam, open **Sign to Text & Voice**, select a mode, and choose **Start Gesture Recognition**. Press `Q` in its camera window or use the app's stop control. Start with the static eight-class mode only after the manual checks above; do not present 40-word recognition as reliable.
