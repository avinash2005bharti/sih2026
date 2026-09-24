# Sovereign On-Premise Agentic AI Workbench

**SIH 2026 Project: Fully Air-Gapped, Sovereign Agentic AI Operating Platform**  
Repository: [https://github.com/avinash2005bharti/sih2026.git](https://github.com/avinash2005bharti/sih2026.git)

A complete on-premise workbench for autonomous multi-agent orchestration, local LLM execution, knowledge graph synthesis, industrial OCR, and real-time streaming inference without external cloud dependencies.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client_Layer [1. Client Presentation Tier (Port 5173)]
        UI[React 18 + Vite UI]
        Views[Chat Workbench · Documents · Knowledge Graph · Agents · Monitoring · Reports]
    end

    subgraph Gateway_Layer [2. Application & Gateway Tier (Port 5000)]
        NodeBackend[Node.js / Express Gateway]
        SocketHub[Socket.IO Server: Real-Time Token & Agent Step Streaming]
        Security[JWT RBAC Controller & Egress Telemetry Proxy]
    end

    subgraph AI_Services_Layer [3. AI Services & Multi-Agent Orchestration Tier (Port 8000)]
        FastAPIService[Python FastAPI Service]
        
        subgraph Orchestration [LangGraph StateGraph DAG Engine]
            Classifier[Deterministic 16-Task Classifier]
            RouterNode[Router Node]
            PlannerNode[Planner Node]
            SelectorNode[Agent Selector Node]
            ExecutorNode[Sandboxed Executor Node]
            VerifierNode[Verifier Node]
            FinalizerNode[Finalizer Node]
        end

        subgraph Agents [16 Specialized Domain Agents]
            DomainAgents[General · Coding · Document · Spreadsheet · PPT · OCR · Vision<br/>Knowledge · Memory · Filesystem · Maintenance · Safety · Compliance · Risk · Reporting · Router]
        end

        subgraph MCP_Tools [Sandboxed Tools & Model Context Protocol Layer]
            Tools[18 Sandboxed Workspace Tools + 9 MCP Server Modules<br/>Filesystem · Document · Python Sandbox · Spreadsheet · PPT · OCR · Vision · RAG · Memory]
        end

        subgraph Memory [Tripartite Cognitive Memory Subsystem]
            STM[Short-Term Memory: Redis/Valkey Sliding Window]
            LTM[Long-Term Memory: Qdrant Vector DB + Mem0]
            Graph[Knowledge Graph: Neo4j Cypher Property Graph]
        end

        subgraph Vision_OCR [OCR & Multimodal Vision Engine]
            PaddleOCR[PaddleOCR Engine + CV Preprocessor (Deskew, Binarize, Denoise)]
            LocalVision[Local Vision Models (Moondream / Qwen2.5-VL)]
        end

        subgraph AirGap [Sovereign Security Guard]
            NetGuard[Socket-Level Egress Interceptor & Rolling SHA-256 Audit Chain]
        end
    end

    subgraph Host_Inference [4. Host Local LLM Runtime (Port 11434)]
        HostOllama[Ollama Daemon on Windows Host]
        Hardware{Hardware Probe}
        NvidiaGPU[(NVIDIA CUDA GPU)]
        HostCPU[(Host Multi-Core CPU)]
    end

    subgraph Infrastructure [5. Storage & Vector Databases (Docker Compose)]
        MongoDB[(MongoDB 8.0<br/>Port 27017)]
        Valkey[(Valkey Cache<br/>Port 6379)]
        Qdrant[(Qdrant Vector DB<br/>Port 6333)]
        Neo4j[(Neo4j Graph DB<br/>Ports 7474 / 7687)]
    end

    %% Flow Connections
    UI <-->|WebSocket Events & REST| Gateway_Layer
    Gateway_Layer <-->|HTTP REST & SSE Relay| FastAPIService
    Gateway_Layer -->|Mongoose ORM| MongoDB
    Gateway_Layer -->|Session Cache| Valkey

    FastAPIService --> Orchestration
    Orchestration --> Agents
    Agents --> MCP_Tools
    Agents --> Memory
    Agents --> Vision_OCR
    FastAPIService --> AirGap

    FastAPIService -->|Local HTTP REST & Embeddings| HostOllama
    HostOllama --> Hardware
    Hardware -->|CUDA Detected| NvidiaGPU
    Hardware -->|No CUDA| HostCPU

    Memory -->|Vector Embeddings| Qdrant
    Memory -->|Cypher Queries| Neo4j
    Memory -->|Sliding Window State| Valkey
    Memory -->|Metadata & Checkpoints| MongoDB
```

```text
                  ┌─────────────────────────────────────────────────────────┐
                  │                 React 18 / Vite UI                      │
                  │                http://localhost:5173                    │
                  │  (Chat · Documents · Knowledge · Agents · Monitoring)   │
                  └───────────────────────────┬─────────────────────────────┘
                                              │
                                     WebSocket / Socket.IO
                                              │
                  ┌───────────────────────────▼─────────────────────────────┐
                  │               Node.js / Express Backend                 │
                  │                http://localhost:5000                    │
                  │  (JWT RBAC · Token Streaming · Socket Hub · Document IO) │
                  └─────────────┬─────────────────────────────┬─────────────┘
                                │                             │
                           HTTP / SSE                   Mongoose / Cache
                                │                             │
                  ┌─────────────▼───────────────┐ ┌───────────▼─────────────┐
                  │  Python FastAPI AI Service  │ │  Infrastructure Storage │
                  │    http://localhost:8000    │ │  (Docker Compose Stack) │
                  │ ─────────────────────────── │ │ ─────────────────────── │
                  │ • LangGraph StateGraph DAG  │ │ • MongoDB 8.0  (:27017) │
                  │ • 16 Specialized Agents     │ │ • Valkey Cache (:6379)  │
                  │ • 18 Tools + 9 MCP Modules  │ │ • Qdrant Vector(:6333)  │
                  │ • Tripartite Memory System  │ │ • Neo4j Graph  (:7474)  │
                  │ • PaddleOCR & Vision Studio │ └─────────────────────────┘
                  │ • Sovereign Air-Gap Guard   │
                  └─────────────┬───────────────┘
                                │
                     http://localhost:11434
                                │
                  ┌─────────────▼───────────────┐
                  │   Local Ollama on Windows   │
                  │       (Host Runtime)        │
                  └─────────────┬───────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
      NVIDIA GPU Acceleration           CPU Mode Fallback
     (Auto-detected via CUDA)      (Intel / AMD / Integrated)
```

### Infrastructure Layer (Docker Compose)
Docker Compose is used **exclusively** for underlying storage, caching, and vector indexing engines:
- **MongoDB** (Port `27017`): User directory, role-based access control, conversation threads, and artifact metadata.
- **Valkey** (Port `6379`): Redis-compatible ultra-fast caching and Short-Term Memory (STM) sliding windows.
- **Qdrant** (Port `6333`): Vector database for semantic document embeddings and Long-Term Memory (LTM).
- **Neo4j** (Ports `7474`, `7687`): Knowledge graph for entity relationships, task provenance, and graph memory.

> [!IMPORTANT]
> **Ollama runs directly on the Windows host machine**, not inside a Docker container. This guarantees native hardware access to NVIDIA GPUs via host CUDA drivers while seamlessly falling back to CPU execution on laptops and standard PCs without dedicated graphics.

---

## 📁 Repository Directory Structure

```text
sih2026-main/
├── .env.example                       # Reference environment variables
├── AGENTS.md                          # Autonomous agent guidelines
├── docker-compose.yml                 # Root multi-container infrastructure
├── start-all.bat                      # One-click Windows startup script
├── start-services.ps1                 # Automated PowerShell service launcher
├── stop-all.bat                       # Graceful service shutdown script
├── IMPLEMENTATION_SUMMARY.md          # Implementation progress tracking
├── SOVEREIGN_BACKEND_ARCHITECTURE.md  # Detailed Architecture Specification
├── README.md                          # Platform documentation (This file)
│
├── FRONTEND/                          # React 18 + Vite Web Application
│   ├── package.json                   # UI dependencies (Tailwind, Lucide, Socket.IO)
│   ├── vite.config.js                 # Dev server proxying & build configuration
│   ├── src/
│   │   ├── App.jsx                    # Root router with protected RBAC views
│   │   ├── api/                       # 13 Axios API clients (auth, chat, docs, etc.)
│   │   ├── components/                # Chat, layout, admin modals & common UI
│   │   ├── context/                   # AuthContext & ChatContext providers
│   │   └── pages/                     # 11 Main pages (Chat, Documents, Monitoring, etc.)
│
├── BACKEND/                           # Node.js + Express Gateway
│   ├── server.js                      # Server startup & Socket.IO initialization
│   ├── src/
│   │   ├── app.js                     # Express middleware & route registrations
│   │   ├── controllers/               # 11 Controllers (auth, chat, docs, admin, etc.)
│   │   ├── models/                    # 14 Mongoose models (User, Conversation, Task, etc.)
│   │   ├── routes/                    # 13 REST API route files
│   │   ├── services/                  # Hardware probe, Ollama, Python AI proxy, Brevo mail
│   │   └── sockets/                   # Real-time WebSocket event streaming
│
├── AI-SERVICES/                       # Python FastAPI AI Microservice
│   ├── main.py                        # FastAPI entry point & workspace static file server
│   ├── requirements.txt               # Dependencies (LangGraph, PaddleOCR, Qdrant, etc.)
│   ├── api/routes/                    # 8 Route modules (chat, health, documents, vision, etc.)
│   ├── orchestrator/                  # LangGraph StateGraph DAG orchestrator
│   │   ├── graph.py                   # Master state graph coordinating Router, Planner, Exec
│   │   ├── task_classifier.py         # Deterministic 16-task intent classifier
│   │   └── nodes/                     # 6 DAG nodes: Router, Planner, Selector, Exec, Verify, Finalize
│   ├── agents/                        # 16 Domain-specialized agents (General, Code, Doc, etc.)
│   ├── tools/                         # Sandboxed tool registry + 9 MCP server modules
│   ├── memory/                        # Tripartite memory (STM, LTM, Neo4j Graph, ContextBuilder)
│   ├── ocr/                           # Industrial PaddleOCR service & image preprocessor
│   ├── rag/                           # Document chunking, parser & vector retriever
│   ├── core/                          # Config, logging, hardware detection & air-gap guard
│   └── workspace/                     # Strictly isolated sandbox for tool execution & reports
│
└── docker-compose/                    # Infrastructure container stack
    ├── docker-compose.yml             # MongoDB, Valkey, Qdrant, and Neo4j specifications
    └── README.md                      # Database administration & port guide
```

---

## 🤖 Multi-Agent Orchestrator & 16 Specialized Agents

The workbench coordinates complex user requests through a **LangGraph StateGraph DAG** ([`AI-SERVICES/orchestrator/graph.py`](./AI-SERVICES/orchestrator/graph.py)). Rather than relying on a single generic model, requests are classified into 16 distinct categories and routed to dedicated agents:

```text
User Request
     │
     ▼
[Deterministic Task Classifier] ──(Direct Chat)──► [Finalizer Node] ──► Response
     │
     ▼ (Complex / Multi-Step Task)
[Planner Node] (Decomposes task into structured step plan)
     │
     ▼
┌──► [Agent Selector Node] (Picks optimal agent: Coding, Document, OCR, etc.)
│    │
│    ▼
│    [Sandboxed Executor Node] (Executes tools, Python scripts, file operations)
│    │
│    ▼
│    [Verifier Node] (Evaluates outputs; triggers retries if errors occur)
│    │
└─── (Next Step in Plan)
     │
     ▼ (All Steps Verified)
[Finalizer Node] (Synthesizes comprehensive markdown report & deliverable links)
```

### The 16 Specialized Domain Agents
1. **`GeneralAgent`**: Conversational reasoning, intent analysis, workspace document access.
2. **`RouterAgent`**: Intent classification, agent selection, execution planning.
3. **`CodingAgent`**: Python and terminal script generation, debugging, sandbox execution.
4. **`DocumentAgent`**: Document repository intelligence, SOP authoring, vector search.
5. **`SpreadsheetAgent`**: Excel/CSV tabular analysis, statistics, data filtering.
6. **`PPTAgent`**: Structured PowerPoint presentation creation.
7. **`OCRAgent`**: Industrial text and tabular extraction using local PaddleOCR.
8. **`VisionAgent`**: Image inspection, equipment diagrams, visual anomaly identification.
9. **`KnowledgeAgent`**: Hybrid semantic vector retrieval and Neo4j graph queries.
10. **`MemoryAgent`**: STM conversation context and LTM user preference recall.
11. **`FileSystemAgent`**: Sandboxed file and directory manipulation.
12. **`MaintenanceAgent`**: Machinery failure diagnostics and operational log inspection.
13. **`SafetyAgent`**: Safety checklist auditing, PPE compliance, and LOTO validation.
14. **`ComplianceAgent`**: Regulatory gap analysis, ISO/OSHA policy compliance.
15. **`RiskAnalysisAgent`**: Industrial hazard identification, probability/severity scoring.
16. **`ReportingAgent`**: Synthesis of publication-grade executive reports and PDFs.

---

## 🛠️ Model Context Protocol (MCP) & Sandboxed Tools

All file operations, script executions, and document compilations run inside the isolated sandbox directory `AI-SERVICES/workspace`. Tools are exposed via standard interfaces and **9 Model Context Protocol (MCP)** adapters:

- **Filesystem MCP**: `filesystem.list_directory`, `filesystem.read_file`, `filesystem.create_file`, `filesystem.write_file`, `filesystem.delete_file`.
- **Document MCP**: `document.read_pdf`, `document.extract_text`, `document.create_pdf`, `document.create_excel`, `document.create_ppt`.
- **Knowledge MCP**: `knowledge.vector_search`, `knowledge.graph_search`, `knowledge.hybrid_search`.
- **Memory MCP**: `memory.search`, `memory.add`, `memory.update`, `memory.delete`.
- **OCR MCP**: `ocr.extract_text`, `ocr.extract_document`, `ocr.extract_page`.
- **Presentation MCP**: `ppt.create_presentation`, `ppt.add_slide`.
- **Python Execution MCP**: `python.execute`, `python.execute_script`.
- **Spreadsheet MCP**: `spreadsheet.read`, `spreadsheet.create`, `spreadsheet.update`, `spreadsheet.analyze`.
- **Vision MCP**: `vision.analyze_image`, `vision.analyze_document_image`.

---

## 🧠 Tripartite Memory Architecture

The cognitive subsystem integrates three complementary memory models to prevent context loss:
1. **Short-Term Memory (STM)**: Sliding dialogue window (up to 20 messages / 8,000 tokens) cached in Valkey / MongoDB, preventing token exhaustion.
2. **Long-Term Memory (LTM)**: Semantic vector memory stored in Qdrant (`sovereign_ai_memory`) with automatic fact extraction via Mem0.
3. **Knowledge Graph (Episodic Graph)**: Neo4j Cypher property graph maintaining explicit entity relationships:
   - `(:User)-[:STARTED]->(:Conversation)`
   - `(:Conversation)-[:HAS_TASK]->(:Task)`
   - `(:Task)-[:USED_TOOL]->(:Tool)`
   - `(:Task)-[:ACCESSED]->(:Document)`

---

## 🛡️ Sovereign Air-Gap Network Guard

The platform includes a dedicated security subsystem ([`AI-SERVICES/core/network_monitor.py`](./AI-SERVICES/core/network_monitor.py)) guaranteeing total data sovereignty:
- **Active Socket Interception**: Outbound socket connections attempting to reach external internet addresses are intercepted and blocked in real time.
- **Tamper-Evident SHA-256 Audit Chain**: Every internal network socket event and blocked egress attempt is logged to a rolling cryptographic hash chain:
  $$\text{Hash}_n = \text{SHA256}(\text{Hash}_{n-1} + \text{Timestamp} + \text{Destination} + \text{Action})$$
- **Verification Endpoint**: `POST /api/network/test-egress` allows security administrators to trigger live egress tests proving air-gap isolation.
- **Audit Dashboard**: View live air-gap status and cryptographic proofs on the Monitoring page (`http://localhost:5173/monitoring`).

---

## 🚀 Quick Start Guide

### Prerequisites
- **Operating System**: Windows 10/11 (or Linux/macOS)
- **Node.js**: v18+ or v20+
- **Python**: v3.10+
- **Docker**: Docker Desktop (for storage databases)
- **Ollama**: Installed natively on host from [ollama.com](https://ollama.com)

### 1. Install & Start Local Ollama
```powershell
# Verify installation
ollama --version

# Start Ollama daemon
ollama serve
```

Pull the recommended sovereign models:
```powershell
# Chat & Reasoning
ollama pull qwen2.5:1.5b

# Coding & Tool Execution
ollama pull qwen2.5-coder:1.5b

# Vision & Multimodal
ollama pull moondream:latest

# Vector Embeddings
ollama pull nomic-embed-text:latest
```

### 2. Start Storage Infrastructure (Docker Compose)
```powershell
cd docker-compose
docker compose up -d
```
*Starts MongoDB (`27017`), Valkey (`6379`), Qdrant (`6333`), and Neo4j (`7474`, `7687`).*

### 3. Start Application Services

#### Option A: One-Click Startup (Windows)
Run the root batch file:
```cmd
start-all.bat
```
or run the PowerShell launcher:
```powershell
.\start-services.ps1
```

#### Option B: Manual Terminal Startup
Open three separate terminal windows:

**Terminal 1 — Node.js Backend Gateway:**
```powershell
cd BACKEND
npm install
npm run dev
```
*Listens on `http://localhost:5000`.*

**Terminal 2 — Python FastAPI AI Service:**
```powershell
cd AI-SERVICES
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```
*Listens on `http://localhost:8000` (Interactive docs: `http://localhost:8000/docs`).*

**Terminal 3 — React Frontend:**
```powershell
cd FRONTEND
npm install
npm run dev
```
*Listens on `http://localhost:5173`.*

---

## ⚡ Hardware Auto-Detection & Fallback

The workbench includes safe, non-crashing hardware auto-detection:

| Hardware Environment | Auto-Detection Behavior |
|---|---|
| **NVIDIA GPU + CUDA Drivers** | Detected via `nvidia-smi`. Host Ollama assigns model layers to GPU VRAM for high-speed inference. |
| **CPU / Integrated Graphics** | `nvidia-smi` check is safely caught. The system logs CPU execution mode and runs smoothly without crashing. |

> [!NOTE]
> Missing NVIDIA GPUs or drivers will **never crash** any platform service. GPU acceleration is strictly an optimization, not a hard requirement.

---

## 🩺 Health & Diagnostic Endpoints

Verify system connectivity and hardware status at any time:

```powershell
curl http://localhost:5000/api/health
```

### Example Health Response
```json
{
  "success": true,
  "status": "healthy",
  "message": "Sovereign AI Workbench API is healthy",
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
    "node": "healthy",
    "python": "healthy",
    "ollama": "healthy"
  }
}
```

---

## 🧩 Environment Variables Reference

### Backend Gateway (`BACKEND/.env`)
```env
PORT=5000
FRONTEND_URL=http://localhost:5173
JWT_SECRET=your_jwt_secret_key_here
MONGO_URI=mongodb://admin:admin@localhost:27017/sovereign_ai?authSource=admin
AI_SERVICE_URL=http://localhost:8000
PYTHON_AI_SERVICE_URL=http://localhost:8000
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_HOST=http://localhost:11434
BREVO_SENDER_EMAIL=avinashbharti3007@gmail.com
```

### AI Services (`AI-SERVICES/.env`)
```env
APP_NAME=Sovereign AI Service
HOST=0.0.0.0
PORT=8000
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_HOST=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen2.5:1.5b
OLLAMA_CODE_MODEL=qwen2.5-coder:1.5b
OLLAMA_VISION_MODEL=moondream
OLLAMA_EMBED_MODEL=nomic-embed-text:latest
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=sovereign_documents
QDRANT_VECTOR_SIZE=768
NEO4J_URI=bolt://localhost:7687
NEO4J_URL=http://localhost:7474
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=sovereignpass
VALKEY_URL=redis://localhost:6379
OCR_ENGINE=paddleocr
OCR_USE_GPU=false
LOG_LEVEL=INFO
```

---

## 📜 Architectural Deep-Dive

For complete component specifications, LangGraph state machine schemas, tool definitions, and memory sequence diagrams, refer to:
- **[Architecture Guide (SOVEREIGN_BACKEND_ARCHITECTURE.md)](./SOVEREIGN_BACKEND_ARCHITECTURE.md)**
- **[AI Services Specification (AI-SERVICES/README.md)](./AI-SERVICES/README.md)**
- **[Frontend Architecture (FRONTEND/README.md)](./FRONTEND/README.md)**
- **[Infrastructure Stack (docker-compose/README.md)](./docker-compose/README.md)**