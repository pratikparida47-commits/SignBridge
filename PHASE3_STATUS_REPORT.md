# SignBridge Phase 3 status

Date: 2026-11-17
Project: `SignBridge-laptop-repaired`

## Preservation

- The verified backup remains at `C:\Projects\SignBridge-laptop-repaired-final\SignBridge-verified-backup_20261117_192412` (50,415 files copied; 0 failed and 0 mismatched; `.venv`, `.venv-1`, and `__pycache__` excluded).
- Existing training data and active models were not deleted or replaced.
- SHA-256 checks confirm the active manual model, scaler, and labels exactly match the verified backup.
- Original afternoon folders `0` through `29` remain. The webcam append added folders `30` through `59` (900 new frame arrays), without changing the original 900 frames.
- Candidate bundle created separately at `word_model/manual_model/retrained/candidate_20261117_200707/`. The app's active bundle remains unchanged.

## Dataset and candidate

- Alphabet/photo dataset: 14,347 JPGs, A-Z, used by the alphabet training path only; it is not the 40-word landmark dataset and is not loaded by the active manual word model.
- Manual 40-word dataset: 40 label folders, all 40 meet the trainer's structural and hand-presence rule after afternoon recapture. There are 1,142 qualifying sequences in total. A qualifying sequence has 30 finite `(1662,)` frames and at least 15 frames with a hand landmark.
- Candidate training completed only after all 40 classes qualified. The candidate's built-in chronological split is not an independent signer test: 797 fit sequences, 113 validation sequences, 232 test sequences.
- Candidate chronological holdout: 68.10% accuracy, 67.00% balanced accuracy. Per-class precision/recall/F1 and confusion matrix are alongside the candidate bundle.
- Confusion diagnosis: `afternoon` 6/6 correct; `evening` 3/6 correct, with the other 3 predicted `lunch`; `teacher` 0/5, with 4 predicted `lunch` and 1 `water`; `lunch` 0/4. This is not enough evidence to alter labels or claim the confusion is fixed.
- Candidate was not promoted. Its model, scaler, and labels were saved together in its unique folder.

## Independent signer evaluation: complete; candidate failed

The second signer completed a separate webcam session at `word_model/manual_test_sets/session_20261117_201330/`: 5 sequences for each of all 40 classes. The manifest marks it complete and held-out. All 200 sequences passed the evaluator's shape, finite-value, and hand-presence rules; none were skipped. Raw video was not saved. This test session is kept separate from `manual_dataset`.

Candidate evaluation results: **4.50% accuracy**, **4.50% balanced accuracy**, macro precision **2.88%**, macro recall **4.50%**, macro F1 **2.43%**; weighted values are the same to rounding because every class has equal support. All per-class results have support 5. The candidate predicted `namaste` 120 times out of 200. `afternoon`, `evening`, `lunch`, and `teacher` each had 0/5 correct in the independent test. All five `afternoon` examples were classified as `namaste` (4) or `understand` (1); `evening` as `namaste` (3) or `understand` (2); `lunch` as `namaste` (4) or `night` (1); and `teacher` as `lunch` (2), `namaste` (1), or `you` (2). This exposes a severe cross-signer generalization failure, despite the candidate's 68.1% internal chronological score. The data do not establish whether the main cause is signer/domain shift, sign/label mismatch, or feature distribution; more diagnosis and verified references are needed.

The candidate **failed evaluation and was not promoted**. The independent report is `reports/manual_independent_eval_20261117_210511/`: `evaluation_summary.json`, `confusion_matrix.csv`, and `per_class_metrics.csv`. Preserve this test set as a one-time independent result; using it to tune a successor would make it a development set, so a future model needs a new unseen test signer/session.
## Reference gallery

The Streamlit gallery has entries for all 40 words, but local verified word-reference images are still missing for all 40. Existing `ISL custom Data/` photos are alphabet samples, and the drawn landmark chart is not a verified ISL word reference. The official ISLRTC dictionary is video-based; use its entry to verify the exact word and meaning before adding an image. No signs or images were invented or substituted.

## Live-device checks and safety

- Open Palm diagnostics remain in `smart_gesture_control.py`. Added the opt-in `--open-palm-click-only` safety mode. The normal gesture mapping remains unchanged; this test mode allows only Open Palm clicks and ignores the other action gestures. The help output and Python syntax were checked. A real webcam recognition/click was not run: the computer-use surface could not reliably select or isolate the Calculator window, so no desktop click was sent.
- To guide a safe local test: restore Calculator and place it at the lower-right of the screen. Open Palm-only mode puts its 480x360 preview at the upper-left. Click a harmless Calculator digit such as `1`, leave the pointer over that digit, then start the command below from PowerShell. Show an open palm steadily. A successful click should append another `1` to the Calculator display. Press `Q` in the controller preview to stop. The actual test remains pending.

```powershell
.\.venv\Scripts\python.exe smart_gesture_control.py --permission-granted --open-palm-click-only --confidence-limit 65 --cooldown 1.5
```

- English SAPI playback test completed via installed Microsoft David Desktop voice. The software call returned successfully, but I could not independently confirm audible output at the speakers. No Hindi voice matched the app's installed-voice selection rule, so Hindi TTS is unavailable on this Windows installation until a Hindi system voice is installed. The project code was not changed for TTS.
- WO Mic client was not running during this session. The Streamlit speech-to-text code was preserved; live recording/transcription was not verified.
- No live feature is claimed to pass without its physical webcam, microphone, or speaker check.
## Files added or changed for Phase 3

- `word_model/collect_manual_test_set.py` — separate held-out webcam capture; landmarks only.
- `word_model/evaluate_manual_candidate.py` — independent test gate and report generation.
- `smart_gesture_control.py` — added opt-in Open Palm-only click test mode; all other gestures remain unchanged.
- `word_model/manual_dataset/afternoon/30` through `59` — appended landmark recordings; earlier recordings retained.
- `word_model/manual_model/retrained/candidate_20261117_200707/*` — candidate bundle and internal holdout reports; not active.
- `word_model/manual_test_sets/session_20261117_201330/` — complete separate held-out session, 5 sequences per class.
- `reports/manual_independent_eval_20261117_210511/*` — independent accuracy, precision, recall, F1, confusion matrix, and per-class results.
- `PHASE3_STATUS_REPORT.md` — this status record.

## App launch

From the project folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```







