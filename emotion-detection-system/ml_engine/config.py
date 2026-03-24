"""
Configuration for the Emotion Detection ML Engine
"""

import os

# Audio Processing Configuration
SAMPLE_RATE = 16000
DURATION = 3  # seconds
N_MFCC = 40
N_FFT = 2048
HOP_LENGTH = 512
N_MELS = 128

# Emotion Classes
EMOTIONS = ['neutral', 'happy', 'sad', 'angry', 'fearful', 'disgust', 'surprised']
REQUIRED_EMOTIONS = ['neutral', 'happy', 'sad', 'angry', 'fearful', 'disgust', 'surprised']

# Model Architecture
CNN_FILTERS = [64, 128, 256]
CNN_KERNEL_SIZES = [(3, 3), (3, 3), (3, 3)]
LSTM_UNITS = [128, 64]
DENSE_UNITS = [64, 32]
DROPOUT_RATE = 0.3

# Training Configuration
BATCH_SIZE = 32
EPOCHS = 100
LEARNING_RATE = 0.001
VALIDATION_SPLIT = 0.2
TEST_SPLIT = 0.1

# Data Augmentation
NOISE_FACTOR = 0.005
PITCH_SHIFT_STEPS = 2
TIME_STRETCH_RATE = 0.8

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Model Files
MODEL_PATH = os.path.join(MODEL_DIR, 'best_model.keras')
SCALER_PATH = os.path.join(MODEL_DIR, 'scaler.pkl')
ENCODER_PATH = os.path.join(MODEL_DIR, 'encoder.pkl')

# Real-time Processing
CHUNK_DURATION = 1.0  # Process 1 second chunks
OVERLAP = 0.5  # 50% overlap between chunks
CONFIDENCE_THRESHOLD = 0.6
