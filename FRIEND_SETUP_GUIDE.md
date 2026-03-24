# EmoDetect — Setup Guide

Real-time speech emotion detection for call centers. This guide gets you running in minutes using Docker — no Python, no database setup, no manual installs.

---

## What you need

| Tool | Why | Download |
|---|---|---|
| **Docker Desktop** | Runs the entire app in containers | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| **A modern browser** | Chrome or Edge recommended (mic access works best) | — |

That's it. No Python, no Node.js, no MySQL, no manual installs.

---

## Step 1 — Get the project

**Option A — Via Git (recommended):**
```bash
git clone <repo-url>
cd emotion-detection
```

**Option B — Via ZIP:**
Download and extract the ZIP, then open a terminal inside the `emotion-detection` folder.

---

## Step 2 — Start the app

```bash
docker compose up --build
```

> **First run takes 10–20 minutes** — Docker downloads ~2 GB of AI speech models from HuggingFace. This only happens once. Every restart after that is fast (under 30 seconds).

You'll know it's ready when you see this in the terminal:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 3 — Open the app

| What | URL |
|---|---|
| **Dashboard** | http://localhost:5173 |
| **API Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |

---

## Step 4 — Create your account

The app has a built-in login system. On first visit:

1. Click **"Create one for free"** on the login page
2. Enter your name, email, and a password
3. You're in — no email verification needed

---

## Step 5 — Run a call

1. Go to **Live Dashboard**
2. Enter agent name (auto-filled from your account) and customer name
3. Click **Start Call** → allow microphone access when the browser asks
4. Speak — emotions appear in real time
5. Click **End Call** when done
6. Find the recording + emotion timeline in **Call History**

---

## Stopping the app

```bash
# Stop (keeps all data)
docker compose down

# Start again (fast, models already downloaded)
docker compose up

# Stop AND delete all data (calls, recordings, database)
docker compose down -v
```

---

## Where is the data stored?

Everything is stored in Docker named volumes — no files scattered on your computer.

| Volume | What's inside |
|---|---|
| `emotion-detection_backend_db` | SQLite database (all calls, users, emotion logs) |
| `emotion-detection_backend_uploads` | Call recordings (WAV files) |
| `emotion-detection_hf_model_cache` | AI model weights (downloaded once, reused forever) |

To view the database with a GUI tool like **TablePlus** or **DB Browser for SQLite**:
1. Open a terminal and copy the database out of the Docker volume:
   ```bash
   docker cp $(docker compose ps -q backend):/data/emotion_detection.db ./emotion_detection.db
   ```
2. Open `emotion_detection.db` with **DB Browser for SQLite** (free at [sqlitebrowser.org](https://sqlitebrowser.org))

### Want to use MySQL instead?

1. In `docker-compose.yml`, change the `DATABASE_URL` under the backend service:
   ```yaml
   - DATABASE_URL=mysql+pymysql://username:password@host:3306/dbname
   ```
2. Remove the `backend_db` volume mount (line `- backend_db:/data`) since MySQL is external.
3. Rebuild: `docker compose up --build`

> The app works with any SQLAlchemy-compatible database (SQLite, MySQL, PostgreSQL). SQLite is the default and requires zero setup.

---

## Troubleshooting

**"docker compose" command not found**
→ Use `docker-compose` (with a hyphen) for older Docker versions.

**Port 5173 or 8000 already in use**
→ Another app is using that port. Stop it, or change the port in `docker-compose.yml`.

**Microphone not working / emotion stuck**
→ Make sure you clicked "Allow" when the browser asked for microphone access.
→ Check: browser address bar → click the lock icon → Microphone → Allow.

**First run seems stuck**
→ It's downloading AI models (~2 GB). Check terminal for download progress. Let it run.

**Emotions always show "neutral"**
→ Speak louder or move closer to the mic. The system needs clear speech to detect emotion.
→ Background noise can interfere — use headphones or a quiet environment.

**Want to reset everything (fresh start)?**
```bash
docker compose down -v   # deletes all volumes/data
docker compose up --build
```

---

## What AI model does it use?

The app tries models in this order (best to worst):

1. **audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim** ← used in most cases
   - Trained on real telephone speech (Switchboard + Fisher datasets)
   - Detects: angry, happy, sad, neutral
2. **superb/wav2vec2-base-superb-er** — fallback #1
3. **ehcalabres/wav2vec2-lg-xlsr** — fallback #2
4. **Demo mode** (random) — if no internet and no cached models

All models are downloaded automatically from HuggingFace. You don't need to do anything.

---

*Built with FastAPI · React · Wav2Vec2 · SQLite · Docker*
