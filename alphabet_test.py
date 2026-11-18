import cv2
import numpy as np
import tensorflow as tf
from pathlib import Path

# -----------------------------
# PROJECT PATHS
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "isl_alphabet_model.keras"

IMAGE_SIZE = (128, 128)
CONFIDENCE_LIMIT = 70

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


# -----------------------------
# LOAD MODEL
# -----------------------------

print("Loading SignBridge A-Z model...")

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )

model = tf.keras.models.load_model(MODEL_PATH)

print("A-Z model loaded successfully!")


# -----------------------------
# START WEBCAM
# -----------------------------

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Webcam not available.")
    exit()

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("Webcam started!")
print("Keep your hand inside the blue square.")
print("Press Q to quit.")


# -----------------------------
# REAL-TIME PREDICTION
# -----------------------------

while True:

    success, frame = camera.read()

    if not success:
        print("Unable to read webcam frame.")
        break

    # Mirror the camera
    frame = cv2.flip(frame, 1)

    height, width = frame.shape[:2]

    # Create square region
    size = min(height, width)

    x1 = (width - size) // 2
    y1 = (height - size) // 2

    x2 = x1 + size
    y2 = y1 + size

    # Crop central region
    hand_region = frame[y1:y2, x1:x2]

    # Resize image
    resized = cv2.resize(
        hand_region,
        IMAGE_SIZE,
        interpolation=cv2.INTER_AREA
    )

    # Convert BGR to RGB because training images
    # were loaded as RGB using Keras
    resized = cv2.cvtColor(
        resized,
        cv2.COLOR_BGR2RGB
    )

    # Normalize image
    image_array = resized.astype("float32") / 255.0

    image_array = np.expand_dims(
        image_array,
        axis=0
    )

    # Predict letter
    predictions = model.predict(
        image_array,
        verbose=0
    )[0]

    index = int(np.argmax(predictions))

    confidence = float(predictions[index]) * 100

    predicted_letter = LETTERS[index]

    # Display prediction
    if confidence >= CONFIDENCE_LIMIT:
        display_text = (
            f"Letter: {predicted_letter} "
            f"({confidence:.1f}%)"
        )
        color = (0, 255, 0)

    else:
        display_text = "Show a clear hand sign"
        color = (0, 0, 255)

    # Draw blue square
    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (255, 0, 0),
        2
    )

    # Display result
    cv2.putText(
        frame,
        display_text,
        (20, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        color,
        2
    )

    cv2.putText(
        frame,
        "SignBridge A-Z Recognition | Press Q to exit",
        (20, height - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "SignBridge - A-Z Alphabet Recognition",
        frame
    )

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# -----------------------------
# RELEASE CAMERA
# -----------------------------

camera.release()
cv2.destroyAllWindows()

print("A-Z testing closed.")