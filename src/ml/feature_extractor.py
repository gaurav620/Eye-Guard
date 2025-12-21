"""
Feature extractor for machine learning.
Extracts time-series features from eye tracking data for fatigue classification.
"""

import numpy as np
from collections import deque
from typing import Dict, List, Optional
from scipy import stats
import joblib

from ..config.config import (
    FEATURE_WINDOW_SIZE,
    SCALER_PATH
)
from ..utils.logger import get_logger

logger = get_logger('feature_extractor')


class FeatureExtractor:
    """Extracts features from eye tracking data for ML model."""
    
    def __init__(self, window_size: int = FEATURE_WINDOW_SIZE):
        """
        Initialize feature extractor.
        
        Args:
            window_size: Number of frames to use for feature calculation
        """
        self.window_size = window_size
        
        # Data buffers
        self.ear_buffer = deque(maxlen=window_size)
        self.blink_rate_buffer = deque(maxlen=window_size)
        self.gaze_stability_buffer = deque(maxlen=window_size)
        self.session_duration_buffer = deque(maxlen=window_size)
        
        # Scaler for normalization
        self.scaler = None
        self._load_scaler()
        
        logger.info(f"Feature extractor initialized with window size {window_size}")
    
    def _load_scaler(self):
        """Load pre-trained scaler if exists."""
        try:
            if SCALER_PATH.exists():
                self.scaler = joblib.load(SCALER_PATH)
                logger.info("Loaded feature scaler from disk")
        except Exception as e:
            logger.warning(f"Could not load scaler: {e}")
            self.scaler = None
    
    def add_data_point(self, ear: float, blink_rate: float, 
                       gaze_stability: float, session_duration: float):
        """
        Add a new data point to the buffers.
        
        Args:
            ear: Eye Aspect Ratio
            blink_rate: Current blink rate (blinks/min)
            gaze_stability: Gaze stability score (0-1)
            session_duration: Session duration in seconds
        """
        self.ear_buffer.append(ear)
        self.blink_rate_buffer.append(blink_rate)
        self.gaze_stability_buffer.append(gaze_stability)
        self.session_duration_buffer.append(session_duration)
    
    def extract_features(self) -> Optional[np.ndarray]:
        """
        Extract feature vector from buffered data.
        
        Returns:
            Feature vector as numpy array, or None if insufficient data
        """
        if len(self.ear_buffer) < 10:  # Need minimum data
            return None
        
        features = []
        
        # ===== EAR Features =====
        ear_array = np.array(self.ear_buffer, dtype=np.float32)
        
        features.extend([
            np.mean(ear_array),  # Mean EAR
            np.std(ear_array),   # Standard deviation
            np.min(ear_array),   # Minimum
            np.max(ear_array),   # Maximum
            np.median(ear_array),  # Median
            stats.skew(ear_array),  # Skewness
            stats.kurtosis(ear_array),  # Kurtosis
        ])
        
        # EAR trend (linear regression slope)
        if len(ear_array) > 1:
            x = np.arange(len(ear_array))
            slope, _, _, _, _ = stats.linregress(x, ear_array)
            features.append(slope)
        else:
            features.append(0.0)
        
        # ===== Blink Rate Features =====
        blink_array = np.array(self.blink_rate_buffer, dtype=np.float32)
        
        features.extend([
            np.mean(blink_array),  # Mean blink rate
            np.std(blink_array),   # Standard deviation
            np.min(blink_array),   # Minimum
            np.max(blink_array),   # Maximum
        ])
        
        # Blink rate trend
        if len(blink_array) > 1:
            x = np.arange(len(blink_array))
            slope, _, _, _, _ = stats.linregress(x, blink_array)
            features.append(slope)
        else:
            features.append(0.0)
        
        # ===== Gaze Stability Features =====
        gaze_array = np.array(self.gaze_stability_buffer, dtype=np.float32)
        
        features.extend([
            np.mean(gaze_array),  # Mean stability
            np.std(gaze_array),   # Standard deviation
            np.min(gaze_array),   # Minimum
        ])
        
        # ===== Session Duration Features =====
        duration_array = np.array(self.session_duration_buffer, dtype=np.float32)
        
        current_duration = duration_array[-1] if len(duration_array) > 0 else 0
        features.extend([
            current_duration / 60.0,  # Duration in minutes
            np.log1p(current_duration),  # Log-transformed duration
        ])
        
        # ===== Derived Features =====
        # EAR * Blink rate interaction
        features.append(np.mean(ear_array) * np.mean(blink_array))
        
        # Fatigue indicators
        features.append(1.0 if np.mean(blink_array) < 10 else 0.0)  # Low blink rate indicator
        features.append(1.0 if np.mean(ear_array) < 0.25 else 0.0)  # Low EAR indicator
        
        # Convert to numpy array
        feature_vector = np.array(features, dtype=np.float32)
        
        # Normalize if scaler is available
        if self.scaler is not None:
            feature_vector = self.scaler.transform(feature_vector.reshape(1, -1)).flatten()
        
        return feature_vector
    
    def get_feature_names(self) -> List[str]:
        """
        Get names of all features.
        
        Returns:
            List of feature names
        """
        return [
            # EAR features
            'ear_mean', 'ear_std', 'ear_min', 'ear_max', 'ear_median',
            'ear_skew', 'ear_kurtosis', 'ear_trend',
            
            # Blink rate features
            'blink_mean', 'blink_std', 'blink_min', 'blink_max', 'blink_trend',
            
            # Gaze stability features
            'gaze_mean', 'gaze_std', 'gaze_min',
            
            # Session duration features
            'duration_minutes', 'duration_log',
            
            # Derived features
            'ear_blink_interaction',
            'low_blink_indicator',
            'low_ear_indicator'
        ]
    
    def get_feature_dict(self) -> Dict[str, float]:
        """
        Get features as a dictionary.
        
        Returns:
            Dictionary mapping feature names to values
        """
        features = self.extract_features()
        if features is None:
            return {}
        
        names = self.get_feature_names()
        return dict(zip(names, features))
    
    def reset(self):
        """Reset all buffers."""
        self.ear_buffer.clear()
        self.blink_rate_buffer.clear()
        self.gaze_stability_buffer.clear()
        self.session_duration_buffer.clear()
        logger.debug("Feature extractor reset")
    
    @staticmethod
    def create_and_save_scaler(training_data: np.ndarray, save_path: str = None):
        """
        Create and save a feature scaler from training data.
        
        Args:
            training_data: 2D array of training features (n_samples, n_features)
            save_path: Path to save scaler (uses default if None)
        """
        from sklearn.preprocessing import StandardScaler
        
        if save_path is None:
            save_path = SCALER_PATH
        
        scaler = StandardScaler()
        scaler.fit(training_data)
        
        joblib.dump(scaler, save_path)
        logger.info(f"Scaler saved to {save_path}")
        
        return scaler


if __name__ == "__main__":
    # Test feature extractor
    extractor = FeatureExtractor(window_size=30)
    
    # Simulate adding data
    for i in range(50):
        ear = 0.30 + np.random.normal(0, 0.02)
        blink_rate = 15 + np.random.normal(0, 2)
        gaze_stability = 0.8 + np.random.normal(0, 0.1)
        duration = i * 2  # 2 seconds per iteration
        
        extractor.add_data_point(ear, blink_rate, gaze_stability, duration)
    
    # Extract features
    features = extractor.extract_features()
    feature_dict = extractor.get_feature_dict()
    
    print("Feature Vector Shape:", features.shape if features is not None else None)
    print(f"\nTotal Features: {len(extractor.get_feature_names())}")
    print("\nFeature Dictionary:")
    for name, value in feature_dict.items():
        print(f"  {name}: {value:.4f}")
    
    print("\nFeature extractor test completed!")
