"""
Audio Preprocessing Module for Emotion Detection
Handles MFCC extraction, data augmentation, and feature normalization
"""

import numpy as np
import librosa
import librosa.display
import noisereduce as nr
from typing import Tuple, List, Optional
import random

from config import (
    SAMPLE_RATE, DURATION, N_MFCC, N_FFT, HOP_LENGTH, N_MELS,
    NOISE_FACTOR, PITCH_SHIFT_STEPS, TIME_STRETCH_RATE
)


class AudioPreprocessor:
    """Handles all audio preprocessing tasks"""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE, duration: float = DURATION):
        self.sample_rate = sample_rate
        self.duration = duration
        self.target_length = int(sample_rate * duration)
    
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file and resample if necessary"""
        audio, sr = librosa.load(file_path, sr=self.sample_rate, duration=self.duration)
        return audio, sr
    
    def pad_or_truncate(self, audio: np.ndarray) -> np.ndarray:
        """Ensure audio is exactly target_length"""
        if len(audio) < self.target_length:
            # Pad with zeros
            padding = self.target_length - len(audio)
            audio = np.pad(audio, (0, padding), mode='constant')
        elif len(audio) > self.target_length:
            # Truncate
            audio = audio[:self.target_length]
        return audio
    
    def reduce_noise(self, audio: np.ndarray) -> np.ndarray:
        """Apply noise reduction using noisereduce library"""
        try:
            reduced_noise = nr.reduce_noise(y=audio, sr=self.sample_rate)
            return reduced_noise
        except Exception as e:
            print(f"Noise reduction failed: {e}")
            return audio
    
    def extract_mfcc(self, audio: np.ndarray) -> np.ndarray:
        """Extract MFCC features from audio"""
        # Ensure audio is the right length
        audio = self.pad_or_truncate(audio)
        
        # Extract MFCCs
        mfccs = librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=N_MFCC,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            n_mels=N_MELS
        )
        
        # Add delta and delta-delta features for temporal information
        mfcc_delta = librosa.feature.delta(mfccs)
        mfcc_delta2 = librosa.feature.delta(mfccs, order=2)
        
        # Stack all features
        features = np.vstack([mfccs, mfcc_delta, mfcc_delta2])
        
        return features
    
    def extract_features_for_cnn_lstm(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract features shaped for CNN+LSTM input
        Returns shape: (time_steps, n_mfcc, 1) for CNN+LSTM
        """
        mfcc = self.extract_mfcc(audio)
        
        # Transpose to (time_steps, features)
        mfcc = mfcc.T
        
        # Add channel dimension for CNN (time_steps, features, 1)
        mfcc = np.expand_dims(mfcc, axis=-1)
        
        return mfcc
    
    def add_noise(self, audio: np.ndarray, noise_factor: float = NOISE_FACTOR) -> np.ndarray:
        """Add random noise for data augmentation"""
        noise = np.random.randn(len(audio))
        augmented = audio + noise_factor * noise
        return augmented.astype(type(audio[0]))
    
    def pitch_shift(self, audio: np.ndarray, n_steps: int = PITCH_SHIFT_STEPS) -> np.ndarray:
        """Shift pitch for data augmentation"""
        return librosa.effects.pitch_shift(
            y=audio, 
            sr=self.sample_rate, 
            n_steps=random.randint(-n_steps, n_steps)
        )
    
    def time_stretch(self, audio: np.ndarray, rate: float = TIME_STRETCH_RATE) -> np.ndarray:
        """Stretch time for data augmentation"""
        stretched = librosa.effects.time_stretch(y=audio, rate=rate)
        return self.pad_or_truncate(stretched)
    
    def augment_audio(self, audio: np.ndarray, augmentations: List[str] = None) -> List[np.ndarray]:
        """
        Apply multiple augmentations to create varied training data
        Returns list of augmented audio samples
        """
        if augmentations is None:
            augmentations = ['noise', 'pitch', 'time']
        
        augmented_samples = [audio]  # Original
        
        if 'noise' in augmentations:
            augmented_samples.append(self.add_noise(audio))
        
        if 'pitch' in augmentations:
            try:
                augmented_samples.append(self.pitch_shift(audio))
            except Exception as e:
                print(f"Pitch shift failed: {e}")
        
        if 'time' in augmentations:
            try:
                augmented_samples.append(self.time_stretch(audio, rate=0.9))
                augmented_samples.append(self.time_stretch(audio, rate=1.1))
            except Exception as e:
                print(f"Time stretch failed: {e}")
        
        return augmented_samples
    
    def preprocess_file(self, file_path: str, augment: bool = False) -> List[np.ndarray]:
        """
        Complete preprocessing pipeline for a single file
        Returns list of feature arrays (original + augmented if requested)
        """
        # Load audio
        audio, _ = self.load_audio(file_path)
        
        # Reduce noise
        audio = self.reduce_noise(audio)
        
        # Normalize
        audio = librosa.util.normalize(audio)
        
        if augment:
            # Generate augmented samples
            audio_samples = self.augment_audio(audio)
        else:
            audio_samples = [audio]
        
        # Extract features for each sample
        features_list = []
        for sample in audio_samples:
            features = self.extract_features_for_cnn_lstm(sample)
            features_list.append(features)
        
        return features_list
    
    def preprocess_stream_chunk(self, audio_chunk: np.ndarray) -> np.ndarray:
        """
        Fast preprocessing for real-time audio streams
        """
        # Quick noise reduction
        audio_chunk = self.reduce_noise(audio_chunk)
        
        # Normalize
        audio_chunk = librosa.util.normalize(audio_chunk)
        
        # Extract features
        features = self.extract_features_for_cnn_lstm(audio_chunk)
        
        return features


class VoiceActivityDetector:
    """Simple Voice Activity Detection for speaker segmentation"""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.energy_threshold = 0.01
        self.silence_duration = 0.3  # seconds
    
    def detect_voice_activity(self, audio: np.ndarray) -> List[Tuple[int, int]]:
        """
        Detect voice activity segments in audio
        Returns list of (start_frame, end_frame) tuples
        """
        # Calculate frame energy
        frame_length = int(0.025 * self.sample_rate)  # 25ms frames
        hop_length = int(0.01 * self.sample_rate)     # 10ms hop
        
        energy = librosa.feature.rms(
            y=audio, 
            frame_length=frame_length, 
            hop_length=hop_length
        )[0]
        
        # Voice activity detection
        voiced_frames = energy > self.energy_threshold
        
        # Find continuous segments
        segments = []
        start = None
        
        for i, is_voiced in enumerate(voiced_frames):
            if is_voiced and start is None:
                start = i
            elif not is_voiced and start is not None:
                # Check if segment is long enough
                duration = (i - start) * hop_length / self.sample_rate
                if duration > self.silence_duration:
                    segments.append((
                        start * hop_length,
                        i * hop_length
                    ))
                start = None
        
        # Handle last segment
        if start is not None:
            segments.append((
                start * hop_length,
                len(voiced_frames) * hop_length
            ))
        
        return segments
    
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Quick check if chunk contains speech"""
        energy = np.sqrt(np.mean(audio_chunk ** 2))
        return energy > self.energy_threshold


# Singleton instances
_preprocessor = None
_vad = None

def get_preprocessor() -> AudioPreprocessor:
    """Get singleton preprocessor instance"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = AudioPreprocessor()
    return _preprocessor

def get_vad() -> VoiceActivityDetector:
    """Get singleton VAD instance"""
    global _vad
    if _vad is None:
        _vad = VoiceActivityDetector()
    return _vad
