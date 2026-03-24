"""
Synthetic Dataset Generator for Emotion Detection
Generates realistic MFCC-like features for training when real datasets are unavailable
"""

import numpy as np
import os
import pickle
from typing import Tuple, List
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf

from config import (
    EMOTIONS, SAMPLE_RATE, DURATION, N_MFCC, 
    BATCH_SIZE, EPOCHS, MODEL_PATH, SCALER_PATH, ENCODER_PATH
)


class SyntheticEmotionDataset:
    """
    Generate synthetic MFCC features that mimic real emotion patterns
    Based on research about acoustic properties of emotions
    """
    
    def __init__(self, num_samples: int = 5000, time_steps: int = 94, n_features: int = 120):
        self.num_samples = num_samples
        self.time_steps = time_steps
        self.n_features = n_features
        self.emotions = EMOTIONS
        
        # Emotion acoustic characteristics (based on research)
        # Each emotion has distinct patterns in pitch, energy, and spectral features
        self.emotion_profiles = {
            'neutral': {
                'pitch_mean': 150, 'pitch_std': 20,
                'energy_mean': 0.5, 'energy_std': 0.1,
                'spectral_mean': 0.0, 'spectral_std': 0.5,
                'tempo_variation': 0.1
            },
            'happy': {
                'pitch_mean': 220, 'pitch_std': 40,
                'energy_mean': 0.7, 'energy_std': 0.15,
                'spectral_mean': 0.3, 'spectral_std': 0.6,
                'tempo_variation': 0.3
            },
            'sad': {
                'pitch_mean': 120, 'pitch_std': 15,
                'energy_mean': 0.3, 'energy_std': 0.08,
                'spectral_mean': -0.2, 'spectral_std': 0.4,
                'tempo_variation': 0.05
            },
            'angry': {
                'pitch_mean': 280, 'pitch_std': 50,
                'energy_mean': 0.85, 'energy_std': 0.2,
                'spectral_mean': 0.5, 'spectral_std': 0.7,
                'tempo_variation': 0.4
            },
            'fearful': {
                'pitch_mean': 250, 'pitch_std': 45,
                'energy_mean': 0.6, 'energy_std': 0.18,
                'spectral_mean': 0.2, 'spectral_std': 0.55,
                'tempo_variation': 0.35
            },
            'disgust': {
                'pitch_mean': 160, 'pitch_std': 25,
                'energy_mean': 0.55, 'energy_std': 0.12,
                'spectral_mean': -0.1, 'spectral_std': 0.45,
                'tempo_variation': 0.15
            },
            'surprised': {
                'pitch_mean': 300, 'pitch_std': 60,
                'energy_mean': 0.75, 'energy_std': 0.22,
                'spectral_mean': 0.4, 'spectral_std': 0.65,
                'tempo_variation': 0.5
            }
        }
    
    def _generate_emotion_sample(self, emotion: str) -> np.ndarray:
        """Generate a single synthetic MFCC sample for an emotion"""
        profile = self.emotion_profiles[emotion]
        
        # Generate base pattern
        sample = np.random.randn(self.time_steps, self.n_features)
        
        # Apply emotion-specific transformations
        # Pitch-related features (first ~40 coefficients)
        pitch_effect = np.random.normal(
            profile['pitch_mean'] / 500,  # Normalize
            profile['pitch_std'] / 500,
            (self.time_steps, 40)
        )
        sample[:, :40] += pitch_effect
        
        # Energy-related features (next ~40 coefficients)
        energy_effect = np.random.normal(
            profile['energy_mean'],
            profile['energy_std'],
            (self.time_steps, 40)
        )
        sample[:, 40:80] += energy_effect
        
        # Spectral features (remaining coefficients)
        spectral_effect = np.random.normal(
            profile['spectral_mean'],
            profile['spectral_std'],
            (self.time_steps, 40)
        )
        sample[:, 80:120] += spectral_effect
        
        # Add temporal variation
        tempo_var = profile['tempo_variation']
        temporal_mask = np.sin(np.linspace(0, 2 * np.pi * tempo_var * 5, self.time_steps))
        sample = sample * temporal_mask[:, np.newaxis]
        
        # Add channel dimension for CNN
        sample = np.expand_dims(sample, axis=-1)
        
        return sample.astype(np.float32)
    
    def generate_dataset(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate complete synthetic dataset
        Returns X, y arrays
        """
        X = []
        y = []
        
        samples_per_emotion = self.num_samples // len(self.emotions)
        
        print(f"Generating {samples_per_emotion} samples per emotion...")
        
        for emotion in self.emotions:
            print(f"  Generating {emotion} samples...")
            for _ in range(samples_per_emotion):
                sample = self._generate_emotion_sample(emotion)
                X.append(sample)
                y.append(emotion)
        
        X = np.array(X)
        y = np.array(y)
        
        # Shuffle
        indices = np.random.permutation(len(X))
        X = X[indices]
        y = y[indices]
        
        print(f"Generated dataset: X.shape={X.shape}, y.shape={y.shape}")
        
        return X, y


def prepare_data_for_training(
    X: np.ndarray, 
    y: np.ndarray,
    test_size: float = 0.2,
    val_size: float = 0.125  # 0.125 * 0.8 = 0.1 of total
) -> Tuple:
    """
    Prepare data for training with encoding and normalization
    """
    print("Preparing data for training...")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    y_categorical = tf.keras.utils.to_categorical(y_encoded)
    
    print(f"Classes: {label_encoder.classes_}")
    
    # Split data
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y_categorical, test_size=test_size, random_state=42, stratify=y_encoded
    )
    
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=val_size, random_state=42
    )
    
    # Normalize features (fit on training data only)
    # Reshape for scaler: (samples * time_steps, features)
    scaler = StandardScaler()
    
    original_shape = X_train.shape
    X_train_reshaped = X_train.reshape(-1, original_shape[2])
    X_val_reshaped = X_val.reshape(-1, X_val.shape[2])
    X_test_reshaped = X_test.reshape(-1, X_test.shape[2])
    
    X_train_scaled = scaler.fit_transform(X_train_reshaped).reshape(original_shape)
    X_val_scaled = scaler.transform(X_val_reshaped).reshape(X_val.shape)
    X_test_scaled = scaler.transform(X_test_reshaped).reshape(X_test.shape)
    
    print(f"Training set: {X_train_scaled.shape}")
    print(f"Validation set: {X_val_scaled.shape}")
    print(f"Test set: {X_test_scaled.shape}")
    
    return (
        X_train_scaled, X_val_scaled, X_test_scaled,
        y_train, y_val, y_test,
        label_encoder, scaler
    )


def save_preprocessing_objects(encoder: LabelEncoder, scaler: StandardScaler, model_dir: str):
    """Save preprocessing objects for inference"""
    os.makedirs(model_dir, exist_ok=True)
    
    with open(ENCODER_PATH, 'wb') as f:
        pickle.dump(encoder, f)
    
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    
    print(f"Saved preprocessing objects to {model_dir}")


def load_preprocessing_objects(model_dir: str) -> Tuple[LabelEncoder, StandardScaler]:
    """Load preprocessing objects for inference"""
    with open(ENCODER_PATH, 'rb') as f:
        encoder = pickle.load(f)
    
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    
    return encoder, scaler


if __name__ == '__main__':
    # Generate and save synthetic dataset
    dataset = SyntheticEmotionDataset(num_samples=7000)
    X, y = dataset.generate_dataset()
    
    # Prepare data
    prepared_data = prepare_data_for_training(X, y)
    
    # Save preprocessed data
    os.makedirs('../data', exist_ok=True)
    np.save('../data/X_train.npy', prepared_data[0])
    np.save('../data/X_val.npy', prepared_data[1])
    np.save('../data/X_test.npy', prepared_data[2])
    np.save('../data/y_train.npy', prepared_data[3])
    np.save('../data/y_val.npy', prepared_data[4])
    np.save('../data/y_test.npy', prepared_data[5])
    
    # Save preprocessing objects
    save_preprocessing_objects(prepared_data[6], prepared_data[7], 'models')
    
    print("Dataset generation complete!")
