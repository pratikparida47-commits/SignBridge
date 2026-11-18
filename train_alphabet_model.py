import tensorflow as tf
from tensorflow.keras import layers, models
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import numpy as np
import joblib

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "ISL custom Data"
MODEL_DIR = BASE_DIR / "models" / "candidates" / "isl_alphabet"

IMAGE_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 12

print("Loading alphabet images...")

images = []
labels = []

for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    folder = DATA_DIR / letter

    if not folder.exists():
        continue

    files = list(folder.glob("*"))

    count = 0

    for path in files:
        if path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        try:
            image = tf.keras.utils.load_img(
                path,
                target_size=IMAGE_SIZE
            )

            image = tf.keras.utils.img_to_array(image)
            images.append(image)
            labels.append(letter)
            count += 1

        except Exception as error:
            print("Skipped:", path.name, error)

    print(f"{letter}: {count} images loaded")

if len(images) == 0:
    raise RuntimeError("No images found!")

missing_letters = sorted(set("ABCDEFGHIJKLMNOPQRSTUVWXYZ") - set(labels))
if missing_letters:
    raise ValueError(
        "Refusing to train a reduced alphabet model. These letters have no "
        f"usable samples: {missing_letters}"
    )

X = np.array(images, dtype="float32") / 255.0
labels = np.array(labels)

encoder = LabelEncoder()
y = encoder.fit_transform(labels)

print("\nTotal images:", len(X))
print("Letters found:", list(encoder.classes_))

# Split dataset while keeping class proportions
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

model = models.Sequential([
    layers.Input(shape=(128, 128, 3)),

    layers.Conv2D(32, (3, 3), activation="relu"),
    layers.MaxPooling2D(),

    layers.Conv2D(64, (3, 3), activation="relu"),
    layers.MaxPooling2D(),

    layers.Conv2D(128, (3, 3), activation="relu"),
    layers.MaxPooling2D(),

    layers.Flatten(),
    layers.Dense(128, activation="relu"),
    layers.Dropout(0.4),

    layers.Dense(len(encoder.classes_), activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

print("\nStarting alphabet model training...")

model.fit(
    X_train,
    y_train,
    validation_split=0.15,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE
)

loss, accuracy = model.evaluate(X_test, y_test)

print("\nTest accuracy:", round(accuracy * 100, 2), "%")

predictions = np.argmax(
    model.predict(X_test),
    axis=1
)

print("\nClassification report:")
print(classification_report(
    y_test,
    predictions,
    labels=np.arange(len(encoder.classes_)),
    target_names=encoder.classes_,
    zero_division=0
))

MODEL_DIR.mkdir(parents=True, exist_ok=True)

model.save(MODEL_DIR / "isl_alphabet_model.keras")
joblib.dump(
    encoder,
    MODEL_DIR / "isl_alphabet_labels.pkl"
)

print("\nALPHABET CANDIDATE SAVED SUCCESSFULLY!")
print("Model:", MODEL_DIR / "isl_alphabet_model.keras")
