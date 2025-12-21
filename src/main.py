"""
Main application file for Eyeguard - Eye Strain Detection System.
Integrates all components and provides the main GUI interface.
"""

import sys
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.camera_manager import CameraManager
from src.core.eye_detector import EyeDetector
from src.core.blink_analyzer import BlinkAnalyzer
from src.core.gaze_tracker import GazeTracker
from src.core.session_manager import SessionManager
from src.core.alert_system import AlertSystem, AlertSeverity
from src.ml.feature_extractor import FeatureExtractor
from src.ml.fatigue_model import FatigueClassifier
from src.config.config import (
    WINDOW_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    COLORS,
    FATIGUE_LABELS,
    MODEL_PATH,
    GUI_UPDATE_INTERVAL,
    SHOW_FPS,
    SHOW_LANDMARKS
)
from src.utils.logger import get_logger

logger = get_logger('main_app')


class EyeguardApp:
    """Main Eyeguard application with GUI."""
    
    def __init__(self, root):
        """
        Initialize the Eyeguard application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLORS['bg_primary'])
        
        # Initialize components
        logger.info("Initializing Eyeguard components...")
        
        self.camera = CameraManager()
        self.eye_detector = EyeDetector()
        self.blink_analyzer = BlinkAnalyzer()
        self.gaze_tracker = GazeTracker()
        self.session_manager = SessionManager()
        self.alert_system = AlertSystem()
        self.feature_extractor = FeatureExtractor()
        
        # ML Model (load if exists)
        self.fatigue_classifier = None
        self._load_ml_model()
        
        # State
        self.is_running = False
        self.session_active = False
        self.current_frame = None
        self.last_update_time = time.time()
        
        # GUI Setup
        self._setup_gui()
        
        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("Eyeguard application initialized")
    
    def _load_ml_model(self):
        """Load the ML model if it exists."""
        try:
            if MODEL_PATH.exists():
                self.fatigue_classifier = FatigueClassifier(input_dim=21, num_classes=4)
                self.fatigue_classifier.load_model(MODEL_PATH)
                logger.info("Fatigue classification model loaded")
            else:
                logger.warning(f"Model not found at {MODEL_PATH}. Run model_trainer.py first.")
                logger.warning("Fatigue prediction will be disabled.")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.fatigue_classifier = None
    
    def _setup_gui(self):
        """Setup the GUI layout."""
        # Main container
        main_frame = tk.Frame(self.root, bg=COLORS['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Video feed
        left_panel = tk.Frame(main_frame, bg=COLORS['bg_secondary'], relief=tk.RIDGE, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Video feed label
        self.video_label = tk.Label(left_panel, bg='black')
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel - Metrics and controls
        right_panel = tk.Frame(main_frame, bg=COLORS['bg_secondary'], width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # App title
        title_label = tk.Label(
            right_panel,
            text="EYEGUARD",
            font=("Arial", 24, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent']
        )
        title_label.pack(pady=(10, 5))
        
        subtitle_label = tk.Label(
            right_panel,
            text="Eye Strain Detection System",
            font=("Arial", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Control buttons
        button_frame = tk.Frame(right_panel, bg=COLORS['bg_secondary'])
        button_frame.pack(pady=10)
        
        self.start_button = tk.Button(
            button_frame,
            text="START SESSION",
            command=self.start_session,
            bg=COLORS['success'],
            fg='white',
            font=("Arial", 12, "bold"),
            width=15,
            height=2
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = tk.Button(
            button_frame,
            text="STOP SESSION",
            command=self.stop_session,
            bg=COLORS['danger'],
            fg='white',
            font=("Arial", 12, "bold"),
            width=15,
            height=2,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Metrics frame
        metrics_frame = tk.LabelFrame(
            right_panel,
            text="Real-Time Metrics",
            font=("Arial", 12, "bold"),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            relief=tk.RIDGE,
            bd=2
        )
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create metric labels
        self._create_metric_row(metrics_frame, "Session Duration:", "session_duration", 0)
        self._create_metric_row(metrics_frame, "Total Blinks:", "total_blinks", 1)
        self._create_metric_row(metrics_frame, "Blink Rate:", "blink_rate", 2)
        self._create_metric_row(metrics_frame, "Eye Aspect Ratio:", "ear", 3)
        self._create_metric_row(metrics_frame, "Gaze Stability:", "gaze_stability", 4)
        self._create_metric_row(metrics_frame, "Fatigue Level:", "fatigue_level", 5)
        
        # Status frame
        status_frame = tk.LabelFrame(
            right_panel,
            text="Status",
            font=("Arial", 12, "bold"),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            relief=tk.RIDGE,
            bd=2
        )
        status_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 10))
        
        self.status_text = tk.Label(
            status_frame,
            text="System Ready",
            font=("Arial", 10),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['info'],
            wraplength=350,
            justify=tk.LEFT
        )
        self.status_text.pack(padx=10, pady=10)
        
        # Dictionary to store metric labels
        self.metric_labels = {}
    
    def _create_metric_row(self, parent, label_text, metric_name, row):
        """Create a metric display row."""
        label = tk.Label(
            parent,
            text=label_text,
            font=("Arial", 10),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_secondary'],
            anchor='w'
        )
        label.grid(row=row, column=0, sticky='w', padx=10, pady=5)
        
        value_label = tk.Label(
            parent,
            text="--",
            font=("Arial", 10, "bold"),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            anchor='e'
        )
        value_label.grid(row=row, column=1, sticky='e', padx=10, pady=5)
        
        self.metric_labels[metric_name] = value_label
    
    def start_session(self):
        """Start a monitoring session."""
        if self.session_active:
            return
        
        logger.info("Starting session...")
        
        # Open camera
        if not self.camera.open():
            self.update_status("Error: Could not open camera!", COLORS['danger'])
            return
        
        # Start session
        self.session_manager.start_session()
        self.session_active = True
        self.is_running = True
        
        # Reset analyzers
        self.blink_analyzer.reset()
        self.gaze_tracker.reset()
        self.alert_system.reset()
        self.feature_extractor.reset()
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("Session started - Monitoring active", COLORS['success'])
        
        # Start video processing
        self.process_frame()
        
        logger.info("Session started successfully")
    
    def stop_session(self):
        """Stop the monitoring session."""
        if not self.session_active:
            return
        
        logger.info("Stopping session...")
        
        self.is_running = False
        self.session_active = False
        
        # Stop session
        self.session_manager.end_session()
        
        # Release camera
        self.camera.release()
        
        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Session stopped", COLORS['warning'])
        
        # Clear video
        self.video_label.config(image='')
        
        logger.info("Session stopped")
    
    def process_frame(self):
        """Process a single frame from the camera."""
        if not self.is_running:
            return
        
        # Read frame
        ret, frame = self.camera.read_frame()
        if not ret:
            logger.warning("Failed to read frame")
            self.root.after(GUI_UPDATE_INTERVAL, self.process_frame)
            return
        
        # Preprocess
        frame = self.camera.preprocess_frame(frame)
        
        # Detect eyes
        eye_data = self.eye_detector.process_frame(frame)
        
        if eye_data:
            # Analyze blink
            blink_detected = self.blink_analyzer.process_ear(eye_data.avg_ear)
            blink_stats = self.blink_analyzer.get_stats()
            
            # Track gaze
            gaze_data = self.gaze_tracker.calculate_gaze(
                eye_data.left_iris_center,
                eye_data.right_iris_center,
                eye_data.left_eye_landmarks,
                eye_data.right_eye_landmarks
            )
            
            # Update session metrics
            self.session_manager.update_metrics(
                ear=eye_data.avg_ear,
                blink_rate=blink_stats.blink_rate,
                blink_detected=blink_detected
            )
            
            # Get session duration
            duration = self.session_manager.get_session_duration()
            
            # Extract features for ML
            gaze_stability = gaze_data.gaze_stability if gaze_data else 0.5
            self.feature_extractor.add_data_point(
                ear=eye_data.avg_ear,
                blink_rate=blink_stats.blink_rate,
                gaze_stability=gaze_stability,
                session_duration=duration
            )
            
            # Predict fatigue level
            fatigue_level = 0
            if self.fatigue_classifier:
                features = self.feature_extractor.extract_features()
                if features is not None:
                    pred_class, confidence, probs = self.fatigue_classifier.predict_single(features)
                    fatigue_level = pred_class
                    self.session_manager.current_session.current_fatigue_level = fatigue_level
            
            # Check for alerts
            alerts = self.alert_system.check_alerts(
                blink_rate=blink_stats.blink_rate,
                fatigue_level=fatigue_level,
                session_duration=duration,
                gaze_stability=gaze_stability
            )
            
            # Handle alerts
            for alert in alerts:
                self.session_manager.record_alert(
                    alert.alert_type.value,
                    alert.severity.value,
                    alert.message
                )
                self.show_alert(alert)
            
            # Draw eye landmarks if enabled
            if SHOW_LANDMARKS:
                frame = self.eye_detector.draw_eye_landmarks(frame, eye_data)
            
            # Update metrics display
            self.update_metrics(blink_stats, eye_data, gaze_data, fatigue_level)
        
        # Add FPS if enabled
        if SHOW_FPS:
            frame = self.camera.draw_fps(frame, self.camera.get_fps())
        
        # Convert frame to PhotoImage and display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img_tk = ImageTk.PhotoImage(image=img)
        
        self.video_label.config(image=img_tk)
        self.video_label.image = img_tk
        
        # Schedule next frame
        self.root.after(GUI_UPDATE_INTERVAL, self.process_frame)
    
    def update_metrics(self, blink_stats, eye_data, gaze_data, fatigue_level):
        """Update the metrics display."""
        duration = self.session_manager.get_session_duration()
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        self.metric_labels['session_duration'].config(
            text=f"{minutes:02d}:{seconds:02d}"
        )
        
        self.metric_labels['total_blinks'].config(
            text=str(blink_stats.total_blinks)
        )
        
        # Blink rate with color coding
        blink_rate_text = f"{blink_stats.blink_rate:.1f}/min"
        if blink_stats.is_low_blink_rate:
            color = COLORS['warning']
        else:
            color = COLORS['success']
        self.metric_labels['blink_rate'].config(text=blink_rate_text, fg=color)
        
        self.metric_labels['ear'].config(text=f"{eye_data.avg_ear:.3f}")
        
        if gaze_data:
            self.metric_labels['gaze_stability'].config(
                text=f"{gaze_data.gaze_stability:.2f}"
            )
        
        # Fatigue level with color coding
        fatigue_text = FATIGUE_LABELS.get(fatigue_level, "Unknown")
        if fatigue_level == 0:
            color = COLORS['success']
        elif fatigue_level == 1:
            color = COLORS['info']
        elif fatigue_level == 2:
            color = COLORS['warning']
        else:
            color = COLORS['danger']
        self.metric_labels['fatigue_level'].config(text=fatigue_text, fg=color)
    
    def show_alert(self, alert):
        """Show an alert notification."""
        # Update status text
        if alert.severity == AlertSeverity.CRITICAL:
            color = COLORS['danger']
        elif alert.severity == AlertSeverity.WARNING:
            color = COLORS['warning']
        else:
            color = COLORS['info']
        
        self.update_status(f"ALERT: {alert.message}", color)
        
        # Log alert
        logger.warning(f"Alert: {alert.message}")
        
        # Could add popup notification here
    
    def update_status(self, message, color=None):
        """Update the status message."""
        if color is None:
            color = COLORS['text_primary']
        self.status_text.config(text=message, fg=color)
    
    def on_closing(self):
        """Handle window closing."""
        logger.info("Closing application...")
        
        if self.session_active:
            self.stop_session()
        
        # Release resources
        self.eye_detector.release()
        
        self.root.destroy()
        logger.info("Application closed")


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("EYEGUARD - EYE STRAIN DETECTION SYSTEM")
    logger.info("=" * 60)
    logger.info("Starting application...")
    
    root = tk.Tk()
    app = EyeguardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
