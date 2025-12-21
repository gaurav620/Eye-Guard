"""
Flask REST API Backend for Eyeguard.
Provides endpoints for eye tracking data, analytics, and reports.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sys
from pathlib import Path
from datetime import datetime, timedelta
import base64
import io

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.database import get_database
from src.utils.data_analyzer import DataAnalyzer
from src.utils.report_generator import ReportGenerator
from src.utils.data_exporter import DataExporter
from src.utils.logger import get_logger

logger = get_logger('api')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web frontend

# Initialize services
db = get_database()
analyzer = DataAnalyzer()
report_gen = ReportGenerator()
exporter = DataExporter()


# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check."""
    return jsonify({
        'status': 'healthy',
        'service': 'Eyeguard API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


# Session endpoints
@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get recent sessions for a user."""
    user = request.args.get('user', 'default_user')
    limit = int(request.args.get('limit', 50))
    
    try:
        sessions = db.get_recent_sessions(user, limit=limit)
        return jsonify({
            'success': True,
            'data': sessions,
            'count': len(sessions)
        })
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """Get specific session details."""
    try:
        # This would need to be implemented in database.py
        return jsonify({
            'success': True,
            'data': {'session_id': session_id, 'message': 'Session details'}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sessions/create', methods=['POST'])
def create_session():
    """Create a new session."""
    data = request.json
    user = data.get('user_profile', 'default_user')
    
    try:
        session_id = db.create_session(user)
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Session created successfully'
        })
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Analytics endpoints
@app.route('/api/analytics/wellness', methods=['GET'])
def get_wellness_score():
    """Get wellness score for a user."""
    user = request.args.get('user', 'default_user')
    days = int(request.args.get('days', 7))
    
    try:
        wellness = analyzer.calculate_wellness_score(user, days)
        return jsonify({
            'success': True,
            'data': wellness
        })
    except Exception as e:
        logger.error(f"Error calculating wellness: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/patterns', methods=['GET'])
def get_patterns():
    """Get usage patterns for a user."""
    user = request.args.get('user', 'default_user')
    days = int(request.args.get('days', 30))
    
    try:
        patterns = analyzer.detect_patterns(user, days)
        return jsonify({
            'success': True,
            'data': patterns
        })
    except Exception as e:
        logger.error(f"Error detecting patterns: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/suggestions', methods=['GET'])
def get_suggestions():
    """Get improvement suggestions."""
    user = request.args.get('user', 'default_user')
    
    try:
        suggestions = analyzer.get_improvement_suggestions(user)
        return jsonify({
            'success': True,
            'data': suggestions
        })
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Summary endpoints
@app.route('/api/summary/daily', methods=['GET'])
def get_daily_summary():
    """Get daily summary."""
    user = request.args.get('user', 'default_user')
    date_str = request.args.get('date')  # YYYY-MM-DD format
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
        summary = db.get_daily_summary(user, date)
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error getting daily summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/summary/weekly', methods=['GET'])
def get_weekly_summary():
    """Get weekly summary."""
    user = request.args.get('user', 'default_user')
    
    try:
        # Get last 7 days
        summaries = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            summary = db.get_daily_summary(user, date)
            if summary:
                summary['date'] = date.strftime('%Y-%m-%d')
                summaries.append(summary)
        
        return jsonify({
            'success': True,
            'data': summaries
        })
    except Exception as e:
        logger.error(f"Error getting weekly summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Export endpoints
@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """Export data to CSV."""
    user = request.args.get('user', 'default_user')
    days = int(request.args.get('days', 30))
    
    try:
        filepath = exporter.export_to_csv(user, days)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/json', methods=['GET'])
def export_json():
    """Export data to JSON."""
    user = request.args.get('user', 'default_user')
    
    try:
        filepath = exporter.export_to_json(user, include_analytics=True)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Report endpoints
@app.route('/api/reports/generate', methods=['GET', 'POST'])
def generate_report():
    """Generate PDF report."""
    if request.method == 'POST':
        data = request.json
        user = data.get('user', 'default_user')
        date_str = data.get('date')
    else:  # GET
        user = request.args.get('user', 'default_user')
        date_str = request.args.get('date')
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else None
        filepath = report_gen.generate_daily_report(user, date)
        
        return jsonify({
            'success': True,
            'filepath': str(filepath),
            'message': 'Report generated successfully'
        })
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Stats endpoint for dashboard
@app.route('/api/stats/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive stats for dashboard."""
    user = request.args.get('user', 'default_user')
    
    try:
        # Get recent sessions
        sessions = db.get_recent_sessions(user, limit=10)
        
        # Calculate aggregates
        total_sessions = len(sessions)
        total_duration = sum(s.get('duration_seconds', 0) for s in sessions)
        avg_blink_rate = sum(s.get('avg_blink_rate', 0) for s in sessions) / total_sessions if total_sessions > 0 else 0
        total_alerts = sum(s.get('alerts_triggered', 0) for s in sessions)
        
        # Get wellness
        wellness = analyzer.calculate_wellness_score(user, 7)
        
        # Get latest session
        latest_session = sessions[0] if sessions else None
        
        return jsonify({
            'success': True,
            'data': {
                'total_sessions': total_sessions,
                'total_duration_hours': round(total_duration / 3600, 2),
                'avg_blink_rate': round(avg_blink_rate, 1),
                'total_alerts': total_alerts,
                'wellness_score': wellness.get('score', 0),
                'wellness_grade': wellness.get('grade', 'N/A'),
                'latest_session': latest_session,
                'recent_sessions': sessions[:5]
            }
        })
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("EYEGUARD REST API SERVER")
    print("=" * 60)
    print("Starting server on http://localhost:5000")
    print("API Documentation: http://localhost:5000/api/health")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8080, debug=True)
