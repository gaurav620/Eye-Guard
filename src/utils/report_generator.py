"""
PDF Report Generator for Eyeguard.
Generates professional PDF reports with charts, statistics, and insights.
"""

import io
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import numpy as np

from ..config.config import REPORTS_DIR, FATIGUE_LABELS, APP_VERSION, APP_AUTHOR
from ..utils.database import get_database
from ..utils.logger import get_logger

logger = get_logger('report_generator')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 100


class ReportGenerator:
    """Generates comprehensive PDF reports with visualizations."""
    
    def __init__(self):
        """Initialize report generator."""
        self.db = get_database()
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Report generator initialized")
    
    def generate_daily_report(self, user_profile: str = "default_user", 
                              date: datetime = None) -> Path:
        """
        Generate daily report for a user.
        
        Args:
            user_profile: User profile name
            date: Date for report (default: today)
            
        Returns:
            Path to generated PDF
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        filename = f"eyeguard_daily_report_{user_profile}_{date_str}.pdf"
        filepath = REPORTS_DIR / filename
        
        logger.info(f"Generating daily report for {user_profile} on {date_str}")
        
        # Create PDF
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#00A8E8'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2D2D2D'),
            spaceAfter=12
        )
        
        # Title
        story.append(Paragraph("Eyeguard Daily Report", title_style))
        story.append(Paragraph(f"Eye Strain Detection & Analysis", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Header info
        info_data = [
            ["Date:", date_str],
            ["User:", user_profile],
            ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Version:", APP_VERSION]
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Get data
        summary = self.db.get_daily_summary(user_profile, date)
        
        if not summary or summary.get('session_count', 0) == 0:
            story.append(Paragraph("No data available for this date.", styles['Normal']))
            doc.build(story)
            logger.info(f"Report generated (no data): {filepath}")
            return filepath
        
        # Summary Statistics
        story.append(Paragraph("📊 Daily Summary", heading_style))
        
        total_duration = summary.get('total_duration', 0) or 0
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        
        summary_data = [
            ["Total Sessions", str(summary.get('session_count', 0))],
            ["Total Screen Time", f"{hours}h {minutes}m"],
            ["Average Blink Rate", f"{summary.get('avg_blink_rate', 0):.1f}/min"],
            ["Average EAR", f"{summary.get('avg_ear', 0):.3f}"],
            ["Total Alerts", str(summary.get('total_alerts', 0))],
            ["Breaks Taken", str(summary.get('total_breaks', 0))]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F5F5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Health Assessment
        story.append(Paragraph("💚 Health Assessment", heading_style))
        
        avg_blink = summary.get('avg_blink_rate', 0) or 0
        if avg_blink >= 15 and avg_blink <= 25:
            health_status = "Excellent"
            health_color = colors.green
            recommendation = "Your blink rate is within the healthy range. Keep it up!"
        elif avg_blink >= 10:
            health_status = "Good"
            health_color = colors.blue
            recommendation = "Blink rate is acceptable but could be improved. Try to blink more consciously."
        elif avg_blink >= 5:
            health_status = "Fair"
            health_color = colors.orange
            recommendation = "Low blink rate detected. Take frequent breaks and practice blinking exercises."
        else:
            health_status = "Needs Attention"
            health_color = colors.red
            recommendation = "Very low blink rate. Please consult an eye care professional if this persists."
        
        health_text = f"<b>Status:</b> <font color='{health_color.hexval()}'>{health_status}</font><br/><br/>{recommendation}"
        story.append(Paragraph(health_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Generate charts
        try:
            # Get sessions for the day
            sessions = self.db.get_recent_sessions(user_profile, limit=50)
            day_sessions = [s for s in sessions if s['start_time'].startswith(date_str)]
            
            if day_sessions:
                # Chart 1: Blink rate over sessions
                chart1_path = self._create_blink_rate_chart(day_sessions)
                if chart1_path:
                    story.append(Paragraph("📈 Blink Rate Trend", heading_style))
                    img = Image(str(chart1_path), width=6*inch, height=3.5*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.2*inch))
                
                # Chart 2: Session duration
                chart2_path = self._create_session_duration_chart(day_sessions)
                if chart2_path:
                    story.append(Paragraph("⏱️ Session Durations", heading_style))
                    img2 = Image(str(chart2_path), width=6*inch, height=3.5*inch)
                    story.append(img2)
                    story.append(Spacer(1, 0.2*inch))
        
        except Exception as e:
            logger.error(f"Error creating charts: {e}")
        
        # Recommendations
        story.append(PageBreak())
        story.append(Paragraph("💡 Personalized Recommendations", heading_style))
        
        recommendations = []
        if avg_blink < 12:
            recommendations.append("• Practice the 20-20-20 rule: Every 20 minutes, look at something 20 feet away for 20 seconds")
        if summary.get('total_breaks', 0) < 3:
            recommendations.append("• Take more frequent breaks throughout the day")
        if total_duration > 14400:  # 4 hours
            recommendations.append("• Consider reducing total screen time or breaking it into shorter sessions")
        
        recommendations.append("• Use artificial tears or eye drops if you experience dryness")
        recommendations.append("• Ensure proper lighting and screen positioning")
        recommendations.append("• Adjust screen brightness to match ambient lighting")
        
        for rec in recommendations:
            story.append(Paragraph(rec, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Generated by Eyeguard v{APP_VERSION} | Developed by {APP_AUTHOR}", footer_style))
        
        # Build PDF
        doc.build(story)
        logger.info(f"Daily report generated successfully: {filepath}")
        
        return filepath
    
    def _create_blink_rate_chart(self, sessions: list) -> Path:
        """Create blink rate trend chart."""
        try:
            fig, ax = plt.subplots(figsize=(10, 5))
            
            session_nums = list(range(1, len(sessions) + 1))
            blink_rates = [s.get('avg_blink_rate', 0) for s in sessions]
            
            ax.plot(session_nums, blink_rates, marker='o', linewidth=2, 
                   color='#00A8E8', markersize=8)
            ax.axhline(y=15, color='green', linestyle='--', alpha=0.5, label='Healthy Min (15/min)')
            ax.axhline(y=20, color='blue', linestyle='--', alpha=0.5, label='Optimal (20/min)')
            
            ax.set_xlabel('Session Number', fontsize=12, fontweight='bold')
            ax.set_ylabel('Blink Rate (per minute)', fontsize=12, fontweight='bold')
            ax.set_title('Blink Rate Across Sessions', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            chart_path = REPORTS_DIR / 'temp_blink_chart.png'
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return chart_path
        except Exception as e:
            logger.error(f"Error creating blink rate chart: {e}")
            return None
    
    def _create_session_duration_chart(self, sessions: list) -> Path:
        """Create session duration bar chart."""
        try:
            fig, ax = plt.subplots(figsize=(10, 5))
            
            session_nums = list(range(1, len(sessions) + 1))
            durations = [s.get('duration_seconds', 0) / 60 for s in sessions]  # Convert to minutes
            
            colors_list = ['#4CAF50' if d < 30 else '#FF9800' if d < 60 else '#F44336' 
                          for d in durations]
            
            ax.bar(session_nums, durations, color=colors_list, alpha=0.7, edgecolor='black')
            
            ax.set_xlabel('Session Number', fontsize=12, fontweight='bold')
            ax.set_ylabel('Duration (minutes)', fontsize=12, fontweight='bold')
            ax.set_title('Session Duration Distribution', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            
            chart_path = REPORTS_DIR / 'temp_duration_chart.png'
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return chart_path
        except Exception as e:
            logger.error(f"Error creating duration chart: {e}")
            return None


if __name__ == "__main__":
    # Test report generation
    generator = ReportGenerator()
    report_path = generator.generate_daily_report("test_user")
    print(f"Report generated: {report_path}")
