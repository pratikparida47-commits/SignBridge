# SignBridge Phase 2 report

Date: 2026-11-17

## Backup

A verified copy is at `C:\Projects\SignBridge-laptop-repaired-final\SignBridge-verified-backup_20261117_192412`. Robocopy reported 50,415 files copied, 0 failed, and 0 mismatched (about 1.135 GB). It contains project code, datasets, models, assets, logs, and documentation. Only `.venv`, `.venv-1`, and Python `__pycache__` directories were excluded.

An earlier PowerShell copy attempt stopped on an unavailable path inside `.venv`; its partial folder is `SignBridge-backup_20261117_192039`. Use the verified backup above.

## Dataset audit

### Alphabet photos

`ISL custom Data/` contains 14,347 JPG photographs across 26 folders, A through Z. Counts range from 546 to 561 images per letter. `train_alphabet_model.py` reads these images to train an alphabet candidate; `alphabet_test.py` separately loads an alphabet model. The main Streamlit app and its active 8-class/40-word recognizers do not load this photo dataset. These alphabet photos are not 40-word sign references.

### 40-word landmark data

`word_model/manual_dataset/` contains 40 label folders, 30 sequence folders per label, and 30 `.npy` frames per sequence. Every audited array has shape `(1662,)` with finite values. Features are pose (132), face (1404), left hand (63), and right hand (63), concatenated in that order.

The manual trainer's quality rule requires a hand in at least 15 of 30 frames. Eligible sequences by label:

| Label | Eligible sequences | Label | Eligible sequences |
|---|---:|---|---:|
| aboard | 26 | afternoon | 0 |
| bad | 30 | beside | 30 |
| book | 30 | byebye | 30 |
| camera | 30 | car | 30 |
| computer | 29 | correct | 30 |
| deaf | 30 | evening | 28 |
| family | 30 | food | 30 |
| friend | 30 | good | 30 |
| happy | 25 | house | 30 |
| lunch | 20 | man | 20 |
| marry | 30 | middle | 30 |
| morning | 30 | namaste | 30 |
| night | 30 | pen | 17 |
| place | 30 | practice | 30 |
| prisoner | 30 | sad | 30 |
| sorry | 30 | strong | 30 |
| sweet | 30 | teacher | 23 |
| time | 30 | understand | 28 |
| water | 30 | week | 30 |
| woman | 27 | you | 26 |

All 900 `afternoon` frames have zero hand landmarks. They were preserved. The collector now has `--append`, which will create new numbered sequences after the current ones and leave these originals in place. A camera-backed capture still has to be run on the laptop.

## Model audit and evaluation

The app previously requested `manual_model/signbridge_manual_40.keras`, which is not present. The manual-specific bundle on disk is `signbridge_manual_40_new.keras`, `manual_scaler.pkl`, and `manual_labels.json`; these files were written together and have the same recorded timestamp. The model shape is `(None, 30, 1662) -> (None, 40)`, the scaler expects 1,662 features, and the 40 labels exactly match the sorted dataset directories. The recognizer and manual live-test tool now select this bundle and the recognizer rejects a label/dataset order mismatch.

The 40-class trainer was not run because it correctly refuses to train while `afternoon` has no usable sequences. No model or scaler binary was replaced.

A read-only diagnostic was run against the existing manual-specific model using the per-class chronological tail (ceil 20% of eligible sequences, 15+ hand-present frames per sequence). It scored **87.17% accuracy / 86.54% balanced accuracy on 226 sequences from 39 classes**. `afternoon` had no test examples. `evening` and `teacher` were sometimes predicted as `afternoon`; `lunch` and `teacher` had weak recall. Training provenance for the existing model is not recorded, so some diagnostic sequences may have been used during its original training. This is not a clean independent test and is not a promotion result.

Artifacts are in `reports/phase2_manual_model_evaluation_20261117/`: `confusion_matrix.csv`, `per_class_metrics.csv`, and `summary.txt`.

The trainer now writes future candidates to unique timestamped subfolders under `manual_model/retrained/`, and saves its chronological holdout confusion matrix, accuracy, balanced accuracy, and per-class metrics. It continues to refuse reduced-class models and does not update the bundle used by the app.

## Reference gallery

The supplied `word_model/40_ISL_Signs_Chart.jpg` is a computer-drawn rendering of landmark arrays, not a verified sign-language reference. The three existing assets (`hello`, `stop`, `thank_you`) belong to the small static gesture demo and do not cover the 40-word vocabulary. The gallery now lists all 40 manual labels; **all 40 local word-reference images still need to be supplied and verified**. The 14,347 alphabet photographs are not used as substitutes.

The official [ISLRTC dictionary](https://divyangjan.depwd.gov.in/islrtc/) is linked from every gallery card. ISLRTC describes this dictionary as video-based and permits technology-development use with acknowledgement and no resale/profiteering; each target word and sense still needs review before a local image is added. See the [ISLRTC FAQ](https://islrtc.nic.in/faq/).

## Air Switch diagnostics

The active 8-class static model has 63 features and includes `OPEN_PALM`; its CSV has 800 rows, 100 per class. The action mapping calls `pyautogui.click()`. Its controller can only send actions when confidence reaches the selected threshold (65% default), the prediction remains stable for five frames, cooldown has expired, and the Streamlit permission checkbox was enabled. Each click is consumed until the gesture changes or the hand disappears, so holding the same palm does not repeatedly click.

The controller now logs prediction, confidence/threshold, Open Palm stability count, permission flag, cooldown remaining, and the blocking reason. Streamlit passes explicit permission to the child process. A mocked dispatch check confirmed that `OPEN_PALM` reaches the click function. A real desktop click was not sent: the UI automation could not keep the click test target isolated, and the webcam/controller could not be validated here. Run Smart Gesture Control on the laptop and use the new log lines to identify the live blocking gate.

## Preservation and checks

The WO Mic/browser WAV speech-to-text block, Hindi/English TTS paths, and all other pages were left in place. Streamlit AppTest rendered all nine pages with no app exceptions; the Text to Sign page showed 40 missing-image notices. Syntax checks passed for the edited Python files, and `load_bundle()` loaded the selected 40-class bundle successfully. Real camera, microphone, speaker, and mouse hardware behavior still needs laptop verification.

## Changed files

- `app.py` — 40-word gallery and explicit Smart Gesture permission argument.
- `smart_gesture_control.py` — Open Palm gate diagnostics and permission enforcement.
- `word_model/recognize_manual.py` — correct manual bundle selection and class-order guard.
- `word_model/live_manual_test.py` — same corrected manual model path.
- `word_model/collect_manual_signs.py` — append-only capture mode.
- `word_model/train_manual_model.py` — unique candidates and saved evaluation artifacts.
- `README.md` — dataset, bundle, and safe recapture instructions.
- `assets/signs/word_refs/README.md` — missing reference list and image verification requirements.
- `reports/phase2_manual_model_evaluation_20261117/*` — diagnostic metrics artifacts.

## Commands

Run the Streamlit app from `SignBridge-laptop-repaired`:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

After confirming the laptop camera and sign are visible, append 30 afternoon sequences while preserving the original data:

```powershell
.\.venv\Scripts\python.exe word_model\collect_manual_signs.py --word afternoon --append
```

Only after checking that all 40 labels have usable sequences, train a new candidate and review its saved evaluation outputs:

```powershell
.\.venv\Scripts\python.exe word_model\train_manual_model.py
```

Candidates and their confusion/per-class reports will be written under `word_model/manual_model/retrained/candidate_<timestamp>/`. They are not automatically promoted.
