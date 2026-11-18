"""Truthful SignBridge 2.0 vocabulary and evaluation helpers."""

from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent

STATIC_GESTURES = (
    ("OPEN_PALM", "Hello"),
    ("FIST", "Stop"),
    ("THUMBS_UP", "Thank you"),
    ("THUMBS_DOWN", "No"),
    ("POINT_UP", "Help"),
    ("VICTORY", "Yes"),
    ("CROSSED_FINGERS", "Please"),
    ("I_LOVE_YOU", "I love you"),
)

WORD_LABELS = (
    "aboard", "afternoon", "bad", "beside", "book", "byebye",
    "camera", "car", "computer", "correct", "deaf", "evening",
    "family", "food", "friend", "good", "happy", "house",
    "lunch", "man", "marry", "middle", "morning", "namaste",
    "night", "pen", "place", "practice", "prisoner", "sad",
    "sorry", "strong", "sweet", "teacher", "time", "understand",
    "water", "week", "woman", "you",
)

ISL_ALPHABET = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def load_manual_labels():
    path = BASE_DIR / "word_model" / "manual_model" / "manual_labels.json"
    if not path.is_file():
        raise FileNotFoundError(f"40-word label file was not found: {path}")
    labels = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(labels, list) or tuple(labels) != WORD_LABELS:
        raise ValueError("The active 40-word labels do not match the verified vocabulary and order.")
    return labels


def dictionary_entries():
    entries = []
    for label in load_manual_labels():
        entries.append({
            "word": label,
            "meaning": label.replace("_", " ").title(),
            "category": "40-word sequence vocabulary",
            "reference_status": "Unavailable - verified reference not supplied",
            "source": "Manual model label; not presented as verified ISL",
            "recognition_status": "Model present; live accuracy unverified",
        })
    for gesture, meaning in STATIC_GESTURES:
        entries.append({
            "word": meaning,
            "meaning": meaning,
            "category": "Trained static pose",
            "reference_status": "Custom pose - not presented as verified ISL",
            "source": "Bundled SignBridge static model",
            "recognition_status": "Structured validation passed; live accuracy unverified",
        })
    return entries
