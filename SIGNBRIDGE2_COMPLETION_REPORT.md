# SignBridge 2.0 Completion Report

Date: 2026-11-18

## Summary

SignBridge 2.0 was implemented directly in the existing project. Existing static recognition, 40-word recognition, Smart Gesture Control, speech-to-text, TTS, geolocation/SOS, history, gallery, and launcher behavior were preserved. No datasets, recordings, reference images, labels, or trained models were replaced or retrained.

## New or upgraded modules

- Navigation for SignBridge 2.0 dashboard modules.
- Live recognition aliases that reuse the existing static and 40-word engines.
- Searchable dictionary cards for the 40 existing model labels. Missing references are clearly unavailable; no unverified image is presented as ISL.
- ISL alphabet lesson checklist with an official ISLRTC link. It does not claim that the existing alphabet model is live-validated.
- Word Communication Board with add/remove, undo by removal, clear, copy/download, common phrases, and recognition-history additions.
- Browser Speech Synthesis controls for English, Hindi, Odia selection, speech speed, repeat, and stop. Playback depends on browser/device voices.
- Live Location page with coordinate validation, reported accuracy, app-receipt time, Google Maps, and an OpenStreetMap embed. The installed geolocation component returns no GPS sample timestamp or explicit permission error code.
- Model Evaluation page with same-signer per-class metrics and confusion matrices, plus a separate chronological sequence-folder candidate result. Static and dynamic availability is derived from local data.
- Selectable OpenCV camera indices 0–3 for static recognition, 40-word recognition, and Smart Gesture Control.
- Smart Gesture's safer default action profile is Open Palm click-only; the all-keyboard-action profile still requires explicit permission.
- Dictionary search spans all 40 model labels and the eight custom static poses. Static features are labeled custom and unverified as ISL.
- Communication board supports adding recent recognition-history messages, undoing the last addition, removing individual items, clearing, copying, downloading, and transferring the sentence to browser speech.
- Updated SignBridge 2.0 branding and footer.

## Verified recognition status

- Static model: 8 classes and 800 dataset rows. Structural model checks passed. Live accuracy is not validated.
- 40-word model: 40 labels preserved in the exact existing order. Active bundle loaded with 40 outputs and 1,662 features. Active accuracy on a separate recording session from the same signer was **4.5% on 200 sequences (5 per word)**; balanced accuracy 4.5%, macro F1 2.50%.
- The unpromoted candidate scored **68.10% accuracy / 67.00% balanced accuracy** on a chronological sequence-folder split from its training dataset. That is not an independent signer/session result, and it did not generalize to the separate same-signer session (4.5%); it remains unpromoted.
- The source diagnosis confirms training/test differences in hand and face landmark missingness, left/right hand-slot distribution, and temporal motion. The code-level feature order and extraction arithmetic match after float32 conversion. Saved recordings have no source video or historical extractor/session metadata, so semantic label errors or capture/version contributions cannot be isolated as the single cause. No model or scaler/class mapping mismatch was found.
- Dynamic training remains blocked: `dataset/dynamic_gestures.csv` has 10 rows, all for `WATER`; 11 required labels are missing.
- A GitHub repository search for FDMSE-ISL returned no matching repositories; the official ISLRTC URL and dataset metadata endpoints could not be retrieved in this environment. No dataset was downloaded because access/license could not be verified. No model training occurred.

## Tests passed

- Python compilation passed for `app.py`, `signbridge_2.py`, `recognition.py`, `gesture_catalog.py`, `smart_gesture_control.py`, and `word_model/recognize_manual.py`.
- The existing collector and live 40-word extractor were compared; pose/face/left-hand/right-hand feature ordering and normalized extraction values match for equivalent landmark inputs.
- `pip check` passed: no broken requirements found.
- SignBridge 2.0 vocabulary smoke test passed: 8 static entries, 40 preserved word labels, 48 truthfully classified entries.
- Streamlit AppTest passed all 17 page routes, including Live ISL Recognition, ISL Digital Dictionary, and Word Communication Board aliases.
- Sentence builder AppTest passed for add, undo, and remove. The 40-word practice selector contains the exact 40 labels in preserved order.
- Active manual bundle loaded successfully: model input `(30, 1662)`, 40 outputs, scaler `n_features_in_ = 1662`, and exact label order. A mocked recognizer test confirmed an invalid practice label is rejected before camera access and camera index 3 is passed through for a valid target.
- The static model launched with a mocked camera returning no frame at index 3; no prediction, history write, or mouse/keyboard action occurred.
- Dynamic trainer validation refused to train and listed the 11 missing labels (`DOCTOR`, `DRINK`, `FOOD`, `GOODBYE`, `HOME`, `HUNGRY`, `PAIN`, `THIRSTY`, `TOILET`, `WHAT`, `WHERE`); no dynamic model was trained or replaced.
- `run_signbridge.bat` launched the updated Streamlit instance on port 8502 because port 8501 was already occupied. The updated instance's `/_stcore/health` returned HTTP 200, and the browser opened the updated app. A pre-existing instance on port 8501 was left untouched.
- In the browser, Speaker Voice reported five available `en-IN` voices after the browser voice list loaded. No speech was played, so audible output is unverified.
- App Test ran with a real, local camera frame and a no-hand detector stub; this did not evaluate a gesture or write predictions.
- A browser automation attempt to select the off-screen Live ISL navigation option briefly launched the static recognizer unexpectedly. It was stopped immediately with the app's Stop control; the child processes exited, the sidebar returned to Recognition Stopped, and `conversation_history.csv` remained unchanged (last write 09:29:09, before the launch). No Smart Gesture action was involved.
- One initial sentence-builder test attempt clicked a disabled button before rerunning after text entry; the corrected AppTest passed. This was a test-harness sequencing issue, not an application failure.
- Geolocation, clipboard, microphone, and physical audio playback were not activated or verified.

## Completion status

### A. Fixed and tested

- Shared interpreter launch checks and camera-index argument wiring.
- Model/scaler/vocabulary compatibility checks; exact 40-word order preserved.
- Dictionary, alphabet checklist, communication board, recognition-page aliases, and all 17 Streamlit routes.
- Safer Smart Gesture defaults and existing mocked-action tests; no automated real desktop input was sent.

### B. Fixed but not hardware-tested

- Browser voice-list status refresh and language availability messaging; actual audio output still needs a physical check.
- Camera selection and recognition entry points; mocked camera tests do not establish live gesture accuracy.
- Existing location, speech-input, SOS, and stop flows remain available, but device permissions and service outcomes were not exercised.

### C. Live-tested successfully

- Updated Streamlit app startup and HTTP health response on port 8502.
- Browser page loading/navigation and voice enumeration (five `en-IN` voices reported).
- Camera index 0 previously returned a real frame in the inspection environment; a no-hand detector smoke test produced no prediction.

### D. Still failing or not validated

- The active 40-word model achieved only **4.5% accuracy** on 200 same-signer held-out-session sequences; this is not reliable live recognition.
- Static live recognition accuracy is unmeasured. No claim is made that any of the 40 words or eight static poses were correctly recognized in a live gesture test.

### E. Blocked by missing data

- Dynamic model training is blocked: the CSV contains 10 `WATER` rows and lacks 11 required labels. The 40-word data also contains unusable `afternoon` sequences with no hand landmarks.
- The existing collector appends project-native landmark rows and the trainer checks schema and full class coverage. A general external-dataset importer was not added: no source license, data format, or label/feature mapping could be verified, so importing would risk changing gesture semantics. No external dataset was imported.

### F. Requires manual confirmation

- Try each webcam index on the demonstration laptop, test all static poses and 40 practice targets, and record live results separately.
- Test browser microphone permission, actual English/Hindi/Odia speech playback, browser location permission/denial, and the SOS review/share flow.
- Test Smart Gesture only in a safe desktop context; its real mouse/keyboard actions were not performed.

## Not hardware-tested

- Live static gesture accuracy.
- Live 40-word gesture accuracy.
- Browser microphone or real Google speech recognition.
- Audible browser/SAPI5 Hindi, English or Odia output.
- Browser GPS location, permission denial, and GPS/network errors. The installed component does not return explicit permission error details or the GPS sample timestamp.
- Real webcam recognition and real mouse/keyboard dispatch.

## Acquisitions and models

No dataset or model was acquired or replaced. FDMSE-ISL was not located through the repository search, and network retrieval of the ISLRTC site and metadata services was blocked or rate-limited in this environment. Therefore no dataset/license eligibility is asserted and no resource was downloaded. The app links to ISLRTC but does not treat arbitrary external content as verified ISL references.

## Changed files

- `app.py`
- `signbridge_2.py`
- `recognition.py`
- `smart_gesture_control.py`
- `word_model/recognize_manual.py`
- `README.md`
- `SIGNBRIDGE2_COMPLETION_REPORT.md`

Earlier files changed by Step 5, including `recognition.py`, `gesture_catalog.py`, `requirements.txt`, and the diagnostic reports, remain in place.

Timestamped backup:
- `reports/signbridge2_prechange_20261118_084127`
- `reports/signbridge2_followup_prechange_20261118_090917`
- `reports/signbridge2_recognition_prechange_20261118_091200`
- `reports/signbridge2_docs_prechange_20261118_091602`

## Run

```powershell
Set-Location 'C:\Projects\SignBridge-laptop-repaired-final\SignBridge-laptop-repaired'
.\run_signbridge.bat
```

Open the URL printed by Streamlit, usually `http://localhost:8501`. If that port is occupied, Streamlit may use another port (the updated instance used `http://localhost:8502` during this validation). The app requires HTTPS or localhost for browser geolocation; no location or SOS message is sent automatically.
