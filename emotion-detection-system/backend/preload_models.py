"""
Pre-download HuggingFace models into the Docker image during `docker build`.

Run automatically by the Dockerfile. Downloads models into $HF_HOME so they
are baked into the image layer — no internet needed at container runtime.

Models downloaded:
  1. audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim  (~1.5 GB)  — primary
  2. superb/wav2vec2-base-superb-er                          (~360 MB)  — fallback
"""

from huggingface_hub import snapshot_download
import os

MODELS = [
    ("audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim", "~1.5 GB — primary model"),
    ("superb/wav2vec2-base-superb-er",                        "~360 MB — fallback model"),
]

for repo_id, note in MODELS:
    print(f"\nDownloading {repo_id}  ({note})...")
    try:
        snapshot_download(repo_id=repo_id)
        print(f"  ✓ {repo_id} cached")
    except Exception as e:
        print(f"  ✗ Failed to download {repo_id}: {e}")
        raise SystemExit(1)

print("\nAll models pre-downloaded. They are now baked into the Docker image.")
