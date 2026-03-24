"""
Training Script for Emotion Detection Model
Trains CNN+LSTM hybrid model and generates accuracy report
"""

import os
import sys
import numpy as np
import pickle
import json
from datetime import datetime
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    accuracy_score, precision_score, recall_score, f1_score
)
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from config import (
    MODEL_PATH, EPOCHS, BATCH_SIZE, MODEL_DIR, LOG_DIR
)
from model import EmotionModel, create_model_for_training
from synthetic_dataset import (
    SyntheticEmotionDataset, prepare_data_for_training,
    save_preprocessing_objects
)


def plot_training_history(history, save_path=None):
    """Plot training history curves"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Accuracy
    axes[0, 0].plot(history.history['accuracy'], label='Train')
    axes[0, 0].plot(history.history['val_accuracy'], label='Validation')
    axes[0, 0].set_title('Model Accuracy')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Accuracy')
    axes[0, 0].legend()
    axes[0, 0].grid(True)
    
    # Loss
    axes[0, 1].plot(history.history['loss'], label='Train')
    axes[0, 1].plot(history.history['val_loss'], label='Validation')
    axes[0, 1].set_title('Model Loss')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Loss')
    axes[0, 1].legend()
    axes[0, 1].grid(True)
    
    # F1 Score
    if 'f1_score' in history.history:
        axes[1, 0].plot(history.history['f1_score'], label='Train')
        axes[1, 0].plot(history.history['val_f1_score'], label='Validation')
        axes[1, 0].set_title('F1 Score')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('F1 Score')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
    
    # Learning rate
    if 'lr' in history.history:
        axes[1, 1].plot(history.history['lr'])
        axes[1, 1].set_title('Learning Rate')
        axes[1, 1].set_xlabel('Epoch')
        axes[1, 1].set_ylabel('Learning Rate')
        axes[1, 1].grid(True)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Training history plot saved to {save_path}")
    
    return fig


def plot_confusion_matrix(y_true, y_pred, class_names, save_path=None):
    """Plot confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=class_names,
        yticklabels=class_names
    )
    plt.title('Confusion Matrix', fontsize=16)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.ylabel('True Label', fontsize=12)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Confusion matrix saved to {save_path}")
    
    return plt.gcf()


def generate_accuracy_report(
    model, X_test, y_test, label_encoder, 
    output_dir=LOG_DIR
):
    """Generate comprehensive accuracy report"""
    print("\n" + "="*60)
    print("GENERATING ACCURACY REPORT")
    print("="*60)
    
    # Get predictions
    y_pred_probs = model.predict(X_test)
    y_pred = np.argmax(y_pred_probs, axis=1)
    y_true = np.argmax(y_test, axis=1)
    
    class_names = label_encoder.classes_
    
    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted')
    f1 = f1_score(y_true, y_pred, average='weighted')
    
    # Per-class metrics
    report = classification_report(
        y_true, y_pred, 
        target_names=class_names,
        output_dict=True
    )
    
    # Print report
    print(f"\nOverall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")
    
    print("\n" + "-"*60)
    print("Per-Class Performance:")
    print("-"*60)
    for emotion in class_names:
        if emotion in report:
            metrics = report[emotion]
            print(f"{emotion:12s} - Precision: {metrics['precision']:.3f}, "
                  f"Recall: {metrics['recall']:.3f}, F1: {metrics['f1-score']:.3f}, "
                  f"Support: {int(metrics['support'])}")
    
    # Save report to JSON
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'overall_metrics': {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1)
        },
        'per_class_metrics': report,
        'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
    }
    
    report_path = os.path.join(output_dir, 'accuracy_report.json')
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    print(f"\nReport saved to {report_path}")
    
    # Plot confusion matrix
    cm_path = os.path.join(output_dir, 'confusion_matrix.png')
    plot_confusion_matrix(y_true, y_pred, class_names, save_path=cm_path)
    
    return report_data


def train_model():
    """Main training function"""
    print("="*60)
    print("EMOTION DETECTION MODEL TRAINING")
    print("CNN + LSTM Hybrid Architecture")
    print("="*60)
    
    # Set random seeds for reproducibility
    np.random.seed(42)
    tf.random.set_seed(42)
    
    # Generate synthetic dataset
    print("\n[1/5] Generating synthetic dataset...")
    dataset = SyntheticEmotionDataset(num_samples=7000)
    X, y = dataset.generate_dataset()
    
    # Prepare data
    print("\n[2/5] Preparing data...")
    (
        X_train, X_val, X_test,
        y_train, y_val, y_test,
        label_encoder, scaler
    ) = prepare_data_for_training(X, y)
    
    # Save preprocessing objects
    save_preprocessing_objects(label_encoder, scaler, MODEL_DIR)
    
    # Create model
    print("\n[3/5] Building CNN+LSTM model...")
    num_classes = len(label_encoder.classes_)
    model = create_model_for_training(
        num_classes=num_classes,
        time_steps=X_train.shape[1],
        n_features=X_train.shape[2]
    )
    model.summary()
    
    # Train model
    print(f"\n[4/5] Training model for up to {EPOCHS} epochs...")
    print(f"Training on {len(X_train)} samples, validating on {len(X_val)} samples")
    
    history = model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE
    )
    
    # Plot training history
    history_path = os.path.join(LOG_DIR, 'training_history.png')
    plot_training_history(history, save_path=history_path)
    
    # Save model
    print("\n[5/5] Saving model...")
    model.save(MODEL_PATH)
    
    # Generate accuracy report
    report = generate_accuracy_report(
        model, X_test, y_test, label_encoder
    )
    
    # Final summary
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"Final Test Accuracy: {report['overall_metrics']['accuracy']*100:.2f}%")
    print(f"Target Accuracy: 85%")
    
    if report['overall_metrics']['accuracy'] >= 0.85:
        print("✓ Target accuracy achieved!")
    else:
        print("⚠ Target accuracy not reached. Consider:")
        print("  - Increasing dataset size")
        print("  - Tuning hyperparameters")
        print("  - Adding more augmentation")
    
    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Logs saved to: {LOG_DIR}")
    
    return model, history, report


if __name__ == '__main__':
    train_model()
