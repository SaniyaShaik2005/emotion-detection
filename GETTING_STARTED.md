# Getting Started — EmoDetect Setup Guide

> This guide is for someone setting up the project from scratch on a new machine.
> Follow every step in order. Do not skip steps.

---

## What You Need Before Starting

Make sure the following are installed on your machine:

| Requirement | Version | Download |
|---|---|---|
| Python | 3.10 or higher | https://www.python.org/downloads/ |
| Node.js | 18 or higher | https://nodejs.org/ |
| MySQL Server | 8.0 | https://dev.mysql.com/downloads/mysql/ |
| Git | Any | https://git-scm.com/ |

To check if they are already installed, open a terminal and run:
```bash
python --version
node --version
mysql --version
git --version
```

---

## Step 1 — Get the Project Files

If you have the project as a ZIP file, extract it to `C:\emotion-detection\`.

If you are cloning from Git:
```bash
git clone <repository-url> C:\emotion-detection
```

Your folder structure should look like this after extracting:
```
C:\emotion-detection\
├── app\                        ← Frontend
└── emotion-detection-system\   ← Backend + ML
```

---

## Step 2 — Set Up the MySQL Database

### 2a. Start MySQL Server

Open MySQL command line or any MySQL client (TablePlus, MySQL Workbench, etc.) and connect as root.

### 2b. Create the database

Run this SQL command:
```sql
CREATE DATABASE emotion_detection;
```

That's it. The tables (calls, emotion_logs, users) are created **automatically** when you first start the backend. You do not need to run any SQL scripts.

### 2c. Note your MySQL credentials

You will need:
- Host: `127.0.0.1`
- Port: `3306`
- Username: your MySQL username (usually `root`)
- Password: your MySQL root password

---

## Step 3 — Set Up the Backend (Python)

Open a terminal and navigate to the backend folder:

```bash
cd C:\emotion-detection\emotion-detection-system
```

### 3a. Create the Python virtual environment

```bash
python -m venv EMDS
```

This creates a folder called `EMDS` inside `emotion-detection-system\`. It is an isolated Python environment so packages installed here do not affect the rest of your computer.

### 3b. Activate the virtual environment

**On Windows (PowerShell):**
```powershell
.\EMDS\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
EMDS\Scripts\activate.bat
```

**On Mac/Linux:**
```bash
source EMDS/bin/activate
```

You will see `(EMDS)` appear at the start of your terminal prompt when it is active:
```
(EMDS) PS C:\emotion-detection\emotion-detection-system>
```

> **Important:** Every time you open a new terminal to run the backend, you must activate the venv again with the command above.

### 3c. Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, SQLAlchemy, TensorFlow, and many other packages. It may take 5-10 minutes.

### 3d. Install PyTorch and Transformers (for the AI model)

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers safetensors
```

> **Note:** This installs the CPU-only version of PyTorch (~500MB). It is sufficient to run the model. If you have an NVIDIA GPU and want faster inference, visit https://pytorch.org/get-started/locally/ for GPU installation instructions.

### 3e. Configure the database connection

Navigate into the backend folder:
```bash
cd backend
```

Create a file called `.env` in that folder:
```
C:\emotion-detection\emotion-detection-system\backend\.env
```

Add this line inside the file (replace with your actual MySQL credentials):
```
DATABASE_URL=mysql+pymysql://root:YourPasswordHere@127.0.0.1:3306/emotion_detection
```

> **If your password contains special characters** like `@`, `#`, `$`, you must encode them:
> - `@` → `%40`
> - `#` → `%23`
> - `$` → `%24`
>
> Example: password `Hello@2024` becomes `Hello%402024` in the URL.

---

## Step 4 — Start the Backend

Make sure you are in the backend folder with the venv active:

```bash
cd C:\emotion-detection\emotion-detection-system\backend
```

```bash
python main.py
```

### What you should see:

```
Starting up Emotion Detection API...
Database initialized successfully
Loading audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim (MSP-Podcast natural speech, dimensional) ...
```

**First time only:** The AI model (~1.3GB) will download from HuggingFace automatically. This takes 2-10 minutes depending on your internet speed. You will see a progress bar:

```
model.safetensors: 100%|████████████| 661M/661M [01:33<00:00, 7.05MB/s]
✓ Audeering model loaded — outputs arousal/dominance/valence ...
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Every time after:** The model loads from local cache instantly (no download needed).

### Verify the backend is running:

Open your browser and go to:
```
http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "active_model": "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim",
  "model_type": "dimensional (arousal/dominance/valence → categorical)"
}
```

> Leave this terminal open. The backend must be running while you use the app.

---

## Step 5 — Set Up the Frontend (React)

Open a **new terminal** (keep the backend terminal running).

Navigate to the frontend folder:
```bash
cd C:\emotion-detection\app
```

### 5a. Install Node dependencies

```bash
npm install
```

This installs React, TypeScript, Tailwind CSS, and all other frontend packages. It may take 2-3 minutes and creates a `node_modules` folder.

---

## Step 6 — Start the Frontend

```bash
npm run dev
```

You should see:
```
  VITE v7.2.4  ready in 432 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

> Leave this terminal open as well. The frontend dev server must keep running.

---

## Step 7 — Open the App

Open your browser and go to:
```
http://localhost:5173
```

You will see the **Login** page.

### Create your first account:

1. Click **"Sign up"** or go to `http://localhost:5173/signup`
2. Enter your name, email, and a password
3. Click **Register**
4. You will be logged in automatically and taken to the Dashboard

---

## Step 8 — Start Your First Call

On the Dashboard page:

1. Enter an **Agent Name** (your name)
2. Enter a **Customer Name** (any name for testing)
3. Click **Start Call**
4. Your browser will ask for **microphone permission** — click **Allow**
5. Start speaking

The emotion display will update in real time as you speak. You should see the current emotion, confidence percentage, and live charts update.

To stop, click **End Call**.

---

## Daily Usage — Quick Start

Once everything is set up, this is all you need to do each day:

**Terminal 1 — Backend:**
```bash
cd C:\emotion-detection\emotion-detection-system
.\EMDS\Scripts\Activate.ps1
cd backend
python main.py
```

**Terminal 2 — Frontend:**
```bash
cd C:\emotion-detection\app
npm run dev
```

Then open `http://localhost:5173` in your browser.

---

## Troubleshooting

### "No module named 'torch'" or "No module named 'transformers'"

You need to install PyTorch and Transformers. Make sure your venv is active then run:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers safetensors
```

### "Can't connect to MySQL server"

- Make sure MySQL Server is running on your machine
- Check your `.env` file has the correct username and password
- If your password has `@` in it, encode it as `%40`
- Try connecting with TablePlus or MySQL Workbench to verify credentials

### "Access denied for user 'root'"

Your MySQL root password in the `.env` file is wrong. Check it and update `.env`.

### "Permission denied" when activating venv on Windows

Run this command first (only needed once):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try activating the venv again.

### Backend shows "demo mode" instead of model name

The AI model failed to load. Check the backend console for the specific error. Usually it means torch/transformers is not installed — see the first troubleshooting item above.

### Browser says "Permission denied" for microphone

- Make sure you are accessing the app via `http://localhost:5173` (not a different address)
- Go to browser Settings → Privacy → Microphone and allow localhost
- On Chrome: click the lock icon in the address bar → allow microphone

### Port 8000 already in use

Another process is using port 8000. Either:
- Find and stop it: `netstat -ano | findstr :8000` then `taskkill /PID <number> /F`
- Or change the backend port in `main.py` (last line: `port=8000` → `port=8001`) and update the frontend's `API_BASE_URL` in `useWebSocket.ts`

### Port 5173 already in use

Another Vite dev server is running. Stop it with Ctrl+C in its terminal, then run `npm run dev` again.

---

## Project Ports Reference

| Service | URL | Purpose |
|---|---|---|
| Frontend | http://localhost:5173 | React app in browser |
| Backend API | http://localhost:8000 | REST API |
| Backend Health | http://localhost:8000/health | Check model status |
| API Docs | http://localhost:8000/docs | Auto-generated Swagger UI |
| MySQL | localhost:3306 | Database |

---

## Folder Reference

| Folder | What it contains |
|---|---|
| `C:\emotion-detection\app\` | React frontend source code |
| `C:\emotion-detection\app\node_modules\` | Installed npm packages (do not edit) |
| `C:\emotion-detection\emotion-detection-system\backend\` | FastAPI server |
| `C:\emotion-detection\emotion-detection-system\backend\uploads\` | Saved call recordings (.wav) |
| `C:\emotion-detection\emotion-detection-system\backend\.env` | Database password (keep private) |
| `C:\emotion-detection\emotion-detection-system\EMDS\` | Python virtual environment |
| `C:\Users\bunny\.cache\huggingface\` | Downloaded AI model cache |

---

*Setup guide for EmoDetect v1.0 — March 2025*
