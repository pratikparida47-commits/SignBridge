# Phase 4: Same-Signer Root-Cause Diagnosis

Date: 2026-11-17
Scope: read-only diagnosis; no model, training dataset, test dataset, application feature, or label file was changed in this phase. New reports below contain derived metrics only.

## Correction to the Phase 3 test provenance

The user confirms that the 200-sequence test session was recorded by the same person who recorded the training data. The session manifest says `held_out_signer: true`, but that field was set by a command-line flag; it is not identity verification. Treat this as a separate held-out recording session from the same signer, not a cross-signer test. The previous Phase 3 report's statement that a second signer recorded it was incorrect. The original session/manifest was not edited.

## Findings

### Label inventory and recorded gesture evidence

The active and candidate label lists contain the same 40 names in the same order: `aboard`, `afternoon`, `bad`, `beside`, `book`, `byebye`, `camera`, `car`, `computer`, `correct`, `deaf`, `evening`, `family`, `food`, `friend`, `good`, `happy`, `house`, `lunch`, `man`, `marry`, `middle`, `morning`, `namaste`, `night`, `pen`, `place`, `practice`, `prisoner`, `sad`, `sorry`, `strong`, `sweet`, `teacher`, `time`, `understand`, `water`, `week`, `woman`, `you`.

The dataset has landmark vectors, not source images/video. I inspected the labels, landmark quality, hand-side slots, and movement measurements, but cannot visually confirm that the user's performed sign matches the English prompt from these files alone.

### 1. Model, scaler, and labels are compatible

- Active and candidate models accept `(30, 1662)` sequences and output 40 classes. Their scalers have 1,662 input features, and both label arrays have the same 40 sorted names as the dataset/test manifest.
- The candidate evaluator loaded the candidate bundle and all 200 test sequences without shape, finite-value, frame-count, class-order, or hand-quality errors.
- SHA-256 checks from Phase 3 show the active model/scaler/labels still match the verified backup. The candidate and active models are separate bundles.
- Conclusion: a model/scaler/class-index mismatch is not supported by the evidence.

### 2. Training and test feature extraction functions agree after float32 conversion

The training collector and runtime extractor both emit pose (132), face (1,404), left hand (63), right hand (63), in that order, total 1,662 values. A source-level comparison using identical synthetic landmarks produced equal arrays after float32 conversion. The training extractor returns float64; the training loader casts to float32, while runtime/test extraction is already float32. That precision difference is removed before the model sees the training data.

The extraction arithmetic itself therefore does not explain a 4.5% result. There is still no per-recording extractor/version metadata for the older dataset, so exact historical camera/model versions cannot be proved from the arrays.

### 3. Data quality and session distribution differ materially, even for the same signer

The training loader accepts a sequence if at least 15 of 30 frames contain hand landmarks. The independent-session collector records only frames where a hand is detected. Thus every test frame has a hand, but valid older training sequences can contain up to 15 hand-missing frames. Across the 40 labels, examples include `lunch` with 16.0% missing-hand frames, `man` 16.2%, `pen` 11.6%, and `aboard` 11.2%; the held-out session has 0% missing-hand frames for these labels.

Face landmarks occupy 1,404/1,662 features (84.5%). They are not used in the sequence-eligibility rule. In training, face landmarks are all-zero for 23.3% of `teacher` frames, 21.9% of `evening`, and 20.3% of `lunch`. In the held-out session these three labels have 0% face-missing frames. The opposite mismatch appears for `morning` (0% training, 20.0% test). This is a confirmed class-conditional quality mismatch; it may reflect framing, occlusion, or landmark tracking, but saved data do not identify which.

Left/right hand slots also differ for several same-signer classes. For example, `lunch` training has 397 right-only, 12 left-only, 95 two-hand, and 96 no-hand frames; its test set has 8 right-only, 3 left-only, 139 two-hand, and 0 no-hand frames. `evening` training has 366 left-only, 162 right-only, 258 two-hand, and 54 no-hand frames; test is two-hand in all 150 frames. These counts do not prove a handedness bug; the recording view contains no raw video or orientation metadata to distinguish a changed gesture, framing, or landmark-side assignment.

### 4. Namaste overprediction is high-confidence for the candidate

On the same 200 sequences:

| Model | Accuracy | Balanced accuracy | Macro precision | Macro recall | Macro F1 | Predicted `namaste` | Mean confidence on those predictions |
|---|---:|---:|---:|---:|---:|---:|---:|
| Active model | 4.50% | 4.50% | 3.65% | 4.50% | 2.50% | 68 | 45.2% |
| Candidate | 4.50% | 4.50% | 2.88% | 4.50% | 2.43% | 120 | 66.9% |

The candidate correctly labels only 5 of its 120 `namaste` predictions (4.17% precision). Its mean top-one margin on those predictions is 46.8 percentage points, so the problem is not just near-tie uncertainty. The active model also fails on this session, but predicts `namaste` less often. The candidate increased this bias without improving accuracy.

For candidate `afternoon`, all 5 test sequences were called `namaste` (4) or `understand` (1); `evening` was `namaste` (3) or `understand` (2); `lunch` was `namaste` (4) or `night` (1); `teacher` was `lunch` (2), `namaste` (1), or `you` (2). Each has 0/5 correct.

### 5. Static and movement-based behavior is measurable but not semantically verifiable here

The model is an LSTM over 30 ordered frames, so it receives temporal features. Training and test collections both skip frames without detected hands when collecting new sequences, but the existing training arrays contain missing-hand frames and no timestamps or source frame rate. This changes the effective motion sequence and temporal spacing. For the same label, measured average hand-frame displacement differs: `lunch` is 0.0362 in training vs 0.0127 in test; `evening` 0.0152 vs 0.0088; `teacher` 0.0113 vs 0.0089; `afternoon` 0.0045 vs 0.0051. These are sequence-motion measurements, not proof that the recorded sign is correct.

The datasets store landmark vectors only; no source webcam images/videos were saved. Therefore I cannot visually verify that a recorded gesture actually means its folder label, nor distinguish a static/transitioning sign from an incorrect performance. The English labels alone are not sufficient ground truth. ISLRTC's dictionary explicitly distinguishes synonyms, homonyms, and multiple sign entries; each word's intended concept must be reviewed against the appropriate reference.

## Root-cause assessment

The evidence rules out a simple model/scaler/label-order mismatch and rules out the extractor's feature ordering or float precision as the main cause. The confirmed technical defect is **training/test sequence-quality and temporal-distribution inconsistency**, combined with absolute image-coordinate features and a large face block that can encode camera/framing/tracker differences. A strong likely contributor is **unverified label-to-gesture consistency across recording sessions**. Since raw frames were not retained, I cannot prove whether mislabeled/differently performed gestures, camera framing, or historical landmark tracking is dominant. I will not claim a more specific cause without reviewing actual sign footage with the signer and an ISL-fluent reviewer.

## Proposed corrections (not applied)

1. Re-review the 40 label meanings and the actual signs with an ISL-fluent reviewer, using an exact dictionary entry/sense for each. Capture review footage only with the signer's consent; preserve existing landmark datasets.
2. Use one shared, versioned extractor and record its version, MediaPipe API/model, camera orientation, signer/session, and sampling policy in each new session manifest.
3. Make training/validation/test use the same 30-frame sampling and hand/face quality policy. Do not quietly retain missing-hand frames in training while filtering them from testing. Assess face/pose/hand feature ablations and hand-centric/body-relative normalization before selecting a feature set; retain face cues only if evidence supports them.
4. Add verified training sessions from multiple signers and sessions, then split by signer/session. Do not use the already-reviewed 200 samples to tune or train if it is to remain a test set.
5. Train a new candidate in a unique output folder only after all 40 verified classes have sufficient clean data. Evaluate once on a new, unused signer/session. Compare it against the active model using the same test set and predeclared metrics. Promote nothing automatically.
6. Verify static and movement-based classes from source videos; sample full motion consistently across time rather than compressing gaps caused by missed detections.

## Evidence artifacts

- `reports/manual_independent_eval_20261117_210511/` — candidate metrics, confusion matrix, and per-class metrics from the same-signer held-out session.
- `reports/manual_active_vs_candidate_20261117_212812/` — active vs candidate metrics, both confusion matrices, and per-word accuracy/precision/recall/F1 on that same session.
- `reports/phase4_same_signer_diagnosis_20261117_213128/` — per-sequence predictions, confidence, margins, true-label probability, and per-class confidence summaries for active and candidate models.
- `reports/phase4_landmark_diagnostic_20261117_213306/train_vs_test_landmark_quality_motion.csv` — per-word face/hand missingness, left/right slot counts, and motion measurements across training and held-out session.

No model, label, training sample, test sample, application feature, or backup was modified in this diagnosis phase. The `held_out_signer` value in the old test manifest remains uncorrected pending the user's direction; the analysis above uses the user's explicit correction that the signer was the same.


