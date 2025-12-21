"""
Eye detector module using MediaPipe FaceLandmarker (Tasks API).
Detects facial landmarks, calculates Eye Aspect Ratio (EAR), and tracks eye state.
"""

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pathlib import Path
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass

from ..config.config import (
    FACE_MESH_MAX_FACES,
    FACE_MESH_MIN_DETECTION_CONFIDENCE,
    FACE_MESH_MIN_TRACKING_CONFIDENCE,
    LEFT_EYE_INDICES,
    RIGHT_EYE_INDICES,
    LEFT_IRIS_INDICES,
    RIGHT_IRIS_INDICES,
    EAR_THRESHOLD
)
from ..utils.logger import get_logger

logger = get_logger('eye_detector')

# Path to the model file
MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "face_landmarker.task"


@dataclass
class EyeData:
    """Data class for eye tracking information."""
    left_ear: float
    right_ear: float
    avg_ear: float
    left_eye_open: bool
    right_eye_open: bool
    both_eyes_open: bool
    left_eye_landmarks: List[Tuple[float, float]]
    right_eye_landmarks: List[Tuple[float, float]]
    left_iris_center: Optional[Tuple[float, float]]
    right_iris_center: Optional[Tuple[float, float]]


class EyeDetector:
    """Eye detection and tracking using MediaPipe FaceLandmarker (Tasks API)."""
    
    def __init__(self):
        """Initialize MediaPipe FaceLandmarker."""
        self.face_landmarker = None
        self.face_detected = False
        self.last_eye_data = None
        
        # Check if model exists
        if not MODEL_PATH.exists():
            logger.warning(f"Model not found at {MODEL_PATH}. Please download face_landmarker.task")
            raise FileNotFoundError(
                f"FaceLandmarker model not found at {MODEL_PATH}. "
                "Please download it from: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
            )
        
        # Create FaceLandmarker options
        base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=FACE_MESH_MAX_FACES,
            min_face_detection_confidence=FACE_MESH_MIN_DETECTION_CONFIDENCE,
            min_face_presence_confidence=FACE_MESH_MIN_TRACKING_CONFIDENCE,
            min_tracking_confidence=FACE_MESH_MIN_TRACKING_CONFIDENCE,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False
        )
        
        self.face_landmarker = vision.FaceLandmarker.create_from_options(options)
        logger.info("Eye detector initialized with MediaPipe FaceLandmarker (Tasks API)")
    
    def process_frame(self, frame: np.ndarray) -> Optional[EyeData]:
        """
        Process a frame and detect eyes.
        
        Args:
            frame: BGR image from camera
            
        Returns:
            EyeData object if face detected, None otherwise
        """
        if self.face_landmarker is None:
            return None
            
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Process with FaceLandmarker
        results = self.face_landmarker.detect(mp_image)
        
        if not results.face_landmarks:
            self.face_detected = False
            return None
        
        self.face_detected = True
        
        # Get first face landmarks
        face_landmarks = results.face_landmarks[0]
        
        # Extract eye data
        h, w = frame.shape[:2]
        
        # Get eye landmarks
        left_eye_points = self._get_eye_landmarks(face_landmarks, LEFT_EYE_INDICES, w, h)
        right_eye_points = self._get_eye_landmarks(face_landmarks, RIGHT_EYE_INDICES, w, h)
        
        # Calculate EAR for both eyes
        left_ear = self._calculate_ear(left_eye_points)
        right_ear = self._calculate_ear(right_eye_points)
        avg_ear = (left_ear + right_ear) / 2.0
        
        # Determine eye state
        left_eye_open = left_ear > EAR_THRESHOLD
        right_eye_open = right_ear > EAR_THRESHOLD
        both_eyes_open = left_eye_open and right_eye_open
        
        # Get iris centers if available
        left_iris = self._get_iris_center(face_landmarks, LEFT_IRIS_INDICES, w, h)
        right_iris = self._get_iris_center(face_landmarks, RIGHT_IRIS_INDICES, w, h)
        
        # Create EyeData object
        eye_data = EyeData(
            left_ear=left_ear,
            right_ear=right_ear,
            avg_ear=avg_ear,
            left_eye_open=left_eye_open,
            right_eye_open=right_eye_open,
            both_eyes_open=both_eyes_open,
            left_eye_landmarks=left_eye_points,
            right_eye_landmarks=right_eye_points,
            left_iris_center=left_iris,
            right_iris_center=right_iris
        )
        
        self.last_eye_data = eye_data
        return eye_data
    
    def _get_eye_landmarks(self, landmarks, indices: List[int], 
                          width: int, height: int) -> List[Tuple[float, float]]:
        """
        Extract eye landmark coordinates.
        
        Args:
            landmarks: MediaPipe face landmarks (NormalizedLandmarkList)
            indices: List of landmark indices for an eye
            width: Image width
            height: Image height
            
        Returns:
            List of (x, y) tuples
        """
        points = []
        for idx in indices:
            if idx < len(landmarks):
                landmark = landmarks[idx]
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                points.append((x, y))
        return points
    
    def _get_iris_center(self, landmarks, indices: List[int],
                         width: int, height: int) -> Optional[Tuple[float, float]]:
        """
        Calculate iris center from landmarks.
        
        Args:
            landmarks: MediaPipe face landmarks
            indices: List of iris landmark indices
            width: Image width
            height: Image height
            
        Returns:
            (x, y) tuple of iris center
        """
        if not indices:
            return None
        
        iris_points = []
        for idx in indices:
            if idx < len(landmarks):
                landmark = landmarks[idx]
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                iris_points.append((x, y))
        
        if not iris_points:
            return None
        
        # Calculate center as mean of all iris points
        center_x = int(np.mean([p[0] for p in iris_points]))
        center_y = int(np.mean([p[1] for p in iris_points]))
        
        return (center_x, center_y)
    
    def _calculate_ear(self, eye_points: List[Tuple[float, float]]) -> float:
        """
        Calculate Eye Aspect Ratio (EAR).
        
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        
        Where p1-p6 are the eye landmarks in the order:
        p1, p2, p3, p4, p5, p6 = eye_points
        
        Args:
            eye_points: List of 6 eye landmark points
            
        Returns:
            EAR value (typically 0.2-0.4 for open eyes, <0.2 for closed)
        """
        if len(eye_points) != 6:
            return 0.0
        
        # Convert to numpy array for easier computation
        points = np.array(eye_points, dtype=np.float32)
        
        # Vertical distances
        vertical_1 = np.linalg.norm(points[1] - points[5])
        vertical_2 = np.linalg.norm(points[2] - points[4])
        
        # Horizontal distance
        horizontal = np.linalg.norm(points[0] - points[3])
        
        # Avoid division by zero
        if horizontal == 0:
            return 0.0
        
        # Calculate EAR
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        
        return ear
    
    def draw_landmarks(self, frame: np.ndarray, 
                      eye_data: Optional[EyeData] = None,
                      show_ear: bool = True) -> np.ndarray:
        """
        Draw eye landmarks and EAR values on frame.
        
        Args:
            frame: Input frame
            eye_data: EyeData object (uses last detected if None)
            show_ear: Whether to show EAR values
            
        Returns:
            Frame with overlays
        """
        if eye_data is None:
            eye_data = self.last_eye_data
        
        if eye_data is None:
            return frame
        
        # Draw left eye
        for point in eye_data.left_eye_landmarks:
            cv2.circle(frame, point, 2, (0, 255, 0), -1)
        
        # Draw right eye
        for point in eye_data.right_eye_landmarks:
            cv2.circle(frame, point, 2, (0, 255, 0), -1)
        
        # Draw left eye contour
        if len(eye_data.left_eye_landmarks) >= 6:
            points = np.array(eye_data.left_eye_landmarks, dtype=np.int32)
            cv2.polylines(frame, [points], True, (0, 255, 0), 1)
        
        # Draw right eye contour
        if len(eye_data.right_eye_landmarks) >= 6:
            points = np.array(eye_data.right_eye_landmarks, dtype=np.int32)
            cv2.polylines(frame, [points], True, (0, 255, 0), 1)
        
        # Draw iris centers
        if eye_data.left_iris_center:
            cv2.circle(frame, eye_data.left_iris_center, 3, (255, 0, 0), -1)
        
        if eye_data.right_iris_center:
            cv2.circle(frame, eye_data.right_iris_center, 3, (255, 0, 0), -1)
        
        # Show EAR values
        if show_ear:
            ear_text = f"L_EAR: {eye_data.left_ear:.3f} | R_EAR: {eye_data.right_ear:.3f}"
            cv2.putText(frame, ear_text, (10, frame.shape[0] - 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            avg_text = f"AVG_EAR: {eye_data.avg_ear:.3f}"
            cv2.putText(frame, avg_text, (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Eye state indicator
            state_text = "Eyes: "
            if eye_data.both_eyes_open:
                state_text += "OPEN"
                state_color = (0, 255, 0)
            else:
                state_text += "CLOSED"
                state_color = (0, 0, 255)
            
            cv2.putText(frame, state_text, (frame.shape[1] - 200, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, state_color, 2)
        
        return frame
    
    # Alias for backwards compatibility
    def draw_eye_landmarks(self, frame: np.ndarray, 
                          eye_data: Optional[EyeData] = None,
                          show_ear: bool = True) -> np.ndarray:
        """Alias for draw_landmarks for backwards compatibility."""
        return self.draw_landmarks(frame, eye_data, show_ear)
    
    def release(self):
        """Release MediaPipe resources."""
        if hasattr(self, 'face_landmarker') and self.face_landmarker is not None:
            self.face_landmarker.close()
            self.face_landmarker = None
            logger.info("Eye detector resources released")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.release()
        except Exception:
            pass  # Ignore errors during cleanup


if __name__ == "__main__":
    # Test eye detector
    from .camera_manager import CameraManager
    
    logger.info("Starting eye detector test...")
    
    camera = CameraManager()
    detector = EyeDetector()
    
    if not camera.open():
        logger.error("Failed to open camera")
        exit(1)
    
    logger.info("Camera opened. Press 'q' to quit.")
    
    try:
        while True:
            ret, frame = camera.read_frame()
            if not ret:
                logger.warning("Failed to read frame")
                break
            
            frame = camera.preprocess_frame(frame)
            
            # Detect eyes
            eye_data = detector.process_frame(frame)
            
            # Draw landmarks
            frame = detector.draw_landmarks(frame, eye_data)
            
            # Draw FPS
            frame = camera.draw_fps(frame, camera.get_fps())
            
            # Show detection status
            if detector.face_detected:
                cv2.putText(frame, "Face: DETECTED", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Face: NOT DETECTED", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow("Eye Detector Test", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        camera.release()
        detector.release()
        cv2.destroyAllWindows()
        logger.info("Eye detector test completed")
