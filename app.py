
import streamlit as st
import subprocess
import sys
import importlib.util
import math
import pandas as pd
import speech_recognition as sr
import io
import json
import re
from datetime import datetime
import hashlib
from streamlit import iframe as component_html

from signbridge_2 import (
    ISL_ALPHABET,
    WORD_LABELS,
    dictionary_entries,
)
from web_safety import safe_script_json

from pathlib import Path
from streamlit_mic_recorder import mic_recorder
from streamlit_geolocation import streamlit_geolocation


# =========================================================
# SIGNBRIDGE | PREMIUM ACCESSIBILITY PLATFORM
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

HISTORY_FILE = BASE_DIR / "conversation_history.csv"
CONTACT_FILE = BASE_DIR / "emergency_contact.json"
RECOGNITION_FILE = BASE_DIR / "recognition.py"
MANUAL_RECOGNITION_FILE = BASE_DIR / "word_model" / "recognize_manual.py"
MANUAL_LABELS_FILE = BASE_DIR / "word_model" / "manual_model" / "manual_labels.json"
MANUAL_REFERENCE_DIR = BASE_DIR / "assets" / "signs" / "word_refs"
SMART_GESTURE_FILE = BASE_DIR / "smart_gesture_control.py"
SIGNS_DIR = BASE_DIR / "assets" / "signs"
LOG_DIR = BASE_DIR / "logs"


def validated_location_coordinates(location):
    if not isinstance(location, dict):
        return None

    raw_latitude = location.get("latitude")
    raw_longitude = location.get("longitude")
    if isinstance(raw_latitude, bool) or isinstance(raw_longitude, bool):
        return None

    try:
        latitude = float(raw_latitude)
        longitude = float(raw_longitude)
    except (TypeError, ValueError, OverflowError):
        return None

    if (
        not math.isfinite(latitude)
        or not math.isfinite(longitude)
        or not -90 <= latitude <= 90
        or not -180 <= longitude <= 180
    ):
        return None

    return latitude, longitude


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="SignBridge 2.0 | Communication Platform",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# SESSION STATE
# =========================================================

if "recognition_process" not in st.session_state:
    st.session_state.recognition_process = None

if "recognition_process_mode" not in st.session_state:
    st.session_state.recognition_process_mode = None

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "recognised_speech" not in st.session_state:
    st.session_state.recognised_speech = ""

if "sentence_words" not in st.session_state:
    st.session_state.sentence_words = []


# =========================================================
# COLOUR SYSTEM
# =========================================================

CREAM = "#FFE8D6"
BEIGE = "#DDBEA9"
TERRACOTTA = "#CB997E"
SAGE = "#B7B7A4"
OLIVE = "#A5A58D"
DARK_OLIVE = "#6B705C"

INK = "#303429"
MUTED = "#747666"
SURFACE = "#FFFAF4"
BORDER = "#E9D9C9"


# =========================================================
# PREMIUM CSS DESIGN SYSTEM
# =========================================================

st.html(
    f"""
    <style>

    @import url(
      'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap'
    );

    :root {{
        --cream: {CREAM};
        --beige: {BEIGE};
        --terracotta: {TERRACOTTA};
        --sage: {SAGE};
        --olive: {OLIVE};
        --dark-olive: {DARK_OLIVE};
        --ink: {INK};
        --muted: {MUTED};
        --surface: {SURFACE};
        --border: {BORDER};
    }}

    /* Main background */

    .stApp {{
        background:
            radial-gradient(
                circle at 85% 5%,
                rgba(203,153,126,0.12),
                transparent 25%
            ),
            radial-gradient(
                circle at 5% 45%,
                rgba(165,165,141,0.12),
                transparent 28%
            ),
            #F7F2EA;
        color: var(--ink);
        font-family: 'DM Sans', sans-serif;
    }}

    .main .block-container {{
        max-width: 1450px;
        padding: 2.2rem 3rem 3rem;
    }}

    /* Typography */

    h1, h2, h3 {{
        color: var(--ink) !important;
        font-family: 'DM Sans', sans-serif;
        letter-spacing: -0.8px;
    }}

    p, label {{
        color: var(--muted);
    }}

    /* Sidebar */

    [data-testid="stSidebar"] {{
        background:
            linear-gradient(
                180deg,
                #606650 0%,
                #6B705C 50%,
                #525844 100%
            );
        border-right: 1px solid rgba(255,255,255,0.12);
    }}

    [data-testid="stSidebar"] * {{
        color: #FFF5EB;
    }}

    [data-testid="stSidebar"] .stRadio label {{
        padding: 10px 12px;
        border-radius: 11px;
        transition: 0.25s ease;
    }}

    [data-testid="stSidebar"] .stRadio label:hover {{
        background: rgba(255,232,214,0.16);
        transform: translateX(3px);
    }}

    .brand-logo {{
        text-align: center;
        padding: 14px 0 8px;
    }}

    .brand-symbol {{
        width: 58px;
        height: 58px;
        border-radius: 19px;
        background: linear-gradient(135deg, #FFE8D6, #DDBEA9);
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 28px;
        margin: auto auto 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }}

    .brand-name {{
        font-size: 27px;
        font-weight: 800;
        letter-spacing: -1px;
        color: #FFF5EB;
    }}

    .brand-tagline {{
        font-size: 10px;
        letter-spacing: 2px;
        color: #E5D9CA;
        text-transform: uppercase;
    }}

    .sidebar-label {{
        font-size: 10px;
        letter-spacing: 2px;
        font-weight: 800;
        color: #E5D9CA;
        margin-top: 20px;
    }}

    .sidebar-footer {{
        text-align: center;
        color: #E5D9CA;
        font-size: 10px;
        letter-spacing: 1px;
        padding-top: 20px;
    }}

    /* Hero */

    .hero {{
        position: relative;
        overflow: hidden;
        padding: 44px 42px;
        min-height: 270px;
        border-radius: 25px;
        background:
            linear-gradient(
                115deg,
                #555D48 0%,
                #6B705C 50%,
                #898C75 100%
            );
        box-shadow: 0 16px 40px rgba(55,60,45,0.16);
        animation: heroAppear 0.8s ease both;
    }}

    .hero::before {{
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        border: 1px solid rgba(255,255,255,0.19);
        border-radius: 50%;
        right: -60px;
        top: -85px;
        box-shadow:
            0 0 0 24px rgba(255,255,255,0.035),
            0 0 0 50px rgba(255,255,255,0.025),
            0 0 0 80px rgba(255,255,255,0.018);
        animation: slowFloat 12s ease-in-out infinite;
    }}

    .hero::after {{
        content: "SB";
        position: absolute;
        right: 50px;
        bottom: -65px;
        font-family: 'Playfair Display', serif;
        font-size: 190px;
        font-weight: 800;
        color: rgba(255,255,255,0.055);
        transform: rotate(-10deg);
    }}

    .hero-content {{
        position: relative;
        z-index: 2;
    }}

    .hero-kicker {{
        font-size: 11px;
        letter-spacing: 3px;
        color: #F4D8C2;
        font-weight: 800;
        text-transform: uppercase;
    }}

    .hero-title {{
        font-family: 'Playfair Display', serif;
        font-size: clamp(35px, 5vw, 57px);
        line-height: 1.08;
        font-weight: 700;
        color: #FFF7EE;
        margin: 18px 0 12px;
        max-width: 620px;
    }}

    .hero-description {{
        color: #EEE5D9;
        font-size: 15px;
        line-height: 1.8;
        max-width: 650px;
    }}

    /* Sections */

    .eyebrow {{
        font-size: 10px;
        color: #A26F55;
        letter-spacing: 2.5px;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 5px;
    }}

    .section-title {{
        color: var(--ink);
        font-size: 27px;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 17px;
    }}

    .section-description {{
        font-size: 14px;
        line-height: 1.7;
        margin-bottom: 20px;
    }}

    /* Feature cards */

    .feature-card {{
        background: linear-gradient(
            145deg,
            #FFFCF7,
            #F8EEE3
        );
        border: 1px solid var(--border);
        border-radius: 19px;
        padding: 23px;
        min-height: 160px;
        margin-bottom: 15px;
        box-shadow: 0 5px 18px rgba(65,69,56,0.045);
        transition:
            transform 0.3s ease,
            box-shadow 0.3s ease,
            border-color 0.3s ease;
        animation: cardAppear 0.65s ease both;
    }}

    .feature-card:hover {{
        transform: translateY(-6px);
        box-shadow: 0 15px 30px rgba(65,69,56,0.11);
        border-color: var(--terracotta);
    }}

    .feature-icon {{
        width: 43px;
        height: 43px;
        border-radius: 14px;
        background: #F1E2D4;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 21px;
        margin-bottom: 16px;
    }}

    .feature-card h3 {{
        font-size: 17px;
        font-weight: 800;
        margin: 0 0 9px;
        color: var(--dark-olive) !important;
    }}

    .feature-card p {{
        font-size: 13px;
        line-height: 1.7;
        margin: 0;
        color: #747666;
    }}

    /* Small dashboard panels */

    .panel {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 5px 18px rgba(65,69,56,0.045);
        margin-bottom: 15px;
    }}

    .panel-label {{
        color: #858875;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }}

    .panel-number {{
        color: var(--dark-olive);
        font-size: 32px;
        font-weight: 800;
        margin-top: 8px;
    }}

    .panel-caption {{
        color: #8A8A7A;
        font-size: 12px;
    }}

    .status-pill {{
        display: inline-block;
        padding: 7px 12px;
        border-radius: 20px;
        background: #E6E9DB;
        color: #596248;
        font-size: 11px;
        font-weight: 800;
    }}

    /* Buttons */

    .stButton > button {{
        background: linear-gradient(
            120deg,
            #CB997E,
            #B77D61
        );
        border: none;
        color: white !important;
        border-radius: 12px;
        min-height: 45px;
        font-weight: 800;
        transition: all 0.25s ease;
    }}

    .stButton > button:hover {{
        background: #A96F55;
        transform: translateY(-3px);
        box-shadow: 0 9px 20px rgba(169,111,85,0.22);
    }}

    .stDownloadButton > button {{
        background: #6B705C;
        color: white !important;
        border-radius: 12px;
        border: none;
        font-weight: 700;
    }}

    .stDownloadButton > button:hover {{
        background: #515843;
    }}

    /* Inputs */

    .stTextArea textarea,
    .stTextInput input {{
        background: #FFFCF7;
        border: 1px solid var(--border);
        border-radius: 12px;
    }}

    /* Metrics */

    [data-testid="stMetric"] {{
        background: #FFFCF7;
        padding: 17px;
        border-radius: 16px;
        border: 1px solid var(--border);
        box-shadow: 0 5px 16px rgba(65,69,56,0.045);
    }}

    [data-testid="stMetricValue"] {{
        color: var(--dark-olive);
    }}

    /* Tables */

    [data-testid="stDataFrame"] {{
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
    }}

    /* Animations */

    @keyframes heroAppear {{
        from {{
            opacity: 0;
            transform: translateY(18px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes cardAppear {{
        from {{
            opacity: 0;
            transform: translateY(12px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes slowFloat {{
        0%, 100% {{
            transform: translateY(0) rotate(0deg);
        }}
        50% {{
            transform: translateY(18px) rotate(8deg);
        }}
    }}

    /* Footer */

    .footer {{
        border-top: 1px solid var(--border);
        margin-top: 35px;
        padding-top: 20px;
        text-align: center;
        color: #969584;
        font-size: 11px;
        letter-spacing: 1.5px;
    }}

    /* Mobile */

    @media(max-width: 768px) {{
        .main .block-container {{
            padding: 1rem 1rem 2rem;
        }}

        .hero {{
            padding: 28px 23px;
        }}

        .hero-title {{
            font-size: 37px;
        }}

        .hero::after {{
            font-size: 120px;
            right: 15px;
        }}
    }}

    @media(prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            transition-duration: 0.01ms !important;
        }}
    }}

    </style>
    """
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def section_heading(kicker, heading, description=None):

    description_html = (
        f'<div class="section-description">{description}</div>'
        if description else ""
    )

    st.html(
        f"""
        <div class="eyebrow">{kicker}</div>
        <div class="section-title">{heading}</div>
        {description_html}
        """
    )


def feature_card(icon, title, description):

    st.html(
        f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
        """
    )


def start_recognition(script_path, mode_name, arguments=None):

    if not script_path.exists():
        st.error(f"Recognition script was not found: {script_path.name}")
        return

    required_modules_by_mode = {
        "Static gestures (8)": (
            "cv2", "joblib", "mediapipe", "numpy", "pandas", "pyttsx3"
        ),
        "40-word sequences": (
            "cv2", "joblib", "mediapipe", "numpy", "sklearn",
            "tensorflow", "pyttsx3",
        ),
        "Smart Gesture Control": (
            "cv2", "joblib", "mediapipe", "numpy", "pandas",
            "pyautogui",
        ),
    }
    required_modules = required_modules_by_mode.get(mode_name, ())
    if required_modules:
        missing_modules = [
            name for name in required_modules
            if importlib.util.find_spec(name) is None
        ]
        if missing_modules:
            st.error(
                f"{mode_name} cannot start because its Python "
                f"environment is missing: {', '.join(missing_modules)}. "
                "Launch SignBridge with run_signbridge.bat or the project's "
                "own Python environment."
            )
            st.code(sys.executable)
            return

    process = st.session_state.recognition_process

    if process is not None and process.poll() is None:
        st.warning("Gesture recognition is already running.")
        return

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / "recognition.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"\n--- Starting {mode_name} at {datetime.now().isoformat(timespec='seconds')} ---\n")
            log_file.write(f"Python interpreter: {sys.executable}\n")
            log_file.flush()
            st.session_state.recognition_process = subprocess.Popen(
                [sys.executable, str(script_path), *(arguments or [])],
                cwd=str(BASE_DIR),
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
        st.session_state.recognition_process_mode = mode_name
        st.session_state.recognition_log_path = str(log_path)

        st.info(
            f"{mode_name} launch requested. The camera window opens separately; "
            "if it closes or cannot access the camera, check the diagnostic below."
        )

    except Exception as error:
        st.error(f"Unable to start recognition: {error}")


def stop_recognition():

    process = st.session_state.recognition_process

    if process is not None and process.poll() is None:

        process.terminate()

        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)

        st.success("Gesture recognition stopped.")

    else:
        st.info("Gesture recognition is not running.")

    st.session_state.recognition_process = None
    st.session_state.recognition_process_mode = None


def recognition_is_running():

    process = st.session_state.recognition_process

    return process is not None and process.poll() is None


def get_history():

    if not HISTORY_FILE.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(HISTORY_FILE)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.error(f"Unable to read conversation history: {error}")
        return pd.DataFrame()


def render_footer():

    st.html(
        """
        <div class="footer">
            SIGNBRIDGE 2.0 &nbsp; • &nbsp;
            BREAKING COMMUNICATION BARRIERS
            <br><br>
            CONNECTING PEOPLE THROUGH COMMUNICATION
        </div>
        """
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.html(
        """
        <div class="brand-logo">
            <div class="brand-symbol">🤝</div>
            <div class="brand-name">SignBridge 2.0</div>
            <div class="brand-tagline">
                AI Communication Platform
            </div>
        </div>
        """
    )

    st.divider()

    st.html('<div class="sidebar-label">YOUR WORKSPACE</div>')

    pages = [
        "Home",
        "Live ISL Recognition",
        "Sign to Text & Voice",
        "Recognition History",
        "Conversation History",
        "Speech to Text",
        "ISL Digital Dictionary",
        "Text to Sign",
        "ISL Alphabet Learning",
        "Word Communication Board",
        "Quick Communication Board",
        "Speaker Voice",
        "Live Location",
        "About Project",
        "Emergency SOS",
        "Smart Gesture Control",
        "Model Evaluation",
    ]

    navigation_selection = st.radio(
        "Navigation",
        pages,
        key="page",
        label_visibility="collapsed"
    )
    live_recognition_shortcut = navigation_selection == "Live ISL Recognition"
    dictionary_shortcut = navigation_selection == "ISL Digital Dictionary"

    page_aliases = {
        "Live ISL Recognition": "Sign to Text & Voice",
        "Recognition History": "Conversation History",
        "ISL Digital Dictionary": "Text to Sign",
        "Word Communication Board": "Quick Communication Board",
    }
    selected_page = page_aliases.get(navigation_selection, navigation_selection)

    st.divider()

    st.markdown("### SYSTEM STATUS")

    if recognition_is_running():
        running_mode = st.session_state.recognition_process_mode or "Recognition"
        st.success(f"● {running_mode} Running")
    else:
        st.warning("● Recognition Stopped")

    st.html(
        """
        <div class="sidebar-footer">
            DESIGNED FOR ACCESSIBILITY<br>
            SIGNBRIDGE 2.0 • 2026
        </div>
        """
    )


# =========================================================
# HOME DASHBOARD
# =========================================================

if selected_page == "Home":

    history_df = get_history()

    total_messages = len(history_df)

    unique_gestures = (
        history_df["Gesture"].nunique()
        if "Gesture" in history_df.columns
        else 0
    )

    st.html(
        """
        <div class="hero">
            <div class="hero-content">
                <div class="hero-kicker">
                    THE FUTURE OF ACCESSIBLE COMMUNICATION
                </div>

                <div class="hero-title">
                A world where<br>
                everyone can be heard.
                </div>

                <div class="hero-description">
                Different ways to communicate. One way to connect.
                <br><br>
                SignBridge brings hand gestures, text and voice
                together to make communication easier for everyone.
                <br><br>
                Because every person deserves to be understood. ❤️
                </div>
            </div>
        </div>
        """
    )

    st.write("")

    section_heading(
        "YOUR OVERVIEW",
        "Communication at a glance"
    )

    m1, m2, m3 = st.columns(3)

    with m1:
        st.metric(
            "Total Conversations",
            total_messages,
            help="Messages saved in conversation history."
        )

    with m2:
        st.metric(
            "Unique Gestures",
            unique_gestures,
            help="Different gestures recorded in history."
        )

    with m3:
        st.metric(
            "Available Gestures",
            8,
            help="Current original custom gesture vocabulary."
        )

    st.write("")

    section_heading(
        "EXPLORE THE PLATFORM",
        "Your communication tools"
    )

    c1, c2 = st.columns(2)

    with c1:

        feature_card(
            "👋",
            "Sign to Text & Voice",
            "Turn recognised custom hand gestures into "
            "written messages and spoken output."
        )

        feature_card(
            "🎤",
            "Speech to Text",
            "Capture spoken messages through your connected "
            "microphone and convert them into text."
        )

        feature_card(
            "📜",
            "Conversation History",
            "Keep track of previously recognised messages "
            "and download your conversation records."
        )

    with c2:

        feature_card(
            "🖐️",
            "Text to Sign",
            "Explore available sign illustrations for "
            "selected messages."
        )

        feature_card(
            "🤖",
            "AI Recognition",
            "Use computer vision and machine learning "
            "to identify custom hand gestures."
        )

        feature_card(
            "💬",
            "Two-Way Communication",
            "Bring gestures, written messages and speech "
            "together in one platform."
        )

    st.write("")

    extra_feature_cols = st.columns(3)
    extra_features = [
        ("🆘", "Emergency SOS", "Prepare a reviewed SMS link with an optional location."),
        ("🗣️", "Quick Communication Board", "Choose common phrases in English or Hindi, or write a custom message."),
        ("🖱️", "Smart Gesture Control", "Opt in to a local computer-control demo using the existing 8 static labels."),
    ]
    for column, feature in zip(extra_feature_cols, extra_features):
        with column:
            feature_card(*feature)

    st.write("")

    section_heading(
        "QUICK ACCESS",
        "Where would you like to go?"
    )

    q1, q2, q3 = st.columns(3)

    with q1:

        if st.button(
            "👋 Open Gesture Recognition",
            width="stretch"
        ):
            st.session_state.page = "Sign to Text & Voice"
            st.rerun()

    with q2:

        if st.button(
            "🎤 Open Speech Tools",
            width="stretch"
        ):
            st.session_state.page = "Speech to Text"
            st.rerun()

    with q3:

        if st.button(
            "📜 View Conversations",
            width="stretch"
        ):
            st.session_state.page = "Conversation History"
            st.rerun()

    st.write("")

    if not history_df.empty:

        section_heading(
            "LATEST ACTIVITY",
            "Recent conversations"
        )

        st.dataframe(
            history_df.tail(5).iloc[::-1],
            width="stretch",
            hide_index=True
        )

    st.info(
        "SignBridge currently demonstrates eight custom static "
        "gestures. It is not a complete Indian Sign Language translator."
    )


# =========================================================
# SIGN TO TEXT & VOICE
# =========================================================

elif selected_page == "Sign to Text & Voice":

    section_heading(
        "GESTURE RECOGNITION",
        "Sign to Text & Voice",
        "Transform your custom hand gestures into written "
        "and spoken communication."
    )

    if live_recognition_shortcut:
        st.warning(
            "This shortcut opens the existing webcam recognition engines; it is not "
            "a separately validated ISL recognition model. The 40-word model's "
            "saved same-signer evaluation is 4.5%."
        )

    recognition_modes = {
        "Static gestures (8)": RECOGNITION_FILE,
        "40-word sequences": MANUAL_RECOGNITION_FILE,
    }
    selected_mode = st.radio(
        "Recognition mode",
        list(recognition_modes),
        horizontal=True,
        key="recognition_mode_choice",
    )
    if selected_mode == "40-word sequences":
        st.info(
            "Word recognition uses the separate manual sequence model. Its saved "
            "same-signer held-out-session accuracy is 4.5%; do not rely on it as "
            "a working word translator for this demo."
        )

    camera_index = st.selectbox(
        "Camera device index",
        options=[0, 1, 2, 3],
        index=0,
        key="recognition_camera_index",
        help="Try another index if the default webcam is unavailable.",
    )
    practice_label = ""
    manual_labels = []
    if selected_mode == "40-word sequences":
        if MANUAL_LABELS_FILE.is_file():
            try:
                manual_labels = json.loads(
                    MANUAL_LABELS_FILE.read_text(encoding="utf-8")
                )
                if tuple(manual_labels) != WORD_LABELS:
                    st.error("The active 40-word labels do not match the preserved vocabulary order.")
                    manual_labels = []
                if manual_labels:
                    practice_label = st.selectbox(
                        "Manual practice target",
                        manual_labels,
                        help="Shown in the camera window for comparison only; it is not supplied to the model.",
                    )
            except (OSError, json.JSONDecodeError) as error:
                st.error(f"The 40-word practice list could not be loaded: {error}")
        else:
            st.error("The 40-word label file is missing; the practice list cannot be loaded.")

    col1, col2 = st.columns(2)

    with col1:

        st.html(
            """
            <div class="panel">
                <div class="panel-label">CAMERA CONTROL</div>
                <h3>Start recognition</h3>
                <p>
                    Open the separate webcam recognition window
                    and show your trained gestures.
                </p>
            </div>
            """
        )

        if st.button(
            "▶ Start Gesture Recognition",
            width="stretch"
        ):
            arguments = ["--camera-index", str(camera_index)]
            if selected_mode == "40-word sequences" and practice_label:
                arguments.extend(["--practice-label", practice_label])
            start_recognition(
                recognition_modes[selected_mode],
                selected_mode,
                arguments,
            )

    with col2:

        st.html(
            """
            <div class="panel">
                <div class="panel-label">SYSTEM CONTROL</div>
                <h3>Stop recognition</h3>
                <p>
                    Stop the current webcam recognition
                    process when you finish.
                </p>
            </div>
            """
        )

        if st.button(
            "⏹ Stop Gesture Recognition",
            width="stretch"
        ):
            stop_recognition()

    if recognition_is_running():
        st.success("Gesture recognition is running.")
    else:
        st.warning("Gesture recognition is currently stopped.")
        log_path = st.session_state.get("recognition_log_path")
        process = st.session_state.get("recognition_process")
        if process is not None and process.poll() not in (None, 0) and log_path:
            try:
                log_lines = Path(log_path).read_text(encoding="utf-8", errors="replace").splitlines()
                st.error("The recognition process exited with an error. Recent details:")
                st.code("\n".join(log_lines[-18:]))
            except OSError as error:
                st.error(f"The recognition process exited; its log could not be read: {error}")

    st.write("")

    section_heading(
        "CUSTOM VOCABULARY",
        "Available gestures"
    )

    if selected_mode == "Static gestures (8)":
        gestures = [
            ("OPEN_PALM", "Hello"),
            ("FIST", "Stop"),
            ("THUMBS_UP", "Thank you"),
            ("THUMBS_DOWN", "No"),
            ("POINT_UP", "Help"),
            ("VICTORY", "Yes"),
            ("CROSSED_FINGERS", "Please"),
            ("I_LOVE_YOU", "I love you")
        ]

        gesture_columns = st.columns(4)
        for index, (gesture, message) in enumerate(gestures):
            with gesture_columns[index % 4]:
                feature_card("🖐️", gesture, message)
    else:
        if MANUAL_LABELS_FILE.is_file():
            if manual_labels:
                st.caption(
                    "The selected target appears in the camera window only. "
                    "It does not alter model input or prediction."
                )
                st.dataframe(
                    pd.DataFrame({"Word label": manual_labels}),
                    width="stretch",
                    hide_index=True,
                )
        else:
            st.error("Manual model label file is missing.")


# =========================================================
# CONVERSATION HISTORY
# =========================================================

elif selected_page == "Conversation History":

    section_heading(
        "YOUR COMMUNICATION RECORDS",
        "Conversation History",
        "Review and download the messages recognised "
        "by your SignBridge system."
    )

    if HISTORY_FILE.exists():

        try:

            df = pd.read_csv(HISTORY_FILE)

            if not df.empty:

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Total Messages", len(df))

                with col2:

                    if "Gesture" in df.columns:
                        st.metric(
                            "Unique Gestures",
                            df["Gesture"].nunique()
                        )

                st.divider()

                st.subheader("Previous Conversations")

                search_text = st.text_input(
                    "Search conversations",
                    placeholder="Search gesture, message, date, or time",
                )
                visible_df = df
                if search_text.strip():
                    search_pattern = re.escape(search_text.strip())
                    matches = df.astype(str).apply(
                        lambda column: column.str.contains(
                            search_pattern, case=False, na=False, regex=True
                        )
                    ).any(axis=1)
                    visible_df = df[matches]
                    st.caption(f"Showing {len(visible_df)} matching records.")

                st.dataframe(
                    visible_df.iloc[::-1],
                    width="stretch",
                    hide_index=True
                )

                st.subheader("Manage records")
                row_options = list(df.index)
                selected_row = st.selectbox(
                    "Select a record to delete",
                    row_options,
                    format_func=lambda row: (
                        f"{df.loc[row].get('Date', '')} "
                        f"{df.loc[row].get('Time', '')} — "
                        f"{df.loc[row].get('Message', '')}"
                    ),
                    key="history_delete_row",
                )
                if st.button("Delete selected record", key="delete_history_record"):
                    df.drop(index=selected_row).to_csv(HISTORY_FILE, index=False)
                    st.success("Selected conversation record deleted.")
                    st.rerun()

                confirm_clear = st.checkbox(
                    "I understand this will permanently clear the conversation history in this project copy.",
                    key="confirm_clear_history",
                )
                if st.button(
                    "Clear all history",
                    type="secondary",
                    disabled=not confirm_clear,
                    key="clear_history_records",
                ):
                    df.iloc[0:0].to_csv(HISTORY_FILE, index=False)
                    st.success("Conversation history cleared.")
                    st.rerun()

                csv_data = df.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    label="⬇ Download Conversation History",
                    data=csv_data,
                    file_name="conversation_history.csv",
                    mime="text/csv",
                    width="stretch"
                )

            else:
                st.info("No conversation records found yet.")

        except Exception as error:

            st.error(
                f"Unable to read conversation history: {error}"
            )

    else:

        st.info(
            "No conversation history found. "
            "Start gesture recognition to create your first record."
        )


# =========================================================
# SPEECH TO TEXT
# =========================================================

elif selected_page == "Speech to Text":

    section_heading(
        "VOICE INPUT",
        "Speech to Text",
        "Convert spoken words into written messages "
        "using your connected microphone."
    )

    st.html(
        """
        <div class="panel">
            <div class="panel-label">MICROPHONE CONNECTION</div>
            <h3>Ready to listen?</h3>
            <p>
                Recording uses the microphone selected by your browser.
                If using WO Mic, select it as the browser or system input
                and allow microphone access for this site.
            </p>
        </div>
        """
    )

    speech_language = st.radio(
        "Recognition language",
        ["English", "Hindi"],
        horizontal=True,
        key="speech_language_choice",
    )

    st.subheader("Record your speech")

    audio = mic_recorder(
        start_prompt="🎤 Start Recording",
        stop_prompt="⏹ Stop Recording",
        just_once=True,
        use_container_width=True,
        format="wav",
        key="speech_recorder"
    )

    if audio and audio.get("bytes"):

        current_audio_key = (
            hashlib.sha256(audio["bytes"]).hexdigest() + ":" + speech_language
        )

        st.subheader("Recorded Audio")

        st.audio(
            audio["bytes"],
            format="audio/wav"
        )

        try:

            if st.session_state.get("last_transcribed_audio_key") == current_audio_key:
                raise StopIteration

            recognizer = sr.Recognizer()

            with sr.AudioFile(
                io.BytesIO(audio["bytes"])
            ) as source:

                audio_data = recognizer.record(source)

            with st.spinner("Converting speech into text..."):

                recognition_locale = "hi-IN" if speech_language == "Hindi" else "en-IN"
                recognised_text = recognizer.recognize_google(
                    audio_data,
                    language=recognition_locale
                )

            st.session_state.recognised_speech = recognised_text
            st.session_state.last_transcribed_audio_key = current_audio_key

            st.success("Speech successfully converted!")

        except sr.UnknownValueError:

            st.warning(
                "Your voice was not clear enough. "
                "Please speak slowly and try again."
            )

        except sr.RequestError as error:

            st.error(f"Speech service error: {error}")

        except StopIteration:
            pass

        except Exception as error:

            st.error(f"Audio processing error: {error}")

    else:
        st.info(
            "No recording is available yet. Allow microphone access in your browser, "
            "check the selected input device, and use the recorder above."
        )

    st.divider()

    section_heading(
        "TRANSCRIPTION",
        "Recognised Speech"
    )

    st.text_area(
        "Your converted text",
        value=st.session_state.recognised_speech,
        height=150,
        disabled=True
    )

    speech_col1, speech_col2 = st.columns(2)
    with speech_col1:
        if st.button("🔊 Speak recognised text", width="stretch"):
            if not st.session_state.recognised_speech.strip():
                st.info("Record and transcribe a message first.")
            else:
                import pyttsx3
                try:
                    engine = pyttsx3.init("sapi5") if sys.platform == "win32" else pyttsx3.init()
                    if speech_language == "Hindi":
                        hindi_voice = next((
                            voice for voice in engine.getProperty("voices")
                            if any(tag in (voice.name + " " + voice.id).lower()
                                   for tag in ("hindi", "hi-in", "hemant", "kalpana"))
                        ), None)
                        if hindi_voice is None:
                            st.error("No Hindi system voice is installed. Install a Hindi voice in Windows to speak Hindi text.")
                            raise StopIteration
                        engine.setProperty("voice", hindi_voice.id)
                    engine.say(st.session_state.recognised_speech)
                    engine.runAndWait()
                    engine.stop()
                except StopIteration:
                    pass
                except Exception as error:
                    st.error(f"Speech output is unavailable: {error}")
    with speech_col2:
        if st.button("➕ Save to Conversation History", width="stretch"):
            if st.session_state.recognised_speech.strip():
                now = datetime.now()
                history_row = pd.DataFrame([{
                    "Date": now.strftime("%Y-%m-%d"),
                    "Time": now.strftime("%H:%M:%S"),
                    "Gesture": "SPEECH",
                    "Message": st.session_state.recognised_speech,
                    "Confidence": "",
                }])
                header = not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0
                history_row.to_csv(HISTORY_FILE, mode="a", header=header, index=False)
                st.success("Speech text saved to conversation history.")
            else:
                st.info("Record and transcribe a message first.")

    if st.button(
        "🗑 Clear Recognised Text",
        width="stretch"
    ):

        st.session_state.recognised_speech = ""
        st.rerun()


# =========================================================
# TEXT TO SIGN
# =========================================================

elif selected_page == "Text to Sign":

    section_heading(
        "VERIFIED REFERENCES ONLY" if dictionary_shortcut else "VISUAL SIGN LIBRARY",
        "ISL Digital Dictionary" if dictionary_shortcut else "Text to Sign",
        (
            "Search the trained vocabulary and custom-pose catalogue. "
            "Reference media is shown only when supplied and verified."
            if dictionary_shortcut
            else "Choose a message and view its available hand-sign illustration."
        )
    )

    sign_images = {
        "hello": ("Hello", SIGNS_DIR / "hello.png"),
        "stop": ("Stop", SIGNS_DIR / "stop.png"),
        "thank you": ("Thank you", SIGNS_DIR / "thank_you.png"),
        "thanks": ("Thank you", SIGNS_DIR / "thank_you.png"),
    }
    sign_text = st.text_area(
        "Enter an English or Hindi message",
        placeholder="Type a sentence or paragraph. Only supplied sign images are shown as signs.",
        height=120,
        key="text_to_sign_input",
    )
    import string
    raw_sign_tokens = re.findall(
        r"[^\W_]+(?:['’][^\W_]+)?|[^\w\s]", sign_text, re.UNICODE
    )
    sign_tokens = []
    token_index = 0
    while token_index < len(raw_sign_tokens):
        current = raw_sign_tokens[token_index]
        if (
            current.lower() == "thank"
            and token_index + 1 < len(raw_sign_tokens)
            and raw_sign_tokens[token_index + 1].lower().strip(string.punctuation) == "you"
        ):
            sign_tokens.append("Thank you")
            token_index += 2
        else:
            sign_tokens.append(current)
            token_index += 1
    if sign_tokens:
        st.caption(f"{len(sign_tokens)} words or punctuation marks")
        if "text_sign_index" not in st.session_state:
            st.session_state.text_sign_index = 0
        st.session_state.text_sign_index = min(
            st.session_state.text_sign_index, len(sign_tokens) - 1
        )
        previous_col, next_col = st.columns(2)
        with previous_col:
            if st.button("← Previous", width="stretch", disabled=st.session_state.text_sign_index == 0):
                st.session_state.text_sign_index -= 1
                st.rerun()
        with next_col:
            if st.button("Next →", width="stretch", disabled=st.session_state.text_sign_index >= len(sign_tokens) - 1):
                st.session_state.text_sign_index += 1
                st.rerun()
        token = sign_tokens[st.session_state.text_sign_index]
        st.subheader(f"{st.session_state.text_sign_index + 1} / {len(sign_tokens)}: {token}")
        sign_entry = sign_images.get(token.strip(string.punctuation).lower())
        if sign_entry and sign_entry[1].is_file():
            st.image(str(sign_entry[1]), caption=f"Available reference: {sign_entry[0]}", width="stretch")
        elif token in ".,!?;:—-()[]{}\"'“”‘’":
            st.info("Punctuation is kept as text; no sign image is needed.")
        else:
            st.info(
                "No verified sign representation is supplied for this word. "
                "SignBridge does not invent an ISL sign or fingerspelling animation."
            )
    else:
        st.info("Enter a message to browse its available word-by-word references.")
    st.caption("Verified image references currently supplied: Hello, Stop, and Thank you. Hindi input is preserved as text; matching Hindi sign assets are not included.")

    st.divider()
    section_heading(
        "40-WORD MODEL REFERENCES",
        "Reference gallery",
        "Only verified ISL references are shown as signs. Missing image files are marked so they can be supplied and reviewed."
    )
    if MANUAL_LABELS_FILE.is_file():
        manual_labels = json.loads(MANUAL_LABELS_FILE.read_text(encoding="utf-8"))
        st.caption(
            "The 40-word landmark dataset contains model features, not reference images. "
            "The existing landmark chart is a computer-drawn visualization and is not used as a verified sign reference."
        )
        dictionary_filter = st.text_input(
            "Search dictionary vocabulary",
            key="dictionary_40_search",
            placeholder="Search a word or custom gesture",
        )
        filtered_labels = [
            label for label in manual_labels
            if dictionary_filter.lower().strip() in label.lower()
        ]
        if not filtered_labels:
            st.info("No 40-word dictionary entries matched your search.")
        for offset in range(0, len(filtered_labels), 4):
            gallery_columns = st.columns(4)
            for column, label in zip(gallery_columns, filtered_labels[offset:offset + 4]):
                reference_path = MANUAL_REFERENCE_DIR / f"{label}.png"
                with column:
                    st.markdown(f"**{label.replace('_', ' ').title()}**")
                    if reference_path.is_file():
                        st.image(str(reference_path), caption=f"ISL reference: {label}", width="stretch")
                    else:
                        st.info("Verified image needed. Please supply an ISLRTC-verified reference.")
                    st.link_button(
                        "Open ISLRTC dictionary",
                        "https://divyangjan.depwd.gov.in/islrtc/",
                        help="Search this word in the official Indian Sign Language Dictionary. The dictionary provides video references."
                    )

        st.subheader("Eight trained custom static poses")
        query = dictionary_filter.lower().strip()
        static_entries = [
            entry for entry in dictionary_entries()
            if entry["category"] == "Trained static pose"
            and (not query or query in entry["word"].lower() or query in entry["meaning"].lower())
        ]
        if not static_entries:
            st.info("No trained static-pose entries matched your search.")
        for offset in range(0, len(static_entries), 4):
            columns = st.columns(4)
            for column, entry in zip(columns, static_entries[offset:offset + 4]):
                with column:
                    st.markdown(f"**{entry['word']}**")
                    st.write(entry["meaning"])
                    st.caption(entry["reference_status"])
                    st.caption(entry["recognition_status"])
    else:
        st.error("The 40-word reference gallery could not load because manual_labels.json is missing.")


# =========================================================
# ABOUT PROJECT
# =========================================================

elif selected_page == "About Project":

    section_heading(
        "THE STORY BEHIND THE PLATFORM",
        "About SignBridge",
        "Technology designed to help make communication "
        "more accessible."
    )

    st.subheader("Problem and objectives")
    st.write(
        "People may need a quick way to communicate when speech, hearing, "
        "or movement makes a conversation difficult. SignBridge combines "
        "small, explicitly limited gesture vocabularies with speech, text, "
        "and phrase-board tools for an educational demonstration."
    )
    st.write(
        "The objective is to make a local prototype that turns supported "
        "hand poses or recorded word sequences into readable text, offers "
        "optional speech output, and keeps a user-managed conversation log."
    )

    st.subheader("How the recognition works")
    st.write(
        "The static mode extracts 63 normalized hand-landmark features and "
        "uses the saved Random Forest model for its original eight custom labels. "
        "The manual word mode extracts 1,662 holistic features over 30 frames "
        "and loads a separate LSTM model with its matching scaler and label list. "
        "These are distinct pipelines and are not general sign-language translation."
    )

    feature_card(
        "🤝",
        "Project Identity",
        "SignBridge – AI-Powered Communication System."
    )

    feature_card(
        "🎯",
        "Our Objective",
        "Reduce communication barriers by recognising custom "
        "hand gestures and converting them into text and voice."
    )

    section_heading(
        "TECHNOLOGY STACK",
        "Tools behind SignBridge"
    )

    technologies = [
        "Python",
        "Streamlit",
        "OpenCV",
        "MediaPipe",
        "Machine Learning",
        "Random Forest Classifier",
        "NumPy",
        "Pandas",
        "pyttsx3",
        "SpeechRecognition"
    ]

    tech_columns = st.columns(3)

    for index, technology in enumerate(technologies):

        with tech_columns[index % 3]:

            feature_card(
                "⚙️",
                technology,
                "Used in the SignBridge application."
            )

    section_heading(
        "CUSTOM GESTURE VOCABULARY",
        "Supported gestures"
    )

    gesture_data = {
        "Gesture": [
            "OPEN_PALM",
            "FIST",
            "THUMBS_UP",
            "THUMBS_DOWN",
            "POINT_UP",
            "VICTORY",
            "CROSSED_FINGERS",
            "I_LOVE_YOU"
        ],
        "Message": [
            "Hello",
            "Stop",
            "Thank you",
            "No",
            "Help",
            "Yes",
            "Please",
            "I love you"
        ]
    }

    st.dataframe(
        pd.DataFrame(gesture_data),
        width="stretch",
        hide_index=True
    )

    st.subheader("Social Impact")

    st.write(
        "SignBridge aims to make everyday communication easier "
        "and more accessible by bringing gestures, text and "
        "speech into one platform."
    )

    st.subheader("Features and benefits")
    st.write(
        "The prototype provides two webcam recognition modes, a speech input "
        "page, a limited visual reference library, an English/Hindi phrase board, "
        "conversation export, an SMS-link preparation page, and an optional "
        "gesture-control demo. These tools can support demonstrations and "
        "experimentation; they are not replacements for interpreters or "
        "validated assistive communication devices."
    )
    st.subheader("Future improvements")
    st.write(
        "Next steps include recapturing invalid sequences, collecting diverse "
        "recording sessions, evaluating with a participant-separated test set, "
        "reviewing vocabulary with Deaf and signing communities, adding verified "
        "sign references, and testing the webcam and microphone on target laptops."
    )

    st.warning(
        "This is a demonstration using eight custom static gestures. "
        "It is not a complete Indian Sign Language (ISL) translator. "
        "Full sign-language translation requires additional recognition "
        "of hand movement, facial expressions, body posture and grammar."
    )
    # =========================================================
# EMERGENCY SOS
# =========================================================

elif selected_page == "Emergency SOS":

    section_heading(
        "QUICK EMERGENCY ASSISTANCE",
        "Emergency SOS",
        "Prepare a reviewed message link for your trusted contact."
    )

    st.warning(
        "This feature prepares an SMS. You must confirm "
        "sending it in your messaging app."
    )

    st.subheader("Trusted Emergency Contact")

    saved_contact = {}
    if CONTACT_FILE.is_file():
        try:
            loaded_contact = json.loads(CONTACT_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            st.error(f"Saved emergency contact could not be read: {error}")
        else:
            if not isinstance(loaded_contact, dict):
                st.error("Saved emergency contact has an invalid format. Re-enter and save it again.")
            elif any(
                not isinstance(loaded_contact.get(field, ""), str)
                for field in ("name", "phone")
            ):
                st.error("Saved emergency contact fields are invalid. Re-enter and save them again.")
            else:
                saved_contact = loaded_contact
    st.session_state.setdefault("emergency_contact_name", saved_contact.get("name", ""))
    st.session_state.setdefault("emergency_contact_phone", saved_contact.get("phone", ""))
    st.caption("The trusted contact is stored locally in this project folder; avoid saving it on a shared computer.")

    contact_name = st.text_input(
        "Contact name",
        placeholder="Enter trusted person's name",
        key="emergency_contact_name",
    )

    phone_number = st.text_input(
        "Mobile number with country code",
        placeholder="+919876543210",
        key="emergency_contact_phone",
    )

    if st.button("Save trusted contact", key="save_emergency_contact"):
        if not contact_name.strip() or not re.fullmatch(r"\+?[0-9]{10,15}", phone_number.strip()):
            st.error("Enter a contact name and a valid number with country code before saving.")
        else:
            try:
                CONTACT_FILE.write_text(
                    json.dumps({"name": contact_name.strip(), "phone": phone_number.strip()}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except OSError as error:
                st.error(f"Could not save the trusted contact: {error}")
            else:
                st.success("Trusted contact saved on this device.")

    st.subheader("Select Emergency Type")

    emergency_type = st.selectbox(
        "What help do you need?",
        [
            "Medical Emergency",
            "Police Help",
            "Accident",
            "General Emergency"
        ]
    )

    emergency_language = st.radio("Message language", ["English", "Hindi"], horizontal=True, key="emergency_language")
    emergency_messages = {
        "Medical Emergency": {"English": "I need medical assistance. Please help me.", "Hindi": "मुझे चिकित्सा सहायता चाहिए। कृपया मदद करें।"},
        "Police Help": {"English": "I need police assistance. Please help me.", "Hindi": "मुझे पुलिस सहायता चाहिए। कृपया मदद करें।"},
        "Accident": {"English": "An accident has happened. Please send help.", "Hindi": "दुर्घटना हुई है। कृपया मदद भेजें।"},
        "General Emergency": {"English": "I am in an emergency. Please contact me immediately.", "Hindi": "मैं आपात स्थिति में हूँ। कृपया तुरंत मुझसे संपर्क करें।"}
    }

    message = emergency_messages[emergency_type][emergency_language]

    message = st.text_area(
        "Emergency message",
        value=message,
        height=100,
        key=f"emergency_message_{emergency_language}_{emergency_type}",
    )

    st.subheader("📍 Current Location")

    location = streamlit_geolocation()
    coordinates = validated_location_coordinates(location)

    # ==========================================
    # CURRENT LOCATION
    # ==========================================

    if coordinates is not None:
        latitude, longitude = coordinates
        location_link = (
            f"https://www.google.com/maps?q={latitude},{longitude}"
        )

        st.success("Location detected successfully!")
        st.write(f"Latitude: {latitude}")
        st.write(f"Longitude: {longitude}")

        st.link_button(
            "View My Location on Google Maps",
            location_link
        )

    else:
        location_link = None
        if (
            location is None
            or location == {}
            or (
                isinstance(location, dict)
                and location.get("latitude") is None
                and location.get("longitude") is None
            )
        ):
            st.info(
                "No location was received. Allow location access, use the "
                "location button again, and check browser permission or timeout. "
                "You can prepare the message without including a location."
            )
        else:
            st.warning(
                "The browser returned invalid coordinates. The location "
                "will be omitted; you can still prepare the message."
            )

    # ==========================================
    # PREPARE EMERGENCY SMS
    # ==========================================

    sms_confirmed = st.checkbox("I have reviewed the contact and message and want to prepare an SMS link.", key="confirm_prepare_sos")
    if st.button("Prepare Emergency SMS link", type="primary", disabled=not sms_confirmed):

        import re
        import urllib.parse

        cleaned_number = phone_number.strip()

        if not contact_name.strip():
            st.error("Please enter the contact name.")

        elif not message.strip():
            st.error("Please enter an emergency message.")

        elif not re.fullmatch(r"\+?[0-9]{10,15}", cleaned_number):
            st.error(
                "Please enter a valid phone number with country code."
            )

        else:
            sms_body = (
                "🚨 EMERGENCY ALERT!\n"
                f"From: {contact_name}\n"
                f"Emergency: {emergency_type}\n"
                f"Message: {message}\n"
            )

            if location_link:
                sms_body += (
                    f"\nMy Current Location:\n{location_link}"
                )
            else:
                sms_body += "\nLocation is unavailable."

            sms_url = (
                f"sms:{cleaned_number}"
                f"?body={urllib.parse.quote(sms_body)}"
            )

            st.success("SMS link prepared. No message has been sent.")

            st.link_button(
                "Open SMS App",
                sms_url
            )


# =========================================================
# QUICK COMMUNICATION BOARD
# =========================================================

elif selected_page == "Quick Communication Board":

    section_heading(
        "QUICK MESSAGES",
        "Quick Communication Board",
        "Choose a message and let SignBridge speak for you."
    )

    # Select speaking language
    language = st.radio(
        "Choose Language",
        ["English", "Hindi"],
        horizontal=True
    )

    if st.session_state.get("quick_message_language") != language:
        st.session_state.pop("quick_message", None)
        st.session_state["quick_message_language"] = language

    # Messages in both languages
    messages = {
        "help": {
            "English": "I need help",
            "Hindi": "मुझे मदद चाहिए"
        },
        "water": {
            "English": "I need water",
            "Hindi": "मुझे पानी चाहिए"
        },
        "food": {
            "English": "I need food",
            "Hindi": "मुझे खाना चाहिए"
        },
        "pain": {
            "English": "I am in pain",
            "Hindi": "मुझे दर्द हो रहा है"
        },
        "washroom": {
            "English": "I need a washroom",
            "Hindi": "मुझे शौचालय जाना है"
        },
        "family": {
            "English": "Please call my family",
            "Hindi": "कृपया मेरे परिवार को बुलाइए"
        },
        "hello": {"English": "Hello", "Hindi": "नमस्ते"},
        "yes": {"English": "Yes", "Hindi": "हाँ"},
        "no": {"English": "No", "Hindi": "नहीं"},
        "emergency": {"English": "This is an emergency. Please call for help.", "Hindi": "यह आपात स्थिति है। कृपया मदद के लिए फोन करें।"},
        "medical": {"English": "I need medical help.", "Hindi": "मुझे चिकित्सा सहायता चाहिए।"},
        "thank_you": {"English": "Thank you", "Hindi": "धन्यवाद"},
        "goodbye": {"English": "Goodbye", "Hindi": "अलविदा"},
        "please_wait": {"English": "Please wait", "Hindi": "कृपया प्रतीक्षा करें"}
    }

    # Message buttons
    phrase_columns = st.columns(3)
    for index, (key, translations) in enumerate(messages.items()):
        button_text = translations[language]
        with phrase_columns[index % 3]:
            if st.button(button_text, width="stretch", key=f"quick_phrase_{key}"):
                st.session_state["quick_message"] = translations[language]

    custom_message = st.text_input("Write a custom message", key="quick_custom_message")
    if st.button("Use custom message", key="use_quick_custom_message", disabled=not custom_message.strip()):
        st.session_state["quick_message"] = custom_message.strip()

    st.divider()
    st.subheader("Sentence builder")

    sentence_col, add_col, undo_col = st.columns([4, 1, 1])
    with sentence_col:
        sentence_word = st.text_input(
            "Add a word or phrase",
            key="sentence_builder_word",
            placeholder="e.g. water",
        )
    with add_col:
        if st.button("Add", width="stretch", disabled=not sentence_word.strip()):
            st.session_state.sentence_words.append(sentence_word.strip())
            st.rerun()
    with undo_col:
        if st.button(
            "Undo",
            width="stretch",
            disabled=not st.session_state.sentence_words,
        ):
            st.session_state.sentence_words.pop()
            st.rerun()

    word_cols = st.columns(4)
    for index, word in enumerate(st.session_state.sentence_words):
        with word_cols[index % 4]:
            if st.button(word, key=f"sentence_remove_{index}", help="Click to remove this word"):
                st.session_state.sentence_words.pop(index)
                st.rerun()

    sentence = " ".join(st.session_state.sentence_words)
    if sentence:
        st.success(sentence)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("Clear sentence", width="stretch"):
                st.session_state.sentence_words = []
                st.rerun()
        with c2:
            st.download_button(
                "Download text",
                sentence,
                file_name="signbridge_sentence.txt",
                width="stretch",
            )
        with c3:
            if st.button("Use as quick message", width="stretch"):
                st.session_state["quick_message"] = sentence
                st.rerun()
        with c4:
            clipboard_text = safe_script_json(sentence)
            component_html(
                f"""
                <button id="copy-sentence" type="button">Copy sentence</button>
                <span id="copy-status" role="status" aria-live="polite"></span>
                <script>
                  document.getElementById("copy-sentence").addEventListener("click", async () => {{
                    const value = {clipboard_text};
                    const status = document.getElementById("copy-status");
                    try {{
                      await navigator.clipboard.writeText(value);
                      status.textContent = "Copied.";
                    }} catch (error) {{
                      const field = document.createElement("textarea");
                      field.value = value;
                      document.body.appendChild(field);
                      field.select();
                      const copied = document.execCommand("copy");
                      field.remove();
                      status.textContent = copied
                        ? "Copied."
                        : "Clipboard unavailable; use Download text.";
                    }}
                  }});
                </script>
                """,
                height=48,
            )

    history_df = get_history()
    if not history_df.empty and "Message" in history_df.columns:
        recent_messages = (
            history_df["Message"]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .tail(8)
            .tolist()
        )
        if recent_messages:
            st.caption("Add a recent recognized or spoken message")
            recent_columns = st.columns(2)
            for index, recent in enumerate(recent_messages):
                with recent_columns[index % 2]:
                    if st.button(recent[:80], key=f"recent_sentence_{index}", width="stretch"):
                        st.session_state.sentence_words.append(recent)
                        st.rerun()

    # Display and speak selected message
    if "quick_message" in st.session_state:

        selected_message = st.session_state["quick_message"]

        st.success(f"Selected Message: {selected_message}")
        st.code(selected_message, language=None)

        speak_col, clear_col = st.columns(2)
        with speak_col:
          speak_message_clicked = st.button("🔊 Speak Message", width="stretch")
        with clear_col:
          clear_message_clicked = st.button("Clear Message", width="stretch")

        if clear_message_clicked:
            st.session_state.pop("quick_message", None)
            st.rerun()

        if speak_message_clicked:

            import pyttsx3

            try:
                engine = pyttsx3.init("sapi5")
                voices = engine.getProperty("voices")

                if language == "Hindi":

                    hindi_voice = next(
                        (
                            voice for voice in voices
                            if any(word in (
                                voice.name + " " + voice.id
                            ).lower() for word in [
                                "hindi", "hi-in", "hemant", "kalpana"
                            ])
                        ),
                        None
                    )

                    if hindi_voice is None:
                        st.error(
                            "Hindi voice is not installed. "
                            "Please install a Hindi speech voice in Windows."
                        )
                    else:
                        engine.setProperty("voice", hindi_voice.id)
                        engine.say(selected_message)
                        engine.runAndWait()

                else:
                    english_voice = next(
                        (
                            voice for voice in voices
                            if any(word in (
                                voice.name + " " + voice.id
                            ).lower() for word in [
                                "english", "en-us", "en-gb"
                            ])
                        ),
                        None
                    )

                    if english_voice:
                        engine.setProperty("voice", english_voice.id)

                    engine.say(selected_message)
                    engine.runAndWait()

                engine.stop()

            except Exception as e:
                st.error(f"Speech error: {e}")
# =========================================================
# SMART GESTURE CONTROL
# =========================================================

elif selected_page == "Smart Gesture Control":

    section_heading(
        "TOUCH-FREE COMPUTER ACCESS",
        "Smart Gesture Control",
        "Control your computer using simple hand gestures."
    )

    st.info(
        "The existing 8-class model drives these actions. Open Palm remains a mouse click. "
        "Pointing cursor movement, pinch clicking, and swipe actions are not trained in this model."
    )

    controls_enabled = st.checkbox(
        "I understand these gestures will send real keyboard/mouse input, and I give permission to start the controller.",
        key="smart_control_permission",
    )
    if (
        not controls_enabled
        and st.session_state.get("recognition_process_mode") == "Smart Gesture Control"
    ):
        stop_recognition()
        st.warning("Smart Gesture Control stopped because permission was withdrawn.")

    sensitivity = st.slider("Recognition sensitivity", 50, 90, 65, 5, help="Higher values require more model confidence.")
    cooldown_seconds = st.slider("Action cooldown (seconds)", 0.5, 3.0, 1.5, 0.5)
    action_profile = st.radio(
        "Action profile",
        ["Open Palm click only (safer)", "All listed actions"],
        help="Click-only mode ignores all keyboard actions. Full mode requires the permission checkbox above.",
        key="smart_action_profile",
    )
    smart_camera_index = st.selectbox(
        "Smart Gesture camera index",
        options=[0, 1, 2, 3],
        index=0,
        key="smart_camera_index",
    )

    st.markdown("### Gesture actions")
    controls = [
        ("OPEN_PALM", "Mouse click"),
        ("FIST", "Stop the gesture controller"),
        ("POINT_UP", "Page Up"),
        ("CROSSED_FINGERS", "Page Down"),
        ("VICTORY", "Alt + Tab"),
        ("THUMBS_UP", "Enter"),
        ("THUMBS_DOWN", "Escape"),
    ]
    if action_profile == "Open Palm click only (safer)":
        controls = [controls[0]]
    st.dataframe(
        pd.DataFrame(controls, columns=["Gesture", "Computer action"]),
        width="stretch",
        hide_index=True,
    )

    start_col, stop_col = st.columns(2)
    with start_col:
        if st.button("▶ Start Smart Gesture Control", width="stretch", disabled=not controls_enabled):
            controller_args = [
                "--confidence-limit", str(sensitivity),
                "--cooldown", str(cooldown_seconds),
                "--camera-index", str(smart_camera_index),
                "--permission-granted",
            ]
            if action_profile == "Open Palm click only (safer)":
                controller_args.append("--open-palm-click-only")
            start_recognition(
                SMART_GESTURE_FILE,
                "Smart Gesture Control",
                controller_args,
            )
    with stop_col:
        if st.button("🛑 EMERGENCY STOP — stop controller", type="primary", width="stretch"):
            stop_recognition()

    if recognition_is_running():
        st.success(
            f"{st.session_state.recognition_process_mode or 'Recognition'} is running."
        )
    else:
        st.warning("Smart Gesture Control is currently stopped.")

    st.caption(
        "The controller also has a confidence threshold and cooldown to reduce "
        "accidental repeated actions. Press Q in its camera window or use Stop here."
    )

# =========================================================
# SPEAKER VOICE / TEXT-TO-SPEECH
# =========================================================

elif selected_page == "Speaker Voice":

    section_heading(
        "BROWSER TEXT-TO-SPEECH",
        "Speaker Voice",
        "Build, review and speak text using voices available on this device."
    )

    if st.button(
        "Load sentence builder text",
        disabled=not st.session_state.sentence_words,
    ):
        st.session_state.speaker_voice_text = " ".join(st.session_state.sentence_words)
        st.rerun()

    speaker_text = st.text_area(
        "Text to speak",
        value=" ".join(st.session_state.sentence_words),
        height=130,
        key="speaker_voice_text",
    )
    language_option = st.radio(
        "Preferred language",
        ["English", "Hindi", "Odia", "Browser default"],
        horizontal=True,
        key="speaker_voice_language",
    )
    locale_map = {
        "English": "en-IN",
        "Hindi": "hi-IN",
        "Odia": "or-IN",
        "Browser default": "",
    }
    speed = st.slider("Speech speed", 0.6, 1.5, 1.0, 0.1)

    js_language = locale_map[language_option]
    js_text = safe_script_json(speaker_text)
    js_locale = safe_script_json(js_language)
    component_html(
        f"""
        <div style="font:14px sans-serif;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <button id="speak-text" type="button">Speak</button>
          <button id="repeat-text" type="button">Repeat</button>
          <button id="stop-text" type="button">Stop</button>
          <span id="speech-status" role="status" aria-live="polite"></span>
        </div>
        <script>
          const text = {js_text};
          const requestedLocale = {js_locale};
          const status = document.getElementById("speech-status");
          let previousText = text;
          function speak(value) {{
            if (!("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) {{
              status.textContent = "Speech synthesis is not supported by this browser.";
              return;
            }}
            if (!value.trim()) {{
              status.textContent = "Enter text before speaking.";
              return;
            }}
            window.speechSynthesis.cancel();
            const voices = window.speechSynthesis.getVoices();
            const language = requestedLocale.toLowerCase().split("-")[0];
            const matchingVoice = language
              ? voices.find(voice => voice.lang && voice.lang.toLowerCase().startsWith(language))
              : null;
            const utterance = new SpeechSynthesisUtterance(value);
            utterance.lang = requestedLocale || (matchingVoice ? matchingVoice.lang : "");
            utterance.rate = {speed};
            if (matchingVoice) utterance.voice = matchingVoice;
            utterance.onstart = () => {{
              status.textContent = matchingVoice
                ? "Speaking with " + matchingVoice.name + "."
                : "No matching voice listed; using browser default if available.";
            }};
            utterance.onend = () => {{
              status.textContent += " Playback ended; confirm sound on this device.";
            }};
            utterance.onerror = event => {{
              status.textContent = "Speech error: " + event.error;
            }};
            previousText = value;
            window.speechSynthesis.speak(utterance);
          }}
          document.getElementById("speak-text").onclick = () => speak(text);
          document.getElementById("repeat-text").onclick = () => speak(previousText);
          document.getElementById("stop-text").onclick = () => {{
            if ("speechSynthesis" in window) {{
              window.speechSynthesis.cancel();
              status.textContent = "Speech cancelled.";
            }} else {{
              status.textContent = "Speech synthesis is not supported by this browser.";
            }}
          }};
          function updateVoiceStatus() {{
            if (!("speechSynthesis" in window)) {{
              status.textContent = "Speech synthesis is not supported by this browser.";
              return;
            }}
            const voices = window.speechSynthesis.getVoices();
            if (!voices.length) {{
              status.textContent = "Waiting for browser/device voices.";
              return;
            }}
            if (!requestedLocale) {{
              status.textContent = voices.length + " device voice(s) available; browser default will be used.";
              return;
            }}
            const language = requestedLocale.toLowerCase().split("-")[0];
            const matching = voices.filter(
              voice => voice.lang && voice.lang.toLowerCase().startsWith(language)
            );
            status.textContent = matching.length
              ? matching.length + " voice(s) available for " + requestedLocale + "."
              : "No " + requestedLocale + " voice listed; browser default will be attempted.";
          }}
          if ("speechSynthesis" in window) {{
            window.speechSynthesis.addEventListener("voiceschanged", updateVoiceStatus);
            setTimeout(updateVoiceStatus, 500);
          }} else {{
            updateVoiceStatus();
          }}
        </script>
        """,
        height=70,
    )
    st.caption("Playback depends on browser/device voices; the status cannot confirm that audio was physically heard.")

# =========================================================
# ISL ALPHABET LEARNING
# =========================================================

elif selected_page == "ISL Alphabet Learning":

    section_heading(
        "FINGER-SPELLING LEARNING",
        "ISL Alphabet Learning",
        "Browse letters and mark practice progress. Alphabet recognition is enabled only with a validated model."
    )

    selected_letter = st.selectbox("Choose a letter", list(ISL_ALPHABET), key="alphabet_letter")

    alphabet_col, practice_col = st.columns([1, 1])
    with alphabet_col:
        st.markdown(f"## {selected_letter}")
        st.info(
            "Lesson: find this letter in an expert-verified ISL fingerspelling "
            "reference, observe the hand shape and orientation, then practice "
            "briefly. Do not substitute an ASL alphabet shape."
        )
        st.warning(
            "A verified ISL alphabet reference image is not bundled here; "
            "this lesson does not invent or display a sign."
        )
        st.link_button(
            "Open official ISLRTC alphabet/dictionary",
            "https://divyangjan.depwd.gov.in/islrtc/",
            help="Verify the letter before presenting it as ISL.",
        )
    with practice_col:
        practiced = st.checkbox(
            f"I practiced {selected_letter} using a verified reference",
            key=f"alphabet_practiced_{selected_letter}",
        )
        completed_letters = set(
            st.session_state.get("alphabet_practice_completed", [])
        )
        if practiced:
            completed_letters.add(selected_letter)
        else:
            completed_letters.discard(selected_letter)
        st.session_state.alphabet_practice_completed = sorted(completed_letters)
        st.caption(
            "Progress is stored for this browser session; it is not saved across "
            "sessions or accounts."
        )
        st.progress(
            len(completed_letters) / len(ISL_ALPHABET),
            text=f"{len(completed_letters)} / {len(ISL_ALPHABET)} letters practiced",
        )

    st.divider()
    st.caption("Recognition: alphabet model availability is separate from this lesson checklist.")
    if Path(BASE_DIR / "models" / "isl_alphabet_model.keras").is_file():
        st.warning("An alphabet model file exists, but it has not been live-validated by this audit.")
    else:
        st.info("No active alphabet model is available.")

# =========================================================
# LIVE LOCATION
# =========================================================

elif selected_page == "Live Location":

    section_heading(
        "DEVICE LOCATION",
        "Live Location",
        "Request browser geolocation and create a reviewed Google Maps link."
    )

    st.warning("Location only works securely on localhost or HTTPS and requires browser permission.")
    location = streamlit_geolocation()
    coordinates = validated_location_coordinates(location)

    if coordinates is None:
        st.info(
            "No valid location received. Use the location button above and allow "
            "browser access; denial, timeout, unavailable GPS, or an insecure "
            "origin can prevent a result."
        )
        if location not in (None, {}):
            if (
                isinstance(location, dict)
                and location.get("latitude") is None
                and location.get("longitude") is None
            ):
                st.info("The location component has not returned a position yet.")
            else:
                st.error("The browser returned invalid coordinates; they were not used.")
    else:
        latitude, longitude = coordinates
        accuracy = location.get("accuracy") if isinstance(location, dict) else None
        try:
            accuracy_value = float(accuracy) if accuracy is not None else None
        except (TypeError, ValueError):
            accuracy_value = None

        st.success("Valid location received.")
        st.write(f"Latitude: {latitude}")
        st.write(f"Longitude: {longitude}")
        if accuracy_value is not None and math.isfinite(accuracy_value) and accuracy_value >= 0:
            st.write(f"Accuracy: approximately {accuracy_value:.1f} metres")
        location_signature = (latitude, longitude, accuracy_value)
        if st.session_state.get("last_location_signature") != location_signature:
            st.session_state.last_location_signature = location_signature
            st.session_state.last_location_received = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
        st.caption(
            "Last received by this app: "
            f"{st.session_state.last_location_received}. "
            "The geolocation component does not provide the GPS sample timestamp."
        )
        st.link_button(
            "Open in Google Maps",
            f"https://www.google.com/maps?q={latitude},{longitude}",
        )
        from urllib.parse import urlencode

        map_bounds = {
            "bbox": ",".join((
                str(max(-180.0, longitude - 0.01)),
                str(max(-90.0, latitude - 0.01)),
                str(min(180.0, longitude + 0.01)),
                str(min(90.0, latitude + 0.01)),
            )),
            "layer": "mapnik",
            "marker": f"{latitude},{longitude}",
        }
        map_url = (
            "https://www.openstreetmap.org/export/embed.html"
            f"?{urlencode(map_bounds)}"
        )
        st.iframe(map_url, height=360)

# =========================================================
# MODEL EVALUATION
# =========================================================

elif selected_page == "Model Evaluation":

    section_heading(
        "MEASURED MODEL STATUS",
        "Model Evaluation",
        "Only existing measured reports are shown. No synthetic or hardcoded accuracy is added."
    )

    evaluation_summary = BASE_DIR / "reports" / "phase4_same_signer_diagnosis_20261117_213128" / "summary.json"
    if evaluation_summary.is_file():
        try:
            summary = json.loads(evaluation_summary.read_text(encoding="utf-8"))
            active = summary["models"]["active"]
            candidate = summary["models"]["candidate"]
            metric_cols = st.columns(4)
            metric_cols[0].metric("Active accuracy", f"{active['accuracy']:.1%}")
            metric_cols[1].metric("Candidate accuracy", f"{candidate['accuracy']:.1%}")
            metric_cols[2].metric("Test sequences", summary["sequences"])
            metric_cols[3].metric("Classes", summary["classes"])
            st.warning(
                f"Evaluation identity: {summary.get('identity_basis', 'not recorded')}. "
                "This separate-session test is same-signer evidence, not a "
                "signer-independent or live-webcam accuracy claim."
            )
            st.dataframe(
                pd.DataFrame({
                    "Metric": ["Accuracy", "Balanced accuracy", "Macro precision", "Macro recall", "Macro F1", "Weighted F1"],
                    "Active": [
                        active["accuracy"], active["balanced_accuracy"], active["macro_precision"],
                        active["macro_recall"], active["macro_f1"], active["weighted_f1"],
                    ],
                    "Candidate": [
                        candidate["accuracy"], candidate["balanced_accuracy"], candidate["macro_precision"],
                        candidate["macro_recall"], candidate["macro_f1"], candidate["weighted_f1"],
                    ],
                }),
                width="stretch",
                hide_index=True,
            )
            metrics_dir = evaluation_summary.parent
            model_choice = st.radio(
                "Per-class report",
                ["Active model", "Unpromoted candidate"],
                horizontal=True,
                key="evaluation_model_choice",
            )
            prefix = "active" if model_choice == "Active model" else "candidate"
            class_report_path = metrics_dir / f"{prefix}_per_class_metrics.csv"
            confusion_path = metrics_dir / f"{prefix}_confusion_matrix.csv"
            if class_report_path.is_file():
                st.dataframe(
                    pd.read_csv(class_report_path),
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.info(f"No per-class report is present for {model_choice.lower()}.")
            if confusion_path.is_file():
                with st.expander(f"{model_choice} confusion matrix"):
                    st.dataframe(
                        pd.read_csv(confusion_path, index_col=0),
                        width="stretch",
                    )
        except (OSError, json.JSONDecodeError, KeyError) as error:
            st.error(f"The saved 40-word evaluation summary could not be read: {error}")
    else:
        st.info("No 40-word evaluation summary is available.")

    candidate_holdout_path = (
        BASE_DIR / "word_model" / "manual_model" / "retrained"
        / "candidate_20261117_200707" / "evaluation_summary.json"
    )
    if candidate_holdout_path.is_file():
        try:
            candidate_holdout = json.loads(
                candidate_holdout_path.read_text(encoding="utf-8")
            )
            st.subheader("Candidate sequence-folder holdout")
            st.metric(
                "Candidate held-out accuracy",
                f"{candidate_holdout['accuracy']:.1%}",
            )
            st.caption(
                f"{candidate_holdout['test_sequences']} test sequences; "
                f"split: {candidate_holdout['split']}. This is an in-dataset "
                "chronological sequence-folder split, not an independent signer "
                "or recording-session result. The candidate is not the active model."
            )
        except (OSError, json.JSONDecodeError, KeyError) as error:
            st.error(f"The candidate holdout summary could not be read: {error}")

    st.divider()
    st.subheader("Static and dynamic model status")
    statics_col, dynamic_col = st.columns(2)
    static_dataset_path = BASE_DIR / "dataset" / "hand_signs.csv"
    dynamic_dataset_path = BASE_DIR / "dataset" / "dynamic_gestures.csv"
    try:
        static_dataset = pd.read_csv(static_dataset_path)
        static_label_column = "label" if "label" in static_dataset else None
        static_class_count = (
            int(static_dataset[static_label_column].nunique())
            if static_label_column
            else 0
        )
        static_row_count = len(static_dataset)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        static_class_count = 0
        static_row_count = 0
        st.error(f"Could not inspect the static dataset: {error}")
    try:
        dynamic_dataset = pd.read_csv(dynamic_dataset_path)
        dynamic_label_column = "label" if "label" in dynamic_dataset else None
        dynamic_counts = (
            dynamic_dataset[dynamic_label_column].value_counts().to_dict()
            if dynamic_label_column
            else {}
        )
        dynamic_row_count = len(dynamic_dataset)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        dynamic_counts = {}
        dynamic_row_count = 0
        st.error(f"Could not inspect the dynamic dataset: {error}")

    with statics_col:
        st.metric("Static dataset classes", static_class_count)
        st.metric("Static landmark rows", static_row_count)
        st.info("No held-out live static-gesture accuracy report is available.")
    with dynamic_col:
        st.metric("Dynamic dataset rows", dynamic_row_count)
        st.write("Rows by label:", dynamic_counts or "No labelled samples found.")
        st.info("Dynamic training remains blocked until all required labels have valid samples.")

# =========================================================
# FOOTER
# =========================================================

render_footer()
