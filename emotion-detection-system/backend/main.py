"""
FastAPI Backend for Real-Time Emotion Detection
WebSocket endpoint for continuous audio streaming
"""

import os
import sys
import asyncio
import json
import uuid
import wave
import io
import hashlib
import base64
import time
import math
import numpy as np
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

# Add ml_engine to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ml_engine'))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from database import db_manager, init_database, Call, User

# ── Audeering model classes defined at module level so they survive pickling ──
# These mirror the exact architecture from the audeering model card.
# Source: https://huggingface.co/audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim
try:
    import torch
    import torch.nn as nn
    from transformers import Wav2Vec2Model, Wav2Vec2PreTrainedModel

    class _AudeeringRegressionHead(nn.Module):
        """Regression head that maps pooled wav2vec2 features → 3 dimensional values."""
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
        """
        Wav2Vec2-Large-Robust fine-tuned on MSP-Podcast.
        Outputs 3 continuous values: [arousal, dominance, valence] in ~[0, 1].
        Pre-trained on Switchboard+Fisher (real telephone speech) → robust to call audio.
        1.17M HuggingFace downloads — de facto production standard for open-source SER.
        """
        # Required by newer transformers versions (4.40+) for weight-tying support
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
            hidden_states = outputs[0]                       # (B, T, H)
            hidden_states = torch.mean(hidden_states, dim=1) # mean pool → (B, H)
            logits = self.classifier(hidden_states)           # (B, 3)
            return hidden_states, logits

    _AUDEERING_CLASSES_AVAILABLE = True
except ImportError:
    _AUDEERING_CLASSES_AVAILABLE = False

# Check if model exists and import accordingly
MODEL_AVAILABLE = False
try:
    from model import EmotionInference
    from preprocessing import get_preprocessor, get_vad
    import pickle
    MODEL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML model not available: {e}")
    print("Running in demo mode with simulated predictions")


# Configuration
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

SECRET_KEY = os.getenv('SECRET_KEY', 'emotion-detection-secret-key-2024')


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(user_id: int, email: str) -> str:
    data = f"{user_id}:{email}:{int(time.time())}"
    sig = hashlib.sha256(f"{data}:{SECRET_KEY}".encode()).hexdigest()[:16]
    return base64.urlsafe_b64encode(f"{data}:{sig}".encode()).decode()


def verify_token(token: str) -> dict | None:
    """Verify and decode an auth token"""
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        parts = decoded.rsplit(':', 1)
        if len(parts) != 2:
            return None
        data, sig = parts
        expected = hashlib.sha256(f"{data}:{SECRET_KEY}".encode()).hexdigest()[:16]
        if sig != expected:
            return None
        data_parts = data.split(':')
        if len(data_parts) != 3:
            return None
        return {'user_id': int(data_parts[0]), 'email': data_parts[1]}
    except Exception:
        return None

# Global model instances
emotion_model = None
preprocessor = None
vad = None
audeering_model = None           # audeering MSP-Podcast (BEST — real telephone speech, dimensional)
audeering_processor = None
superb_model = None              # superb/wav2vec2-base-superb-er (2nd — IEMOCAP natural speech)
superb_feature_extractor = None
hf_model = None                  # ehcalabres wav2vec2 (3rd fallback — RAVDESS acted speech)
hf_feature_extractor = None      # HuggingFace feature extractor

AUDEERING_MODEL_ID = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"
SUPERB_MODEL_ID = "superb/wav2vec2-base-superb-er"
HF_MODEL_ID = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"

# ── Dimensional → categorical mapping for audeering model ─────────────────────
# The audeering model outputs arousal, dominance, valence (each ~0–1).
# We map to categorical using Gaussian similarity to prototype points in the
# circumplex model of affect (Russell, 1980).  Bandwidth σ = 0.30.
_EMOTION_PROTOTYPES = {
    # (arousal_center, valence_center) — dominance not used for 4-class mapping
    'angry':   (0.75, 0.20),   # high energy, very negative
    'happy':   (0.75, 0.80),   # high energy, very positive
    'sad':     (0.25, 0.25),   # low energy, negative
    'neutral': (0.45, 0.60),   # moderate energy, slightly positive (typical neutral speech)
}
_PROTO_BANDWIDTH = 0.30

def _dims_to_categorical(arousal: float, dominance: float, valence: float) -> tuple:
    """
    Convert (arousal, dominance, valence) → (emotion, confidence, probabilities).
    Uses Gaussian similarity to circumplex prototypes so the mapping is smooth
    and reflects genuine uncertainty rather than hard thresholds.
    """
    scores = {}
    for emotion, (a_c, v_c) in _EMOTION_PROTOTYPES.items():
        dist = math.sqrt((arousal - a_c) ** 2 + (valence - v_c) ** 2)
        scores[emotion] = math.exp(-dist / _PROTO_BANDWIDTH)

    total = sum(scores.values()) or 1.0
    probs = {k: round(v / total, 3) for k, v in scores.items()}
    top = max(probs, key=probs.get)
    return top, round(probs[top], 3), probs

# Map superb model label codes → canonical emotion names
SUPERB_LABEL_MAP = {
    'ang': 'angry',   'angry': 'angry',
    'hap': 'happy',   'happy': 'happy',
    'exc': 'happy',   # excited → happy
    'neu': 'neutral', 'neutral': 'neutral',
    'sad': 'sad',
}

# Class bias for SUPERB/IEMOCAP model.
# IEMOCAP "neutral" was recorded as completely flat/monotone acted speech.
# Real conversational speech is more animated than that, so the model
# consistently maps it toward 'angry' (the closest high-energy class).
# These multipliers shift the balance back toward neutral without
# suppressing genuinely angry callers.
SUPERB_CLASS_BIAS = {
    'angry':   0.60,  # strong penalty — real speech is rarely IEMOCAP-level angry
    'happy':   1.10,
    'neutral': 1.30,  # strong boost — real business speech is nearly always neutral
    'sad':     1.00,
}

# Map HF label variants → our canonical 7-class set (ehcalabres fallback)
HF_LABEL_MAP = {
    'angry': 'angry', 'anger': 'angry', 'ang': 'angry',
    'disgust': 'disgust', 'dis': 'disgust',
    'fearful': 'fearful', 'fear': 'fearful', 'fea': 'fearful',
    'happy': 'happy', 'hap': 'happy',
    'neutral': 'neutral', 'neu': 'neutral',
    'calm': 'neutral', 'cal': 'neutral',
    'sad': 'sad',
    'surprised': 'surprised', 'sur': 'surprised',
}

# Per-call rolling audio accumulator (2-second context window for model accuracy)
audio_accumulators: dict = {}
ACCUMULATOR_SAMPLES = 16000 * 2   # 2 seconds at 16 kHz

# Per-call prediction history for majority voting
prediction_history: dict = {}
HISTORY_SIZE = 3   # vote over last 3 predictions (~0.75s lag)

# VAD: chunk RMS must exceed this to count as speech.
# Room noise is typically 0.001-0.008; speech is 0.015+
VAD_THRESHOLD = 0.012

# Class bias correction — this model (trained on English RAVDESS actors) systematically
# over-predicts 'angry' on real-world speech. Multiply raw probs then renormalize.
CLASS_BIAS = {
    'angry':     0.70,   # mild penalty
    'disgust':   0.85,
    'fearful':   0.90,
    'happy':     1.20,   # mild boost
    'neutral':   1.15,   # mild boost
    'sad':       1.00,
    'surprised': 1.10,
}


def _load_audeering_model() -> bool:
    """
    Load audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim.

    WHY this model:
    - Pre-trained on Switchboard + Fisher (real telephone speech, not clean studio audio)
    - Fine-tuned on MSP-Podcast (100,000+ natural spontaneous speech utterances)
    - Outputs DIMENSIONAL emotion: arousal / dominance / valence (0–1 each)
    - Dimensional output has NO categorical bias — "angry" is derived from high
      arousal + low valence, not from a model that was shown acted anger.
    - 1.17 million HuggingFace downloads — the production standard for open-source SER.
    """
    global audeering_model, audeering_processor
    if not _AUDEERING_CLASSES_AVAILABLE:
        raise RuntimeError("torch/transformers not available")

    from transformers import Wav2Vec2Processor

    print(f"Loading {AUDEERING_MODEL_ID} (MSP-Podcast natural speech, dimensional) ...")
    audeering_processor = Wav2Vec2Processor.from_pretrained(AUDEERING_MODEL_ID)
    audeering_model = _AudeeringEmotionModel.from_pretrained(AUDEERING_MODEL_ID)
    audeering_model.eval()

    print("✓ Audeering model loaded — outputs arousal/dominance/valence, "
          "maps to angry/happy/neutral/sad via circumplex model. No angry bias.")
    return True


def audeering_predict(audio_array: np.ndarray) -> dict:
    """
    Predict emotion using the audeering dimensional model.
    Returns the same dict shape as superb_predict/hf_predict so the rest
    of the pipeline is unchanged.
    """
    import torch
    try:
        inputs = audeering_processor(
            audio_array, sampling_rate=16000, return_tensors="pt", padding=True
        )
        with torch.no_grad():
            _, logits = audeering_model(inputs["input_values"])

        # logits shape: (1, 3) → [arousal, dominance, valence], already in ~[0, 1]
        arousal, dominance, valence = logits[0].tolist()

        emotion, confidence, probs = _dims_to_categorical(arousal, dominance, valence)

        print(f"[AUDEERING] A={arousal:.2f} D={dominance:.2f} V={valence:.2f} "
              f"→ probs={probs} → {emotion}")

        return {
            'emotion': emotion,
            'confidence': confidence,
            'probabilities': probs,
            # Pass raw dims through so frontend/DB can store them if needed
            'arousal': round(arousal, 3),
            'dominance': round(dominance, 3),
            'valence': round(valence, 3),
        }
    except Exception as e:
        print(f"Audeering prediction error: {e}")
        return get_demo_prediction()


def _load_superb_model() -> bool:
    """
    Load superb/wav2vec2-base-superb-er — trained on IEMOCAP (natural conversational speech).
    Uses standard AutoModelForAudioClassification — no custom weight remapping needed.
    4 classes: angry, happy, neutral, sad.
    """
    global superb_model, superb_feature_extractor
    from transformers import AutoModelForAudioClassification, AutoFeatureExtractor

    print(f"Loading {SUPERB_MODEL_ID} (IEMOCAP natural-speech model) ...")
    superb_feature_extractor = AutoFeatureExtractor.from_pretrained(SUPERB_MODEL_ID)
    superb_model = AutoModelForAudioClassification.from_pretrained(SUPERB_MODEL_ID)
    superb_model.eval()

    labels = list(superb_model.config.id2label.values())
    print(f"✓ SUPERB model loaded — natural speech detection active! Labels: {labels}")
    return True


def _load_hf_custom() -> bool:
    """
    Load the ehcalabres wav2vec2 emotion model from local cache.

    The checkpoint uses a non-standard 2-layer classification head
    (classifier.dense + classifier.output) rather than the HuggingFace
    default (projector + classifier), so we build a custom nn.Module that
    exactly matches the checkpoint and load the weights with key remapping.
    """
    global hf_model, hf_feature_extractor
    import glob, torch, torch.nn as nn
    from transformers import Wav2Vec2Model, Wav2Vec2Config, Wav2Vec2FeatureExtractor
    from safetensors.torch import load_file

    # Locate the cached snapshot
    cache_base = os.path.expanduser('~/.cache/huggingface/hub')
    model_slug = 'models--ehcalabres--wav2vec2-lg-xlsr-en-speech-emotion-recognition'
    snapshots = glob.glob(os.path.join(cache_base, model_slug, 'snapshots', '*'))
    if not snapshots:
        raise FileNotFoundError("Model not found in HuggingFace cache — run with internet access once to download it")
    snapshot_dir = snapshots[0]

    safetensors_path = os.path.join(snapshot_dir, 'model.safetensors')
    config_path = snapshot_dir

    print(f"Loading HuggingFace model from cache: {snapshot_dir}")

    class _Wav2Vec2EmotionModel(nn.Module):
        """
        Matches the ehcalabres checkpoint architecture exactly.
        The original training used Wav2Vec2ClassificationHead which applies:
          dropout → dense → tanh → dropout → out_proj
        Using relu instead of tanh (as we did before) produces a completely
        distorted feature space and garbage predictions.
        """
        def __init__(self, config):
            super().__init__()
            self.wav2vec2 = Wav2Vec2Model(config)
            hidden = config.hidden_size          # 1024 for xlsr-large
            self.dense = nn.Linear(hidden, hidden)
            self.out_proj = nn.Linear(hidden, config.num_labels)
            self.id2label = config.id2label

        def forward(self, input_values, attention_mask=None):
            outputs = self.wav2vec2(input_values, attention_mask=attention_mask)
            hidden = outputs.last_hidden_state   # (B, T, H)

            # Attention-mask-aware mean pooling
            if attention_mask is not None:
                mask = self.wav2vec2._get_feature_vector_attention_mask(
                    hidden.shape[1], attention_mask
                )
                hidden = hidden * mask.unsqueeze(-1).float()
                pooled = hidden.sum(1) / mask.sum(1, keepdim=True).float().clamp(min=1)
            else:
                pooled = hidden.mean(1)

            # Classification head — MUST use tanh (matches Wav2Vec2ClassificationHead)
            x = torch.tanh(self.dense(pooled))
            return self.out_proj(x)

    config = Wav2Vec2Config.from_pretrained(config_path)
    config.num_labels = 8   # override None in config.json
    model = _Wav2Vec2EmotionModel(config)

    # Load safetensors and remap the classifier keys
    raw_state = load_file(safetensors_path)
    remapped = {}
    for k, v in raw_state.items():
        if k == 'classifier.dense.weight':    remapped['dense.weight'] = v
        elif k == 'classifier.dense.bias':    remapped['dense.bias'] = v
        elif k == 'classifier.output.weight': remapped['out_proj.weight'] = v
        elif k == 'classifier.output.bias':   remapped['out_proj.bias'] = v
        else:                                 remapped[k] = v

    missing, unexpected = model.load_state_dict(remapped, strict=False)
    unexpected_real = [k for k in unexpected if not k.startswith('wav2vec2.masked_spec')]
    if unexpected_real:
        print(f"[HF] Unexpected keys (ignored): {unexpected_real}")
    if missing:
        raise RuntimeError(f"[HF] Missing keys after remap: {missing}")

    model.eval()
    hf_model = model

    # Standard Wav2Vec2 feature extractor (no preprocessor_config.json needed)
    hf_feature_extractor = Wav2Vec2FeatureExtractor(
        feature_size=1, sampling_rate=16000, padding_value=0.0,
        do_normalize=True, return_attention_mask=True,
    )

    labels = list(config.id2label.values())
    print(f"✓ HuggingFace wav2vec2 model loaded — real-voice detection active! Labels: {labels}")
    return True


def load_model():
    """Load best available emotion model in priority order."""
    global emotion_model, preprocessor, vad
    global audeering_model, audeering_processor
    global superb_model, superb_feature_extractor
    global hf_model, hf_feature_extractor

    # ── 1. Audeering MSP-Podcast model (production standard, no angry bias) ───
    try:
        _load_audeering_model()
        return True
    except Exception as e:
        print(f"Audeering model not available ({e}). Trying SUPERB model …")
        audeering_model = None
        audeering_processor = None

    # ── 2. SUPERB IEMOCAP model ───────────────────────────────────────────────
    try:
        _load_superb_model()
        return True
    except Exception as e:
        print(f"SUPERB model not available ({e}). Trying ehcalabres model …")
        superb_model = None
        superb_feature_extractor = None

    # ── 3. ehcalabres RAVDESS model (fallback — has angry bias) ──────────────
    try:
        _load_hf_custom()
        return True
    except Exception as e:
        print(f"HuggingFace model not available ({e}). Trying local model …")
        hf_model = None
        hf_feature_extractor = None

    # ── 4. Try local CNN+LSTM model ────────────────────────────────────────────
    if not MODEL_AVAILABLE:
        print("Running in demo mode (install requirements to enable real detection)")
        return False

    try:
        model_path = os.path.join(os.path.dirname(__file__), '..', 'ml_engine', 'models', 'best_model.keras')
        encoder_path = os.path.join(os.path.dirname(__file__), '..', 'ml_engine', 'models', 'encoder.pkl')

        if os.path.exists(model_path) and os.path.exists(encoder_path):
            with open(encoder_path, 'rb') as f:
                encoder = pickle.load(f)
            emotion_model = EmotionInference(model_path, list(encoder.classes_))
            preprocessor = get_preprocessor()
            vad = get_vad()
            print(f"✓ CNN+LSTM model loaded with emotions: {encoder.classes_}")
            return True
        else:
            print("Local model files not found. Running in demo mode.")
            return False
    except Exception as e:
        print(f"Error loading local model: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("Starting up Emotion Detection API...")
    init_database()
    load_model()
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Emotion Detection API",
    description="Real-time speech emotion detection for call centers",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class CallStartRequest(BaseModel):
    agent_name: str = "Agent"
    customer_name: str = "Customer"


class EmotionResponse(BaseModel):
    emotion: str
    confidence: float
    probabilities: dict
    timestamp: str


class CallSummary(BaseModel):
    call_id: str
    duration_seconds: int
    dominant_emotion: Optional[str]
    emotion_distribution: dict
    avg_confidence: float


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# Demo emotion generator (when no model is available)
def get_demo_prediction():
    """Generate demo emotion prediction"""
    import random
    emotions = ['neutral', 'happy', 'sad', 'angry', 'fearful', 'disgust', 'surprised']
    emotion = random.choice(emotions)
    confidence = random.uniform(0.6, 0.95)
    probabilities = {e: random.uniform(0.01, 0.3) for e in emotions}
    probabilities[emotion] = confidence
    total = sum(probabilities.values())
    probabilities = {k: round(v / total, 3) for k, v in probabilities.items()}
    return {'emotion': emotion, 'confidence': round(confidence, 3), 'probabilities': probabilities}


def superb_predict(audio_array: np.ndarray) -> dict:
    """Predict emotion using the SUPERB wav2vec2 model (IEMOCAP-trained, natural speech)."""
    import torch
    try:
        inputs = superb_feature_extractor(
            audio_array, sampling_rate=16000, return_tensors="pt", padding=True
        )
        with torch.no_grad():
            logits = superb_model(**inputs).logits

        # Temperature scaling — softens over-confident predictions
        TEMPERATURE = 2.0
        scores = torch.softmax(logits / TEMPERATURE, dim=1)[0].tolist()
        id2label = superb_model.config.id2label

        # Map label codes → canonical names, merge duplicates
        raw_probs: dict = {}
        for i, score in enumerate(scores):
            label = SUPERB_LABEL_MAP.get(id2label[i].lower(), id2label[i].lower())
            raw_probs[label] = raw_probs.get(label, 0.0) + score

        # Apply class bias — IEMOCAP neutral is flat/monotone, real conversational
        # speech is more animated, causing the model to over-predict 'angry'.
        adjusted = {k: v * SUPERB_CLASS_BIAS.get(k, 1.0) for k, v in raw_probs.items()}
        total = sum(adjusted.values())
        probabilities = {k: round(v / total, 3) for k, v in adjusted.items()}

        top_label = max(probabilities, key=probabilities.get)

        # Log raw vs corrected probabilities — shows in backend console for debugging
        print(f"[SUPERB] raw={raw_probs} → corrected={probabilities} → {top_label}")

        return {
            'emotion': top_label,
            'confidence': round(probabilities[top_label], 3),
            'probabilities': probabilities,
        }
    except Exception as e:
        print(f"SUPERB prediction error: {e}")
        return get_demo_prediction()


def hf_predict(audio_array: np.ndarray) -> dict:
    """Predict emotion using the directly loaded HuggingFace wav2vec2 model."""
    import torch
    try:
        inputs = hf_feature_extractor(
            audio_array, sampling_rate=16000, return_tensors="pt", padding=True
        )
        with torch.no_grad():
            logits = hf_model(**inputs)

        # Temperature scaling (T=3.0) — prevents extreme confidence values.
        TEMPERATURE = 3.0
        scores = torch.softmax(logits / TEMPERATURE, dim=1)[0].tolist()
        id2label = hf_model.id2label

        # Normalize labels + merge duplicates (e.g. 'calm' + 'neutral' → 'neutral')
        raw_probs: dict = {}
        for i, score in enumerate(scores):
            label = HF_LABEL_MAP.get(id2label[i].lower(), id2label[i].lower())
            raw_probs[label] = raw_probs.get(label, 0.0) + score

        # Apply class bias correction — compensates for model's over-prediction of 'angry'
        adjusted = {k: v * CLASS_BIAS.get(k, 1.0) for k, v in raw_probs.items()}
        total = sum(adjusted.values())
        probabilities = {k: round(v / total, 3) for k, v in adjusted.items()}

        top_label = max(probabilities, key=probabilities.get)
        return {
            'emotion': top_label,
            'confidence': round(probabilities[top_label], 3),
            'probabilities': probabilities,
        }
    except Exception as e:
        print(f"HF prediction error: {e}")
        return get_demo_prediction()


def process_audio_chunk(audio_data: bytes, call_id: str, time_offset: float) -> dict:
    """Process an audio chunk using a rolling 2-second context window."""
    try:
        # Convert raw PCM bytes → float32
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        audio_energy = float(np.sqrt(np.mean(audio_array ** 2)))

        # VAD on the CURRENT CHUNK energy (not context) so silence is detected
        # immediately when the user stops talking, not after a 2s lag.
        if audio_energy < VAD_THRESHOLD:
            # Clear the rolling accumulator on silence — keeping silent audio in the
            # context window causes the model to output wrong/neutral predictions when
            # speech resumes (silence pollutes the 2-second window).
            audio_accumulators.pop(call_id, None)
            # Reset prediction history so stale votes don't persist into next speech
            prediction_history.pop(call_id, None)
            return {
                'emotion': 'silence',
                'confidence': 1.0,
                'probabilities': {'silence': 1.0},
                'is_speech': False,
                'audio_energy': audio_energy,
            }

        # Update rolling context accumulator
        if call_id not in audio_accumulators:
            audio_accumulators[call_id] = audio_array
        else:
            combined = np.concatenate([audio_accumulators[call_id], audio_array])
            audio_accumulators[call_id] = combined[-ACCUMULATOR_SAMPLES:]

        context = audio_accumulators[call_id]

        # Need at least 0.5 s to avoid mic-onset noise false positives
        if len(context) < 8000:
            return {
                'emotion': 'neutral',
                'confidence': 0.5,
                'probabilities': {'neutral': 1.0},
                'is_speech': True,
                'audio_energy': audio_energy,
            }

        # Predict using best available model
        if audeering_model:
            result = audeering_predict(context)
        elif superb_model:
            result = superb_predict(context)
        elif hf_model:
            result = hf_predict(context)
        elif emotion_model and preprocessor:
            features = preprocessor.preprocess_stream_chunk(context)
            result = emotion_model.predict_emotion(features)
        else:
            result = get_demo_prediction()

        # Confidence floor: audeering/superb derive 4 classes (random = 25%),
        # ehcalabres has 8 (random = 12.5%). Higher floor for 4-class.
        confidence_floor = 0.40 if (audeering_model or superb_model) else 0.30
        if result['confidence'] < confidence_floor:
            result['emotion'] = 'neutral'

        # Majority voting over last HISTORY_SIZE predictions per call
        if call_id not in prediction_history:
            prediction_history[call_id] = []
        prediction_history[call_id].append(result['emotion'])
        if len(prediction_history[call_id]) > HISTORY_SIZE:
            prediction_history[call_id] = prediction_history[call_id][-HISTORY_SIZE:]

        history = prediction_history[call_id]
        vote_counts: dict = {}
        for e in history:
            vote_counts[e] = vote_counts.get(e, 0) + 1
        voted_emotion = max(vote_counts, key=vote_counts.get)

        result['emotion'] = voted_emotion
        result['is_speech'] = True
        result['audio_energy'] = audio_energy
        return result

    except Exception as e:
        print(f"Error processing audio: {e}")
        return {'emotion': 'error', 'confidence': 0.0, 'probabilities': {}, 'is_speech': False, 'audio_energy': 0.0}


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, call_id: str):
        await websocket.accept()
        self.active_connections[call_id] = {
            'websocket': websocket,
            'start_time': datetime.utcnow(),
            'emotion_history': []
        }
    
    def disconnect(self, call_id: str):
        if call_id in self.active_connections:
            del self.active_connections[call_id]
    
    async def send_emotion(self, call_id: str, data: dict):
        if call_id in self.active_connections:
            await self.active_connections[call_id]['websocket'].send_json(data)
    
    def add_emotion_to_history(self, call_id: str, emotion_data: dict):
        if call_id in self.active_connections:
            self.active_connections[call_id]['emotion_history'].append(emotion_data)
    
    def get_emotion_history(self, call_id: str) -> List[dict]:
        if call_id in self.active_connections:
            return self.active_connections[call_id]['emotion_history']
        return []


manager = ConnectionManager()


# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Emotion Detection API",
        "version": "1.0.0",
        "model_loaded": emotion_model is not None,
        "endpoints": {
            "websocket": "/ws/stream/{call_id}",
            "calls": "/api/calls",
            "analytics": "/api/analytics"
        }
    }


@app.get("/health")
async def health_check():
    if audeering_model is not None:
        active_model = AUDEERING_MODEL_ID
        model_type = "dimensional (arousal/dominance/valence → categorical)"
    elif superb_model is not None:
        active_model = SUPERB_MODEL_ID
        model_type = "categorical-4 (IEMOCAP)"
    elif hf_model is not None:
        active_model = HF_MODEL_ID
        model_type = "categorical-8 (RAVDESS)"
    elif emotion_model is not None:
        active_model = "local-cnn-lstm"
        model_type = "local"
    else:
        active_model = "demo-mode"
        model_type = "random"
    return {
        "status": "healthy",
        "model_loaded": any([audeering_model, superb_model, hf_model, emotion_model]),
        "active_model": active_model,
        "model_type": model_type,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/calls/start")
async def start_call(request: CallStartRequest):
    """Start a new call session"""
    call_id = str(uuid.uuid4())
    
    call = db_manager.create_call(
        call_id=call_id,
        agent_name=request.agent_name,
        customer_name=request.customer_name
    )
    
    return {
        "call_id": call_id,
        "start_time": call.start_time.isoformat(),
        "status": "active"
    }


@app.post("/api/calls/{call_id}/end")
async def end_call(call_id: str):
    """End a call session — computes overall stats from DB records (reliable even after WS disconnect)"""
    loop = asyncio.get_event_loop()

    # Run synchronous DB calls in thread pool so they don't block the event loop
    db_emotions = await loop.run_in_executor(None, db_manager.get_call_emotions, call_id)

    emotion_stats = None
    if db_emotions:
        emotion_counts: dict = {}
        total_confidence = 0.0
        valid = 0

        for e in db_emotions:
            emotion = e.get('emotion', 'unknown')
            if emotion in ('silence', 'error'):
                continue
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_confidence += e.get('confidence', 0.0)
            valid += 1

        if emotion_counts:
            total = sum(emotion_counts.values())
            emotion_stats = {
                'dominant_emotion': max(emotion_counts, key=emotion_counts.get),
                'distribution': {k: round(v / total, 3) for k, v in emotion_counts.items()},
                'avg_confidence': round(total_confidence / valid, 3)
            }

    await loop.run_in_executor(None, db_manager.end_call, call_id, emotion_stats)
    manager.disconnect(call_id)

    return {"status": "ended", "call_id": call_id, "emotion_stats": emotion_stats}


@app.get("/api/calls")
async def get_calls(limit: int = 100, offset: int = 0):
    """Get call history"""
    calls = db_manager.get_call_history(limit=limit, offset=offset)
    return {"calls": calls, "total": len(calls)}


@app.get("/api/calls/{call_id}")
async def get_call(call_id: str):
    """Get call details"""
    call = db_manager.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    emotions = db_manager.get_call_emotions(call_id)
    
    return {
        "call": call.to_dict(),
        "emotions": emotions
    }


@app.get("/api/calls/{call_id}/emotions")
async def get_call_emotions(call_id: str):
    """Get emotion timeline for a call"""
    call = db_manager.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    emotions = db_manager.get_call_emotions(call_id)
    return {"call_id": call_id, "emotions": emotions}


@app.delete("/api/calls/{call_id}")
async def delete_call(call_id: str):
    """Delete a call record"""
    success = db_manager.delete_call(call_id)
    if not success:
        raise HTTPException(status_code=404, detail="Call not found or could not be deleted")
    return {"status": "deleted", "call_id": call_id}


@app.get("/api/calls/{call_id}/export")
async def export_call(call_id: str):
    """Export call data as JSON"""
    call = db_manager.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    emotions = db_manager.get_call_emotions(call_id)
    export_data = {
        "metadata": call.to_dict(),
        "emotions": emotions
    }
    return export_data


@app.get("/api/calls/{call_id}/transcript")
async def get_transcript(call_id: str):
    """Generate a simple transcript from emotion logs"""
    call = db_manager.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    emotions = db_manager.get_call_emotions(call_id)
    
    transcript = []
    transcript.append(f"Call ID: {call_id}")
    transcript.append(f"Agent: {call.agent_name}")
    transcript.append(f"Customer: {call.customer_name}")
    transcript.append(f"Date: {call.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    transcript.append("-" * 30)
    
    for e in emotions:
        if not e.get('is_speech', True):
            continue
        time_str = f"[{e['time_offset_seconds']:.1f}s]"
        emotion = e['emotion'].upper()
        confidence = f"(conf: {e['confidence']:.2f})"
        transcript.append(f"{time_str} Detected Emotion: {emotion} {confidence}")
        
    return {"transcript": "\n".join(transcript)}


@app.get("/api/analytics/agents")
async def get_agent_analytics(agent_name: Optional[str] = None, days: int = 30):
    """Get agent performance analytics computed from call data"""
    analytics = db_manager.compute_agent_analytics(agent_name=agent_name, days=days)
    return {"analytics": analytics}


@app.get("/api/analytics/summary")
async def get_analytics_summary(days: int = 30):
    """Get overall analytics summary"""
    summary = db_manager.get_overall_summary(days=days)
    return summary


@app.get("/api/analytics/emotions-trend")
async def get_emotions_trend(days: int = 7):
    """Get daily emotion breakdown for trend charts"""
    trend = db_manager.get_emotions_trend(days=days)
    return {"trend": trend}


@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    existing = db_manager.get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = db_manager.create_user(
        email=request.email,
        name=request.name,
        password_hash=hash_password(request.password)
    )
    token = create_token(user['id'], user['email'])
    return {
        "token": token,
        "user": {k: v for k, v in user.items() if k != 'password_hash'}
    }


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login an existing user"""
    user = db_manager.get_user_by_email(request.email)
    if not user or user['password_hash'] != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.get('is_active', True):
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_token(user['id'], user['email'])
    return {
        "token": token,
        "user": {k: v for k, v in user.items() if k not in ('password_hash', 'is_active')}
    }


class UpdateProfileRequest(BaseModel):
    name: str


@app.put("/api/auth/profile")
async def update_profile(request: UpdateProfileRequest, authorization: Optional[str] = Header(None)):
    """Update logged-in user's display name"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Authorization required")
    payload = verify_token(authorization[7:])
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    db_manager.update_user_name(payload['user_id'], request.name)
    return {"message": "Profile updated", "name": request.name}


# WebSocket endpoint for real-time streaming
@app.websocket("/ws/stream/{call_id}")
async def websocket_stream(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for real-time audio streaming
    Client sends audio chunks, server returns emotion predictions
    """
    await manager.connect(websocket, call_id)
    
    # Initialize audio buffer for file saving
    audio_buffer = []
    chunk_counter = 0
    
    try:
        while True:
            # Receive message from WebSocket
            message = await websocket.receive()
            
            # Handle text messages (control commands)
            if 'text' in message and message['text']:
                text_data = message['text']
                data = json.loads(text_data)
                
                if data.get('action') == 'stop':
                    break
                
                elif data.get('action') == 'config':
                    # Handle configuration
                    await websocket.send_json({
                        'type': 'config_ack',
                        'sample_rate': 16000,
                        'chunk_size': 1024
                    })
            
            # Handle binary messages (audio data)
            elif 'bytes' in message and message['bytes']:
                audio_bytes = message['bytes']
                chunk_counter += 1
                audio_buffer.append(audio_bytes)
                
                # Calculate time offset
                time_offset = chunk_counter * 0.5  # Assuming 500ms chunks
                
                # Process audio and get emotion — run in thread pool so model
                # inference doesn't block the async event loop (which would cause
                # the WebSocket connection to drop mid-call).
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, process_audio_chunk, audio_bytes, call_id, time_offset
                )
                
                # Add metadata
                response = {
                    'type': 'emotion',
                    'timestamp': datetime.utcnow().isoformat(),
                    'time_offset': time_offset,
                    'chunk_id': chunk_counter,
                    **result
                }
                
                # Send result back to client
                await manager.send_emotion(call_id, response)
                
                # Store in database
                db_manager.log_emotion(call_id, {
                    'time_offset': time_offset,
                    'emotion': result['emotion'],
                    'confidence': result['confidence'],
                    'probabilities': result.get('probabilities', {}),
                    'is_speech': result.get('is_speech', True),
                    'audio_energy': result.get('audio_energy')
                })
                
                # Add to history
                manager.add_emotion_to_history(call_id, response)
            
            # Handle disconnect
            elif message.get('type') == 'websocket.disconnect':
                break
    
    except WebSocketDisconnect:
        print(f"Client disconnected for call {call_id}")
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    finally:
        # Save audio file and run post-call analysis
        if audio_buffer:
            audio_path = os.path.join(UPLOAD_DIR, f"{call_id}.wav")
            try:
                with wave.open(audio_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    for chunk in audio_buffer:
                        wf.writeframes(chunk)
                print(f"Audio saved to {audio_path}")
                db_manager.set_audio_path(call_id, audio_path)
                # Schedule full-recording analysis in background
                asyncio.create_task(analyze_full_recording(call_id, audio_path))
            except Exception as e:
                print(f"Error saving audio: {e}")

        # Clean up per-call state
        audio_accumulators.pop(call_id, None)
        prediction_history.pop(call_id, None)
        manager.disconnect(call_id)


def _analyze_full_recording_sync(call_id: str, audio_path: str):
    """
    CPU-bound post-call analysis — always called from a thread pool, never directly
    from an async context, so it is safe to do blocking I/O and model inference here.
    """
    try:
        with wave.open(audio_path, 'rb') as wf:
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        if len(audio) < 8000:   # < 0.5 s — not worth analysing
            return

        CHUNK = 16000 * 3       # 3-second window
        HOP   = 16000           # 1-second step

        predictions = []
        pos = 0
        while pos < len(audio):
            segment = audio[pos: pos + CHUNK]
            if len(segment) < CHUNK:
                segment = np.pad(segment, (0, CHUNK - len(segment)))

            energy = float(np.sqrt(np.mean(segment ** 2)))
            if energy < 0.001:
                pos += HOP
                continue

            if audeering_model:
                result = audeering_predict(segment)
            elif superb_model:
                result = superb_predict(segment)
            elif hf_model:
                result = hf_predict(segment)
            elif emotion_model and preprocessor:
                features = preprocessor.preprocess_stream_chunk(segment)
                result = emotion_model.predict_emotion(features)
            else:
                result = get_demo_prediction()

            if result.get('emotion') not in ('error',):
                result['audio_energy'] = energy
                predictions.append(result)

            pos += HOP

        if not predictions:
            return

        speech = [p for p in predictions if p.get('emotion') != 'silence'] or predictions

        emotion_counts: dict = {}
        total_conf = 0.0
        for p in speech:
            emo = p['emotion']
            emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
            total_conf += p.get('confidence', 0.0)

        total = len(speech)
        dominant = max(emotion_counts, key=emotion_counts.get)

        db_manager.update_emotion_stats(call_id, {
            'dominant_emotion': dominant,
            'distribution': {k: round(v / total, 3) for k, v in emotion_counts.items()},
            'avg_confidence': round(total_conf / total, 3)
        })
        print(f"[Post-call] call={call_id} dominant={dominant} segments={total}")

    except Exception as e:
        print(f"[Post-call] Error analyzing {call_id}: {e}")


async def analyze_full_recording(call_id: str, audio_path: str):
    """
    Post-call async wrapper: offloads all CPU work to a thread pool so the
    event loop stays free to handle new HTTP requests (like /end) immediately.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _analyze_full_recording_sync, call_id, audio_path)


@app.get("/api/calls/{call_id}/recording")
async def get_recording(call_id: str):
    """Stream the saved call recording inline (no Content-Disposition: attachment)"""
    audio_path = os.path.join(UPLOAD_DIR, f"{call_id}.wav")
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Recording not found")
    # Do NOT pass filename= — that adds Content-Disposition: attachment which
    # prevents browsers from streaming the file through an <audio> element.
    return FileResponse(audio_path, media_type="audio/wav")


# Run the server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
