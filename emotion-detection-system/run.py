#!/usr/bin/env python3
"""
Emotion Detection System - Launcher Script
Runs the complete application (backend + frontend) locally
"""

import os
import sys
import subprocess
import argparse
import time
import signal
from pathlib import Path

# Configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
BACKEND_DIR = Path(__file__).parent / "backend"
FRONTEND_DIR = Path(__file__).parent.parent / "app"

# Global process trackers
processes = []


def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🎭 EMOTION DETECTION SYSTEM FOR CALL CENTERS       ║
║                                                              ║
║              Real-time Speech Emotion Recognition            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 Checking dependencies...")
    
    try:
        import tensorflow
        import fastapi
        import librosa
        import uvicorn
        print("✅ All required packages found!")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False


def setup_ml_model():
    """Setup/Train the ML model if needed"""
    model_path = Path(__file__).parent / "ml_engine" / "models" / "best_model.keras"
    
    if model_path.exists():
        print("✅ ML model found!")
        return True
    
    print("🤖 ML model not found. Training new model...")
    print("   (This may take a few minutes)")
    
    ml_engine_dir = Path(__file__).parent / "ml_engine"
    
    try:
        # Run training script
        result = subprocess.run(
            [sys.executable, "train.py"],
            cwd=ml_engine_dir,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Model training complete!")
            return True
        else:
            print("❌ Model training failed!")
            return False
    except Exception as e:
        print(f"❌ Error training model: {e}")
        return False


def start_backend():
    """Start the FastAPI backend server"""
    print(f"\n🚀 Starting backend server on port {BACKEND_PORT}...")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent)
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT), "--reload"],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    processes.append(process)
    return process


def start_frontend():
    """Start the React frontend dev server"""
    print(f"🎨 Starting frontend dev server on port {FRONTEND_PORT}...")
    
    # Check if node_modules exists
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(
            ["npm", "install"],
            cwd=FRONTEND_DIR,
            check=True
        )
    
    process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(FRONTEND_PORT)],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    processes.append(process)
    return process


def print_urls():
    """Print access URLs"""
    time.sleep(2)
    print("\n" + "="*60)
    print("🌐 APPLICATION READY!")
    print("="*60)
    print(f"\n📊 Dashboard:    http://localhost:{FRONTEND_PORT}")
    print(f"🔌 API Docs:     http://localhost:{BACKEND_PORT}/docs")
    print(f"🔍 Health Check: http://localhost:{BACKEND_PORT}/health")
    print("\n" + "="*60)
    print("Press Ctrl+C to stop all services")
    print("="*60 + "\n")


def stream_output(process, name):
    """Stream output from a process"""
    try:
        for line in process.stdout:
            print(f"[{name}] {line}", end='')
    except Exception:
        pass


def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    print("\n\n🛑 Shutting down...")
    
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass
    
    print("✅ All services stopped")
    sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Emotion Detection System Launcher")
    parser.add_argument("--backend-only", action="store_true", help="Start only the backend")
    parser.add_argument("--frontend-only", action="store_true", help="Start only the frontend")
    parser.add_argument("--skip-training", action="store_true", help="Skip model training")
    args = parser.parse_args()
    
    print_banner()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check dependencies
    if not args.frontend_only:
        if not check_dependencies():
            sys.exit(1)
    
    # Setup ML model
    if not args.frontend_only and not args.skip_training:
        if not setup_ml_model():
            print("⚠️  Continuing without trained model (demo mode)")
    
    try:
        # Start services
        if not args.frontend_only:
            backend_proc = start_backend()
            
            # Start backend output streaming in background
            import threading
            backend_thread = threading.Thread(target=stream_output, args=(backend_proc, "BACKEND"))
            backend_thread.daemon = True
            backend_thread.start()
        
        if not args.backend_only:
            # Check Node.js
            try:
                subprocess.run(["node", "--version"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ Node.js not found! Please install Node.js 18+ to run the frontend.")
                if args.frontend_only:
                    sys.exit(1)
                print("⚠️  Continuing without frontend...")
            else:
                frontend_proc = start_frontend()
                
                # Start frontend output streaming
                frontend_thread = threading.Thread(target=stream_output, args=(frontend_proc, "FRONTEND"))
                frontend_thread.daemon = True
                frontend_thread.start()
        
        # Print URLs
        print_urls()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            for process in processes:
                if process.poll() is not None:
                    print(f"\n⚠️  A service has exited with code {process.returncode}")
                    signal_handler(None, None)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        signal_handler(None, None)


if __name__ == "__main__":
    main()
