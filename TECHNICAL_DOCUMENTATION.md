# Emotion Detection System — Full Technical Documentation

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Backend — How It Works](#4-backend--how-it-works)
5. [Frontend — How It Works](#5-frontend--how-it-works)
6. [ML Model — How It Works](#6-ml-model--how-it-works)
7. [Database — Tables & Schema](#7-database--tables--schema)
8. [API Reference](#8-api-reference)
9. [WebSocket Protocol](#9-websocket-protocol)
10. [Authentication System](#10-authentication-system)
11. [Audio Processing Pipeline](#11-audio-processing-pipeline)
12. [Data Flow — End to End](#12-data-flow--end-to-end)

---

## 1. Project Overview

**EmoDetect** is a real-time speech emotion detection system built for call centers. It listens to a live microphone stream from a call agent, analyzes the speech audio every ~0.25 seconds, and predicts the emotional state of the speaker (angry, happy, neutral, sad) with a confidence score. All results are stored in a MySQL database and displayed live on a React dashboard.

**Use case:** A call center supervisor can watch a live dashboard showing the emotional state of a customer during a call. After the call ends, full analytics (dominant emotion, emotion distribution, timeline, confidence) are stored and available for review.

---

## 2. Technology Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Runtime language |
| FastAPI | 0.103+ | REST API + WebSocket server |
| Uvicorn | 0.23+ | ASGI server (runs FastAPI) |
| SQLAlchemy | 2.0+ | ORM for database operations |
| PyMySQL | 1.1+ | MySQL database driver |
| python-dotenv | 1.0+ | Load environment variables from .env |
| PyTorch | 2.0+ | Neural network inference engine |
| Transformers | 4.30+ | HuggingFace model loading |
| TensorFlow | 2.13+ | Fallback CNN+LSTM model |
| NumPy | 1.24+ | Audio array processing |
| librosa | 0.10+ | Audio feature extraction |
| noisereduce | 3.0+ | Background noise filtering |
| safetensors | latest | Efficient model weight loading |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 19.2 | UI framework |
| TypeScript | 5.9 | Type-safe JavaScript |
| Vite | 7.2 | Build tool and dev server |
| React Router | 7.13 | Client-side routing |
| Tailwind CSS | 3.4 | Utility-first CSS |
| ShadcnUI | latest | Pre-built accessible UI components |
| Recharts | 2.15 | Charts and graphs |
| React Hook Form | 7.70 | Form state management |
| Zod | 4.3 | Runtime schema validation |
| Lucide React | 0.562 | Icon library |
| Sonner | 2.0 | Toast notifications |

### Database
| Technology | Purpose |
|---|---|
| MySQL 8.0 | Primary production database |
| SQLite | Local development fallback |
| TablePlus | GUI client for viewing data |

---

## 3. Project Structure

```
C:\emotion-detection\
│
├── app/                                  ← React Frontend
│   ├── src/
│   │   ├── main.tsx                      ← App entry point
│   │   ├── App.tsx                       ← Routing & layout
│   │   ├── index.css                     ← Global styles
│   │   │
│   │   ├── pages/                        ← Full page components
│   │   │   ├── Dashboard.tsx             ← Live call monitoring
│   │   │   ├── CallHistory.tsx           ← Past call records
│   │   │   ├── Analytics.tsx             ← Agent performance charts
│   │   │   ├── Login.tsx                 ← Sign in page
│   │   │   ├── Signup.tsx                ← Registration page
│   │   │   ├── Profile.tsx               ← User profile editor
│   │   │   └── Settings.tsx              ← App settings
│   │   │
│   │   ├── components/
│   │   │   ├── dashboard/
│   │   │   │   ├── CallControls.tsx      ← Start/End call buttons
│   │   │   │   ├── CurrentEmotion.tsx    ← Live emotion display
│   │   │   │   ├── EmotionGraph.tsx      ← Confidence line chart
│   │   │   │   ├── EmotionDistribution.tsx ← Doughnut chart
│   │   │   │   └── EmotionTimeline.tsx   ← Segment timeline
│   │   │   ├── ui/                       ← 60+ ShadcnUI components
│   │   │   └── ErrorBoundary.tsx         ← Error fallback UI
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts           ← WebSocket + mic recording logic
│   │   │   ├── useApi.ts                 ← HTTP fetch helpers
│   │   │   └── use-mobile.ts             ← Responsive detection
│   │   │
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx           ← Login state & token storage
│   │   │
│   │   ├── types/
│   │   │   └── index.ts                  ← All TypeScript interfaces
│   │   │
│   │   └── lib/
│   │       └── utils.ts                  ← cn() class helper
│   │
│   ├── package.json                      ← npm dependencies
│   ├── vite.config.ts                    ← Vite build config
│   ├── tailwind.config.js                ← Tailwind config
│   └── tsconfig.json                     ← TypeScript config
│
└── emotion-detection-system/            ← Python Backend
    ├── backend/
    │   ├── main.py                       ← FastAPI app (900+ lines)
    │   ├── database.py                   ← SQLAlchemy models & queries
    │   ├── .env                          ← Database URL (not committed)
    │   └── uploads/                      ← Saved WAV recordings per call
    │
    ├── ml_engine/                        ← Local CNN+LSTM fallback model
    │   ├── model.py                      ← CNN+LSTM architecture
    │   ├── preprocessing.py              ← MFCC feature extraction
    │   ├── config.py                     ← Model hyperparameters
    │   ├── train.py                      ← Training script
    │   └── models/
    │       ├── best_model.keras          ← Trained weights
    │       ├── encoder.pkl               ← Label encoder
    │       └── scaler.pkl                ← Feature scaler
    │
    ├── EMDS/                             ← Python virtual environment
    ├── requirements.txt                  ← All Python dependencies
    └── .env                              ← DATABASE_URL for MySQL
```

---

## 4. Backend — How It Works

### Entry Point: `main.py`

The backend is a single FastAPI application in `backend/main.py`. It handles:
- REST API for calls, analytics, and auth
- WebSocket for real-time audio streaming
- Model loading on startup
- Database operations via `database.py`

### Startup Sequence

When `python main.py` is run:

```
1. FastAPI lifespan starts
2. init_database() → creates MySQL tables if they don't exist
3. load_model() → tries to load the best available ML model:
      a. audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim (BEST)
      b. superb/wav2vec2-base-superb-er (fallback)
      c. ehcalabres/wav2vec2-lg-xlsr... (fallback)
      d. local CNN+LSTM from ml_engine/models/ (fallback)
      e. demo random predictions (last resort)
4. Uvicorn starts serving on port 8000
```

### Per-Call Audio Processing Flow

```
Browser mic → PCM audio chunks (4096 samples / 0.256s per chunk)
     ↓
WebSocket /ws/stream/{call_id}
     ↓
process_audio_chunk() [runs in thread pool — does NOT block event loop]
     ↓
┌─────────────────────────────────────────────────────┐
│  1. Convert bytes → float32 numpy array              │
│  2. Calculate chunk RMS energy                       │
│  3. VAD check: energy < 0.012 → return "silence"     │
│  4. Append chunk to 2-second rolling accumulator     │
│  5. If buffer < 1 second → return "neutral" (warmup) │
│  6. Run ML model on 2-second context window          │
│  7. Apply confidence floor (0.40 for 4-class models) │
│  8. Majority vote over last 3 predictions            │
└─────────────────────────────────────────────────────┘
     ↓
Send emotion result back to browser via WebSocket
     ↓
Log emotion to MySQL database (emotion_logs table)
```

### Thread Pool Architecture

Model inference (PyTorch) is CPU-blocking and takes 1-2 seconds per call. Running it directly inside an `async` function would freeze the event loop, causing all WebSocket connections and HTTP requests to stop responding. The solution:

```python
# All blocking operations run in a thread pool executor
result = await loop.run_in_executor(None, process_audio_chunk, audio_bytes, call_id, time_offset)
```

This keeps the async event loop free to:
- Accept new WebSocket connections
- Handle HTTP requests (like `/api/calls/end`)
- Send responses back while inference runs in background threads

### Call End Flow

```
Browser clicks "End Call"
     ↓
1. stopCall() in frontend:
   - Stops MediaRecorder
   - Stops microphone track
   - Closes AudioContext
   - Sends {action: "stop"} to WebSocket
   - Closes WebSocket
   - Calls POST /api/calls/{id}/end [always runs, even if WS dropped]
     ↓
2. Backend WebSocket finally block:
   - Saves full audio to uploads/{call_id}.wav
   - Schedules analyze_full_recording() as background task
   - Cleans up accumulators and prediction history
     ↓
3. POST /api/calls/{id}/end handler:
   - Reads all emotion logs from DB for this call
   - Computes dominant emotion + distribution + avg confidence
   - Updates calls table with final stats
     ↓
4. analyze_full_recording() (background, thread pool):
   - Loads the saved WAV file
   - Runs model on 3-second overlapping windows
   - Updates calls table with comprehensive post-call stats
```

### Key Configuration Constants

```python
ACCUMULATOR_SAMPLES = 16000 * 2   # 2-second rolling audio window
HISTORY_SIZE = 3                   # Vote over last 3 predictions
VAD_THRESHOLD = 0.012              # Minimum RMS to count as speech
TEMPERATURE = 2.0                  # Softmax temperature (audeering)
```

---

## 5. Frontend — How It Works

### Entry Point Chain

```
index.html → main.tsx → App.tsx
```

**main.tsx** wraps the app in:
1. `BrowserRouter` — enables client-side routing
2. `AuthProvider` — provides login state to all components
3. `ErrorBoundary` — catches React crashes gracefully

### Routing (App.tsx)

```
Public routes (no login required):
  /login    → Login.tsx
  /signup   → Signup.tsx

Protected routes (redirect to /login if not authenticated):
  /dashboard   → Dashboard.tsx   (default landing)
  /history     → CallHistory.tsx
  /analytics   → Analytics.tsx
  /settings    → Settings.tsx
  /profile     → Profile.tsx
```

Protected routes are wrapped in a guard that reads `AuthContext`. If `isAuthenticated` is false, the user is redirected to `/login`.

### Dashboard Page — Core Live Feature

`Dashboard.tsx` is the most important page. It:

1. Calls `useWebSocket()` hook to get all connection state and actions
2. Renders `CallControls.tsx` — the Start/End call panel
3. Renders `CurrentEmotion.tsx` — live emotion badge with emoji
4. Renders `EmotionGraph.tsx` — confidence % over time (line chart)
5. Renders `EmotionTimeline.tsx` — color-coded emotion segments
6. Renders `EmotionDistribution.tsx` — doughnut chart of emotion percentages

### useWebSocket Hook — The Core Hook

`src/hooks/useWebSocket.ts` contains ALL the audio and connection logic:

```
startCall(agentName, customerName)
   → POST /api/calls/start
   → returns call_id

connect(call_id)
   → navigator.mediaDevices.getUserMedia({ audio: true })
   → new AudioContext({ sampleRate: 16000 })
   → new WebSocket(ws://localhost:8000/ws/stream/{call_id})
   → on open: send config message, start ScriptProcessor
   → ScriptProcessor.onaudioprocess:
         every 4096 samples (0.256s):
         - get float32 audio data
         - convert to Int16 PCM
         - ws.send(pcmData.buffer)  ← raw binary, no encoding
   → ws.onmessage:
         - parse JSON emotion prediction
         - smoothing: only update displayed emotion after 2 consecutive same predictions
         - add every prediction to emotionHistory (for charts)

stopCall()
   → always runs regardless of WebSocket state
   → stops MediaRecorder, mic track, AudioContext
   → sends {action: "stop"} if WS still open
   → closes WebSocket
   → POST /api/calls/{id}/end
   → resets all state (isConnected=false, isRecording=false)
```

### Frontend Smoothing Logic

To prevent the emotion display flickering between emotions every 0.25 seconds, two smoothing layers are applied:

**Layer 1 — Backend:** Majority vote over last 3 predictions. If predictions are [neutral, neutral, angry], the voted result is neutral.

**Layer 2 — Frontend:** The displayed emotion only changes when the same emotion appears 2 times in a row from the backend. A single-frame spike of "angry" won't show on screen.

```typescript
if (data.emotion === lastRawEmotionRef.current) {
  consecutiveCountRef.current += 1;
} else {
  lastRawEmotionRef.current = data.emotion;
  consecutiveCountRef.current = 1;
}
if (consecutiveCountRef.current >= 2) {
  setLastEmotion(data);  // only now update the display
}
```

### State Management

No Redux or Zustand — state is managed with:
- `React.useState` for component-local state
- `React.useRef` for WebSocket, AudioContext, stream refs (not state — don't trigger re-renders)
- `AuthContext` (React Context) for user/token across all pages
- `localStorage` for persisting auth token across page refreshes

---

## 6. ML Model — How It Works

### Model Priority Chain

The backend tries to load the best model available. If a model fails (e.g., not downloaded yet, dependency missing), it falls back to the next:

```
1. audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim  ← BEST (production)
2. superb/wav2vec2-base-superb-er                          ← Good (IEMOCAP)
3. ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition ← Fallback (RAVDESS)
4. Local CNN+LSTM from ml_engine/models/best_model.keras   ← Last resort
5. Random demo predictions                                  ← If nothing loads
```

### Primary Model: audeering (Production Standard)

**Model ID:** `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim`
**Downloads:** 1,170,000+ on HuggingFace
**Training data:**
- Pre-trained on Switchboard + Fisher (real telephone calls between real people)
- Fine-tuned on MSP-Podcast (100,000+ natural spontaneous speech utterances from podcasts)

**Why this is better than others:**
- Most models (RAVDESS, IEMOCAP) were trained on actors performing emotions in a studio
- Audeering was trained on real people speaking naturally in real situations
- It understands the difference between normal animated speech and genuine anger

**How it works — Dimensional Emotion:**

Instead of classifying audio into categories like "angry" or "happy" directly, the audeering model outputs three continuous numbers:

```
Audio → Wav2Vec2 encoder → mean pooling → regression head → [arousal, dominance, valence]

arousal   = how energetic / excited the speech is      (0 = very calm, 1 = very energetic)
dominance = how dominant / controlling the speech is   (0 = submissive, 1 = dominant)
valence   = how positive / negative the emotion is     (0 = very negative, 1 = very positive)
```

These three numbers are then mapped to a categorical emotion using the Russell Circumplex Model of Affect — a psychological model where all emotions can be placed on a 2D grid of arousal vs valence:

```
HIGH AROUSAL
      |
angry |  happy
(−val)|  (+val)
      |
──────┼──────── VALENCE
      |
  sad |  neutral
(−val)|  (+val)
      |
LOW AROUSAL
```

**Mapping formula (Gaussian similarity to prototype points):**

```python
_EMOTION_PROTOTYPES = {
    'angry':   (arousal=0.75, valence=0.20),
    'happy':   (arousal=0.75, valence=0.80),
    'sad':     (arousal=0.25, valence=0.25),
    'neutral': (arousal=0.45, valence=0.60),  # slightly positive — normal speech
}
# Distance from each prototype → softmax → probabilities
```

**Why this eliminates the angry bias:**

Normal conversational speech sits at arousal ~0.45, valence ~0.60 — right next to the "neutral" prototype. It has to be genuinely highly energetic AND strongly negative in tone before it gets close to the "angry" prototype at (0.75, 0.20).

Old categorical models (RAVDESS) had a built-in bias: actors performing "angry" in a studio sound similar to any normal energetic speech. The model couldn't tell the difference. The audeering model doesn't have an "angry" class — it just measures energy and sentiment.

### Architecture Deep Dive

```
Input: 2 seconds of 16kHz PCM audio (32,000 float32 samples)
   ↓
Wav2Vec2FeatureExtractor: normalize (zero mean, unit variance)
   ↓
Wav2Vec2Model (large-robust, 12 transformer layers):
   - CNN feature extractor: extracts local acoustic features
   - 12 self-attention transformer layers: models long-range temporal patterns
   - Hidden dimension: 1024
   - Output: sequence of hidden states (shape: [1, T, 1024])
   ↓
Mean pooling over time dimension → [1, 1024]
   ↓
_AudeeringRegressionHead:
   dropout → Linear(1024, 1024) → tanh → dropout → Linear(1024, 3)
   ↓
Output: [arousal, dominance, valence] — 3 float values in ~[0, 1]
   ↓
_dims_to_categorical() → emotion + confidence + probabilities dict
```

### Fallback Model: SUPERB (IEMOCAP-trained)

**Model ID:** `superb/wav2vec2-base-superb-er`
**Training:** IEMOCAP dataset (natural conversation between actors in dyadic sessions)
**Classes:** 4 — angry, happy, neutral, sad
**Architecture:** Wav2Vec2-base + classification head (standard AutoModelForAudioClassification)

This model uses class bias correction to compensate for its tendency to over-predict "angry":
```python
SUPERB_CLASS_BIAS = {
    'angry':   0.60,   # penalize — real speech is rarely IEMOCAP-level angry
    'neutral': 1.30,   # boost — real business speech is nearly always neutral
    'happy':   1.10,
    'sad':     1.00,
}
```

### Voice Activity Detection (VAD)

Before running the model, every audio chunk is checked:
```python
audio_energy = sqrt(mean(audio^2))   # RMS energy
if audio_energy < 0.012:
    return "silence"                  # Don't run expensive model on silence
```

Room background noise: ~0.001-0.008 RMS
Normal speech: ~0.015-0.060 RMS
Loud speech: ~0.060-0.150 RMS

Threshold 0.012 sits cleanly between noise and speech.

### Post-Call Full Analysis

When a call ends, the backend:
1. Saves all audio chunks to a single WAV file: `uploads/{call_id}.wav`
2. Runs a background job (`_analyze_full_recording_sync`) that:
   - Slices the audio into 3-second windows with 1-second hop
   - Runs the model on each window
   - Aggregates results → dominant emotion + distribution
   - Updates the `calls` table with comprehensive statistics

This runs in a thread pool so it doesn't delay the `/end` API response.

---

## 7. Database — Tables & Schema

**Database:** MySQL 8.0 (`emotion_detection` database)
**ORM:** SQLAlchemy 2.0
**Connection string:** `mysql+pymysql://root:password@127.0.0.1:3306/emotion_detection`

### Table: `calls`

Stores one record per call session.

| Column | Type | Description |
|---|---|---|
| id | Integer PK | Auto-increment primary key |
| call_id | String(255) UNIQUE | UUID generated at call start |
| agent_name | String(255) | Name entered in UI |
| customer_name | String(255) | Name entered in UI |
| start_time | DateTime | When call started (UTC) |
| end_time | DateTime (nullable) | When call ended (UTC) |
| duration_seconds | Integer | Calculated on end |
| status | String(50) | "active" / "completed" / "failed" |
| audio_file_path | String(500) | Path to saved WAV file |
| dominant_emotion | String(50) | Most frequent emotion in call |
| emotion_distribution | JSON | `{"neutral": 0.6, "happy": 0.3, "sad": 0.1}` |
| avg_confidence | Float | Average model confidence across call |

### Table: `emotion_logs`

Stores one record per audio chunk prediction (~4 records per second).

| Column | Type | Description |
|---|---|---|
| id | Integer PK | Auto-increment primary key |
| call_id | String(255) FK | References calls.call_id |
| timestamp | DateTime | Exact prediction time (UTC) |
| time_offset_seconds | Float | Seconds since call started |
| emotion | String(50) | Predicted emotion label |
| confidence | Float | Model confidence (0.0 - 1.0) |
| all_probabilities | JSON | `{"neutral": 0.58, "angry": 0.12, ...}` |
| is_speech | Boolean | True if VAD detected speech |
| audio_energy | Float | RMS energy of the chunk |

### Table: `users`

Stores user accounts for the dashboard login.

| Column | Type | Description |
|---|---|---|
| id | Integer PK | Auto-increment primary key |
| email | String(255) UNIQUE | Login identifier |
| name | String(255) | Display name |
| password_hash | String(255) | SHA-256 hash of password |
| role | String(50) | "agent" or "admin" |
| created_at | DateTime | Account creation time (UTC) |
| is_active | Boolean | Whether account is enabled |

### Relationships

```
users (1) ──────────────────── (no FK, users manage calls by name)
calls (1) ──────── (many) emotion_logs
```

---

## 8. API Reference

### Auth Endpoints

| Method | Path | Request Body | Response |
|---|---|---|---|
| POST | `/api/auth/register` | `{name, email, password}` | `{token, user}` |
| POST | `/api/auth/login` | `{email, password}` | `{token, user}` |
| PUT | `/api/auth/profile` | `{name}` + Bearer token | `{message, name}` |

### Call Endpoints

| Method | Path | Response |
|---|---|---|
| POST | `/api/calls/start` | `{call_id, start_time, status}` |
| POST | `/api/calls/{call_id}/end` | `{status, call_id, emotion_stats}` |
| GET | `/api/calls` | `{calls: [...], total}` |
| GET | `/api/calls/{call_id}` | `{call: {...}, emotions: [...]}` |
| GET | `/api/calls/{call_id}/emotions` | `{call_id, emotions: [...]}` |
| GET | `/api/calls/{call_id}/recording` | WAV file download |

### Analytics Endpoints

| Method | Path | Query Params | Response |
|---|---|---|---|
| GET | `/api/analytics/agents` | `agent_name`, `days=30` | `{analytics: [...]}` |
| GET | `/api/analytics/summary` | `days=30` | `{total_calls, top_emotion, ...}` |
| GET | `/api/analytics/emotions-trend` | `days=7` | `{trend: [...]}` |

### System Endpoints

| Method | Path | Response |
|---|---|---|
| GET | `/` | API info |
| GET | `/health` | `{status, model_loaded, active_model, model_type}` |

---

## 9. WebSocket Protocol

**Endpoint:** `ws://localhost:8000/ws/stream/{call_id}`

### Client → Server Messages

**Configuration (JSON text frame):**
```json
{ "action": "config", "sample_rate": 16000, "format": "pcm_16bit" }
```

**Audio data (binary frame):**
- Raw PCM Int16 audio bytes
- 4096 samples per chunk = 0.256 seconds at 16kHz
- Little-endian byte order
- Mono channel

**Stop (JSON text frame):**
```json
{ "action": "stop" }
```

### Server → Client Messages

**Config acknowledgement:**
```json
{ "type": "config_ack", "sample_rate": 16000, "chunk_size": 1024 }
```

**Emotion prediction:**
```json
{
  "type": "emotion",
  "timestamp": "2025-03-21T10:30:45.123Z",
  "time_offset": 3.5,
  "chunk_id": 14,
  "emotion": "neutral",
  "confidence": 0.621,
  "probabilities": {
    "neutral": 0.621,
    "happy": 0.198,
    "angry": 0.112,
    "sad": 0.069
  },
  "is_speech": true,
  "audio_energy": 0.031,
  "arousal": 0.43,
  "dominance": 0.51,
  "valence": 0.64
}
```

---

## 10. Authentication System

Authentication is implemented with a custom stateless token system (no JWT library required).

### Token Format

```
base64( "{user_id}:{email}:{timestamp}:{hmac_signature}" )
```

The HMAC signature is 16 hex characters from SHA-256 of `data:SECRET_KEY`.

### Token Lifetime

Tokens do not expire (no `exp` claim). They are invalidated only by changing the `SECRET_KEY` environment variable.

### Frontend Storage

```typescript
localStorage.setItem('auth_token', token);
localStorage.setItem('auth_user', JSON.stringify(user));
```

On page load, `AuthContext` reads from localStorage to restore session.

### Password Hashing

```python
hashlib.sha256(password.encode()).hexdigest()
```

Plain SHA-256 — no salt, no bcrypt. Suitable for development; upgrade to bcrypt for production.

---

## 11. Audio Processing Pipeline

```
Microphone (physical)
    ↓ getUserMedia({ sampleRate: 16000, channelCount: 1 })
MediaStream
    ↓
AudioContext (sample rate: 16000 Hz)
    ↓
MediaStreamSourceNode
    ↓
ScriptProcessorNode (buffer size: 4096 samples)
    ↓ onaudioprocess fires every 0.256 seconds
Float32Array (values: -1.0 to +1.0)
    ↓ × 32767 + clamp
Int16Array (PCM 16-bit)
    ↓ .buffer
ArrayBuffer → WebSocket.send() as binary
    ↓ (network)
Backend receives bytes
    ↓ np.frombuffer(dtype=np.int16) / 32768.0
float32 numpy array (−1.0 to +1.0)
    ↓ rolling accumulate → 2-second window
numpy array [32000 samples]
    ↓ Wav2Vec2FeatureExtractor (normalize)
PyTorch tensor [1, 32000]
    ↓ Wav2Vec2Model (12 transformer layers)
hidden states [1, T, 1024]
    ↓ mean pooling
[1, 1024]
    ↓ RegressionHead
[arousal, dominance, valence]
    ↓ _dims_to_categorical()
emotion + confidence + probabilities
```

---

## 12. Data Flow — End to End

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           BROWSER (React App)                            │
│                                                                           │
│  User clicks "Start Call"                                                 │
│       ↓                                                                   │
│  POST /api/calls/start → receives call_id (UUID)                          │
│       ↓                                                                   │
│  new WebSocket(ws://localhost:8000/ws/stream/{call_id})                   │
│       ↓                                                                   │
│  AudioContext + ScriptProcessor → raw PCM → ws.send() every 256ms        │
│       ↓                                                                   │
│  ws.onmessage → parse emotion JSON → update React state                   │
│       ↓                                                                   │
│  CurrentEmotion, EmotionGraph, EmotionTimeline re-render live             │
│                                                                           │
│  User clicks "End Call"                                                   │
│       ↓                                                                   │
│  stopCall() → mic off → WS closed → POST /api/calls/{id}/end             │
│       ↓                                                                   │
│  UI resets to "Start New Call" state                                      │
└──────────────────────────────────────────────────────────────────────────┘
                          │  WebSocket binary frames  │  HTTP requests
                          ▼                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND (main.py)                           │
│                                                                           │
│  WebSocket handler receives binary chunk                                   │
│       ↓ (thread pool — does not block event loop)                         │
│  process_audio_chunk():                                                   │
│       → VAD check → accumulate 2s buffer → model inference               │
│       → majority vote → return emotion dict                               │
│       ↓                                                                   │
│  Send emotion JSON back to browser via WebSocket                          │
│       ↓                                                                   │
│  db_manager.log_emotion() → INSERT into emotion_logs                     │
│                                                                           │
│  On call end:                                                             │
│       → Save WAV file to uploads/                                         │
│       → Schedule analyze_full_recording() in thread pool                  │
│       → db_manager.end_call() → UPDATE calls table                       │
└──────────────────────────────────────────────────────────────────────────┘
                          │  SQLAlchemy ORM
                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        MySQL DATABASE                                     │
│                                                                           │
│  calls table:        1 row per call (summary stats)                       │
│  emotion_logs table: ~4 rows per second of speech                        │
│  users table:        1 row per registered agent                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

*Documentation generated for EmoDetect v1.0 — March 2025*
