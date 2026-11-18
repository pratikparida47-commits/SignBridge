import pandas as pd
import joblib

from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix
)
from gesture_catalog import GESTURE_MESSAGES

# ==========================================
# SIGNBRIDGE - MODEL TRAINING
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

CSV_FILE = BASE_DIR / "dataset" / "hand_signs.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_FILE = MODEL_DIR / "signbridge_static_candidate.pkl"
MIN_SAMPLES_PER_CLASS = 30

# ==========================================
# LOAD DATASET
# ==========================================

if not CSV_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {CSV_FILE}")

data = pd.read_csv(CSV_FILE)

print("\n================================")
print("SIGNBRIDGE MODEL TRAINING")
print("================================")

if "label" not in data.columns:
    raise ValueError("Dataset must contain a 'label' column.")

data["label"] = data["label"].astype(str).str.strip()

print("\nTotal samples:", len(data))

available_labels = set(data["label"])
unknown_labels = sorted(available_labels - set(GESTURE_MESSAGES))
if unknown_labels:
    raise ValueError(f"Labels are missing from gesture_catalog.py: {unknown_labels}")

EXPECTED_GESTURES = [
    label for label in GESTURE_MESSAGES if label in available_labels
]
if len(EXPECTED_GESTURES) < 2:
    raise ValueError("At least two gesture classes are required for training.")

# ==========================================
# CHECK GESTURE COUNTS
# ==========================================

counts = data["label"].value_counts()

print("\nGESTURE SAMPLE COUNTS:")

for gesture in EXPECTED_GESTURES:
    count = int(counts.get(gesture, 0))
    print(f"{gesture}: {count}")

    if count < MIN_SAMPLES_PER_CLASS:
        raise ValueError(
            f"{gesture} has {count} samples; collect at least "
            f"{MIN_SAMPLES_PER_CLASS} before training."
        )

unexpected = sorted(set(data["label"]) - set(EXPECTED_GESTURES))

if unexpected:
    raise ValueError(f"Unexpected gesture labels: {unexpected}")

# ==========================================
# PREPARE FEATURES
# ==========================================

X = data.drop("label", axis=1)
y = data["label"]

X = X.apply(pd.to_numeric, errors="coerce")

if X.isnull().any().any():
    raise ValueError("Dataset contains missing or invalid values.")

if X.shape[1] != 63:
    raise ValueError(f"Expected 63 features, found {X.shape[1]}.")

# ==========================================
# SPLIT DATA
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# ==========================================
# CREATE AND TRAIN MODEL
# ==========================================

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)

print("\nTraining AI model...")

model.fit(X_train, y_train)

# ==========================================
# MODEL EVALUATION
# ==========================================

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
balanced_accuracy = balanced_accuracy_score(y_test, predictions)

print("\n================================")
print("MODEL PERFORMANCE")
print("================================")

print(f"Accuracy:          {accuracy * 100:.2f}%")
print(f"Balanced Accuracy: {balanced_accuracy * 100:.2f}%")

print("\nCLASSIFICATION REPORT:")

print(
    classification_report(
        y_test,
        predictions,
        labels=EXPECTED_GESTURES,
        zero_division=0,
        digits=3
    )
)

print("\nCONFUSION MATRIX:")

matrix = confusion_matrix(
    y_test,
    predictions,
    labels=EXPECTED_GESTURES
)

print(
    pd.DataFrame(
        matrix,
        index=EXPECTED_GESTURES,
        columns=EXPECTED_GESTURES
    )
)

# ==========================================
# SAVE MODEL
# ==========================================

MODEL_DIR.mkdir(parents=True, exist_ok=True)

joblib.dump(model, MODEL_FILE)

print("\n================================")
print("STATIC CANDIDATE MODEL SAVED SUCCESSFULLY!")
print("================================")

print("Location:", MODEL_FILE)
print("Recognisable gestures:", len(model.classes_))
print("The active signbridge_model.pkl was not overwritten.")
