# SignBridge — Fest Demo Notes

## 45-second opening

“Communication is essential, but people who use gestures can face barriers when others do not understand them. SignBridge is a small AI-assisted prototype that recognises eight custom static hand poses and converts them into short text and spoken messages. It also includes speech-to-text and a visual reference page. Our goal is to demonstrate how computer vision and machine learning can support more inclusive interactions.”

## Explain the pipeline

1. **Capture:** OpenCV reads a webcam frame.
2. **Detect:** MediaPipe identifies 21 hand landmarks.
3. **Normalise:** Landmark coordinates are made relative to the wrist and hand scale.
4. **Classify:** A trained Random Forest predicts one of eight pose labels.
5. **Communicate:** The label maps to a phrase, which is displayed and spoken.
6. **Record:** The phrase, gesture and confidence are appended to the CSV history.

## Suggested live demo

- If the static recognizer passes the manual live checks on the demo laptop, show `OPEN_PALM` → “Hello”, `THUMBS_UP` → “Thank you”, and `FIST` → “Stop”.
- Open Conversation History and download the CSV.
- Show the Speech to Text page and one of the supplied sign-reference images.

Keep the hand centred, well lit and visible. Test the webcam, intended gestures, microphone and speakers before the presentation. Camera startup is not evidence of correct gesture predictions. If any intended gesture is unstable, explain the pipeline using the included dataset and show the app's other pages; do not claim a live recognition result that did not occur.

## Common viva questions

**1. What problem does SignBridge address?**  
It demonstrates a way to map a limited set of hand poses into text and voice, helping illustrate assistive communication technology.

**2. Why MediaPipe?**  
It provides hand landmarks, allowing the classifier to work with compact geometric features instead of raw image pixels.

**3. Why Random Forest?**  
It is a practical supervised-learning baseline for tabular landmark features, supports multiple classes, and is straightforward to train and evaluate.

**4. What are the model inputs?**  
The x, y and z coordinates of 21 hand landmarks, giving 63 numerical features after normalisation.

**5. How many samples are in the included dataset?**  
800 samples: 100 for each of the eight gesture labels.

**6. Is this a complete sign-language translator?**  
No. It recognises eight custom static poses. Full sign-language translation also needs dynamic motion, facial expression, body posture, grammar and expert-validated vocabulary.

**7. What are the main limitations?**  
A small dataset, sensitivity to camera and lighting conditions, static-pose-only vocabulary, separate local camera window, and online speech transcription.

**8. What would you improve next?**  
Collect diverse participant data, validate with sign-language users and experts, add dynamic gesture modelling, support more vocabulary, and move camera inference into an in-browser or mobile experience.


## Gesture model status (important for judging)

- The bundled Random Forest is genuinely trained on 8 classes and 800 recorded landmark rows (100 per class).
- The project now includes a 20-gesture catalogue and data-collection workflow. The other 12 labels are expansion targets, not yet trained predictions.
- Do not claim 20- or 50-class live recognition until you have collected samples, retrained the model, and tested it under varied conditions.
- Static accuracy has not been measured on a held-out live signer, so do not claim the eight gestures work reliably until they pass the manual checks on the demo laptop. Present the 20-class expansion workflow as a development milestone, not a trained vocabulary.

## 40-word sequence mode status

- A separate 40-output sequence model, scaler, and label list are present. The model/scaler/label bundle, Holistic tracker, camera startup, and a short recognition-loop smoke test passed.
- The recording set has 30 sequence folders per label, but every `afternoon` frame lacks hand landmarks. The trainer therefore refuses to create a new full 40-label candidate until that label is recaptured.
- The saved same-signer held-out evaluation scored 4.5%; `sorry` was predicted as `night` in one of five sequences and was correct in only one. Webcam launch now works in the inspected project environment, but this accuracy is not demonstration-ready. Do not present the 40-word mode as reliable.
