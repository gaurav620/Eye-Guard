"""
Fatigue classification model using TensorFlow/Keras.
Deep learning model for real-time fatigue detection.
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from pathlib import Path
from typing import Optional, Tuple

from ..config.config import (
    MODEL_PATH,
    FATIGUE_LABELS,
    LEARNING_RATE
)
from ..utils.logger import get_logger

logger = get_logger('fatigue_model')


class FatigueClassifier:
    """Neural network model for fatigue classification."""
    
    def __init__(self, input_dim: int = 21, num_classes: int = 4):
        """
        Initialize fatigue classifier.
        
        Args:
            input_dim: Number of input features
            num_classes: Number of fatigue classes (0-3)
        """
        self.input_dim = input_dim
        self.num_classes = num_classes
        self.model = None
        
        logger.info(f"Fatigue classifier initialized: {input_dim} features -> {num_classes} classes")
    
    def build_model(self, architecture: str = 'dense') -> keras.Model:
        """
        Build the neural network model.
        
        Args:
            architecture: Model architecture ('dense' or 'lstm')
            
        Returns:
            Compiled Keras model
        """
        if architecture == 'dense':
            model = self._build_dense_model()
        elif architecture == 'lstm':
            model = self._build_lstm_model()
        else:
            raise ValueError(f"Unknown architecture: {architecture}")
        
        self.model = model
        logger.info(f"Built {architecture} model with {model.count_params()} parameters")
        
        return model
    
    def _build_dense_model(self) -> keras.Model:
        """Build a dense feedforward neural network."""
        model = models.Sequential([
            # Input layer
            layers.Input(shape=(self.input_dim,)),
            
            # Hidden layers with dropout for regularization
            layers.Dense(128, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            layers.Dense(64, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            layers.Dense(32, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            # Output layer
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _build_lstm_model(self) -> keras.Model:
        """Build an LSTM model for sequential data."""
        # Note: This would require reshaping input data to (batch, timesteps, features)
        model = models.Sequential([
            layers.Input(shape=(None, self.input_dim)),  # Variable length sequences
            
            layers.LSTM(64, return_sequences=True),
            layers.Dropout(0.3),
            
            layers.LSTM(32),
            layers.Dropout(0.3),
            
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.2),
            
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
             X_val: Optional[np.ndarray] = None, y_val: Optional[np.ndarray] = None,
             epochs: int = 50, batch_size: int = 32,
             callbacks: Optional[list] = None) -> keras.callbacks.History:
        """
        Train the model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            epochs: Number of training epochs
            batch_size: Batch size
            callbacks: List of Keras callbacks
            
        Returns:
            Training history
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val, y_val)
        
        logger.info(f"Training model for {epochs} epochs...")
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info("Training completed")
        
        return history
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions.
        
        Args:
            X: Feature matrix
            
        Returns:
            Tuple of (predicted_classes, prediction_probabilities)
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() or build_model() first.")
        
        # Get prediction probabilities
        probs = self.model.predict(X, verbose=0)
        
        # Get predicted classes
        predictions = np.argmax(probs, axis=1)
        
        return predictions, probs
    
    def predict_single(self, features: np.ndarray) -> Tuple[int, float, np.ndarray]:
        """
        Predict fatigue level for a single sample.
        
        Args:
            features: Feature vector (1D array)
            
        Returns:
            Tuple of (predicted_class, confidence, all_probabilities)
        """
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        predictions, probs = self.predict(features)
        
        predicted_class = predictions[0]
        confidence = probs[0][predicted_class]
        
        return predicted_class, confidence, probs[0]
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evaluate model performance.
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary of metrics
        """
        if self.model is None:
            raise ValueError("Model not loaded.")
        
        logger.info("Evaluating model...")
        
        results = self.model.evaluate(X_test, y_test, verbose=0)
        
        metrics = {
            'loss': results[0],
            'accuracy': results[1]
        }
        
        # Add precision and recall if available
        if len(results) > 2:
            metrics['precision'] = results[2]
            metrics['recall'] = results[3]
        
        # Get predictions for confusion matrix
        y_pred, _ = self.predict(X_test)
        
        # Calculate per-class accuracy
        from sklearn.metrics import classification_report, confusion_matrix
        
        metrics['confusion_matrix'] = confusion_matrix(y_test, y_pred)
        metrics['classification_report'] = classification_report(
            y_test, y_pred, 
            target_names=[FATIGUE_LABELS[i] for i in range(self.num_classes)],
            output_dict=True
        )
        
        logger.info(f"Evaluation: Accuracy={metrics['accuracy']:.4f}, Loss={metrics['loss']:.4f}")
        
        return metrics
    
    def save_model(self, filepath: Path = None):
        """
        Save model to disk.
        
        Args:
            filepath: Path to save model (uses default if None)
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        if filepath is None:
            filepath = MODEL_PATH
        
        self.model.save(filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: Path = None) -> keras.Model:
        """
        Load model from disk.
        
        Args:
            filepath: Path to model file (uses default if None)
            
        Returns:
            Loaded Keras model
        """
        if filepath is None:
            filepath = MODEL_PATH
        
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        self.model = keras.models.load_model(filepath)
        logger.info(f"Model loaded from {filepath}")
        
        return self.model
    
    def get_model_summary(self) -> str:
        """Get model architecture summary."""
        if self.model is None:
            return "No model built"
        
        import io
        stream = io.StringIO()
        self.model.summary(print_fn=lambda x: stream.write(x + '\n'))
        return stream.getvalue()


if __name__ == "__main__":
    # Test fatigue classifier
    from .dataset_generator import DatasetGenerator
    
    logger.info("Testing fatigue classifier...")
    
    # Generate small test dataset
    generator = DatasetGenerator()
    X, y = generator.generate_synthetic_data(n_samples_per_class=100)
    X_train, X_test, y_train, y_test = generator.split_dataset(X, y)
    
    # Build model
    classifier = FatigueClassifier(input_dim=X.shape[1], num_classes=4)
    model = classifier.build_model(architecture='dense')
    
    print("\nModel Summary:")
    print(classifier.get_model_summary())
    
    # Train for a few epochs
    print("\nTraining model...")
    history = classifier.train(X_train, y_train, X_test, y_test, epochs=5, batch_size=32)
    
    # Evaluate
    print("\nEvaluating model...")
    metrics = classifier.evaluate(X_test, y_test)
    print(f"Test Accuracy: {metrics['accuracy']:.4f}")
    print(f"Confusion Matrix:\n{metrics['confusion_matrix']}")
    
    # Test single prediction
    print("\nTesting single prediction...")
    test_features = X_test[0]
    pred_class, confidence, probs = classifier.predict_single(test_features)
    print(f"Predicted: {FATIGUE_LABELS[pred_class]} (confidence: {confidence:.4f})")
    print(f"All probabilities: {probs}")
    print(f"True label: {FATIGUE_LABELS[y_test[0]]}")
    
    print("\nFatigue classifier test completed!")
