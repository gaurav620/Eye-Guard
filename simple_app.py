"""
Eyeguard - SIMPLE Desktop App
One button to start tracking. Press 'q' to stop.
"""

import cv2
import time
import numpy as np
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.camera_manager import CameraManager
from src.core.eye_detector import EyeDetector
from src.core.blink_analyzer import BlinkAnalyzer
from src.utils.logger import get_logger

logger = get_logger('simple_app')


def main():
    """Simple one-click eye tracking app."""
    
    print("\n" + "="*70)
    print(" "*20 + "EYEGUARD - EYE TRACKING")
    print("="*70)
    print("\n📹 Starting camera... Please wait...")
    
    # Initialize components
    camera = CameraManager(camera_index=0)
    eye_detector = EyeDetector()
    blink_analyzer = BlinkAnalyzer()
    
    # Open camera
    if not camera.open():
        print("❌ ERROR: Could not open camera!")
        print("\n💡 SOLUTIONS:")
        print("   1. macOS: Go to System Settings → Privacy & Security → Camera")
        print("             and grant access to Terminal or your IDE")
        print("   2. Linux: Check camera permissions: ls -l /dev/video*")
        print("   3. Windows: Check Device Manager for camera drivers")
        print("   4. Try another camera index (currently using 0)")
        print("   5. Make sure no other app is using the camera")
        input("\nPress ENTER to exit...")
        return
    
    print("\n✅ Camera opened successfully!")
    print("\n" + "="*70)
    print("  Press 'q' in the video window to STOP")
    print("  The system will track your eyes and count blinks!")
    print("="*70 + "\n")
    
    # Tracking variables
    start_time = time.time()
    total_blinks = 0
    total_frames = 0
    
    cv2.namedWindow('Eyeguard - Eye Tracking', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Eyeguard - Eye Tracking', 800, 600)
    
    try:
        while True:
            # Read frame
            ret, frame = camera.read_frame()
            if not ret:
                continue
            
            # Preprocess
            frame = camera.preprocess_frame(frame)
            total_frames += 1
            
            # Detect eyes
            eye_data = eye_detector.process_frame(frame)
            
            if eye_data:
                # Check for blink
                blink_detected = blink_analyzer.process_ear(eye_data.avg_ear)
                if blink_detected:
                    total_blinks += 1
                    print(f"👁️  Blink #{total_blinks} detected!")
                
                # Draw eye landmarks on frame
                frame = eye_detector.draw_landmarks(frame, eye_data)
                
                # Calculate metrics
                elapsed = time.time() - start_time
                blink_rate = (total_blinks / (elapsed / 60)) if elapsed > 0 else 0
                
                # Display stats on frame
                stats_y = 30
                cv2.putText(frame, f"Duration: {int(elapsed)}s", (10, stats_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Blinks: {total_blinks}", (10, stats_y + 35), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Blink Rate: {blink_rate:.1f}/min", (10, stats_y + 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"EAR: {eye_data.avg_ear:.3f}", (10, stats_y + 105), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Blink rate status
                if blink_rate < 12:
                    status = "LOW - Blink more!"
                    color = (0, 0, 255)  # Red
                elif blink_rate > 25:
                    status = "HIGH"
                    color = (0, 165, 255)  # Orange
                else:
                    status = "HEALTHY"
                    color = (0, 255, 0)  # Green
                
                cv2.putText(frame, f"Status: {status}", (10, stats_y + 140), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            else:
                # No face detected
                cv2.putText(frame, "No face detected - Look at camera", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Show FPS
            fps = camera.get_fps()
            cv2.putText(frame, f"FPS: {fps:.1f}", (frame.shape[1] - 150, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # Display frame
            cv2.imshow('Eyeguard - Eye Tracking', frame)
            
            # Check for 'q' key to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    
    finally:
        # Cleanup
        camera.release()
        eye_detector.release()
        cv2.destroyAllWindows()
        
        # Show summary
        elapsed = time.time() - start_time
        print("\n" + "="*70)
        print(" "*20 + "SESSION COMPLETE")
        print("="*70)
        print(f"\n📊 Duration: {int(elapsed)}s ({int(elapsed/60)}min {int(elapsed%60)}s)")
        print(f"👁️  Total Blinks: {total_blinks}")
        if elapsed > 0:
            print(f"📈 Average Blink Rate: {(total_blinks / (elapsed / 60)):.1f}/min")
            print(f"🎯 Recommended: 15-20 blinks/min")
        print(f"🎬 Frames Processed: {total_frames}")
        print("="*70 + "\n")
        
        input("Press ENTER to exit...")


if __name__ == "__main__":
    main()
