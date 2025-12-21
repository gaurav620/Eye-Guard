"""
Calibration system for personalized eye tracking thresholds.
Allows users to calibrate the system to their individual eye characteristics.
"""

import time
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass, asdict

from ..utils.logger import get_logger

logger = get_logger('calibration')


@dataclass
class CalibrationData:
    """Calibration results for a user."""
    ear_baseline: float  # Average EAR when relaxed
    ear_threshold: float  # Personalized threshold for closed eyes
    blink_baseline: float  # Personal baseline blink rate
    gaze_baseline: float  # Baseline gaze stability
    calibration_date: str
    is_calibrated: bool = True


class CalibrationSystem:
    """Manages user calibration for personalized thresholds."""
    
    def __init__(self):
        """Initialize calibration system."""
        self.calibration_data: Optional[CalibrationData] = None
        logger.info("Calibration system initialized")
    
    def run_calibration(self, eye_detector, blink_analyzer, gaze_tracker, 
                       camera_manager, duration_seconds: int = 30) -> CalibrationData:
        """
        Run calibration process.
        
        Args:
            eye_detector: Eye detector instance
            blink_analyzer: Blink analyzer instance
            gaze_tracker: Gaze tracker instance
            camera_manager: Camera manager instance
            duration_seconds: Calibration duration
            
        Returns:
            CalibrationData with personalized thresholds
        """
        logger.info(f"Starting {duration_seconds}s calibration...")
        
        print("\n" + "="*60)
        print("CALIBRATION WIZARD")
        print("="*60)
        print(f"\nSit comfortably and look at the screen naturally.")
        print(f"Blink normally during the {duration_seconds}-second calibration.\n")
        input("Press ENTER when ready...")
        
        ear_values = []
        blink_count = 0
        gaze_values = []
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        print("\nCalibrating", end="", flush=True)
        
        while time.time() < end_time:
            ret, frame = camera_manager.read_frame()
            if not ret:
                continue
            
            frame = camera_manager.preprocess_frame(frame)
            eye_data = eye_detector.process_frame(frame)
            
            if eye_data:
                ear_values.append(eye_data.avg_ear)
                
                blink_detected = blink_analyzer.process_ear(eye_data.avg_ear)
                if blink_detected:
                    blink_count += 1
                
                gaze_data = gaze_tracker.calculate_gaze(
                    eye_data.left_iris_center,
                    eye_data.right_iris_center,
                    eye_data.left_eye_landmarks,
                    eye_data.right_eye_landmarks
                )
                
                if gaze_data:
                    gaze_values.append(gaze_data.gaze_stability)
            
            # Progress indicator
            if int(time.time() - start_time) % 5 == 0:
                print(".", end="", flush=True)
        
        print(" Done!\n")
        
        # Calculate calibration values
        if not ear_values:
            logger.error("Calibration failed - no data collected")
            raise ValueError("Could not collect calibration data")
        
        ear_baseline = float(np.median(ear_values))
        ear_std = float(np.std(ear_values))
        ear_threshold = max(0.20, ear_baseline - 2 * ear_std)  # 2 std deviations below median
        
        actual_duration_minutes = duration_seconds / 60.0
        blink_baseline = (blink_count / actual_duration_minutes) if actual_duration_minutes > 0 else 15.0
        
        gaze_baseline = float(np.mean(gaze_values)) if gaze_values else 0.7
        
        calibration = CalibrationData(
            ear_baseline=round(ear_baseline, 3),
            ear_threshold=round(ear_threshold, 3),
            blink_baseline=round(blink_baseline, 1),
            gaze_baseline=round(gaze_baseline, 2),
            calibration_date=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.calibration_data = calibration
        
        # Display results
        print("Calibration Results:")
        print(f"  EAR Baseline: {calibration.ear_baseline}")
        print(f"  EAR Threshold: {calibration.ear_threshold}")
        print(f"  Blink Rate Baseline: {calibration.blink_baseline:.1f}/min")
        print(f"  Gaze Stability: {calibration.gaze_baseline}")
        print()
        
        logger.info(f"Calibration completed: {calibration}")
        
        return calibration
    
    def get_personalized_threshold(self, metric: str) -> Optional[float]:
        """
        Get personalized threshold for a metric.
        
        Args:
            metric: Metric name ('ear', 'blink_rate', 'gaze')
            
        Returns:
            Personalized threshold value
        """
        if not self.calibration_data:
            return None
        
        if metric == 'ear':
            return self.calibration_data.ear_threshold
        elif metric == 'blink_rate':
            return self.calibration_data.blink_baseline
        elif metric == 'gaze':
            return self.calibration_data.gaze_baseline
        
        return None
    
    def save_calibration(self, filepath: str):
        """Save calibration data to file."""
        if not self.calibration_data:
            logger.warning("No calibration data to save")
            return
        
        import json
        with open(filepath, 'w') as f:
            json.dump(asdict(self.calibration_data), f, indent=2)
        
        logger.info(f"Calibration saved to {filepath}")
    
    def load_calibration(self, filepath: str) -> bool:
        """
        Load calibration data from file.
        
        Returns:
            True if loaded successfully
        """
        try:
            import json
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.calibration_data = CalibrationData(**data)
            logger.info(f"Calibration loaded from {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
            return False


if __name__ == "__main__":
    print("Calibration system test")
    calib = CalibrationSystem()
    print(f"Initialized: {calib}")
