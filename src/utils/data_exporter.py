"""
Data export utilities for Eyeguard.
Exports session data to CSV, JSON, and Excel formats.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from ..config.config import REPORTS_DIR
from ..utils.database import get_database
from ..utils.logger import get_logger

logger = get_logger('data_export')


class DataExporter:
    """Exports Eyeguard data in various formats."""
    
    def __init__(self):
        """Initialize data exporter."""
        self.db = get_database()
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Data exporter initialized")
    
    def export_to_csv(self, user_profile: str, days: int = 30) -> Path:
        """
        Export session data to CSV.
        
        Args:
            user_profile: User profile name
            days: Number of days of data
            
        Returns:
            Path to CSV file
        """
        sessions = self.db.get_recent_sessions(user_profile, limit=1000)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eyeguard_sessions_{user_profile}_{timestamp}.csv"
        filepath = REPORTS_DIR / filename
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = [
                'session_id', 'start_time', 'end_time', 'duration_minutes',
                'total_blinks', 'avg_blink_rate', 'avg_ear', 'min_ear', 'max_ear',
                'fatigue_level', 'alerts_triggered', 'breaks_taken'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for session in sessions:
                writer.writerow({
                    'session_id': session.get('session_id'),
                    'start_time': session.get('start_time'),
                    'end_time': session.get('end_time'),
                    'duration_minutes': round(session.get('duration_seconds', 0) / 60, 2),
                    'total_blinks': session.get('total_blinks'),
                    'avg_blink_rate': round(session.get('avg_blink_rate', 0), 2),
                    'avg_ear': round(session.get('avg_ear', 0), 3),
                    'min_ear': round(session.get('min_ear', 0), 3),
                    'max_ear': round(session.get('max_ear', 0), 3),
                    'fatigue_level': session.get('fatigue_level'),
                    'alerts_triggered': session.get('alerts_triggered'),
                    'breaks_taken': session.get('breaks_taken')
                })
        
        logger.info(f"Exported {len(sessions)} sessions to CSV: {filepath}")
        return filepath
    
    def export_to_json(self, user_profile: str, include_analytics: bool = True) -> Path:
        """
        Export data to JSON with optional analytics.
        
        Args:
            user_profile: User profile name
            include_analytics: Include wellness score and patterns
            
        Returns:
            Path to JSON file
        """
        sessions = self.db.get_recent_sessions(user_profile, limit=100)
        
        data = {
            'export_info': {
                'user_profile': user_profile,
                'export_timestamp': datetime.now().isoformat(),
                'total_sessions': len(sessions)
            },
            'sessions': sessions
        }
        
        if include_analytics:
            from .data_analyzer import DataAnalyzer
            analyzer = DataAnalyzer()
            data['analytics'] = analyzer.export_analytics_json(user_profile)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eyeguard_data_{user_profile}_{timestamp}.json"
        filepath = REPORTS_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Exported data to JSON: {filepath}")
        return filepath
    
    def export_to_excel(self, user_profile: str) -> Path:
        """
        Export sessions to Excel with multiple sheets.
        
        Args:
            user_profile: User profile name
            
        Returns:
            Path to Excel file
        """
        try:
            import pandas as pd
        except ImportError:
            logger.error("pandas not installed - cannot export to Excel")
            raise
        
        sessions = self.db.get_recent_sessions(user_profile, limit=1000)
        
        # Prepare sessions data
        sessions_df = pd.DataFrame([{
            'Session ID': s.get('session_id'),
            'Start Time': s.get('start_time'),
            'End Time': s.get('end_time'),
            'Duration (min)': round(s.get('duration_seconds', 0) / 60, 2),
            'Total Blinks': s.get('total_blinks'),
            'Avg Blink Rate': round(s.get('avg_blink_rate', 0), 2),
            'Avg EAR': round(s.get('avg_ear', 0), 3),
            'Fatigue Level': s.get('fatigue_level'),
            'Alerts': s.get('alerts_triggered'),
            'Breaks': s.get('breaks_taken')
        } for s in sessions])
        
        # Summary statistics
        summary_data = {
            'Metric': [
                'Total Sessions',
                'Total Screen Time (hours)',
                'Average Blink Rate',
                'Average Session Duration (min)',
                'Total Alerts',
                'Total Breaks'
            ],
            'Value': [
                len(sessions),
                round(sum(s.get('duration_seconds', 0) for s in sessions) / 3600, 2),
                round(sum(s.get('avg_blink_rate', 0) for s in sessions if s.get('avg_blink_rate')) / len(sessions), 2) if sessions else 0,
                round(sum(s.get('duration_seconds', 0) for s in sessions) / (len(sessions) * 60), 2) if sessions else 0,
                sum(s.get('alerts_triggered', 0) for s in sessions),
                sum(s.get('breaks_taken', 0) for s in sessions)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eyeguard_report_{user_profile}_{timestamp}.xlsx"
        filepath = REPORTS_DIR / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            sessions_df.to_excel(writer, sheet_name='Sessions', index=False)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        logger.info(f"Exported data to Excel: {filepath}")
        return filepath


if __name__ == "__main__":
    exporter = DataExporter()
    print("DataExporter initialized")
