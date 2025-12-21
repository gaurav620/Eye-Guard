"""
Configuration file for Eyeguard application.
Contains all global constants, thresholds, and paths.
"""

import os
from pathlib import Path

# ============== PROJECT PATHS ==============
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = DATA_DIR / "logs"
DATASETS_DIR = DATA_DIR / "datasets"
REPORTS_DIR = DATA_DIR / "reports"

# Ensure directories exist
for directory in [DATA_DIR, MODELS_DIR, ASSETS_DIR, LOGS_DIR, DATASETS_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============== EYE DETECTION PARAMETERS ==============
# Eye Aspect Ratio (EAR) thresholds
EAR_THRESHOLD = 0.25  # Below this indicates closed eye
EAR_CONSEC_FRAMES = 3  # Consecutive frames for valid blink

# Blink rate parameters (normal human: 15-20 blinks/min)
NORMAL_BLINK_RATE_MIN = 12  # Minimum healthy blinks per minute
NORMAL_BLINK_RATE_MAX = 25  # Maximum healthy blinks per minute
LOW_BLINK_WARNING = 8  # Alert if below this rate

# ============== FATIGUE DETECTION THRESHOLDS ==============
# Session duration thresholds (in minutes)
MILD_STRAIN_DURATION = 20  # Start noticing strain
MODERATE_STRAIN_DURATION = 40  # Clear eye strain
SEVERE_STRAIN_DURATION = 60  # Critical eye strain

# Eye closure duration (in seconds)
PROLONGED_CLOSURE_THRESHOLD = 2.0  # Indicates drowsiness or strain

# Gaze stability (lower means more movement/instability)
GAZE_STABILITY_THRESHOLD = 0.7  # Scale 0-1

# ============== ALERT SYSTEM CONFIGURATION ==============
# 20-20-20 Rule: Every 20 minutes, look at something 20 feet away for 20 seconds
ALERT_INTERVAL_MINUTES = 20  # Time between break reminders
BREAK_DURATION_SECONDS = 20  # Recommended break duration
SNOOZE_DURATION_MINUTES = 5  # Snooze time for alerts

# Alert severity levels
ALERT_LEVELS = {
    'INFO': {'color': '#4CAF50', 'sound': 'gentle_chime.wav'},
    'WARNING': {'color': '#FF9800', 'sound': 'warning_beep.wav'},
    'CRITICAL': {'color': '#F44336', 'sound': 'urgent_alert.wav'}
}

# ============== CAMERA SETTINGS ==============
CAMERA_INDEX = 0  # Default camera (0 = built-in webcam)
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# ============== ML MODEL PARAMETERS ==============
MODEL_PATH = MODELS_DIR / "fatigue_classifier.h5"
SCALER_PATH = MODELS_DIR / "feature_scaler.pkl"

# Feature engineering
FEATURE_WINDOW_SIZE = 30  # Frames to consider for moving average
PREDICTION_INTERVAL = 10  # Update prediction every N frames

# Fatigue classification labels
FATIGUE_LABELS = {
    0: 'Normal',
    1: 'Mild Strain',
    2: 'Moderate Strain',
    3: 'Severe Strain'
}

# Model training parameters
TRAIN_TEST_SPLIT = 0.2
VALIDATION_SPLIT = 0.15
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 0.001

# ============== GUI SETTINGS ==============
WINDOW_TITLE = "Eyeguard - Eye Strain Detection"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
THEME = "dark"  # Options: "dark", "light"

# Colors (Dark theme)
COLORS = {
    'bg_primary': '#1E1E1E',
    'bg_secondary': '#2D2D2D',
    'bg_tertiary': '#3A3A3A',
    'text_primary': '#FFFFFF',
    'text_secondary': '#B0B0B0',
    'accent': '#00A8E8',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'danger': '#F44336',
    'info': '#2196F3'
}

# Metric display update rate (milliseconds)
GUI_UPDATE_INTERVAL = 100  # 10 FPS for GUI updates

# ============== DATA LOGGING ==============
DATABASE_NAME = "eyeguard_sessions.db"
DATABASE_PATH = DATA_DIR / DATABASE_NAME

# Logging intervals
LOG_METRICS_INTERVAL = 5  # Log metrics every N seconds
SESSION_TIMEOUT = 300  # End session after 5 minutes of inactivity

# ============== REPORTING ==============
REPORT_FORMATS = ['PDF', 'CSV', 'JSON']
CHART_DPI = 150
CHART_STYLE = 'seaborn-v0_8-darkgrid'

# Report types
REPORT_TYPES = {
    'daily': 1,
    'weekly': 7,
    'monthly': 30
}

# ============== USER PROFILES ==============
PROFILES_FILE = DATA_DIR / "user_profiles.json"
DEFAULT_PROFILE = "default_user"

# ============== MEDIAPIPE CONFIGURATION ==============
# Face Mesh parameters
FACE_MESH_MAX_FACES = 1
FACE_MESH_REFINE_LANDMARKS = True
FACE_MESH_MIN_DETECTION_CONFIDENCE = 0.5
FACE_MESH_MIN_TRACKING_CONFIDENCE = 0.5

# Specific landmark indices for eyes (MediaPipe Face Mesh)
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

# Iris landmarks
LEFT_IRIS_INDICES = [468, 469, 470, 471, 472]
RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477]

# ============== DEVELOPMENT & DEBUGGING ==============
DEBUG_MODE = True
SHOW_FPS = True
SHOW_LANDMARKS = True
VERBOSE_LOGGING = True

# ============== VERSION INFO ==============
APP_VERSION = "1.0.0"
APP_AUTHOR = "Gaurav Kumar Mehta, Ayan Biswas, Arpan Mirsha, Arka Bhattacharya"
APP_DESCRIPTION = "Eye Strain Detection System using Computer Vision and Machine Learning"

# ============== HELPER FUNCTIONS ==============
def get_alert_config(severity='INFO'):
    """Get alert configuration for given severity level."""
    return ALERT_LEVELS.get(severity, ALERT_LEVELS['INFO'])

def get_fatigue_label(level):
    """Get fatigue label from numeric level."""
    return FATIGUE_LABELS.get(level, 'Unknown')

def is_low_blink_rate(blink_rate):
    """Check if blink rate indicates eye strain."""
    return blink_rate < LOW_BLINK_WARNING

def calculate_session_severity(duration_minutes, blink_rate, ear_avg):
    """
    Calculate overall session severity based on multiple factors.
    Returns: 0 (Normal), 1 (Mild), 2 (Moderate), 3 (Severe)
    """
    severity_score = 0
    
    # Factor 1: Session duration
    if duration_minutes > SEVERE_STRAIN_DURATION:
        severity_score += 3
    elif duration_minutes > MODERATE_STRAIN_DURATION:
        severity_score += 2
    elif duration_minutes > MILD_STRAIN_DURATION:
        severity_score += 1
    
    # Factor 2: Blink rate
    if blink_rate < 5:
        severity_score += 3
    elif blink_rate < 8:
        severity_score += 2
    elif blink_rate < 12:
        severity_score += 1
    
    # Factor 3: Average EAR (eye openness)
    if ear_avg < 0.15:  # Eyes very tired/closing
        severity_score += 2
    elif ear_avg < 0.20:
        severity_score += 1
    
    # Normalize to 0-3 scale
    if severity_score >= 6:
        return 3  # Severe
    elif severity_score >= 4:
        return 2  # Moderate
    elif severity_score >= 2:
        return 1  # Mild
    else:
        return 0  # Normal

if __name__ == "__main__":
    print(f"Eyeguard v{APP_VERSION}")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Configuration loaded successfully!")
