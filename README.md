# Emotion Detection System

A real-time speech emotion detection system with a FastAPI backend and a React (Vite) frontend.

## 🚀 Quick Start (Docker)

The easiest way to run the project is using Docker Compose. This will set up the Backend, Frontend, and a MySQL database automatically.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- [Git](https://git-scm.com/) (optional, for cloning).

### Setup Instructions

1. **Clone or Download the Project:**
   ```bash
   git clone <your-repo-url>
   cd emotion-detection
   ```

2. **Configure Environment Variables:**
   The project uses `.env` files for configuration. Example templates are provided.
   - **Backend:** `emotion-detection-system/backend/.env.example`
   - **Frontend:** `app/.env.example`

   For a quick Docker setup, you can simply run:
   ```bash
   # (On Windows PowerShell)
   cp app/.env.example app/.env
   cp emotion-detection-system/backend/.env.example emotion-detection-system/backend/.env
   ```

3. **Run with Docker Compose:**
   ```bash
   docker compose up --build
   ```

4. **Access the Application:**
   - **Frontend:** [http://localhost:5173](http://localhost:5173)
   - **Backend API:** [http://localhost:8000](http://localhost:8000)
   - **API Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

## 📁 Project Structure

- `app/`: Frontend React application (Vite).
- `emotion-detection-system/`: 
  - `backend/`: FastAPI server logic.
  - `ml_engine/`: Machine learning models and processing.
- `docker-compose.yml`: Orchid orchestration for the entire stack.

## 🛠 Troubleshooting

- **Database Connection:** If the backend fails to connect to the database, ensure the `db` container is healthy (`docker compose ps`).
- **NPM Install Errors:** If you run into issues with the frontend build, you might need to delete `app/node_modules` and try again.
- **Port Conflicts:** Ensure ports `3306`, `8000`, and `5173` are not being used by other applications.

---
*Developed for Real-Time Emotion Analysis.*
