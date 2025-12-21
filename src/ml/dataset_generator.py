"""
Dataset generator for training fatigue classification model.
Generates synthetic data and manages real collected data.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List
from datetime import datetime

from ..config.config import (
    DATASETS_DIR,
    TRAIN_TEST_SPLIT,
    NORMAL_BLINK_RATE_MIN,
    NORMAL_BLINK_RATE_MAX
)
from ..utils.logger import get_logger

logger = get_logger('dataset_generator')


class DatasetGenerator:
    """Generates synthetic training data for fatigue classification."""
    
    def __init__(self):
        """Initialize dataset generator."""
        self.feature_names = [
            'ear_mean', 'ear_std', 'ear_min', 'ear_max', 'ear_median',
            'ear_skew', 'ear_kurtosis', 'ear_trend',
            'blink_mean', 'blink_std', 'blink_min', 'blink_max', 'blink_trend',
            'gaze_mean', 'gaze_std', 'gaze_min',
            'duration_minutes', 'duration_log',
            'ear_blink_interaction',
            'low_blink_indicator',
            'low_ear_indicator'
        ]
        
        logger.info("Dataset generator initialized")
    
    def generate_synthetic_data(self, n_samples_per_class: int = 500) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic training data.
        
        Classes:
        0: Normal - No fatigue
        1: Mild Strain - Early signs
        2: Moderate Strain - Clear fatigue
        3: Severe Strain - Critical fatigue
        
        Args:
            n_samples_per_class: Number of samples to generate per class
            
        Returns:
            Tuple of (features, labels)
        """
        logger.info(f"Generating {n_samples_per_class * 4} synthetic samples...")
        
        all_features = []
        all_labels = []
        
        # Class 0: Normal
        features = self._generate_class_features(
            n_samples=n_samples_per_class,
            ear_mean=(0.28, 0.35),
            blink_rate=(NORMAL_BLINK_RATE_MIN, NORMAL_BLINK_RATE_MAX),
            gaze_stability=(0.7, 0.95),
            duration=(5, 30)  # Minutes
        )
        all_features.append(features)
        all_labels.extend([0] * n_samples_per_class)
        
        # Class 1: Mild Strain
        features = self._generate_class_features(
            n_samples=n_samples_per_class,
            ear_mean=(0.26, 0.30),
            blink_rate=(9, 14),
            gaze_stability=(0.6, 0.8),
            duration=(20, 45)
        )
        all_features.append(features)
        all_labels.extend([1] * n_samples_per_class)
        
        # Class 2: Moderate Strain
        features = self._generate_class_features(
            n_samples=n_samples_per_class,
            ear_mean=(0.22, 0.28),
            blink_rate=(5, 10),
            gaze_stability=(0.5, 0.7),
            duration=(40, 70)
        )
        all_features.append(features)
        all_labels.extend([2] * n_samples_per_class)
        
        # Class 3: Severe Strain
        features = self._generate_class_features(
            n_samples=n_samples_per_class,
            ear_mean=(0.18, 0.25),
            blink_rate=(2, 7),
            gaze_stability=(0.3, 0.6),
            duration=(60, 120)
        )
        all_features.append(features)
        all_labels.extend([3] * n_samples_per_class)
        
        # Combine all
        X = np.vstack(all_features)
        y = np.array(all_labels)
        
        # Shuffle
        indices = np.random.permutation(len(y))
        X = X[indices]
        y = y[indices]
        
        logger.info(f"Generated dataset: X shape={X.shape}, y shape={y.shape}")
        
        return X, y
    
    def _generate_class_features(self, n_samples: int, ear_mean: Tuple[float, float],
                                 blink_rate: Tuple[float, float],
                                 gaze_stability: Tuple[float, float],
                                 duration: Tuple[float, float]) -> np.ndarray:
        """
        Generate features for a specific fatigue class.
        
        Args:
            n_samples: Number of samples to generate
            ear_mean: (min, max) range for average EAR
            blink_rate: (min, max) range for blink rate
            gaze_stability: (min, max) range for gaze stability
            duration: (min, max) range for session duration in minutes
            
        Returns:
            Feature matrix (n_samples, n_features)
        """
        features = []
        
        for _ in range(n_samples):
            # Generate base metrics
            ear_avg = np.random.uniform(*ear_mean)
            blink_avg = np.random.uniform(*blink_rate)
            gaze_avg = np.random.uniform(*gaze_stability)
            dur_min = np.random.uniform(*duration)
            
            # EAR features (with realistic variance)
            ear_values = np.random.normal(ear_avg, 0.02, 30)
            ear_values = np.clip(ear_values, 0.15, 0.40)
            
            feat = [
                np.mean(ear_values),  # ear_mean
                np.std(ear_values),   # ear_std
                np.min(ear_values),   # ear_min
                np.max(ear_values),   # ear_max
                np.median(ear_values),  # ear_median
                self._safe_skew(ear_values),  # ear_skew
                self._safe_kurtosis(ear_values),  # ear_kurtosis
                np.random.uniform(-0.01, 0.01),  # ear_trend
            ]
            
            # Blink rate features
            blink_values = np.random.normal(blink_avg, 2, 30)
            blink_values = np.clip(blink_values, 0, 30)
            
            feat.extend([
                np.mean(blink_values),  # blink_mean
                np.std(blink_values),   # blink_std
                np.min(blink_values),   # blink_min
                np.max(blink_values),   # blink_max
                np.random.uniform(-0.5, 0.5),  # blink_trend
            ])
            
            # Gaze stability features
            gaze_values = np.random.normal(gaze_avg, 0.1, 30)
            gaze_values = np.clip(gaze_values, 0, 1)
            
            feat.extend([
                np.mean(gaze_values),  # gaze_mean
                np.std(gaze_values),   # gaze_std
                np.min(gaze_values),   # gaze_min
            ])
            
            # Duration features
            feat.extend([
                dur_min,  # duration_minutes
                np.log1p(dur_min * 60),  # duration_log (in seconds)
            ])
            
            # Derived features
            feat.append(ear_avg * blink_avg)  # ear_blink_interaction
            feat.append(1.0 if blink_avg < 10 else 0.0)  # low_blink_indicator
            feat.append(1.0 if ear_avg < 0.25 else 0.0)  # low_ear_indicator
            
            features.append(feat)
        
        return np.array(features, dtype=np.float32)
    
    @staticmethod
    def _safe_skew(values):
        """Calculate skewness safely."""
        from scipy import stats
        if len(values) < 3:
            return 0.0
        try:
            return stats.skew(values)
        except:
            return 0.0
    
    @staticmethod
    def _safe_kurtosis(values):
        """Calculate kurtosis safely."""
        from scipy import stats
        if len(values) < 4:
            return 0.0
        try:
            return stats.kurtosis(values)
        except:
            return 0.0
    
    def save_dataset(self, X: np.ndarray, y: np.ndarray, filename: str = None):
        """
        Save dataset to disk.
        
        Args:
            X: Feature matrix
            y: Labels
            filename: Output filename (auto-generated if None)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"synthetic_dataset_{timestamp}.npz"
        
        filepath = DATASETS_DIR / filename
        
        np.savez(filepath, X=X, y=y, feature_names=self.feature_names)
        logger.info(f"Dataset saved to {filepath}")
        
        # Also save as CSV for easy inspection
        csv_path = filepath.with_suffix('.csv')
        df = pd.DataFrame(X, columns=self.feature_names)
        df['label'] = y
        df.to_csv(csv_path, index=False)
        logger.info(f"Dataset CSV saved to {csv_path}")
    
    def load_dataset(self, filename: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load dataset from disk.
        
        Args:
            filename: Dataset filename
            
        Returns:
            Tuple of (X, y)
        """
        filepath = DATASETS_DIR / filename
        
        data = np.load(filepath)
        X = data['X']
        y = data['y']
        
        logger.info(f"Loaded dataset from {filepath}: X shape={X.shape}, y shape={y.shape}")
        
        return X, y
    
    def split_dataset(self, X: np.ndarray, y: np.ndarray, 
                     test_size: float = TRAIN_TEST_SPLIT) -> Tuple:
        """
        Split dataset into train and test sets.
        
        Args:
            X: Feature matrix
            y: Labels
            test_size: Fraction for test set
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        from sklearn.model_selection import train_test_split
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        logger.info(f"Dataset split: Train={len(X_train)}, Test={len(X_test)}")
        
        return X_train, X_test, y_train, y_test


if __name__ == "__main__":
    # Test dataset generator
    generator = DatasetGenerator()
    
    # Generate synthetic data
    X, y = generator.generate_synthetic_data(n_samples_per_class=500)
    
    print(f"Generated dataset: {X.shape}")
    print(f"Label distribution: {np.bincount(y)}")
    print(f"\nFeature names ({len(generator.feature_names)}):")
    for i, name in enumerate(generator.feature_names):
        print(f"  {i}: {name}")
    
    # Save dataset
    generator.save_dataset(X, y, "test_dataset.npz")
    
    # Split dataset
    X_train, X_test, y_train, y_test = generator.split_dataset(X, y)
    print(f"\nTrain set: {X_train.shape}")
    print(f"Test set: {X_test.shape}")
    
    print("\nDataset generator test completed!")
