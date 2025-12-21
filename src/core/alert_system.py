"""
Alert system for Eyeguard.
Multi-level alert system with 20-20-20 rule implementation.
"""

import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum

from ..config.config import (
    ALERT_INTERVAL_MINUTES,
    BREAK_DURATION_SECONDS,
    SNOOZE_DURATION_MINUTES,
    ALERT_LEVELS,
    get_alert_config
)
from ..utils.logger import get_logger

logger = get_logger('alert_system')


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertType(Enum):
    """Types of alerts."""
    BREAK_REMINDER = "BREAK_REMINDER"  # 20-20-20 rule
    LOW_BLINK_RATE = "LOW_BLINK_RATE"
    PROLONGED_FOCUS = "PROLONGED_FOCUS"
    FATIGUE_DETECTED = "FATIGUE_DETECTED"
    SESSION_DURATION = "SESSION_DURATION"


@dataclass
class Alert:
    """Data class for an alert."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: float
    is_dismissed: bool = False
    is_snoozed: bool = False
    snooze_until: Optional[float] = None


@dataclass
class AlertSystemState:
    """State of the alert system."""
    alerts_triggered: int = 0
    alerts_dismissed: int = 0
    alerts_snoozed: int = 0
    last_break_reminder: Optional[float] = None
    active_alerts: List[Alert] = field(default_factory=list)
    alert_history: List[Alert] = field(default_factory=list)


class AlertSystem:
    """Manages alerts and notifications for eye strain detection."""
    
    def __init__(self):
        """Initialize alert system."""
        self.state = AlertSystemState()
        self.session_start_time = time.time()
        self.next_break_time = time.time() + (ALERT_INTERVAL_MINUTES * 60)
        
        # Thresholds
        self.low_blink_threshold = 8  # blinks per minute
        self.prolonged_focus_threshold = 300  # seconds (5 minutes)
        
        logger.info("Alert system initialized")
        logger.info(f"20-20-20 rule: Break every {ALERT_INTERVAL_MINUTES} minutes")
    
    def check_alerts(self, blink_rate: float, fatigue_level: int,
                    session_duration: float, gaze_stability: float = 0.0) -> List[Alert]:
        """
        Check all conditions and generate alerts as needed.
        
        Args:
            blink_rate: Current blink rate (per minute)
            fatigue_level: Current fatigue level (0-3)
            session_duration: Session duration in seconds
            gaze_stability: Gaze stability score (0-1)
            
        Returns:
            List of new alerts generated
        """
        new_alerts = []
        
        # Check 20-20-20 rule
        break_alert = self._check_break_reminder()
        if break_alert:
            new_alerts.append(break_alert)
        
        # Check blink rate
        blink_alert = self._check_blink_rate(blink_rate)
        if blink_alert:
            new_alerts.append(blink_alert)
        
        # Check prolonged focus
        focus_alert = self._check_prolonged_focus(gaze_stability, session_duration)
        if focus_alert:
            new_alerts.append(focus_alert)
        
        # Check fatigue level
        fatigue_alert = self._check_fatigue_level(fatigue_level)
        if fatigue_alert:
            new_alerts.append(fatigue_alert)
        
        # Check session duration
        duration_alert = self._check_session_duration(session_duration)
        if duration_alert:
            new_alerts.append(duration_alert)
        
        # Add new alerts to active alerts
        for alert in new_alerts:
            self.state.active_alerts.append(alert)
            self.state.alert_history.append(alert)
            self.state.alerts_triggered += 1
            logger.info(f"Alert triggered: {alert.alert_type.value} ({alert.severity.value})")
        
        return new_alerts
    
    def _check_break_reminder(self) -> Optional[Alert]:
        """Check if it's time for a break reminder."""
        current_time = time.time()
        
        # Check if we're past the next break time
        if current_time >= self.next_break_time:
            # Check if this is snoozed
            if self.state.last_break_reminder:
                time_since_last = current_time - self.state.last_break_reminder
                if time_since_last < 60:  # Don't spam alerts
                    return None
            
            self.state.last_break_reminder = current_time
            self.next_break_time = current_time + (ALERT_INTERVAL_MINUTES * 60)
            
            return Alert(
                alert_id=f"break_{int(current_time)}",
                alert_type=AlertType.BREAK_REMINDER,
                severity=AlertSeverity.INFO,
                message=f"Time for a break! Look at something 20 feet away for {BREAK_DURATION_SECONDS} seconds.",
                timestamp=current_time
            )
        
        return None
    
    def _check_blink_rate(self, blink_rate: float) -> Optional[Alert]:
        """Check if blink rate is too low."""
        if blink_rate < self.low_blink_threshold:
            # Check if we already have an active low blink alert
            for alert in self.state.active_alerts:
                if alert.alert_type == AlertType.LOW_BLINK_RATE and not alert.is_dismissed:
                    return None  # Already alerted
            
            severity = AlertSeverity.WARNING if blink_rate < 5 else AlertSeverity.INFO
            
            return Alert(
                alert_id=f"blink_{int(time.time())}",
                alert_type=AlertType.LOW_BLINK_RATE,
                severity=severity,
                message=f"Low blink rate detected ({blink_rate:.1f}/min). Remember to blink regularly!",
                timestamp=time.time()
            )
        
        return None
    
    def _check_prolonged_focus(self, gaze_stability: float, duration: float) -> Optional[Alert]:
        """Check for prolonged focused attention."""
        # High stability for long duration indicates prolonged focus
        if gaze_stability > 0.8 and duration > self.prolonged_focus_threshold:
            # Check if we already have an active alert
            for alert in self.state.active_alerts:
                if alert.alert_type == AlertType.PROLONGED_FOCUS and not alert.is_dismissed:
                    return None
            
            return Alert(
                alert_id=f"focus_{int(time.time())}",
                alert_type=AlertType.PROLONGED_FOCUS,
                severity=AlertSeverity.INFO,
                message="You've been focusing for a while. Consider looking away briefly.",
                timestamp=time.time()
            )
        
        return None
    
    def _check_fatigue_level(self, fatigue_level: int) -> Optional[Alert]:
        """Check fatigue level and alert if high."""
        if fatigue_level >= 2:  # Moderate or Severe
            # Check for recent fatigue alerts
            recent_time = time.time() - 300  # Last 5 minutes
            for alert in self.state.active_alerts:
                if (alert.alert_type == AlertType.FATIGUE_DETECTED and 
                    alert.timestamp > recent_time and 
                    not alert.is_dismissed):
                    return None
            
            if fatigue_level == 2:
                severity = AlertSeverity.WARNING
                message = "Moderate eye strain detected. Take a break soon."
            else:  # Level 3
                severity = AlertSeverity.CRITICAL
                message = "Severe eye strain detected! Take a break immediately."
            
            return Alert(
                alert_id=f"fatigue_{int(time.time())}",
                alert_type=AlertType.FATIGUE_DETECTED,
                severity=severity,
                message=message,
                timestamp=time.time()
            )
        
        return None
    
    def _check_session_duration(self, duration: float) -> Optional[Alert]:
        """Check if session has been running too long."""
        duration_minutes = duration / 60.0
        
        # Alert at 60, 90, 120 minutes
        thresholds = [60, 90, 120]
        
        for threshold in thresholds:
            if duration_minutes >= threshold:
                # Check if we've already alerted for this threshold
                alert_id = f"duration_{threshold}"
                for alert in self.state.alert_history:
                    if alert.alert_id == alert_id:
                        return None  # Already alerted
                
                severity = AlertSeverity.WARNING if threshold < 120 else AlertSeverity.CRITICAL
                
                return Alert(
                    alert_id=alert_id,
                    alert_type=AlertType.SESSION_DURATION,
                    severity=severity,
                    message=f"You've been using the screen for {threshold} minutes. Time for a longer break!",
                    timestamp=time.time()
                )
        
        return None
    
    def dismiss_alert(self, alert_id: str):
        """
        Dismiss an alert.
        
        Args:
            alert_id: ID of the alert to dismiss
        """
        for alert in self.state.active_alerts:
            if alert.alert_id == alert_id and not alert.is_dismissed:
                alert.is_dismissed = True
                self.state.alerts_dismissed += 1
                logger.debug(f"Alert dismissed: {alert_id}")
                break
    
    def snooze_alert(self, alert_id: str, duration_minutes: int = SNOOZE_DURATION_MINUTES):
        """
        Snooze an alert.
        
        Args:
            alert_id: ID of the alert to snooze
            duration_minutes: Snooze duration in minutes
        """
        for alert in self.state.active_alerts:
            if alert.alert_id == alert_id:
                alert.is_snoozed = True
                alert.snooze_until = time.time() + (duration_minutes * 60)
                self.state.alerts_snoozed += 1
                
                # If it's a break reminder, update next break time
                if alert.alert_type == AlertType.BREAK_REMINDER:
                    self.next_break_time = alert.snooze_until
                
                logger.debug(f"Alert snoozed: {alert_id} for {duration_minutes} minutes")
                break
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (not dismissed) alerts."""
        current_time = time.time()
        
        active = []
        for alert in self.state.active_alerts:
            if alert.is_dismissed:
                continue
            
            # Check if snooze period is over
            if alert.is_snoozed and alert.snooze_until:
                if current_time >= alert.snooze_until:
                    alert.is_snoozed = False
                    alert.snooze_until = None
                    active.append(alert)
                # Skip snoozed alerts
            else:
                active.append(alert)
        
        return active
    
    def clear_old_alerts(self, age_seconds: int = 300):
        """
        Clear alerts older than specified age.
        
        Args:
            age_seconds: Age threshold in seconds
        """
        current_time = time.time()
        cutoff_time = current_time - age_seconds
        
        self.state.active_alerts = [
            alert for alert in self.state.active_alerts
            if alert.timestamp >= cutoff_time or not alert.is_dismissed
        ]
    
    def reset(self):
        """Reset the alert system."""
        self.state = AlertSystemState()
        self.session_start_time = time.time()
        self.next_break_time = time.time() + (ALERT_INTERVAL_MINUTES * 60)
        logger.info("Alert system reset")
    
    def get_statistics(self) -> Dict:
        """Get alert statistics."""
        return {
            'total_triggered': self.state.alerts_triggered,
            'total_dismissed': self.state.alerts_dismissed,
            'total_snoozed': self.state.alerts_snoozed,
            'active_count': len(self.get_active_alerts()),
            'next_break_in': max(0, self.next_break_time - time.time())
        }


if __name__ == "__main__":
    # Test alert system
    alert_system = AlertSystem()
    
    print("Testing alert system...")
    
    # Test 1: Low blink rate
    alerts = alert_system.check_alerts(
        blink_rate=5.0,
        fatigue_level=0,
        session_duration=100,
        gaze_stability=0.5
    )
    print(f"\nTest 1 - Low blink rate: {len(alerts)} alerts")
    for alert in alerts:
        print(f"  - {alert.alert_type.value}: {alert.message}")
    
    # Test 2: High fatigue
    alerts = alert_system.check_alerts(
        blink_rate=15.0,
        fatigue_level=3,
        session_duration=200,
        gaze_stability=0.7
    )
    print(f"\nTest 2 - High fatigue: {len(alerts)} alerts")
    for alert in alerts:
        print(f"  - {alert.alert_type.value} ({alert.severity.value}): {alert.message}")
    
    # Test 3: Get statistics
    stats = alert_system.get_statistics()
    print(f"\nAlert Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nAlert system test completed!")
