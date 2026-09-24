# Sovereign AI Services - FastAPI Microservice

**Production-Ready Python AI Microservice for Sovereign On-Premise Agentic AI Workbench**  
Repository: [https://github.com/avinash2005bharti/sih2026.git](https://github.com/avinash2005bharti/sih2026.git)

The `AI-SERVICES` component provides the core intelligence layer for the sovereign workbench:
- **LangGraph Multi-Agent Orchestrator**: Deterministic task classification, dynamic DAG planning, step execution, and iterative verification.
- **16 Specialized Domain Agents**: Dedicated prompt engineering, model assignment, and tool whitelists.
- **Sandboxed Tool Registry & MCP Layer**: 18 isolated tools + 9 Model Context Protocol (MCP) server adapters.
- **Tripartite Cognitive Memory**: Short-Term Memory (Valkey/MongoDB sliding window), Long-Term Memory (Qdrant vector collection + Mem0), and Knowledge Graph (Neo4j Cypher).
- **Industrial OCR & Vision Studio**: Local PaddleOCR text extraction with computer vision preprocessing (deskew, binarize, denoise) and multimodal fallback.
- **Sovereign Air-Gap Guard**: Socket-level egress interception and rolling SHA-256 cryptographic audit logs.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (Recommended: Python 3.11)
- Ollama running locally on Windows host (`http://localhost:11434`)
  - `qwen2.5:1.5b` (general chat & reasoning)
  - `qwen2.5-coder:1.5b` (coding & file manipulation)
  - `moondream:latest` (computer vision & image analysis)
  - `nomic-embed-text:latest` (vector embeddings)

### Setup & Run
```bash
# 1. Navigate to directory
cd AI-SERVICES

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start FastAPI service
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI Swagger documentation is available at: `http://localhost:8000/docs`.

---

## 🏛️ Component Architecture

```mermaid
flowchart TD
    subgraph Inbound [FastAPI API Layer (Port 8000)]
        Main[main.py Lifespan & CORS]
        ChatRoute[/api/chat & /api/chat/stream]
        DocRoute[/api/documents]
        VisRoute[/api/vision]
        MemRoute[/api/memory]
        NetRoute[/api/network]
        HealthRoute[/health]
        WorkRoute[/workspace/* Static Artifacts]
    end

    subgraph LangGraph_Orchestrator [LangGraph StateGraph DAG Orchestrator]
        Classifier[Task Classifier: 16 Deterministic Categories]
        RouterNode[Router Node]
        PlannerNode[Planner Node]
        SelectorNode[Agent Selector Node]
        ExecutorNode[Executor Node]
        VerifierNode[Verifier Node]
        FinalizerNode[Finalizer Node]
    end

    subgraph Domain_Agents [16 Domain Specialized Agents]
        AgentGrid[GeneralAgent · CodingAgent · DocumentAgent · SpreadsheetAgent<br/>PPTAgent · OCRAgent · VisionAgent · KnowledgeAgent · MemoryAgent<br/>FileSystemAgent · MaintenanceAgent · SafetyAgent · ComplianceAgent<br/>RiskAnalysisAgent · ReportingAgent · RouterAgent]
    end

    subgraph Tools_MCP [Sandboxed Tool Registry & MCP Integration]
        Registry[tool_registry.py & tools_registry.json]
        MCPs[9 MCP Server Modules: FS, Doc, Code, Data, Pres, OCR, Vis, RAG, Mem]
        Sandbox[AI-SERVICES/workspace/]
    end

    subgraph Memory_System [Tripartite Cognitive Memory Subsystem]
        MasterMem[MemoryManager]
        STM[STM Sliding Window (Valkey/MongoDB)]
        LTM[LTM Vector Recall (Qdrant + Mem0)]
        Graph[Neo4j Cypher Knowledge Graph]
    end

    subgraph Vision_OCR_Subsystem [OCR & Multimodal Vision]
        Paddle[Local PaddleOCR Engine]
        Preprocessor[Image Preprocessor: Deskew, Binarize, Denoise]
        VisionLLM[Moondream / Qwen2.5-VL]
    end

    subgraph Security [Sovereign Air-Gap Guard]
        EgressGuard[Socket Interceptor]
        AuditChain[Rolling SHA-256 Hash Chain]
    end

    %% Wiring
    ChatRoute --> LangGraph_Orchestrator
    LangGraph_Orchestrator --> Domain_Agents
    Domain_Agents --> Tools_MCP
    Domain_Agents --> Memory_System
    Domain_Agents --> Vision_OCR_Subsystem
    Main --> Security
    Tools_MCP --> Sandbox
```

---

## 📁 AI-SERVICES Directory Structure

```text
AI-SERVICES/
├── main.py                    # FastAPI application, lifespan probes, CORS & static file server
├── requirements.txt           # Python package requirements
├── .env                       # Local environment configuration
│
├── api/                       # API Route Endpoints
│   └── routes/
│       ├── health.py          # /health, /api/health/models
│       ├── chat.py            # /api/chat, /api/chat/stream (SSE)
│       ├── models.py          # /api/models, /api/models/{model_name}
│       ├── documents.py       # /api/documents, /api/documents/search, /rag-status
│       ├── vision.py          # /api/vision/analyze, /api/vision/extract-text
│       ├── tasks.py           # /api/tasks (asynchronous task progress)
│       ├── memory_routes.py   # /api/memory/status, /search, /graph
│       └── network.py         # /api/network/status, /audit, /test-egress
│
├── orchestrator/              # LangGraph Multi-Agent Orchestration
│   ├── graph.py               # StateGraph lifecycle coordinator (Router, Planner, Exec loop)
│   ├── state.py               # Pydantic AgenticState data model
│   ├── execution_state.py     # Execution step tracking and status
│   ├── task_classifier.py     # Deterministic 16-task content classifier
│   └── nodes/                 # DAG State Nodes
│       ├── router.py          # Classifies query, selects direct vs multi-step plan
│       ├── planner.py         # Decomposes queries into structured steps
│       ├── agent_selector.py  # Selects optimal domain agent for step
│       ├── executor.py        # Sandboxed tool & script execution
│       ├── verifier.py        # Validates deliverables against expectations
│       └── finalizer.py       # Consolidates response, generates links & updates memory
│
├── agents/                    # 16 Specialized Domain Agents
│   ├── base_agent.py          # Abstract base agent class
│   ├── agent_registry.py      # Master agent registry, system prompts & tool assignments
│   ├── langgraph_agent.py     # Autonomous LangGraph agent executor
│   ├── code_agent.py          # Coding & Python execution agent
│   ├── document_agent.py      # Technical document authoring & repository agent
│   ├── spreadsheet_agent.py   # Excel / CSV data processing agent
│   ├── ppt_agent.py           # PowerPoint presentation agent
│   ├── ocr_agent.py           # Industrial OCR text & table agent
│   ├── vision_agent.py        # Visual inspection & anomaly agent
│   ├── knowledge_agent.py     # Semantic RAG & graph search agent
│   ├── memory_agent.py        # Short & long-term memory agent
│   ├── filesystem_agent.py    # Sandboxed file management agent
│   ├── maintenance_agent.py   # Equipment diagnostic agent
│   ├── safety_agent.py        # Industrial safety & PPE agent
│   ├── compliance_agent.py    # Regulatory SOP audit agent
│   ├── risk_agent.py          # Risk scoring & mitigation agent
│   ├── reporting_agent.py     # Executive report & PDF authoring agent
│   └── router_agent.py        # Routing & intent classification agent
│
├── tools/                     # Sandboxed Tool Registry & MCP Modules
│   ├── tool_registry.py       # Central SovereignTool registry (16 base tools)
│   ├── tools_registry.json    # Machine-readable schema catalog
│   ├── agent_tools.py         # LangChain tool bindings with path sandboxing
│   ├── tool_manager.py        # Dynamic tool registration manager
│   ├── file_tool.py           # Sandboxed file I/O operations
│   ├── code_tool.py           # Subprocess Python & command execution
│   ├── document_tool.py       # ReportLab PDF creation & text inspection
│   ├── spreadsheet_tool.py    # CSV & Excel data analysis
│   ├── excel_tool.py          # Openpyxl workbook generation
│   ├── ppt_tool.py            # Python-pptx presentation generation
│   ├── rag_tool.py            # Vector search & document chunk indexing
│   ├── memory_tool.py         # Long-term memory extraction & save
│   └── MCP Integration:       # Model Context Protocol Adapters
│       ├── filesystem_mcp.py  # filesystem.*
│       ├── document_mcp.py    # document.*
│       ├── knowledge_mcp.py   # knowledge.*
│       ├── memory_mcp.py      # memory.*
│       ├── ocr_mcp.py         # ocr.*
│       ├── ppt_mcp.py         # ppt.*
│       ├── python_mcp.py      # python.*
│       ├── spreadsheet_mcp.py # spreadsheet.*
│       └── vision_mcp.py      # vision.*
│
├── memory/                    # Tripartite Cognitive Memory Subsystem
│   ├── memory_manager.py      # Master coordinator for STM, LTM, and Graph
│   ├── models.py              # Pydantic memory schemas
│   ├── context_builder.py     # Prompt context builder
│   ├── stm/                   # Short-term sliding window (Valkey/MongoDB)
│   ├── ltm/                   # Long-term vector recall (Qdrant + Mem0)
│   ├── graph/                 # Neo4j Cypher knowledge graph client
│   ├── mem0/                  # Local Mem0 storage engine
│   └── embeddings/            # nomic-embed-text local embedding service
│
├── ocr/                       # Industrial OCR Engine
│   ├── ocr_service.py         # Local PaddleOCR wrapper with CPU/GPU auto-detection
│   └── preprocessing.py       # Image preprocessor (deskew, binarize, denoise)
│
├── rag/                       # Document Ingestion & Retrieval
│   ├── retriever.py           # Semantic vector search pipeline
│   ├── parser.py              # PDF, DOCX, TXT, CSV parser
│   ├── embeddings.py          # Vector embedding batcher
│   ├── qdrant_client.py       # Qdrant HTTP REST client
│   └── document_store.py      # Document repository catalog
│
├── core/                      # Platform Foundations
│   ├── config.py              # Pydantic configuration settings
│   ├── logging.py             # Structured logger
│   ├── hardware.py            # nvidia-smi auto-detection probe
│   └── network_monitor.py     # Air-gap guard, egress interceptor & audit chain
│
└── workspace/                 # Strictly Sandboxed Tool Execution Directory
    └── reports/               # Generated reports, PDFs, and spreadsheets
```

---

## 📡 API Endpoint Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Microservice & host Ollama reachability probe |
| `/api/models` | `GET` | Real-time list of installed Ollama models |
| `/api/chat` | `POST` | Dispatches task to LangGraph multi-agent orchestrator |
| `/api/chat/stream` | `POST` | SSE real-time token & agent step streaming |
| `/api/vision/analyze` | `POST` | Multimodal visual inspection & diagram analysis |
| `/api/vision/extract-text`| `POST` | Local PaddleOCR text extraction |
| `/api/documents` | `POST` | Index document chunks into Qdrant vector database |
| `/api/documents/search` | `POST` | Semantic vector search across indexed documents |
| `/api/documents/rag-status`| `GET` | Status of Qdrant vector collection |
| `/api/memory/status` | `GET` | Health of STM, LTM, Qdrant, Neo4j, and Mem0 |
| `/api/memory/search` | `POST` | Semantic search over long-term memories |
| `/api/network/status` | `GET` | Sovereign air-gap network status and cryptographic proof |
| `/api/network/audit` | `GET` | Tamper-evident network audit log (SHA-256 chain) |
| `/api/network/test-egress` | `POST` | Actively tests and verifies outbound egress blocking |
| `/workspace/{file_path}` | `GET` | Direct download / inline preview for generated deliverables |

---

## 🔒 Security & Air-Gap Compliance

- **Zero Cloud Calls**: Verified by [`core/network_monitor.py`](./core/network_monitor.py). All outbound socket connections outside the local sovereign subnet are intercepted and blocked.
- **Cryptographic Audit Chain**: Every network action is hashed into a rolling SHA-256 blockchain-style log.
- **Sandboxed Execution**: Tools only read and write within `AI-SERVICES/workspace/`. Attempts to traverse outside the directory via `../` are blocked by path resolution security checks.
