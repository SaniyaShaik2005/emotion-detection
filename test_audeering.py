import os
import sys
import torch
import numpy as np
import librosa
import math

# Add the backend directory to the path so we can import the model classes
sys.path.append(os.path.join(os.getcwd(), 'emotion-detection-system', 'backend'))

# Import the model classes and helper from main.py
# We manually define the mapping and prototypes here to be safe and independent
_EMOTION_PROTOTYPES = {
    'angry':   (0.75, 0.20),
    'happy':   (0.75, 0.80),
    'sad':     (0.25, 0.25),
    'neutral': (0.45, 0.60),
}
_PROTO_BANDWIDTH = 0.30

def _dims_to_categorical(arousal, dominance, valence):
    scores = {}
    for emotion, (a_c, v_c) in _EMOTION_PROTOTYPES.items():
        dist = math.sqrt((arousal - a_c) ** 2 + (valence - v_c) ** 2)
        scores[emotion] = math.exp(-dist / _PROTO_BANDWIDTH)
    total = sum(scores.values()) or 1.0
    probs = {k: round(v / total, 3) for k, v in scores.items()}
    top = max(probs, key=probs.get)
    return top, round(probs[top], 3), probs

# Minimal model class definition (must match backend/main.py precisely)
import torch.nn as nn
from transformers import Wav2Vec2Model, Wav2Vec2PreTrainedModel, Wav2Vec2Processor

class _AudeeringRegressionHead(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.dropout = nn.Dropout(config.final_dropout)
        self.out_proj = nn.Linear(config.hidden_size, config.num_labels)
    def forward(self, features):
        x = self.dropout(features)
        x = self.dense(x)
        x = torch.tanh(x)
        x = self.dropout(x)
        x = self.out_proj(x)
        return x

class _AudeeringEmotionModel(Wav2Vec2PreTrainedModel):
    _tied_weights_keys = []
    @property
    def all_tied_weights_keys(self):
        return []
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.wav2vec2 = Wav2Vec2Model(config)
        self.classifier = _AudeeringRegressionHead(config)
        self.init_weights()
    def forward(self, input_values):
        outputs = self.wav2vec2(input_values)
        hidden_states = outputs[0]
        hidden_states = torch.mean(hidden_states, dim=1)
        logits = self.classifier(hidden_states)
        return hidden_states, logits

def run_test():
    model_id = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"
    sample_path = "emotion-detection-system/backend/uploads/074a0418-bde6-41e3-a648-8f58691b66cd.wav"
    
    print(f"Loading processor and model: {model_id}...")
    processor = Wav2Vec2Processor.from_pretrained(model_id)
    model = _AudeeringEmotionModel.from_pretrained(model_id)
    model.eval()
    
    print(f"Loading audio file: {sample_path}...")
    # Load 2 seconds from the middle
    y, sr = librosa.load(sample_path, sr=16000, duration=2.0)
    
    print("Running inference...")
    inputs = processor(y, sampling_rate=16000, return_tensors="pt", padding=True)
    with torch.no_grad():
        _, logits = model(inputs["input_values"])
    
    arousal, dominance, valence = logits[0].tolist()
    emotion, confidence, probs = _dims_to_categorical(arousal, dominance, valence)
    
    print("\n" + "="*40)
    print("AUDEERING MODEL PREDICTION RESULT")
    print("="*40)
    print(f"Detected Emotion: {emotion.upper()}")
    print(f"Confidence:       {confidence*100:.1f}%")
    print(f"Arousal:          {arousal:.3f} (Energy/Excitement)")
    print(f"Dominance:        {dominance:.3f}")
    print(f"Valence:          {valence:.3f} (Positivity/Negativity)")
    print("-" * 40)
    print("Full Probabilities:")
    for k, v in probs.items():
        print(f"  {k:<10}: {v*100:>5.1f}%")
    print("="*40)

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"Error during test: {e}")
