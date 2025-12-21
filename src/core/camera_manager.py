"""
Camera manager for Eyeguard application.
Handles webcam initialization, frame capture, and preprocessing.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
import time

from ..config.config import (
    CAMERA_INDEX,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS
)
from ..utils.logger import get_logger

logger = get_logger('camera')


class CameraManager:
    """Manages webcam access and frame capture."""
    
    def __init__(self, camera_index: int = CAMERA_INDEX):
        """
        Initialize camera manager.
        
        Args:
            camera_index: Camera device index (0 for default webcam)
        """
        self.camera_index = camera_index
        self.cap = None
        self.is_opened = False
        self.frame_count = 0
        self.fps_start_time = time.time()
        self.fps = 0.0
        
        logger.info(f"Initializing camera manager with index {camera_index}")
    
    def open(self) -> bool:
        """
        Open the camera device.
        
        Returns:
            True if camera opened successfully, False otherwise
        """
        try:
            # Try with default backend first
            self.cap = cv2.VideoCapture(self.camera_index)
            
            # Add a small delay for camera initialization
            time.sleep(0.5)
            
            # Try to read a test frame
            ret, _ = self.cap.read()
            
            if not ret or not self.cap.isOpened():
                logger.warning(f"Failed to open camera {self.camera_index} with default backend, trying alternatives...")
                self.cap.release()
                
                # Try with V4L2 backend on Linux or other backends
                try:
                    self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_ANY)
                    time.sleep(0.5)
                    ret, _ = self.cap.read()
                    if not ret:
                        logger.error(f"Failed to open camera {self.camera_index} with all backends")
                        self.cap.release()
                        return False
                except Exception as e:
                    logger.error(f"Failed to open camera {self.camera_index}: {e}")
                    return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to get latest frames
            
            # Verify properties were set
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            logger.info(f"Camera opened: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            self.is_opened = True
            return True
            
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            if self.cap:
                self.cap.release()
            return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from the camera.
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_opened or self.cap is None:
            return False, None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret:
                logger.warning("Failed to read frame from camera")
                return False, None
            
            # Update FPS counter
            self.frame_count += 1
            if self.frame_count % 30 == 0:
                current_time = time.time()
                elapsed = current_time - self.fps_start_time
                if elapsed > 0:
                    self.fps = 30 / elapsed
                self.fps_start_time = current_time
            
            return True, frame
            
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return False, None
    
    def get_frame_size(self) -> Tuple[int, int]:
        """
        Get current frame dimensions.
        
        Returns:
            Tuple of (width, height)
        """
        if self.cap is None:
            return (0, 0)
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.fps
    
    def release(self):
        """Release the camera resource."""
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False
            logger.info("Camera released")
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to the camera.
        
        Returns:
            True if reconnection successful
        """
        logger.info("Attempting camera reconnection...")
        self.release()
        time.sleep(1)
        return self.open()
    
    @staticmethod
    def preprocess_frame(frame: np.ndarray, flip: bool = True) -> np.ndarray:
        """
        Preprocess frame for better detection.
        
        Args:
            frame: Input BGR frame
            flip: Whether to flip frame horizontally (for mirror effect)
            
        Returns:
            Preprocessed frame
        """
        if flip:
            frame = cv2.flip(frame, 1)
        
        return frame
    
    @staticmethod
    def draw_fps(frame: np.ndarray, fps: float) -> np.ndarray:
        """
        Draw FPS on frame.
        
        Args:
            frame: Input frame
            fps: FPS value to display
            
        Returns:
            Frame with FPS overlay
        """
        fps_text = f"FPS: {fps:.1f}"
        cv2.putText(frame, fps_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        return frame
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


if __name__ == "__main__":
    # Test camera
    with CameraManager() as cam:
        if not cam.is_opened:
            print("Failed to open camera")
            exit(1)
        
        print("Camera opened successfully. Press 'q' to quit.")
        
        while True:
            ret, frame = cam.read_frame()
            if not ret:
                print("Failed to read frame")
                break
            
            frame = CameraManager.preprocess_frame(frame)
            frame = CameraManager.draw_fps(frame, cam.get_fps())
            
            cv2.imshow("Camera Test", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()
        print("Camera test completed")
