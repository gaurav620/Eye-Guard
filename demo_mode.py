#!/usr/bin/env python3
"""
Eyeguard - DEMO MODE
Simulates eye tracking without requiring a camera.
Useful for testing the API and UI without hardware.
"""

import sys
import time
import random
import numpy as np
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.blink_analyzer import BlinkAnalyzer
from src.core.session_manager import SessionManager
from src.core.alert_system import AlertSystem
from src.ml.feature_extractor import FeatureExtractor
from src.ml.fatigue_model import FatigueClassifier
from src.utils.logger import get_logger

logger = get_logger('demo_mode')


def simulate_eye_metrics():
    """Generate realistic simulated eye metrics."""
    # Simulate Eye Aspect Ratio (EAR)
    base_ear = 0.35 + random.gauss(0, 0.05)
    base_ear = max(0.1, min(0.5, base_ear))  # Clamp to reasonable range
    
    # Simulate gaze
    gaze_x = 0.5 + random.gauss(0, 0.1)
    gaze_y = 0.5 + random.gauss(0, 0.1)
    gaze_x = max(0, min(1, gaze_x))
    gaze_y = max(0, min(1, gaze_y))
    
    return {
        'ear': base_ear,
        'gaze_x': gaze_x,
        'gaze_y': gaze_y,
        'blink_detected': random.random() < 0.05  # ~5% chance per frame
    }


def main():
    """Run demo mode."""
    
    print("\n" + "="*70)
    print(" "*15 + "EYEGUARD - DEMO MODE (No Camera Required)")
    print("="*70)
    print("\n📊 Simulating eye tracking data...")
    print("   This demo shows the system working with synthetic data\n")
    
    # Initialize components
    session_mgr = SessionManager(user_profile="demo_user")
    blink_analyzer = BlinkAnalyzer()
    alert_system = AlertSystem()
    feature_extractor = FeatureExtractor()
    fatigue_classifier = FatigueClassifier()
    fatigue_classifier.load_model()
    
    # Create session
    session_id = session_mgr.start_session()
    print(f"✓ Session started: ID={session_id}\n")
    
    print("="*70)
    print("  Running 30-second demo simulation...")
    print("="*70 + "\n")
    
    start_time = time.time()
    frame_count = 0
    blink_count = 0
    
    try:
        while time.time() - start_time < 30:  # Run for 30 seconds
            # Simulate metrics
            metrics = simulate_eye_metrics()
            frame_count += 1
            
            # Update analyzers
            if blink_analyzer.process_ear(metrics['ear']):
                blink_count += 1
            
            # Get blink rate
            current_blink_rate = blink_analyzer.get_blink_rate()
            
            # Extract features periodically
            if frame_count % 30 == 0:
                # Add data point to feature extractor
                feature_extractor.add_data_point(
                    ear=metrics['ear'],
                    blink_rate=current_blink_rate,
                    gaze_stability=0.8,  # Simulated
                    session_duration=time.time() - start_time
                )
                
                features = feature_extractor.extract_features()
                
                if features is not None:
                    # Make prediction
                    pred_class, confidence, probs = fatigue_classifier.predict_single(features)
                    
                    # Check for alerts
                    elapsed = time.time() - start_time
                    alerts = alert_system.check_alerts(
                        blink_rate=current_blink_rate,
                        fatigue_level=pred_class,
                        session_duration=elapsed,
                        gaze_stability=0.8
                    )
                    
                    # Display status
                    fatigue_labels = ["Normal", "Mild Fatigue", "Moderate Fatigue", "Severe Fatigue"]
                    
                    print(f"\n⏱️  Time: {elapsed:.1f}s | Frames: {frame_count} | Blinks: {blink_count}")
                    print(f"📊 Blink Rate: {current_blink_rate:.1f}/min | EAR: {metrics['ear']:.3f}")
                    print(f"🧠 Fatigue Level: {fatigue_labels[pred_class]}")
                    
                    if alerts:
                        print(f"⚠️  Alerts: {len(alerts)} triggered")
                        for alert in alerts:
                            print(f"   - {alert.alert_type.name}: {alert.message}")
            
            # Small delay to simulate frame processing
            time.sleep(0.033)  # ~30 FPS
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    
    # End session
    session_mgr.end_session()
    
    # Print summary
    duration = time.time() - start_time
    print("\n" + "="*70)
    print("DEMO SUMMARY")
    print("="*70)
    print(f"✓ Duration: {duration:.1f} seconds")
    print(f"✓ Frames processed: {frame_count}")
    print(f"✓ Blinks detected: {blink_count}")
    print(f"✓ Average blink rate: {(blink_count / duration * 60):.1f}/min")
    print(f"✓ Session ID: {session_id}")
    print(f"✓ All core systems working!")
    print("="*70 + "\n")
    
    print("💡 NEXT STEPS:")
    print("   1. Try the API: flask --app api.app run")
    print("   2. View web dashboard: Open web/dashboard.html in browser")
    print("   3. Check database: data/eyeguard_sessions.db")
    print("\n")


if __name__ == "__main__":
    main()
