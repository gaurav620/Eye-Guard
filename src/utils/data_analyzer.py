"""
Data analyzer for advanced analytics and insights.
Provides trend analysis, pattern recognition, and wellness scoring.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from scipy import stats

from ..utils.database import get_database
from ..utils.logger import get_logger

logger = get_logger('data_analyzer')


class DataAnalyzer:
    """Advanced analytics and insights for eye strain data."""
    
    def __init__(self):
        """Initialize data analyzer."""
        self.db = get_database()
        logger.info("Data analyzer initialized")
    
    def calculate_wellness_score(self, user_profile: str, days: int = 7) -> Dict:
        """
        Calculate overall wellness score (0-100).
        
        Args:
            user_profile: User profile name
            days: Number of days to analyze
            
        Returns:
            Dictionary with score and breakdown
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all sessions in the period
        sessions = self.db.get_recent_sessions(user_profile, limit=1000)
        period_sessions = [
            s for s in sessions 
            if start_date.isoformat() <= s['start_time'] <= end_date.isoformat()
        ]
        
        if not period_sessions:
            return {
                'score': 0,
                'grade': 'N/A',
                'message': 'Insufficient data'
            }
        
        score_components = {}
        
        # 1. Blink Rate Score (30 points)
        avg_blink_rates = [s['avg_blink_rate'] for s in period_sessions if s['avg_blink_rate']]
        if avg_blink_rates:
            avg_blink = np.mean(avg_blink_rates)
            if 15 <= avg_blink <= 25:
                blink_score = 30
            elif 12 <= avg_blink < 15 or 25 < avg_blink <= 30:
                blink_score = 20
            elif 8 <= avg_blink < 12:
                blink_score = 10
            else:
                blink_score = 0
        else:
            blink_score = 15  # Neutral
        
        score_components['blink_health'] = blink_score
        
        # 2. Session Duration Score (25 points)
        avg_duration = np.mean([s['duration_seconds'] for s in period_sessions if s['duration_seconds']])
        if avg_duration < 1800:  # < 30 min
            duration_score = 25
        elif avg_duration < 3600:  # < 1 hour
            duration_score = 20
        elif avg_duration < 7200:  # < 2 hours
            duration_score = 10
        else:
            duration_score = 0
        
        score_components['session_duration'] = duration_score
        
        # 3. Break Compliance Score (25 points)
        total_sessions = len(period_sessions)
        breaks_taken = sum(s.get('breaks_taken', 0) for s in period_sessions)
        expected_breaks = total_sessions * 2  # Expect 2 breaks per session
        
        if expected_breaks > 0:
            break_ratio = min(1.0, breaks_taken / expected_breaks)
            break_score = int(break_ratio * 25)
        else:
            break_score = 12  # Neutral
        
        score_components['break_compliance'] = break_score
        
        # 4. Alert Response Score (20 points)
        total_alerts = sum(s.get('alerts_triggered', 0) for s in period_sessions)
        if total_alerts < 5:
            alert_score = 20
        elif total_alerts < 15:
            alert_score = 15
        elif total_alerts < 30:
            alert_score = 10
        else:
            alert_score = 5
        
        score_components['alert_frequency'] = alert_score
        
        # Total Score
        total_score = sum(score_components.values())
        
        # Grade
        if total_score >= 90:
            grade = 'A+'
            message = 'Excellent eye health habits!'
        elif total_score >= 80:
            grade = 'A'
            message = 'Great job maintaining healthy screen habits!'
        elif total_score >= 70:
            grade = 'B'
            message = 'Good habits, but room for improvement.'
        elif total_score >= 60:
            grade = 'C'
            message = 'Fair. Consider taking more breaks.'
        elif total_score >= 50:
            grade = 'D'
            message = 'Needs improvement. Focus on blinking and breaks.'
        else:
            grade = 'F'
            message = 'Poor eye health habits. Please make changes!'
        
        return {
            'score': total_score,
            'grade': grade,
            'message': message,
            'breakdown': score_components,
            'metrics': {
                'avg_blink_rate': avg_blink if avg_blink_rates else 0,
                'avg_session_duration': avg_duration / 60,  # minutes
                'breaks_taken': breaks_taken,
                'total_alerts': total_alerts
            }
        }
    
    def detect_patterns(self, user_profile: str, days: int = 30) -> Dict:
        """
        Detect usage patterns and trends.
        
        Args:
            user_profile: User profile name
            days: Number of days to analyze
            
        Returns:
            Dictionary with detected patterns
        """
        sessions = self.db.get_recent_sessions(user_profile, limit=1000)
        
        if len(sessions) < 5:
            return {'insufficient_data': True}
        
        patterns = {}
        
        # Extract metrics
        durations = [s['duration_seconds'] for s in sessions if s['duration_seconds']]
        blink_rates = [s['avg_blink_rate'] for s in sessions if s['avg_blink_rate']]
        
        # 1. Duration trend
        if len(durations) >= 5:
            x = np.arange(len(durations))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, durations)
            
            if slope > 60:  # Increasing by >1 min per session
                patterns['duration_trend'] = 'increasing'
                patterns['duration_warning'] = True
            elif slope < -60:
                patterns['duration_trend'] = 'decreasing'
                patterns['duration_warning'] = False
            else:
                patterns['duration_trend'] = 'stable'
                patterns['duration_warning'] = False
        
        # 2. Blink rate trend
        if len(blink_rates) >= 5:
            x = np.arange(len(blink_rates))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, blink_rates)
            
            if slope < -0.5:  # Decreasing
                patterns['blink_trend'] = 'declining'
                patterns['blink_warning'] = True
            elif slope > 0.5:
                patterns['blink_trend'] = 'improving'
                patterns['blink_warning'] = False
            else:
                patterns['blink_trend'] = 'stable'
                patterns['blink_warning'] = False
        
        # 3. Peak usage time
        timestamps = [datetime.fromisoformat(s['start_time']) for s in sessions]
        hours = [t.hour for t in timestamps]
        
        if hours:
            peak_hour = max(set(hours), key=hours.count)
            patterns['peak_usage_hour'] = peak_hour
            
            if peak_hour >= 22 or peak_hour <= 6:
                patterns['late_night_usage'] = True
            else:
                patterns['late_night_usage'] = False
        
        # 4. Weekend vs Weekday
        weekday_sessions = sum(1 for t in timestamps if t.weekday() < 5)
        weekend_sessions = len(timestamps) - weekday_sessions
        
        if weekend_sessions > 0:
            patterns['weekday_to_weekend_ratio'] = weekday_sessions / weekend_sessions
        
        return patterns
    
    def get_improvement_suggestions(self, user_profile: str) -> List[str]:
        """
        Generate personalized improvement suggestions.
        
        Args:
            user_profile: User profile name
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Get wellness score and patterns
        wellness = self.calculate_wellness_score(user_profile)
        patterns = self.detect_patterns(user_profile)
        
        # Based on wellness components
        breakdown = wellness.get('breakdown', {})
        
        if breakdown.get('blink_health', 0) < 20:
            suggestions.append("💧 Practice conscious blinking - try blinking exercises every hour")
        
        if breakdown.get('session_duration', 0) < 15:
            suggestions.append("⏱️ Break long sessions into shorter periods (aim for < 30 min)")
        
        if breakdown.get('break_compliance', 0) < 15:
            suggestions.append("☕ Take more frequent breaks - follow the 20-20-20 rule strictly")
        
        if breakdown.get('alert_frequency', 0) < 10:
            suggestions.append("⚠️ Too many alerts triggered - take action when alerts appear")
        
        # Based on patterns
        if patterns.get('duration_warning'):
            suggestions.append("📈 Your session durations are increasing - set a timer!")
        
        if patterns.get('blink_warning'):
            suggestions.append("😴 Declining blink rate detected - get more rest")
        
        if patterns.get('late_night_usage'):
            suggestions.append("🌙 Reduce late-night screen time for better sleep health")
        
        # General tips
        if wellness['score'] < 70:
            suggestions.append("💡 Use the Eyeguard calibration feature for personalized thresholds")
            suggestions.append("🏃 Take a 5-minute walk between long sessions")
        
        return suggestions if suggestions else ["✅ Keep up the great work!"]
    
    def export_analytics_json(self, user_profile: str, days: int = 30) -> Dict:
        """
        Export comprehensive analytics as JSON.
        
        Args:
            user_profile: User profile name
            days: Number of days
            
        Returns:
            Complete analytics dictionary
        """
        wellness = self.calculate_wellness_score(user_profile, days)
        patterns = self.detect_patterns(user_profile, days)
        suggestions = self.get_improvement_suggestions(user_profile)
        
        # Get recent sessions
        sessions = self.db.get_recent_sessions(user_profile, limit=100)
        
        return {
            'user_profile': user_profile,
            'analysis_date': datetime.now().isoformat(),
            'period_days': days,
            'wellness_score': wellness,
            'patterns': patterns,
            'suggestions': suggestions,
            'total_sessions': len(sessions),
            'export_timestamp': datetime.now().isoformat()
        }


if __name__ == "__main__":
    analyzer = DataAnalyzer()
    print("Data analyzer initialized")
