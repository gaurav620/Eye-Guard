"""
Model trainer script for fatigue classification.
Trains and evaluates the fatigue detection model.
"""

import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.dataset_generator import DatasetGenerator
from src.ml.fatigue_model import FatigueClassifier
from src.ml.feature_extractor import FeatureExtractor
from src.config.config import MODEL_PATH, SCALER_PATH, EPOCHS, BATCH_SIZE
from src.utils.logger import get_logger

logger = get_logger('model_trainer')


def train_model(n_samples_per_class: int = 1000, epochs: int = EPOCHS, 
               batch_size: int = BATCH_SIZE):
    """
    Train the fatigue classification model.
    
    Args:
        n_samples_per_class: Number of synthetic samples per class
        epochs: Number of training epochs
        batch_size: Training batch size
    """
    logger.info("=" * 60)
    logger.info("FATIGUE CLASSIFICATION MODEL TRAINING")
    logger.info("=" * 60)
    
    # Step 1: Generate dataset
    logger.info("\nStep 1: Generating synthetic training data...")
    generator = DatasetGenerator()
    X, y = generator.generate_synthetic_data(n_samples_per_class=n_samples_per_class)
    
    logger.info(f"Dataset generated: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Class distribution: {np.bincount(y)}")
    
    # Save dataset
    generator.save_dataset(X, y, "training_dataset.npz")
    
    # Step 2: Split dataset
    logger.info("\nStep 2: Splitting dataset...")
    X_train, X_test, y_train, y_test = generator.split_dataset(X, y, test_size=0.2)
    
    # Further split train into train and validation
    X_train, X_val, y_train, y_val = generator.split_dataset(
        X_train, y_train, test_size=0.15
    )
    
    logger.info(f"Train set: {X_train.shape[0]} samples")
    logger.info(f"Validation set: {X_val.shape[0]} samples")
    logger.info(f"Test set: {X_test.shape[0]} samples")
    
    # Step 3: Create and save scaler
    logger.info("\nStep 3: Creating feature scaler...")
    scaler = FeatureExtractor.create_and_save_scaler(X_train, SCALER_PATH)
    
    # Apply scaling
    from sklearn.preprocessing import StandardScaler
    X_train_scaled = scaler.transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Step 4: Build model
    logger.info("\nStep 4: Building neural network model...")
    classifier = FatigueClassifier(input_dim=X.shape[1], num_classes=4)
    model = classifier.build_model(architecture='dense')
    
    logger.info("\nModel Architecture:")
    print(classifier.get_model_summary())
    
    # Step 5: Train model
    logger.info(f"\nStep 5: Training model for {epochs} epochs...")
    
    # Callbacks
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    
    callbacks = [
        EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        ),
        ModelCheckpoint(
            MODEL_PATH,
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1
        )
    ]
    
    history = classifier.train(
        X_train_scaled, y_train,
        X_val_scaled, y_val,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks
    )
    
    # Step 6: Evaluate model
    logger.info("\nStep 6: Evaluating model on test set...")
    metrics = classifier.evaluate(X_test_scaled, y_test)
    
    logger.info("\n" + "=" * 60)
    logger.info("EVALUATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Test Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"Test Loss: {metrics['loss']:.4f}")
    
    if 'precision' in metrics:
        logger.info(f"Precision: {metrics['precision']:.4f}")
        logger.info(f"Recall: {metrics['recall']:.4f}")
    
    logger.info("\nConfusion Matrix:")
    logger.info(f"\n{metrics['confusion_matrix']}")
    
    logger.info("\nClassification Report:")
    report = metrics['classification_report']
    for class_name, class_metrics in report.items():
        if isinstance(class_metrics, dict):
            logger.info(f"\n{class_name}:")
            for metric_name, value in class_metrics.items():
                logger.info(f"  {metric_name}: {value:.4f}")
    
    # Step 7: Save final model
    logger.info(f"\nStep 7: Saving trained model to {MODEL_PATH}...")
    classifier.save_model(MODEL_PATH)
    
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETED SUCCESSFULLY!")
    logger.info("=" * 60)
    logger.info(f"Model saved to: {MODEL_PATH}")
    logger.info(f"Scaler saved to: {SCALER_PATH}")
    
    return classifier, metrics, history


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train fatigue classification model')
    parser.add_argument('--samples', type=int, default=1000,
                       help='Number of samples per class')
    parser.add_argument('--epochs', type=int, default=50,
                       help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Training batch size')
    parser.add_argument('--validate', action='store_true',
                       help='Only validate existing model')
    
    args = parser.parse_args()
    
    if args.validate:
        logger.info("Validation mode: Loading and evaluating existing model...")
        
        # Load model
        classifier = FatigueClassifier(input_dim=21, num_classes=4)
        classifier.load_model(MODEL_PATH)
        
        # Generate test data
        generator = DatasetGenerator()
        X, y = generator.generate_synthetic_data(n_samples_per_class=200)
        
        # Load scaler and transform
        import joblib
        scaler = joblib.load(SCALER_PATH)
        X_scaled = scaler.transform(X)
        
        # Evaluate
        metrics = classifier.evaluate(X_scaled, y)
        logger.info(f"\nValidation Accuracy: {metrics['accuracy']:.4f}")
        
    else:
        # Train new model
        train_model(
            n_samples_per_class=args.samples,
            epochs=args.epochs,
            batch_size=args.batch_size
        )
