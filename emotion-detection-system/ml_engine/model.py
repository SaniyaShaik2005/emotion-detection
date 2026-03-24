"""
CNN + LSTM Hybrid Model for Emotion Detection
Treats MFCC features as images (CNN) with temporal modeling (LSTM)
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.regularizers import l2
import numpy as np
from typing import Tuple, Optional

from config import (
    CNN_FILTERS, CNN_KERNEL_SIZES, LSTM_UNITS, DENSE_UNITS,
    DROPOUT_RATE, N_MFCC, LEARNING_RATE
)


class EmotionModel:
    """CNN + LSTM Hybrid Model for Speech Emotion Recognition"""
    
    def __init__(
        self,
        input_shape: Tuple[int, int, int],
        num_classes: int,
        model_path: Optional[str] = None
    ):
        """
        Initialize the emotion detection model
        
        Args:
            input_shape: (time_steps, n_features, 1) for CNN input
            num_classes: Number of emotion classes
            model_path: Path to load pre-trained model
        """
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.model = None
        self.history = None
        
        if model_path:
            self.load(model_path)
        else:
            self.build()
    
    def build(self) -> Model:
        """
        Build CNN + LSTM hybrid architecture
        """
        # Input layer
        inputs = layers.Input(shape=self.input_shape, name='input')
        
        x = inputs
        
        # CNN Layers - Treat MFCC as image for spectral pattern detection
        for i, (filters, kernel_size) in enumerate(zip(CNN_FILTERS, CNN_KERNEL_SIZES)):
            # Conv2D layer
            x = layers.Conv2D(
                filters=filters,
                kernel_size=kernel_size,
                padding='same',
                kernel_regularizer=l2(0.001),
                name=f'conv2d_{i+1}'
            )(x)
            
            # Batch normalization for training stability
            x = layers.BatchNormalization(name=f'bn_conv_{i+1}')(x)
            
            # ReLU activation
            x = layers.Activation('relu', name=f'relu_conv_{i+1}')(x)
            
            # Max pooling to reduce spatial dimensions
            x = layers.MaxPooling2D(
                pool_size=(2, 2),
                name=f'maxpool_{i+1}'
            )(x)
            
            # Dropout for regularization
            x = layers.Dropout(DROPOUT_RATE, name=f'dropout_conv_{i+1}')(x)
        
        # Reshape for LSTM: (batch, time_steps, features)
        # Get current shape
        shape = x.shape
        time_steps = shape[1]
        features = shape[2] * shape[3]
        
        x = layers.Reshape((time_steps, features), name='reshape_for_lstm')(x)
        
        # LSTM Layers - Temporal modeling for emotion dynamics
        for i, units in enumerate(LSTM_UNITS):
            return_sequences = (i < len(LSTM_UNITS) - 1)  # Return sequences for all but last
            
            x = layers.LSTM(
                units=units,
                return_sequences=return_sequences,
                dropout=DROPOUT_RATE,
                recurrent_dropout=DROPOUT_RATE,
                kernel_regularizer=l2(0.001),
                name=f'lstm_{i+1}'
            )(x)
            
            x = layers.BatchNormalization(name=f'bn_lstm_{i+1}')(x)
        
        # Dense Layers
        for i, units in enumerate(DENSE_UNITS):
            x = layers.Dense(
                units=units,
                kernel_regularizer=l2(0.001),
                name=f'dense_{i+1}'
            )(x)
            x = layers.BatchNormalization(name=f'bn_dense_{i+1}')(x)
            x = layers.Activation('relu', name=f'relu_dense_{i+1}')(x)
            x = layers.Dropout(DROPOUT_RATE, name=f'dropout_dense_{i+1}')(x)
        
        # Output layer with Softmax for multi-class classification
        outputs = layers.Dense(
            self.num_classes,
            activation='softmax',
            name='output'
        )(x)
        
        # Create model
        self.model = Model(inputs=inputs, outputs=outputs, name='EmotionCNNLSTM')
        
        # Compile model
        self.compile()
        
        return self.model
    
    def compile(self):
        """Compile the model with optimizer and loss function"""
        optimizer = keras.optimizers.Adam(learning_rate=LEARNING_RATE)
        
        self.model.compile(
            optimizer=optimizer,
            loss='categorical_crossentropy',
            metrics=[
                'accuracy',
                keras.metrics.Precision(name='precision'),
                keras.metrics.Recall(name='recall'),
                keras.metrics.F1Score(name='f1_score')
            ]
        )
    
    def summary(self):
        """Print model summary"""
        return self.model.summary()
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        callbacks: Optional[list] = None
    ) -> keras.callbacks.History:
        """
        Train the model
        """
        if callbacks is None:
            callbacks = self._get_default_callbacks()
        
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return self.history
    
    def _get_default_callbacks(self) -> list:
        """Get default training callbacks"""
        return [
            # Early stopping to prevent overfitting
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True,
                verbose=1
            ),
            # Reduce learning rate when plateau
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            ),
            # Model checkpoint
            keras.callbacks.ModelCheckpoint(
                filepath='models/best_model.keras',
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            )
        ]
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions
        Returns probability distribution over emotions
        """
        return self.model.predict(X, verbose=0)
    
    def predict_class(self, X: np.ndarray) -> np.ndarray:
        """
        Predict emotion classes
        Returns class indices
        """
        predictions = self.predict(X)
        return np.argmax(predictions, axis=1)
    
    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict with confidence scores
        Returns (predicted_classes, confidence_scores)
        """
        predictions = self.predict(X)
        classes = np.argmax(predictions, axis=1)
        confidences = np.max(predictions, axis=1)
        return classes, confidences
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evaluate model performance
        Returns dictionary of metrics
        """
        results = self.model.evaluate(X_test, y_test, verbose=0)
        return dict(zip(self.model.metrics_names, results))
    
    def save(self, path: str):
        """Save model to disk"""
        self.model.save(path)
        print(f"Model saved to {path}")
    
    def load(self, path: str):
        """Load model from disk"""
        self.model = keras.models.load_model(path)
        print(f"Model loaded from {path}")
    
    def get_feature_extractor(self) -> Model:
        """
        Extract feature extraction part of the model (up to LSTM)
        Useful for transfer learning or feature analysis
        """
        # Find the last LSTM layer
        lstm_layer = None
        for layer in reversed(self.model.layers):
            if isinstance(layer, layers.LSTM):
                lstm_layer = layer
                break
        
        if lstm_layer:
            return Model(
                inputs=self.model.input,
                outputs=lstm_layer.output
            )
        return None


class EmotionInference:
    """Lightweight inference class for production use"""
    
    def __init__(self, model_path: str, emotion_labels: list):
        self.model = keras.models.load_model(model_path)
        self.emotion_labels = emotion_labels
        print(f"Loaded inference model with emotions: {emotion_labels}")
    
    def predict_emotion(self, features: np.ndarray) -> dict:
        """
        Predict emotion from features
        Returns dict with emotion, confidence, and all probabilities
        """
        # Add batch dimension if needed
        if len(features.shape) == 3:
            features = np.expand_dims(features, axis=0)
        
        # Predict
        predictions = self.model.predict(features, verbose=0)[0]
        
        # Get top prediction
        top_idx = np.argmax(predictions)
        
        return {
            'emotion': self.emotion_labels[top_idx],
            'confidence': float(predictions[top_idx]),
            'probabilities': {
                label: float(prob) 
                for label, prob in zip(self.emotion_labels, predictions)
            }
        }
    
    def predict_batch(self, features_batch: np.ndarray) -> list:
        """Predict emotions for a batch of features"""
        predictions = self.model.predict(features_batch, verbose=0)
        
        results = []
        for pred in predictions:
            top_idx = np.argmax(pred)
            results.append({
                'emotion': self.emotion_labels[top_idx],
                'confidence': float(pred[top_idx]),
                'probabilities': {
                    label: float(prob) 
                    for label, prob in zip(self.emotion_labels, pred)
                }
            })
        
        return results


def create_model_for_training(num_classes: int, time_steps: int = 94, n_features: int = 120) -> EmotionModel:
    """
    Factory function to create model for training
    Default shape assumes 3 seconds of audio at 16kHz with default MFCC settings
    """
    input_shape = (time_steps, n_features, 1)
    return EmotionModel(input_shape=input_shape, num_classes=num_classes)


if __name__ == '__main__':
    # Test model creation
    print("Creating CNN+LSTM Emotion Detection Model...")
    model = create_model_for_training(num_classes=7)
    model.summary()
