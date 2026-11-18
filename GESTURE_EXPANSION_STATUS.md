# SignBridge gesture expansion status

## Verified in this package

- Gesture catalogue: 20 custom static-pose labels.
- Trained classifier: 8 labels.
- Dataset: 800 rows, 100 rows per trained label, 63 landmark features.
- Collection tool: key bindings for all 20 labels.
- Training script: learns every dataset label with at least 30 samples; it no longer hard-codes the original eight classes.
- Recognition maps the model's predicted labels through the shared gesture catalogue.

## What is not yet complete

The 12 new labels are catalogue and collection targets. There are no labelled camera samples for them in the supplied dataset, so they are not currently learned by the model. To make them live-recognisable, collect at least 100 varied real samples per new class, train, and test the updated model. A 50-label expansion is architecturally possible by extending the catalogue and collector map, but needs its own dataset and evaluation.

## Fest presentation advice

The eight-class model is structurally compatible, but live gesture accuracy has not been validated. First run the manual checks on the demonstration laptop; only show intended predictions if they are stable in that test. Present the 20-label catalogue and retraining workflow as the expansion milestone. Do not describe this prototype as a complete ISL translator.

## Step 5 verification — 2026-11-18

- Model input: 63 values, in the same wrist-relative and hand-scale-normalized landmark order used by the collector.
- Model output order: `CROSSED_FINGERS`, `FIST`, `I_LOVE_YOU`, `OPEN_PALM`, `POINT_UP`, `THUMBS_DOWN`, `THUMBS_UP`, `VICTORY`. Runtime now validates this exact vocabulary and input size before opening the camera.
- Runtime confidence threshold (50%) and two consecutive stable frames are unchanged. The runtime now passes named features in the model's fitted column order, avoiding scikit-learn's missing-feature-name warning.
- Model load and camera startup are software/hardware pipeline checks only. No live gesture-accuracy result is claimed. Test all eight labels manually on the demo laptop before relying on them.
