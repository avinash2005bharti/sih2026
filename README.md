# Sovereign On-Premise Agentic AI Workbench

**SIH 2026 Project: Fully Air-Gapped, Sovereign Agentic AI Operating Platform**

A complete on-premise workbench for autonomous multi-agent orchestration, local LLM execution, knowledge graph synthesis, and real-time streaming inference without external cloud dependencies.

---

## 🏛️ System Architecture

```text
                 ┌────────────────────────────────┐
                 │       React / Vite UI          │
                 │      http://localhost:5173     │
                 └───────────────┬────────────────┘
                                 │
                            Socket.IO
                                 │
                 ┌───────────────▼────────────────┐
                 │    Node.js / Express Backend   │
                 │      http://localhost:5000     │
                 └───────────────┬────────────────┘
                                 │
                             HTTP / SSE
                                 │
                 ┌───────────────▼────────────────┐
                 │   Python FastAPI AI Service    │
                 │      http://localhost:8000     │
                 └───────────────┬────────────────┘
                                 │
                      http://localhost:11434
                                 │
                 ┌───────────────▼────────────────┐
                 │    Local Ollama on Windows     │
                 │         (Host Runtime)         │
                 └───────────────┬────────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
     NVIDIA GPU Acceleration               CPU Mode Fallback
      (Auto-detected via CUDA)          (Intel / AMD / Integrated)
```

### Infrastructure Layer (Docker Compose)
Docker Compose is used **exclusively** for underlying storage, caching, and vector indexing engines:
- **MongoDB** (Port `27017`): User directory, conversation history, and agent states
- **Valkey** (Port `6379`): Redis-compatible caching and session state
- **Qdrant** (Port `6333`): Vector database for semantic document embeddings
- **Neo4j** (Ports `7474`, `7687`): Knowledge graph for task relationships and episodic graph memory

> [!IMPORTANT]
> **Ollama runs directly on the Windows host machine**, not inside a Docker container. This guarantees native hardware access to NVIDIA GPUs via host CUDA drivers while seamlessly falling back to CPU execution on laptops and standard PCs without dedicated graphics.

---

## 🚀 Local Ollama Setup

Follow these steps to set up Ollama locally on Windows:

### 1. Install Ollama
Download and run the official Windows installer from [ollama.com/download](https://ollama.com/download).

### 2. Verify Installation
Open a PowerShell terminal and verify Ollama is installed:
```powershell
ollama --version
```
Expected output:
```text
ollama version is 0.x.x
```

### 3. Start Local Ollama Server
In your first terminal, start the Ollama daemon:
```powershell
ollama serve
```
Ollama will start listening on `http://localhost:11434`.

### 4. Check Installed Models
In another terminal, inspect existing models:
```powershell
ollama list
```

### 5. Pull Required Models
Pull the recommended sovereign models into your local Ollama instance:
```powershell
# General Chat Model
ollama pull qwen3:4b

# Coding & Tool-Calling Model
ollama pull qwen2.5-coder:3b

# Vision & Multimodal Model
ollama pull qwen2.5vl:3b

# Vector Embeddings Model
ollama pull nomic-embed-text:latest
```
*(For low-spec or 8 GB RAM laptops, lighter models like `qwen2.5-coder:1.5b` or `qwen3:1.7b` can be used).*

---

## ⚡ Hardware Compatibility & Fallback

The workbench features safe, non-crashing hardware auto-detection:

| Hardware Configuration | Behavior |
|---|---|
| **Machine with NVIDIA GPU + CUDA** | Automatically detected via `nvidia-smi`. Ollama leverages GPU VRAM and tensor cores for maximum inference speed. |
| **Machine without NVIDIA GPU** (Intel/AMD/CPU) | `nvidia-smi` is safely handled without errors. The system logs CPU mode and Ollama executes inference directly on the host CPU. |

> [!NOTE]
> Missing NVIDIA drivers or GPUs will **never crash** the backend, AI service, or frontend. Hardware acceleration is treated purely as an optimization, not a hard requirement.

---

## 🛠️ Step-by-Step Development Startup

To run the complete platform locally, open four terminal windows:

### Terminal 1: Local Ollama
```powershell
ollama serve
```

### Terminal 2: Node.js Backend
```powershell
cd BACKEND
npm run dev
```
*Runs at `http://localhost:5000`.*

### Terminal 3: FastAPI AI Service
```powershell
cd AI-SERVICES
python -m uvicorn main:app --reload --port 8000
```
*Runs at `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).*

### Terminal 4: React Frontend
```powershell
cd FRONTEND
npm run dev
```
*Runs at `http://localhost:5173`.*

### Docker Infrastructure (Storage & Vector Databases)
Start the supporting databases in Docker:
```powershell
cd docker-compose
docker compose up -d
```

---

## 🩺 System Health & Telemetry

You can verify the connectivity and hardware status at any time by requesting the health endpoint:

```powershell
curl http://localhost:5000/api/health
```

### Example Response (CPU Mode Fallback):
```json
{
  "success": true,
  "message": "Sovereign AI Workbench API is running",
  "ollama": {
    "available": true,
    "url": "http://localhost:11434",
    "modelsAvailable": true,
    "count": 4
  },
  "hardware": {
    "nvidiaAvailable": false,
    "mode": "cpu"
  },
  "services": {
    "node": "running",
    "aiService": "healthy"
  }
}
```

### Example Response (NVIDIA GPU Mode):
```json
{
  "success": true,
  "message": "Sovereign AI Workbench API is running",
  "ollama": {
    "available": true,
    "url": "http://localhost:11434",
    "modelsAvailable": true,
    "count": 4
  },
  "hardware": {
    "nvidiaAvailable": true,
    "mode": "gpu"
  },
  "services": {
    "node": "running",
    "aiService": "healthy"
  }
}
```

---

## 👁️ Vision & Multimodal Execution

To analyze diagrams, equipment photos, gauges, or schematics:
1. Attach an image in the chat interface or use the vision API (`/api/vision/analyze`).
2. The image is base64-encoded and forwarded from React -> Socket.IO -> Node.js -> FastAPI -> Local Ollama.
3. If an explicit non-vision model is chosen, the platform returns a descriptive error:
   ```text
   Selected model does not support vision.
   Please select a vision-capable Ollama model.
   ```
   without crashing the session or dropping the Socket.IO connection.

---

## 🧩 Environment Variables Reference

### Backend (`BACKEND/.env`)
```env
PORT=5000
FRONTEND_URL=http://localhost:5173
JWT_SECRET=your_secret_key
MONGO_URI=mongodb://admin:admin@localhost:27017/sovereign_ai?authSource=admin
AI_SERVICE_URL=http://localhost:8000
PYTHON_AI_SERVICE_URL=http://localhost:8000
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_HOST=http://localhost:11434
```

### AI Service (`AI-SERVICES/.env`)
```env
APP_NAME=Sovereign AI Service
HOST=0.0.0.0
PORT=8000
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_HOST=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen3:4b
OLLAMA_CODE_MODEL=qwen2.5-coder:3b
OLLAMA_VISION_MODEL=qwen2.5vl:3b
OLLAMA_EMBED_MODEL=nomic-embed-text:latest
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=sovereign_documents
QDRANT_VECTOR_SIZE=768
LOG_LEVEL=INFO
```