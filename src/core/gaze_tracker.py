"""
Gaze tracker module.
Tracks gaze direction, stability, and screen focus duration.
"""

import numpy as np
from collections import deque
from typing import Tuple, Optional, Dict
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger('gaze_tracker')


@dataclass
class GazeData:
    """Data class for gaze tracking information."""
    left_gaze_ratio: float  # 0-1, left to right
    right_gaze_ratio: float
    avg_gaze_ratio: float
    vertical_gaze_ratio: float  # 0-1, up to down
    gaze_stability: float  # 0-1, higher is more stable
    looking_center: bool
    gaze_direction: str  # "CENTER", "LEFT", "RIGHT", "UP", "DOWN"


class GazeTracker:
    """Tracks gaze direction and stability for eye strain analysis."""
    
    def __init__(self, history_size: int = 30):
        """
        Initialize gaze tracker.
        
        Args:
            history_size: Number of frames to keep for stability calculation
        """
        self.history_size = history_size
        
        # Gaze history for stability calculation
        self.horizontal_history = deque(maxlen=history_size)
        self.vertical_history = deque(maxlen=history_size)
        
        # Thresholds for gaze direction
        self.center_threshold = 0.15  # Distance from center to be considered centered
        self.horizontal_threshold = 0.6  # Threshold for left/right detection
        self.vertical_threshold = 0.6  # Threshold for up/down detection
        
        logger.info(f"Gaze tracker initialized with history size {history_size}")
    
    def calculate_gaze(self, left_iris_center: Optional[Tuple[float, float]],
                      right_iris_center: Optional[Tuple[float, float]],
                      left_eye_landmarks: list,
                      right_eye_landmarks: list) -> Optional[GazeData]:
        """
        Calculate gaze direction and stability.
        
        Args:
            left_iris_center: (x, y) of left iris center
            right_iris_center: (x, y) of right iris center
            left_eye_landmarks: List of left eye landmark points
            right_eye_landmarks: List of right eye landmark points
            
        Returns:
            GazeData object or None if insufficient data
        """
        if not left_iris_center or not right_iris_center:
            return None
        
        if not left_eye_landmarks or not right_eye_landmarks:
            return None
        
        # Calculate gaze ratios for each eye
        left_ratio_h, left_ratio_v = self._calculate_eye_gaze_ratio(
            left_iris_center, left_eye_landmarks
        )
        right_ratio_h, right_ratio_v = self._calculate_eye_gaze_ratio(
            right_iris_center, right_eye_landmarks
        )
        
        # Average gaze ratios
        avg_horizontal = (left_ratio_h + right_ratio_h) / 2.0
        avg_vertical = (left_ratio_v + right_ratio_v) / 2.0
        
        # Update history
        self.horizontal_history.append(avg_horizontal)
        self.vertical_history.append(avg_vertical)
        
        # Calculate stability
        stability = self._calculate_stability()
        
        # Determine gaze direction
        direction = self._determine_gaze_direction(avg_horizontal, avg_vertical)
        looking_center = direction == "CENTER"
        
        return GazeData(
            left_gaze_ratio=left_ratio_h,
            right_gaze_ratio=right_ratio_h,
            avg_gaze_ratio=avg_horizontal,
            vertical_gaze_ratio=avg_vertical,
            gaze_stability=stability,
            looking_center=looking_center,
            gaze_direction=direction
        )
    
    def _calculate_eye_gaze_ratio(self, iris_center: Tuple[float, float],
                                  eye_landmarks: list) -> Tuple[float, float]:
        """
        Calculate gaze ratio for a single eye.
        
        Returns:
            (horizontal_ratio, vertical_ratio) where:
            - horizontal: 0 = looking left, 0.5 = center, 1 = looking right
            - vertical: 0 = looking up, 0.5 = center, 1 = looking down
        """
        if len(eye_landmarks) < 6:
            return (0.5, 0.5)
        
        # Get eye bounding box from landmarks
        points = np.array(eye_landmarks, dtype=np.float32)
        
        x_min = np.min(points[:, 0])
        x_max = np.max(points[:, 0])
        y_min = np.min(points[:, 1])
        y_max = np.max(points[:, 1])
        
        iris_x, iris_y = iris_center
        
        # Calculate horizontal ratio
        eye_width = x_max - x_min
        if eye_width > 0:
            horizontal_ratio = (iris_x - x_min) / eye_width
            horizontal_ratio = np.clip(horizontal_ratio, 0.0, 1.0)
        else:
            horizontal_ratio = 0.5
        
        # Calculate vertical ratio
        eye_height = y_max - y_min
        if eye_height > 0:
            vertical_ratio = (iris_y - y_min) / eye_height
            vertical_ratio = np.clip(vertical_ratio, 0.0, 1.0)
        else:
            vertical_ratio = 0.5
        
        return (horizontal_ratio, vertical_ratio)
    
    def _calculate_stability(self) -> float:
        """
        Calculate gaze stability based on variance in gaze history.
        
        Returns:
            Stability score 0-1 (higher is more stable)
        """
        if len(self.horizontal_history) < 10:
            return 1.0  # Not enough data, assume stable
        
        # Calculate variance in both directions
        h_variance = np.var(list(self.horizontal_history))
        v_variance = np.var(list(self.vertical_history))
        
        # Combined variance
        total_variance = h_variance + v_variance
        
        # Convert to stability score (0-1, lower variance = higher stability)
        # Typical variance range is 0-0.05 for stable gaze
        stability = 1.0 / (1.0 + total_variance * 100)
        
        return np.clip(stability, 0.0, 1.0)
    
    def _determine_gaze_direction(self, horizontal: float, vertical: float) -> str:
        """
        Determine gaze direction from ratios.
        
        Args:
            horizontal: Horizontal gaze ratio (0-1)
            vertical: Vertical gaze ratio (0-1)
            
        Returns:
            Direction string: "CENTER", "LEFT", "RIGHT", "UP", "DOWN"
        """
        # Check if looking at center
        h_centered = abs(horizontal - 0.5) < self.center_threshold
        v_centered = abs(vertical - 0.5) < self.center_threshold
        
        if h_centered and v_centered:
            return "CENTER"
        
        # Determine primary direction
        h_diff = abs(horizontal - 0.5)
        v_diff = abs(vertical - 0.5)
        
        if h_diff > v_diff:
            # Horizontal movement is dominant
            if horizontal < 0.5 - self.center_threshold:
                return "LEFT"
            elif horizontal > 0.5 + self.center_threshold:
                return "RIGHT"
        else:
            # Vertical movement is dominant
            if vertical < 0.5 - self.center_threshold:
                return "UP"
            elif vertical > 0.5 + self.center_threshold:
                return "DOWN"
        
        return "CENTER"
    
    def get_focus_duration(self) -> float:
        """
        Estimate how long the user has been looking at the same direction.
        
        Returns:
            Estimated duration in seconds (based on frame count and assumed FPS)
        """
        if len(self.horizontal_history) < 2:
            return 0.0
        
        # Count consecutive frames with similar gaze (within threshold)
        consecutive_count = 1
        last_h = self.horizontal_history[-1]
        last_v = self.vertical_history[-1]
        
        for i in range(len(self.horizontal_history) - 2, -1, -1):
            h_diff = abs(self.horizontal_history[i] - last_h)
            v_diff = abs(self.vertical_history[i] - last_v)
            
            if h_diff < 0.1 and v_diff < 0.1:  # Similar gaze
                consecutive_count += 1
            else:
                break
        
        # Assume 30 FPS
        duration_seconds = consecutive_count / 30.0
        return duration_seconds
    
    def is_stable_focus(self, threshold: float = 0.7) -> bool:
        """
        Check if gaze is stably focused.
        
        Args:
            threshold: Minimum stability score to be considered stable
            
        Returns:
            True if gaze is stable
        """
        stability = self._calculate_stability()
        return stability >= threshold
    
    def reset(self):
        """Reset gaze tracking history."""
        self.horizontal_history.clear()
        self.vertical_history.clear()
        logger.debug("Gaze tracker reset")


if __name__ == "__main__":
    # Test gaze tracker
    tracker = GazeTracker(history_size=30)
    
    # Simulate some gaze data
    print("Testing gaze tracker...")
    
    # Simulate eye landmarks (simple rectangle)
    left_eye_landmarks = [(100, 100), (120, 95), (140, 100), (140, 110), (120, 115), (100, 110)]
    right_eye_landmarks = [(200, 100), (220, 95), (240, 100), (240, 110), (220, 115), (200, 110)]
    
    # Test 1: Looking center
    gaze_data = tracker.calculate_gaze(
        left_iris_center=(120, 105),
        right_iris_center=(220, 105),
        left_eye_landmarks=left_eye_landmarks,
        right_eye_landmarks=right_eye_landmarks
    )
    print(f"Center gaze: {gaze_data.gaze_direction}, Stability: {gaze_data.gaze_stability:.3f}")
    
    # Test 2: Looking left
    gaze_data = tracker.calculate_gaze(
        left_iris_center=(110, 105),
        right_iris_center=(210, 105),
        left_eye_landmarks=left_eye_landmarks,
        right_eye_landmarks=right_eye_landmarks
    )
    print(f"Left gaze: {gaze_data.gaze_direction}, Ratio: {gaze_data.avg_gaze_ratio:.3f}")
    
    # Test 3: Looking right
    gaze_data = tracker.calculate_gaze(
        left_iris_center=(130, 105),
        right_iris_center=(230, 105),
        left_eye_landmarks=left_eye_landmarks,
        right_eye_landmarks=right_eye_landmarks
    )
    print(f"Right gaze: {gaze_data.gaze_direction}, Ratio: {gaze_data.avg_gaze_ratio:.3f}")
    
    print("\nGaze tracker test completed!")
