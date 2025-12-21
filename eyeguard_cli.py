#!/usr/bin/env python3
"""
Eyeguard CLI - Command-line interface for advanced features.
Provides access to reporting, analytics, calibration, and export.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.report_generator import ReportGenerator
from src.utils.data_analyzer import DataAnalyzer
from src.utils.data_exporter import DataExporter
from src.utils.database import get_database
from src.utils.logger import get_logger

logger = get_logger('cli')


def generate_report(args):
    """Generate PDF report."""
    print("\n📊 Generating PDF Report...")
    generator = ReportGenerator()
    
    try:
        report_path = generator.generate_daily_report(
            user_profile= args.user,
            date=datetime.strptime(args.date, "%Y-%m-%d") if args.date else None
        )
        print(f"✅ Report generated: {report_path}")
        print(f"\nOpen with: open '{report_path}'")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Report generation failed: {e}")


def show_analytics(args):
    """Show analytics and wellness score."""
    print("\n📈 Analyzing Your Data...\n")
    analyzer = DataAnalyzer()
    
    # Wellness Score
    wellness = analyzer.calculate_wellness_score(args.user, args.days)
    print("="*60)
    print("WELLNESS SCORE")
    print("="*60)
    print(f"Score: {wellness['score']}/100")
    print(f"Grade: {wellness['grade']}")
    print(f"Status: {wellness['message']}")
    print("\nBreakdown:")
    for component, score in wellness.get('breakdown', {}).items():
        bar = '█' * (score // 5) + '░' * (20 - score // 5)
        print(f"  {component:20s}: [{bar}] {score}/30")
    
    # Patterns
    print("\n" + "="*60)
    print("USAGE PATTERNS")
    print("="*60)
    patterns = analyzer.detect_patterns(args.user, args.days)
    
    if patterns.get('insufficient_data'):
        print("Insufficient data for pattern analysis")
    else:
        if 'duration_trend' in patterns:
            trend_icon = '📈' if patterns['duration_trend'] == 'increasing' else '📉' if patterns['duration_trend'] == 'decreasing' else '➡️'
            print(f"{trend_icon} Session Duration: {patterns['duration_trend'].upper()}")
        
        if 'blink_trend' in patterns:
            trend_icon = '📈' if patterns['blink_trend'] == 'improving' else '📉' if patterns['blink_trend'] == 'declining' else '➡️'
            print(f"{trend_icon} Blink Rate: {patterns['blink_trend'].upper()}")
        
        if 'peak_usage_hour' in patterns:
            print(f"⏰ Peak Usage: {patterns['peak_usage_hour']}:00")
        
        if patterns.get('late_night_usage'):
            print("🌙 Warning: Late night usage detected")
    
    # Suggestions
    print("\n" + "="*60)
    print("PERSONALIZED RECOMMENDATIONS")
    print("="*60)
    suggestions = analyzer.get_improvement_suggestions(args.user)
    for suggestion in suggestions:
        print(f"{suggestion}")
    print()


def export_data(args):
    """Export data to various formats."""
    exporter = DataExporter()
    
    print(f"\n📁 Exporting data in {args.format.upper()} format...")
    
    try:
        if args.format == 'csv':
            filepath = exporter.export_to_csv(args.user, args.days)
        elif args.format == 'json':
            filepath = exporter.export_to_json(args.user, include_analytics=True)
        elif args.format == 'excel':
            filepath = exporter.export_to_excel(args.user)
        else:
            print(f"❌ Unknown format: {args.format}")
            return
        
        print(f"✅ Data exported: {filepath}")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Export failed: {e}")


def show_history(args):
    """Show session history."""
    db = get_database()
    sessions = db.get_recent_sessions(args.user, limit=args.limit)
    
    print(f"\n📜 Session History ({len(sessions)} sessions)\n")
    print("="*80)
    print(f"{'ID':<6} {'Start Time':<20} {'Duration':<12} {'Blinks':<8} {'Rate':<10} {'Alerts':<8}")
    print("="*80)
    
    for session in sessions[:args.limit]:
        duration = session.get('duration_seconds', 0)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        print(f"{session['session_id']:<6} "
              f"{session['start_time'][:19]:<20} "
              f"{minutes}m {seconds}s{'':<6} "
              f"{session.get('total_blinks', 0):<8} "
              f"{session.get('avg_blink_rate', 0):.1f}/min{'':<3} "
              f"{session.get('alerts_triggered', 0):<8}")
    
    print("="*80)
    print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Eyeguard CLI - Advanced Features',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  eyeguard-cli report --user john --date 2025-01-15
  eyeguard-cli analytics --user john --days 7
  eyeguard-cli export --format excel --user john
  eyeguard-cli history --limit 20 --user john
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate PDF report')
    report_parser.add_argument('--user', default='default_user', help='User profile')
    report_parser.add_argument('--date', help='Date (YYYY-MM-DD), default: today')
    report_parser.set_defaults(func=generate_report)
    
    # Analytics command
    analytics_parser = subparsers.add_parser('analytics', help='Show analytics and wellness score')
    analytics_parser.add_argument('--user', default='default_user', help='User profile')
    analytics_parser.add_argument('--days', type=int, default=7, help='Days to analyze')
    analytics_parser.set_defaults(func=show_analytics)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('--format', choices=['csv', 'json', 'excel'], 
                               default='csv', help='Export format')
    export_parser.add_argument('--user', default='default_user', help='User profile')
    export_parser.add_argument('--days', type=int, default=30, help='Days of data')
    export_parser.set_defaults(func=export_data)
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show session history')
    history_parser.add_argument('--user', default='default_user', help='User profile')
    history_parser.add_argument('--limit', type=int, default=10, help='Number of sessions')
    history_parser.set_defaults(func=show_history)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
