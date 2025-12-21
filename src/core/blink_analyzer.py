"""
Blink analyzer module.
Tracks blink patterns, calculates blink rate, and detects anomalies.
"""

import time
from collections import deque
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime

from ..config.config import (
    EAR_THRESHOLD,
    EAR_CONSEC_FRAMES,
    NORMAL_BLINK_RATE_MIN,
    NORMAL_BLINK_RATE_MAX,
    LOW_BLINK_WARNING
)
from ..utils.logger import get_logger

logger = get_logger('blink_analyzer')


@dataclass
class BlinkEvent:
    """Data class for a single blink event."""
    timestamp: float
    duration_frames: int
    min_ear: float


@dataclass
class BlinkStats:
    """Statistics about blink patterns."""
    total_blinks: int = 0
    blink_rate: float = 0.0  # Blinks per minute
    avg_blink_duration: float = 0.0  # Frames
    time_since_last_blink: float = 0.0  # Seconds
    is_low_blink_rate: bool = False
    recent_blinks: List[BlinkEvent] = field(default_factory=list)


class BlinkAnalyzer:
    """Analyzes blink patterns for eye strain detection."""
    
    def __init__(self, window_size: int = 60):
        """
        Initialize blink analyzer.
        
        Args:
            window_size: Number of seconds to analyze for blink rate
        """
        self.window_size = window_size
        
        # Blink tracking
        self.total_blinks = 0
        self.blink_history = deque(maxlen=1000)  # Store last 1000 blinks
        self.recent_ear_values = deque(maxlen=window_size * 30)  # Assume 30 FPS
        
        # State tracking for blink detection
        self.eye_closed_counter = 0
        self.is_blinking = False
        self.blink_start_time = None
        self.min_ear_during_blink = 1.0
        
        # Timing
        self.start_time = time.time()
        self.last_blink_time = None
        
        logger.info(f"Blink analyzer initialized with {window_size}s window")
    
    def process_ear(self, avg_ear: float) -> bool:
        """
        Process EAR value and detect blinks.
        
        Args:
            avg_ear: Average Eye Aspect Ratio
            
        Returns:
            True if a new blink was detected, False otherwise
        """
        current_time = time.time()
        self.recent_ear_values.append(avg_ear)
        
        blink_detected = False
        
        # Eye closure detection
        if avg_ear < EAR_THRESHOLD:
            self.eye_closed_counter += 1
            
            # Track minimum EAR during potential blink
            if not self.is_blinking:
                self.is_blinking = True
                self.blink_start_time = current_time
                self.min_ear_during_blink = avg_ear
            else:
                self.min_ear_during_blink = min(self.min_ear_during_blink, avg_ear)
        
        else:  # Eye is open
            # Check if a blink just completed
            if self.eye_closed_counter >= EAR_CONSEC_FRAMES:
                # Valid blink detected!
                self._register_blink(current_time, self.eye_closed_counter)
                blink_detected = True
                logger.debug(f"Blink detected! Duration: {self.eye_closed_counter} frames")
            
            # Reset counters
            self.eye_closed_counter = 0
            self.is_blinking = False
            self.min_ear_during_blink = 1.0
        
        return blink_detected
    
    def _register_blink(self, timestamp: float, duration_frames: int):
        """Register a blink event."""
        blink_event = BlinkEvent(
            timestamp=timestamp,
            duration_frames=duration_frames,
            min_ear=self.min_ear_during_blink
        )
        
        self.blink_history.append(blink_event)
        self.total_blinks += 1
        self.last_blink_time = timestamp
    
    def get_blink_rate(self, window_seconds: Optional[int] = None) -> float:
        """
        Calculate blink rate (blinks per minute) over a time window.
        
        Args:
            window_seconds: Time window in seconds (uses instance window if None)
            
        Returns:
            Blinks per minute
        """
        if window_seconds is None:
            window_seconds = self.window_size
        
        if not self.blink_history:
            return 0.0
        
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Count blinks in the window
        recent_blinks = [b for b in self.blink_history if b.timestamp >= cutoff_time]
        
        if not recent_blinks:
            return 0.0
        
        # Calculate rate
        time_span = current_time - recent_blinks[0].timestamp
        if time_span == 0:
            return 0.0
        
        blinks_per_second = len(recent_blinks) / time_span
        blinks_per_minute = blinks_per_second * 60
        
        return blinks_per_minute
    
    def get_stats(self) -> BlinkStats:
        """
        Get current blink statistics.
        
        Returns:
            BlinkStats object with current statistics
        """
        blink_rate = self.get_blink_rate()
        
        # Calculate average blink duration
        if self.blink_history:
            avg_duration = sum(b.duration_frames for b in self.blink_history) / len(self.blink_history)
            recent_blinks = list(self.blink_history)[-10:]  # Last 10 blinks
        else:
            avg_duration = 0.0
            recent_blinks = []
        
        # Time since last blink
        if self.last_blink_time:
            time_since_last = time.time() - self.last_blink_time
        else:
            time_since_last = 0.0
        
        # Check if blink rate is low
        is_low = blink_rate < LOW_BLINK_WARNING
        
        return BlinkStats(
            total_blinks=self.total_blinks,
            blink_rate=blink_rate,
            avg_blink_duration=avg_duration,
            time_since_last_blink=time_since_last,
            is_low_blink_rate=is_low,
            recent_blinks=recent_blinks
        )
    
    def is_healthy_blink_rate(self) -> bool:
        """
        Check if current blink rate is healthy.
        
        Returns:
            True if blink rate is within normal range
        """
        rate = self.get_blink_rate()
        return NORMAL_BLINK_RATE_MIN <= rate <= NORMAL_BLINK_RATE_MAX
    
    def get_blink_pattern_analysis(self) -> Dict:
        """
        Analyze blink patterns for anomalies.
        
        Returns:
            Dictionary with pattern analysis
        """
        if len(self.blink_history) < 10:
            return {
                'sufficient_data': False,
                'pattern': 'INSUFFICIENT_DATA'
            }
        
        # Get recent blinks
        recent = list(self.blink_history)[-20:]
        
        # Calculate inter-blink intervals
        intervals = []
        for i in range(1, len(recent)):
            interval = recent[i].timestamp - recent[i-1].timestamp
            intervals.append(interval)
        
        if not intervals:
            return {'sufficient_data': False}
        
        # Statistics
        import numpy as np
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        # Pattern classification
        pattern = 'NORMAL'
        if mean_interval > 10:  # More than 10 seconds between blinks
            pattern = 'INFREQUENT'
        elif mean_interval < 2:  # Less than 2 seconds
            pattern = 'FREQUENT'
        elif std_interval > 5:  # High variability
            pattern = 'IRREGULAR'
        
        return {
            'sufficient_data': True,
            'pattern': pattern,
            'mean_interval_seconds': mean_interval,
            'std_interval_seconds': std_interval,
            'regularity_score': 1.0 / (1.0 + std_interval)  # 0-1, higher is more regular
        }
    
    def reset(self):
        """Reset the analyzer state."""
        self.total_blinks = 0
        self.blink_history.clear()
        self.recent_ear_values.clear()
        self.eye_closed_counter = 0
        self.is_blinking = False
        self.start_time = time.time()
        self.last_blink_time = None
        logger.info("Blink analyzer reset")
    
    def get_summary(self) -> str:
        """Get a text summary of blink statistics."""
        stats = self.get_stats()
        pattern = self.get_blink_pattern_analysis()
        
        summary = f"""
Blink Analysis Summary:
-----------------------
Total Blinks: {stats.total_blinks}
Current Blink Rate: {stats.blink_rate:.1f} blinks/min
Average Duration: {stats.avg_blink_duration:.1f} frames
Time Since Last Blink: {stats.time_since_last_blink:.1f}s
Health Status: {'LOW' if stats.is_low_blink_rate else 'NORMAL'}
Pattern: {pattern.get('pattern', 'N/A')}
"""
        return summary.strip()


if __name__ == "__main__":
    # Test blink analyzer with simulated data
    import numpy as np
    
    analyzer = BlinkAnalyzer(window_size=60)
    
    # Simulate 1 minute of data with random blinks
    fps = 30
    duration = 60  # seconds
    
    print("Simulating blink detection...")
    
    for frame in range(fps * duration):
        # Simulate normal eye state with occasional blinks
        # Normal EAR is around 0.3, closed is < 0.25
        
        # Random blink every 3-5 seconds
        if frame % (fps * 4) == 0:
            # Simulate blink (3-4 frames of closure)
            ear = 0.15
        else:
            ear = 0.30 + np.random.normal(0, 0.02)
        
        blink_detected = analyzer.process_ear(ear)
        
        if blink_detected:
            stats = analyzer.get_stats()
            print(f"Frame {frame}: Blink! Total: {stats.total_blinks}, Rate: {stats.blink_rate:.1f}/min")
        
        # Simulate frame delay
        time.sleep(0.001)
    
    # Final summary
    print("\n" + analyzer.get_summary())
    print("\nBlink analyzer test completed!")
