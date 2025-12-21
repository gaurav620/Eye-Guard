"""
Session manager for tracking user sessions.
Manages session lifecycle, metrics aggregation, and break tracking.
"""

import time
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass, field

from ..config.config import (
    SESSION_TIMEOUT,
    DEFAULT_PROFILE
)
from ..utils.logger import get_logger
from ..utils.database import get_database

logger = get_logger('session_manager')


@dataclass
class SessionData:
    """Data class for session information."""
    session_id: int
    user_profile: str
    start_time: float
    end_time: Optional[float] = None
    is_active: bool = True
    is_paused: bool = False
    pause_start: Optional[float] = None
    total_pause_duration: float = 0.0
    
    # Metrics
    total_blinks: int = 0
    ear_values: list = field(default_factory=list)
    blink_rates: list = field(default_factory=list)
    fatigue_levels: list = field(default_factory=list)
    alerts_triggered: int = 0
    breaks_taken: int = 0
    
    # Current state
    current_blink_rate: float = 0.0
    current_ear: float = 0.0
    current_fatigue_level: int = 0


class SessionManager:
    """Manages user sessions and metrics aggregation."""
    
    def __init__(self, user_profile: str = DEFAULT_PROFILE):
        """
        Initialize session manager.
        
        Args:
            user_profile: Name of the user profile
        """
        self.user_profile = user_profile
        self.db = get_database()
        self.current_session: Optional[SessionData] = None
        self.last_activity_time = None
        
        logger.info(f"Session manager initialized for user: {user_profile}")
    
    def start_session(self) -> int:
        """
        Start a new session.
        
        Returns:
            session_id of the new session
        """
        if self.current_session and self.current_session.is_active:
            logger.warning("Session already active, ending previous session")
            self.end_session()
        
        # Create session in database
        session_id = self.db.create_session(self.user_profile)
        
        # Create session data object
        self.current_session = SessionData(
            session_id=session_id,
            user_profile=self.user_profile,
            start_time=time.time(),
            is_active=True
        )
        
        self.last_activity_time = time.time()
        
        logger.info(f"Started session {session_id}")
        
        return session_id
    
    def end_session(self):
        """End the current session and save summary."""
        if not self.current_session:
            logger.warning("No active session to end")
            return
        
        if not self.current_session.is_active:
            logger.warning("Session already ended")
            return
        
        self.current_session.end_time = time.time()
        self.current_session.is_active = False
        
        # Calculate summary statistics
        summary = self._calculate_session_summary()
        
        # Save to database
        self.db.end_session(self.current_session.session_id, summary)
        
        logger.info(f"Ended session {self.current_session.session_id}, "
                   f"duration: {summary['duration_seconds']:.1f}s")
        
        self.current_session = None
    
    def pause_session(self):
        """Pause the current session."""
        if not self.current_session or not self.current_session.is_active:
            logger.warning("No active session to pause")
            return
        
        if self.current_session.is_paused:
            logger.warning("Session already paused")
            return
        
        self.current_session.is_paused = True
        self.current_session.pause_start = time.time()
        
        logger.info("Session paused")
    
    def resume_session(self):
        """Resume a paused session."""
        if not self.current_session or not self.current_session.is_paused:
            logger.warning("No paused session to resume")
            return
        
        # Calculate pause duration
        pause_duration = time.time() - self.current_session.pause_start
        self.current_session.total_pause_duration += pause_duration
        
        self.current_session.is_paused = False
        self.current_session.pause_start = None
        self.last_activity_time = time.time()
        
        logger.info(f"Session resumed (paused for {pause_duration:.1f}s)")
    
    def update_metrics(self, ear: float, blink_rate: float, 
                      fatigue_level: int = 0, blink_detected: bool = False):
        """
        Update session metrics with new data.
        
        Args:
            ear: Current Eye Aspect Ratio
            blink_rate: Current blink rate
            fatigue_level: Current fatigue level (0-3)
            blink_detected: Whether a blink was just detected
        """
        if not self.current_session or not self.current_session.is_active:
            return
        
        if self.current_session.is_paused:
            return
        
        # Update metrics
        self.current_session.current_ear = ear
        self.current_session.current_blink_rate = blink_rate
        self.current_session.current_fatigue_level = fatigue_level
        
        # Store for aggregate calculations
        self.current_session.ear_values.append(ear)
        self.current_session.blink_rates.append(blink_rate)
        self.current_session.fatigue_levels.append(fatigue_level)
        
        if blink_detected:
            self.current_session.total_blinks += 1
        
        self.last_activity_time = time.time()
        
        # Log to database periodically (every ~5 seconds)
        if len(self.current_session.ear_values) % 150 == 0:  # Assuming 30 FPS
            self._log_metrics_to_db()
    
    def _log_metrics_to_db(self):
        """Log current metrics to database."""
        if not self.current_session:
            return
        
        metrics_data = {
            'avg_ear': self.current_session.current_ear,
            'blink_count': self.current_session.total_blinks,
            'blink_rate': self.current_session.current_blink_rate,
            'fatigue_prediction': self.current_session.current_fatigue_level
        }
        
        self.db.log_metrics(self.current_session.session_id, metrics_data)
    
    def record_alert(self, alert_type: str, severity: str, message: str = ""):
        """
        Record an alert for the current session.
        
        Args:
            alert_type: Type of alert
            severity: Alert severity level
            message: Alert message
        """
        if not self.current_session:
            return
        
        alert_data = {
            'alert_type': alert_type,
            'severity': severity,
            'message': message
        }
        
        self.db.log_alert(self.current_session.session_id, alert_data)
        self.current_session.alerts_triggered += 1
        
        logger.debug(f"Alert recorded: {alert_type} ({severity})")
    
    def record_break(self, duration: float):
        """
        Record a break taken during the session.
        
        Args:
            duration: Break duration in seconds
        """
        if not self.current_session:
            return
        
        self.current_session.breaks_taken += 1
        logger.info(f"Break recorded: {duration:.1f}s")
    
    def get_session_duration(self, exclude_pauses: bool = True) -> float:
        """
        Get current session duration in seconds.
        
        Args:
            exclude_pauses: Whether to exclude pause time
            
        Returns:
            Duration in seconds
        """
        if not self.current_session:
            return 0.0
        
        if self.current_session.is_paused and self.current_session.pause_start:
            # Don't count current pause
            end_time = self.current_session.pause_start
        else:
            end_time = time.time()
        
        duration = end_time - self.current_session.start_time
        
        if exclude_pauses:
            duration -= self.current_session.total_pause_duration
        
        return duration
    
    def check_timeout(self) -> bool:
        """
        Check if session has timed out due to inactivity.
        
        Returns:
            True if session timed out
        """
        if not self.current_session or not self.current_session.is_active:
            return False
        
        if self.current_session.is_paused:
            return False
        
        if self.last_activity_time is None:
            return False
        
        inactive_time = time.time() - self.last_activity_time
        
        if inactive_time > SESSION_TIMEOUT:
            logger.warning(f"Session timed out after {inactive_time:.1f}s of inactivity")
            self.end_session()
            return True
        
        return False
    
    def _calculate_session_summary(self) -> Dict:
        """Calculate summary statistics for the session."""
        if not self.current_session:
            return {}
        
        import numpy as np
        
        # Calculate averages
        avg_ear = np.mean(self.current_session.ear_values) if self.current_session.ear_values else 0.0
        min_ear = np.min(self.current_session.ear_values) if self.current_session.ear_values else 0.0
        max_ear = np.max(self.current_session.ear_values) if self.current_session.ear_values else 0.0
        
        avg_blink_rate = np.mean(self.current_session.blink_rates) if self.current_session.blink_rates else 0.0
        
        # Most common fatigue level
        if self.current_session.fatigue_levels:
            fatigue_level = int(np.median(self.current_session.fatigue_levels))
        else:
            fatigue_level = 0
        
        duration = self.get_session_duration(exclude_pauses=True)
        
        return {
            'total_blinks': self.current_session.total_blinks,
            'avg_blink_rate': float(avg_blink_rate),
            'avg_ear': float(avg_ear),
            'min_ear': float(min_ear),
            'max_ear': float(max_ear),
            'fatigue_level': fatigue_level,
            'alerts_triggered': self.current_session.alerts_triggered,
            'breaks_taken': self.current_session.breaks_taken,
            'duration_seconds': int(duration)
        }
    
    def get_current_stats(self) -> Dict:
        """Get current session statistics."""
        if not self.current_session:
            return {}
        
        return {
            'session_id': self.current_session.session_id,
            'is_active': self.current_session.is_active,
            'is_paused': self.current_session.is_paused,
            'duration': self.get_session_duration(),
            'total_blinks': self.current_session.total_blinks,
            'current_blink_rate': self.current_session.current_blink_rate,
            'current_ear': self.current_session.current_ear,
            'current_fatigue_level': self.current_session.current_fatigue_level,
            'alerts_triggered': self.current_session.alerts_triggered,
            'breaks_taken': self.current_session.breaks_taken
        }


if __name__ == "__main__":
    # Test session manager
    import numpy as np
    
    manager = SessionManager("test_user")
    
    # Start session
    session_id = manager.start_session()
    print(f"Session started: {session_id}")
    
    # Simulate some activity
    for i in range(100):
        ear = 0.30 + np.random.normal(0, 0.02)
        blink_rate = 15 + np.random.normal(0, 2)
        blink_detected = (i % 20 == 0)  # Blink every 20 frames
        
        manager.update_metrics(ear, blink_rate, fatigue_level=0, blink_detected=blink_detected)
        time.sleep(0.01)
    
    # Test pause/resume
    print("\nPausing session...")
    manager.pause_session()
    time.sleep(1)
    
    print("Resuming session...")
    manager.resume_session()
    
    # Get stats
    stats = manager.get_current_stats()
    print(f"\nCurrent stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # End session
    print("\nEnding session...")
    manager.end_session()
    
    print("\nSession manager test completed!")
