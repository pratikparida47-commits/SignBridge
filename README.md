# SignBridge — AI-Assisted Communication

## SignBridge 2.0 update

The existing Streamlit application is now branded as **SignBridge 2.0 — Breaking Communication Barriers**. Added navigation and in-place modules include Live ISL Recognition, searchable 40-word dictionary entries, an ISL alphabet lesson checklist, a sentence builder, browser Speech Synthesis, live-location and map preparation, and a measured-model evaluation page.

These additions preserve the existing static and 40-word recognition engines. They do not promote unverified signs or alter trained models. Verified ISL reference assets remain required before a sign can be presented as official ISL.

SignBridge is a Python student-project prototype with two separate webcam modes: an **8-class static hand-pose model** and a **40-class manual word-sequence model**. The modes use different model formats and feature pipelines. The static mode maps poses to short messages; the word mode displays and speaks its predicted word. The app also includes speech-to-text, a small visual sign-reference gallery, a quick communication board, Emergency SOS, Smart Gesture Control, and a CSV conversation log.

> **Scope and accessibility note:** SignBridge is not a complete Indian Sign Language (ISL) or other sign-language translator. It recognises a limited set of custom poses only. Do not use it for emergency, medical, legal, or other high-stakes communication.

## Features

- Webcam hand-landmark detection with MediaPipe.
- Random Forest classification of custom hand poses (8 currently trained; 12 expansion labels awaiting data collection).
- LSTM recognition of 40 manual word labels using 30-frame holistic sequences, in a separate recognition mode.
- Text and voice output for recognised gestures.
- Speech-to-text recording (English–India locale) through Google's online recognition service.
- Conversation history with search and CSV export.
- Three supplied visual reference images (Hello, Stop, Thank you).
- Dataset collection and model-training scripts.

## Gesture vocabulary

| Model label | Phrase | Current status |
|---|---|---|
| `OPEN_PALM` | Hello | Trained |
| `FIST` | Stop | Trained |
| `THUMBS_UP` | Thank you | Trained |
| `THUMBS_DOWN` | No | Trained |
| `POINT_UP` | Help | Trained |
| `VICTORY` | Yes | Trained |
| `CROSSED_FINGERS` | Please | Trained |
| `I_LOVE_YOU` | I love you | Trained |
| `CALL_ME` | Call me | Collect data |
| `OK_SIGN` | Okay | Collect data |
| `ROCK_ON` | Great | Collect data |
| `PINCHED_FINGERS` | Wait | Collect data |
| `THREE_FINGERS` | Three | Collect data |
| `FOUR_FINGERS` | Four | Collect data |
| `TWO_FINGERS` | Two | Collect data |
| `ONE_FINGER` | One | Collect data |
| `PINKY_PROMISE` | Promise | Collect data |
| `FINGERS_CROSSED_ALT` | Good luck | Collect data |
| `THUMB_TO_LITTLE` | Family | Collect data |
| `SPREAD_FINGERS` | Show five | Collect data |

## Static gesture expansion: 20 catalogue poses

The active static model is trained on 8 classes (100 samples each; 800 rows total). The catalogue and collector provide 20 labels. The additional 12 labels have no samples in the supplied static CSV and will not be recognised by the active model until you collect data, train a candidate, evaluate it, and promote it deliberately.

To add the remaining catalogue gestures:

1. Run `python collect_data.py` with your webcam.
2. Select a gesture using the displayed keys (1–9, then A/S/D/F/G/H/J/K/L/Z/X).
3. Hold the pose naturally while the collector records up to 100 samples for that class. Vary distance, angle, and lighting; collect samples from more than one person where possible.
4. Repeat until every target class has at least 100 clean samples.
5. Run `python train_model.py`. The trainer discovers the labels in the CSV and requires at least 30 samples per class. It saves `models/signbridge_static_candidate.pkl` and leaves the active 8-class model untouched.
6. Evaluate the candidate on held-out recordings before deliberately promoting it to the active model path.

The static catalogue is separate from the 40-word sequence model below. These are custom static demo poses, not a validated Indian Sign Language vocabulary or continuous ISL translation system. Similar-looking poses can be confused; test and validate with real users before making accessibility claims.

## 40-word sequence mode

The app's **40-word sequences** mode loads the manual-specific `word_model/manual_model/signbridge_manual_40_new.keras`, `manual_scaler.pkl`, and `manual_labels.json` bundle. It does not use the separate legacy `word_model/signbridge_40_words.keras` bundle. The manual dataset has 30 sequence folders of 30 frames per label. In the supplied data, every `afternoon` frame has zero hand landmarks, so a 40-class retrain must wait until real afternoon recordings are collected.

To collect or evaluate manual sequences, run these commands from the project folder:

```bash
python word_model/collect_manual_signs.py
python word_model/train_manual_model.py
```

The collector saves only frames where at least one hand is detected. To preserve the existing invalid afternoon recordings and add new recordings after them, run `python word_model/collect_manual_signs.py --word afternoon --append`. This creates new sequence folders and leaves the old folders untouched. The trainer filters low-hand-quality sequences, uses separate chronological sequence-folder fit/validation/test groups, and refuses to save a reduced-class model. Candidate files are written under `word_model/manual_model/retrained/`; the active manual bundle is not overwritten. Do not retrain until all 40 classes have at least three usable sequences; for a meaningful final evaluation, collect a separate new-session test set for every word.

The 14,347 files in `ISL custom Data/` are alphabet photographs (A–Z), not 40-word references. They are the input to the alphabet candidate training script and are not loaded by the main Streamlit app. The separate 40-word reference gallery lists every model word and marks missing verified illustrations. It does not use the computer-drawn landmark chart as a sign reference. ISLRTC provides a video dictionary; its [official dictionary site](https://divyangjan.depwd.gov.in/islrtc/) is linked from each gallery entry. Local reference images must be verified for ISL meaning and credited to their source before they are added under `assets/signs/word_refs/`.

These are custom static demo poses, not a validated Indian Sign Language vocabulary or continuous ISL translation system. Similar-looking poses can be confused; test and validate with real users before making accessibility claims.

## Requirements

- Windows 10/11 or another desktop OS with a working webcam.
- Python **3.11 recommended**.
- The 40-word mode and its trainer require TensorFlow; Smart Gesture Control uses PyAutoGUI. Both are included in `requirements.txt`.
- Internet access for installation and the Speech-to-Text page.
- A microphone for speech input.
- The included MediaPipe task file and trained model (already in `models/`).

The manual sequence collector and recognizer support both MediaPipe's legacy Holistic API and the current Tasks API. On current MediaPipe versions, the official `holistic_landmarker.task` asset is downloaded on first use if it is missing. You can fetch it in advance with `python word_model\download_holistic_model.py`; this needs internet access. The existing `hand_landmarker.task` is used for static recognition and is a separate asset.

The saved model was serialised with scikit-learn 1.9.1. `requirements.txt` pins that version because loading pickle/joblib models across scikit-learn versions is not guaranteed to be compatible.

## Setup and run (Windows PowerShell)

Extract the project so this README is in the project root. Open PowerShell in that folder and run the existing environment with the launcher:

```powershell
.\run_signbridge.bat
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`). The launcher prints the selected Python interpreter and checks dependencies before starting. If a custom `SIGNBRIDGE_PYTHON` is set, that interpreter is used and checked; otherwise the project `.venv` is preferred, with the existing parent-environment fallbacks retained.

The webcam scripts are child processes of Streamlit and use the exact same interpreter as the app. If the 40-word mode reports a missing module, close the app and start it with `run_signbridge.bat` or `.\.venv\Scripts\python.exe -m streamlit run app.py`; do not launch Streamlit from a different system Python. The selected interpreter is also recorded in `logs\recognition.log`.

The rechecked project environment is Python 3.13.2 / MediaPipe 0.10.35. Its Tasks API adapter and existing Holistic asset initialized successfully, and camera index 0 returned frames in the inspection environment. The earlier dependency/camera-launch failure is resolved when Streamlit is started through the project launcher. This verifies startup only, not gesture accuracy. The environment currently has both `opencv-python` and `opencv-contrib-python` installed; `requirements.txt` now selects the MediaPipe-required contrib package for a clean environment, but the duplicate installed distributions have not been removed. Do not uninstall packages without reviewing and approving that cleanup.

The active sequence model scored 4.5% on a separate recording session from the same signer (200 sequences, five per label). A candidate scored 68.1% on a chronological sequence-folder split from its training dataset; that is not an independent signer/session result, and the candidate is not the active model. The same-signer session errors coincide with confirmed differences in missing hand/face landmarks, left/right hand-slot distribution, and temporal motion. The existing normalized feature extraction functions match, and model/scaler/label shapes and order were checked. Since recordings contain landmarks but no source video or session-level extractor metadata, the exact semantic or capture cause cannot be established. Do not retrain or claim an accuracy improvement without new, independently reviewed data.

Static gesture accuracy has not been measured. Webcam startup is a pipeline check only, not a recognition-quality result. The app allows selecting camera indices 0–3; the available cameras depend on the machine. To create a separate Python 3.11 environment (which modifies the environment and downloads packages), use these commands only if you intend to install dependencies:

```powershell
Set-Location '<project-root>'
py -3.11 -m venv .venv311
& '.venv311\Scripts\python.exe' -m pip install --upgrade pip
& '.venv311\Scripts\python.exe' -m pip install -r '.\requirements.txt'
& '.venv311\Scripts\python.exe' -m pip check
& '.venv311\Scripts\python.exe' -m streamlit run app.py
```

For a different laptop, install Python 3.11 (recommended), open PowerShell in the application folder, then run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The supplied project environment passed dependency checks, the 40-word model/scaler/label bundle loaded with 40 outputs, the Holistic tracker initialized, and camera index 0 returned a frame in the inspection environment. These checks confirm the launch pipeline, not prediction quality. The active sequence model scored 4.5% on a separate recording session by the same signer (200 sequences, five per label); static gesture accuracy has not been measured. See `PHASE4_ROOT_CAUSE_DIAGNOSIS.md` for the confirmed training/test differences and limits of the diagnosis.

The same-signer session diagnosis found class-specific differences in missing hand/face landmarks, left/right hand placement, and movement patterns between training folders and the new capture session. The source-level feature order and extraction arithmetic match, and model/scaler/label order was checked. Since recordings have no source video or session-level extractor metadata, a single semantic or capture cause cannot be proved. The candidate's 68.1% chronological folder holdout is from the training dataset and is not an independent signer/session result.

### ISL dictionary and dataset provenance

The 40-word labels are model vocabulary, not 40 verified ISL references. The gallery only shows assets present in the project; missing references remain unavailable. Static poses are custom demo poses, and the alphabet checklist is a progress tool—not an alphabet classifier. The project does not automatically download FDMSE-ISL or ISLRTC media: access and license conditions could not be verified in this environment, and downloaded media must not be presented as verified without source review and attribution.

### SignBridge 2.0 modules

Navigation shortcuts **Live ISL Recognition**, **ISL Digital Dictionary**, **Recognition History**, and **Word Communication Board** reuse the existing recognition, gallery, history, and communication-board implementations. There is no separate duplicate recognition model. Choose a camera index from 0 to 3 on the recognition page. Smart Gesture Control defaults to Open Palm click-only; full keyboard actions remain available only after choosing that profile and granting permission.

The Speaker Voice page uses browser Speech Synthesis. Voice availability depends on the browser and operating system. Hindi/Odia voice selection is best-effort; status cannot confirm audio was physically heard. Live Location uses the existing geolocation component; click its location button, permit access, and use localhost or HTTPS. This component returns coordinates and accuracy but not a GPS sample timestamp or explicit permission error details. Emergency SOS prepares a reviewed SMS link but does not send it.

On the 40-word recognition page, **Manual practice target** displays the word being tested in the camera window only; it is not passed into the classifier. It does not improve or validate recognition accuracy. The Speaker Voice page waits for the browser's voice list before reporting language availability; press **Speak** to request playback, then verify the physical output yourself.

## Setup (macOS / Linux)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Using the application

1. Start the Streamlit app.
2. Open **Live ISL Recognition** (a shortcut to the existing engines) or **Sign to Text & Voice**. Choose **Static gestures (8)** or **40-word sequences**. Static poses are custom prototype labels and not validated ISL signs.
3. Select camera index 0–3, then choose **Start Gesture Recognition**. A separate OpenCV camera window opens. Check static labels manually; do not rely on the 40-word output (its saved same-signer test was 4.5%). For the 40-word mode, select a practice target to keep track of the word you intend to sign; the selected target is not an input to inference.
4. Press `Q` in the camera window to close it, or use **Stop recognition** in the app.
5. Open **Conversation History** to review or export saved gesture messages.
6. Use **Speech to Text** to record a short spoken message. The browser-selected microphone is used; select WO Mic in the browser or operating-system input settings if applicable. Browser microphone permission and internet access are required for Google's English or Hindi transcription endpoint.
7. Use **ISL Digital Dictionary** for vocabulary search, **ISL Alphabet Learning** for the session-only checklist, and **Speaker Voice** for browser speech controls. References not bundled and verified are marked unavailable; no alphabet recognition is claimed.
8. Use **Word Communication Board** to build a sentence, undo/remove terms, copy/download, and add recent history messages.
9. Use **Smart Gesture Control** to start or stop computer actions. The default profile is Open Palm click-only; full keyboard actions require selecting the broader profile and explicitly granting permission.
10. Use **Live Location** only on localhost or HTTPS. Click the geolocation component's location button, permit access, and verify the displayed coordinates. **Emergency SOS** prepares a reviewed SMS link; the app does not send the SMS itself.

11. **Quick Communication Board** has common English and Hindi phrases plus custom text. Its existing Windows Hindi TTS depends on a Hindi voice being installed; use **Speaker Voice** for browser voice selection and repeat/stop controls.

### Important camera behaviour

The webcam recogniser is launched as a local desktop process. It needs access to the computer's camera and display. It will not access a phone camera merely because the Streamlit page is opened on a phone, and a cloud-hosted Streamlit server generally cannot access the viewer's local webcam through this separate-process design.

## Dataset and retraining

The static dataset contains 800 rows (100 samples per original gesture) and 63 landmark features per row. To collect more static samples, run:

```bash
python collect_data.py
```

To retrain and evaluate the model:

```bash
python train_model.py
```

Back up `dataset/hand_signs.csv` and `models/signbridge_model.pkl` before retraining. Collect samples across different people, lighting conditions, camera distances, and hand orientations. Use a held-out test set from different recording sessions for a meaningful evaluation; random frame-level splits can overestimate real-world performance when adjacent frames are highly similar.

The manual word dataset is separate: it stores 1,662 holistic features for each of 30 frames per sequence. The saved manual model is loaded only with `word_model/manual_model/manual_scaler.pkl` and `manual_labels.json`. Do not combine these with the different `word_model/signbridge_40_words.keras` bundle. The supplied `afternoon` recordings contain no hand landmarks; recapture that label with:

```powershell
Set-Location '<project-root>'
& '.\.venv\Scripts\python.exe' 'word_model\collect_manual_signs.py' --word afternoon --replace-existing
```

The collector preserves the old `afternoon` folder under `word_model/manual_dataset_backups`, then captures 30 sequences of 30 usable frames each. Keep the active hand visible and centered in the camera preview throughout each sequence. Press `S` to start each sequence, hold the sign naturally until 30 frames are captured, and repeat as prompted. If the preview says no hand is detected, adjust lighting, distance, and framing before continuing. Press `Q` to stop; run the same command again to start a fresh capture, using `--replace-existing` to preserve and replace any partial attempt. Re-train only after every label has adequate valid recordings; the trainer refuses to save a reduced-class model.

Use one MediaPipe Holistic pipeline for all sequences in a model. To retain compatibility with the existing recordings, use the Python 3.11 `.venv` environment described above for the `afternoon` recapture and subsequent retraining. If you choose Python 3.13's newer Tasks pipeline instead, recapture all 40 labels with that same pipeline before retraining; do not mix those new recordings with older pipeline recordings without a held-out evaluation.

## Project structure

```text
SignBridge/
├── app.py
├── recognition.py
├── collect_data.py
├── train_model.py
├── hand_test.py
├── requirements.txt
├── conversation_history.csv
├── assets/signs/
├── dataset/hand_signs.csv
└── models/
    ├── hand_landmarker.task
    └── signbridge_model.pkl
```

## Troubleshooting

- **Camera won't open:** close other camera apps, check OS camera permissions, and try another camera index in `recognition.py` if needed.
- **No hand detected:** improve lighting, keep the full hand in frame, and avoid cluttered backgrounds.
- **Model load warning/error:** install the pinned dependencies from `requirements.txt` in a fresh virtual environment.
- **Speech transcription fails:** check internet connectivity, browser microphone permission, and the browser/operating-system input selection. Google's recogniser is an online service.
- **Voice output unavailable:** `pyttsx3` depends on the host operating system's speech engine. On Windows, the project uses the SAPI5 engine.

## Privacy and safety

Gesture history is written to `conversation_history.csv` on the machine running the project. The speech-to-text page uses an online Google recognition endpoint, so recorded speech is transmitted to that service for transcription. Do not record sensitive conversations without informed consent.

## Demo / fest presentation flow

1. Introduce the communication-accessibility problem and the prototype's limited scope.
2. Explain the pipeline: webcam → MediaPipe landmarks → feature normalisation → Random Forest → phrase mapping → speech + CSV history.
3. Demonstrate 3–4 gestures under consistent lighting.
4. Show the conversation log and CSV export.
5. Demonstrate speech-to-text and the visual reference page.
6. Discuss limitations honestly and outline future work: larger diverse datasets, dynamic gesture sequences, ISL expert validation, on-device speech recognition, and in-browser camera capture.

---

**Project:** SignBridge — AI-Assisted Communication  
**Type:** Student prototype / educational demonstration
