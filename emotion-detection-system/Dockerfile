FROM python:3.11-slim

WORKDIR /app

# System dependencies for audio processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch — avoids the huge CUDA variant (~2 GB smaller image)
RUN pip install --no-cache-dir --timeout 600 --retries 5 \
    torch \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements.docker.txt .
RUN pip install --no-cache-dir --timeout 600 --retries 5 -r requirements.docker.txt

# HuggingFace cache path — must be set before any model download or load
ENV HF_HOME=/app/.cache/huggingface

# ─────────────────────────────────────────────────────────────────────────────
# MODEL BAKING (choose one approach):
#
# APPROACH A — Download at runtime (default, smaller image ~2 GB)
#   Models download into a Docker volume on first run (~2 min with good internet)
#   and are reused on every subsequent restart. Good for development / single machine.
#   docker-compose.yml mounts the hf_model_cache volume to persist them.
#
# APPROACH B — Pre-bake into image (larger image ~4 GB, fully self-contained)
#   Models are downloaded ONCE during `docker build` and baked into the image.
#   Recipients need no internet at runtime. Good for sharing / offline deployment.
#   To enable: uncomment the RUN line below and remove the hf_model_cache volume
#   mount from docker-compose.yml (the volume would override the baked-in models).
# ─────────────────────────────────────────────────────────────────────────────

# APPROACH B: uncomment to bake models into the image during build
# RUN python backend/preload_models.py

COPY . .

WORKDIR /app/backend

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
