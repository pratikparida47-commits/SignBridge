import csv
from pathlib import Path
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parent
DATASET_FILE = BASE_DIR / "dataset" / "dynamic_gestures.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_FILE = MODEL_DIR / "signbridge_dynamic_candidate.pkl"

SEQUENCE_LENGTH = 30
FEATURES_PER_FRAME = 65
TOTAL_FEATURES = SEQUENCE_LENGTH * FEATURES_PER_FRAME
EXPECTED_LABELS = {
    "WATER", "FOOD", "DRINK", "TOILET", "HUNGRY", "THIRSTY",
    "PAIN", "DOCTOR", "HOME", "WHERE", "WHAT", "GOODBYE",
}

def main():
    if not DATASET_FILE.exists():
        print("ERROR: Dynamic dataset not found!")
        return

    X = []
    y = []

    with open(DATASET_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)

        expected_features = [
            f"f{i}" for i in range(TOTAL_FEATURES)
        ]

        if reader.fieldnames is None:
            print("ERROR: Dataset is empty!")
            return

        if not all(name in reader.fieldnames for name in expected_features):
            print("ERROR: Dataset columns do not match!")
            return

        for row in reader:
            try:
                label = row["label"].strip()
                features = [
                    float(row[name])
                    for name in expected_features
                ]

                if label and len(features) == TOTAL_FEATURES:
                    X.append(features)
                    y.append(label)

            except (ValueError, KeyError, TypeError):
                print("Skipping an invalid row.")

    if len(X) == 0:
        print("No gesture samples found.")
        print("Collect gesture samples before training.")
        return

    class_counts = {
        label: y.count(label)
        for label in sorted(set(y))
    }

    missing_labels = sorted(EXPECTED_LABELS - set(class_counts))
    unknown_labels = sorted(set(class_counts) - EXPECTED_LABELS)
    if missing_labels or unknown_labels:
        print("Refusing to train a reduced or mismatched dynamic model.")
        print("Missing labels:", missing_labels)
        print("Unknown labels:", unknown_labels)
        return

    print("\nGesture sample counts:")
    for label, count in class_counts.items():
        print(f"{label}: {count}")

    if len(class_counts) < 2:
        print("\nAt least 2 gesture classes are required.")
        return

    if min(class_counts.values()) < 2:
        print("\nEach gesture needs at least 2 samples.")
        return

    # Use stratified splitting only when each class
    # has enough samples for the test set.
    test_count = max(
        len(class_counts),
        round(len(X) * 0.2)
    )

    if test_count >= len(X):
        print("Not enough samples for a separate test set.")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_count,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    print("\nTraining dynamic gesture model...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print(f"\nTest accuracy: {accuracy * 100:.2f}%")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    print("\nConfusion Matrix:")
    print(confusion_matrix(
        y_test,
        predictions,
        labels=model.classes_
    ))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)

    print("\nDYNAMIC MODEL SAVED SUCCESSFULLY!")
    print(f"Location: {MODEL_FILE}")


if __name__ == "__main__":
    main()
