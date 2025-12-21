"""
Database module for Eyeguard application.
Manages SQLite database for session tracking, metrics storage, and user profiles.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

from ..config.config import DATABASE_PATH
from .logger import get_logger

logger = get_logger('database')


class Database:
    """Database manager for Eyeguard application."""
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        """Initialize database connection."""
        self.db_path = db_path
        self._initialize_database()
        logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_profile TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    total_blinks INTEGER DEFAULT 0,
                    avg_blink_rate REAL,
                    avg_ear REAL,
                    min_ear REAL,
                    max_ear REAL,
                    fatigue_level INTEGER,
                    alerts_triggered INTEGER DEFAULT 0,
                    breaks_taken INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Metrics table (time-series data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    left_ear REAL,
                    right_ear REAL,
                    avg_ear REAL,
                    blink_count INTEGER,
                    blink_rate REAL,
                    gaze_stability REAL,
                    fatigue_prediction INTEGER,
                    fatigue_confidence REAL,
                    is_alert_triggered BOOLEAN DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # User profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_name TEXT UNIQUE NOT NULL,
                    calibration_data TEXT,
                    custom_thresholds TEXT,
                    preferences TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT,
                    was_dismissed BOOLEAN DEFAULT 0,
                    was_snoozed BOOLEAN DEFAULT 0,
                    response_time_seconds INTEGER,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # Breaks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS breaks (
                    break_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    break_type TEXT,
                    was_completed BOOLEAN DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # Create indices for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_user 
                ON sessions(user_profile)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_start_time 
                ON sessions(start_time)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_metrics_session 
                ON metrics(session_id, timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_session 
                ON alerts(session_id, timestamp)
            ''')
            
            logger.debug("Database schema created successfully")
    
    # ==================== SESSION OPERATIONS ====================
    
    def create_session(self, user_profile: str = "default_user") -> int:
        """
        Create a new session.
        
        Args:
            user_profile: Name of the user profile
            
        Returns:
            session_id of the created session
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (user_profile, start_time)
                VALUES (?, ?)
            ''', (user_profile, datetime.now()))
            
            session_id = cursor.lastrowid
            logger.info(f"Created new session {session_id} for user {user_profile}")
            return session_id
    
    def end_session(self, session_id: int, summary_data: Optional[Dict] = None):
        """
        End a session and update summary statistics.
        
        Args:
            session_id: ID of the session to end
            summary_data: Optional dictionary with summary statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get session start time
            cursor.execute('SELECT start_time FROM sessions WHERE session_id = ?', (session_id,))
            result = cursor.fetchone()
            if not result:
                logger.error(f"Session {session_id} not found")
                return
            
            start_time = datetime.fromisoformat(result['start_time'])
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            # Update session with summary data
            if summary_data:
                cursor.execute('''
                    UPDATE sessions SET
                        end_time = ?,
                        duration_seconds = ?,
                        total_blinks = ?,
                        avg_blink_rate = ?,
                        avg_ear = ?,
                        min_ear = ?,
                        max_ear = ?,
                        fatigue_level = ?,
                        alerts_triggered = ?,
                        breaks_taken = ?
                    WHERE session_id = ?
                ''', (
                    end_time,
                    duration,
                    summary_data.get('total_blinks', 0),
                    summary_data.get('avg_blink_rate', 0.0),
                    summary_data.get('avg_ear', 0.0),
                    summary_data.get('min_ear', 0.0),
                    summary_data.get('max_ear', 0.0),
                    summary_data.get('fatigue_level', 0),
                    summary_data.get('alerts_triggered', 0),
                    summary_data.get('breaks_taken', 0),
                    session_id
                ))
            else:
                cursor.execute('''
                    UPDATE sessions SET end_time = ?, duration_seconds = ?
                    WHERE session_id = ?
                ''', (end_time, duration, session_id))
            
            logger.info(f"Ended session {session_id}, duration: {duration}s")
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """Get session data by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_recent_sessions(self, user_profile: str = "default_user", limit: int = 10) -> List[Dict]:
        """Get recent sessions for a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sessions
                WHERE user_profile = ?
                ORDER BY start_time DESC
                LIMIT ?
            ''', (user_profile, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== METRICS OPERATIONS ====================
    
    def log_metrics(self, session_id: int, metrics_data: Dict):
        """
        Log real-time metrics for a session.
        
        Args:
            session_id: ID of the current session
            metrics_data: Dictionary containing metric values
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO metrics (
                    session_id, timestamp, left_ear, right_ear, avg_ear,
                    blink_count, blink_rate, gaze_stability,
                    fatigue_prediction, fatigue_confidence, is_alert_triggered
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                datetime.now(),
                metrics_data.get('left_ear'),
                metrics_data.get('right_ear'),
                metrics_data.get('avg_ear'),
                metrics_data.get('blink_count', 0),
                metrics_data.get('blink_rate', 0.0),
                metrics_data.get('gaze_stability', 0.0),
                metrics_data.get('fatigue_prediction'),
                metrics_data.get('fatigue_confidence'),
                metrics_data.get('is_alert_triggered', False)
            ))
    
    def get_session_metrics(self, session_id: int, limit: Optional[int] = None) -> List[Dict]:
        """Get all metrics for a session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM metrics WHERE session_id = ? ORDER BY timestamp DESC'
            if limit:
                query += f' LIMIT {limit}'
            cursor.execute(query, (session_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== ALERT OPERATIONS ====================
    
    def log_alert(self, session_id: int, alert_data: Dict) -> int:
        """Log an alert."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (
                    session_id, timestamp, alert_type, severity, message
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                session_id,
                datetime.now(),
                alert_data.get('alert_type', 'BREAK_REMINDER'),
                alert_data.get('severity', 'INFO'),
                alert_data.get('message', '')
            ))
            return cursor.lastrowid
    
    def update_alert_response(self, alert_id: int, dismissed: bool = False, 
                             snoozed: bool = False, response_time: int = 0):
        """Update alert response data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts SET
                    was_dismissed = ?,
                    was_snoozed = ?,
                    response_time_seconds = ?
                WHERE alert_id = ?
            ''', (dismissed, snoozed, response_time, alert_id))
    
    # ==================== USER PROFILE OPERATIONS ====================
    
    def create_user_profile(self, profile_name: str, calibration_data: Optional[Dict] = None,
                          custom_thresholds: Optional[Dict] = None,
                          preferences: Optional[Dict] = None) -> int:
        """Create a new user profile."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_profiles (
                    profile_name, calibration_data, custom_thresholds, preferences, last_used
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                profile_name,
                json.dumps(calibration_data) if calibration_data else None,
                json.dumps(custom_thresholds) if custom_thresholds else None,
                json.dumps(preferences) if preferences else None,
                datetime.now()
            ))
            profile_id = cursor.lastrowid
            logger.info(f"Created user profile: {profile_name}")
            return profile_id
    
    def get_user_profile(self, profile_name: str) -> Optional[Dict]:
        """Get user profile by name."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_profiles WHERE profile_name = ?
            ''', (profile_name,))
            row = cursor.fetchone()
            if row:
                profile = dict(row)
                # Parse JSON fields
                if profile['calibration_data']:
                    profile['calibration_data'] = json.loads(profile['calibration_data'])
                if profile['custom_thresholds']:
                    profile['custom_thresholds'] = json.loads(profile['custom_thresholds'])
                if profile['preferences']:
                    profile['preferences'] = json.loads(profile['preferences'])
                return profile
            return None
    
    # ==================== ANALYTICS QUERIES ====================
    
    def get_daily_summary(self, user_profile: str, date: datetime) -> Dict:
        """Get summary statistics for a specific day."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as session_count,
                    SUM(duration_seconds) as total_duration,
                    AVG(avg_blink_rate) as avg_blink_rate,
                    AVG(avg_ear) as avg_ear,
                    SUM(alerts_triggered) as total_alerts,
                    SUM(breaks_taken) as total_breaks
                FROM sessions
                WHERE user_profile = ?
                AND start_time >= ? AND start_time < ?
            ''', (user_profile, start_of_day, end_of_day))
            
            row = cursor.fetchone()
            return dict(row) if row else {}
    
    def get_weekly_stats(self, user_profile: str, weeks_back: int = 4) -> List[Dict]:
        """Get weekly statistics."""
        stats = []
        end_date = datetime.now()
        
        for i in range(weeks_back):
            week_end = end_date - timedelta(weeks=i)
            week_start = week_end - timedelta(days=7)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        COUNT(*) as session_count,
                        SUM(duration_seconds) as total_duration,
                        AVG(avg_blink_rate) as avg_blink_rate,
                        SUM(alerts_triggered) as total_alerts
                    FROM sessions
                    WHERE user_profile = ?
                    AND start_time >= ? AND start_time < ?
                ''', (user_profile, week_start, week_end))
                
                row = cursor.fetchone()
                if row:
                    data = dict(row)
                    data['week_start'] = week_start
                    data['week_end'] = week_end
                    stats.append(data)
        
        return stats


# Global database instance
_db_instance = None

def get_database() -> Database:
    """Get the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


if __name__ == "__main__":
    # Test database
    db = Database()
    
    # Create test session
    session_id = db.create_session("test_user")
    print(f"Created session: {session_id}")
    
    # Log some metrics
    db.log_metrics(session_id, {
        'left_ear': 0.28,
        'right_ear': 0.29,
        'avg_ear': 0.285,
        'blink_count': 15,
        'blink_rate': 18.5
    })
    
    # End session
    db.end_session(session_id, {
        'total_blinks': 150,
        'avg_blink_rate': 17.5,
        'avg_ear': 0.28
    })
    
    # Get session data
    session = db.get_session(session_id)
    print(f"Session data: {session}")
    
    print("Database test completed successfully!")
