# Financial Requirements Engineering AI Platform

## 🚀 Overview
A production-grade, multi-agent AI system for financial software requirements engineering. It transforms stakeholder conversations and documents into structured, validated, and compliant requirements.

## 🛠️ Tech Stack
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, TanStack Query, Lucide Icons
- **Backend**: FastAPI, Python 3.10+, Pydantic, SQLAlchemy, Alembic
- **AI**: Ollama (Gemma model), LangGraph (Agent orchestration), Sentence-Transformers (Local Embeddings)
- **Database**: PostgreSQL + `pgvector` (RAG & Persistence), Redis (State Cache)
- **DevOps**: Docker Compose

## 🏗️ Architecture
The system uses a **Coordinator-Specialist** pattern:
1. **Coordinator Agent**: Manages the state graph and routes tasks.
2. **Specialists**:
    - `InteractionAgent`: Adaptive stakeholder interviews.
    - `ExtractionAgent`: Converts NL to structured Pydantic requirements.
    - `QualityAgent`: Detects ambiguity, incompleteness, and duplication.
    - `ConflictAgent`: Identifies contradictions between requirements.
    - `SecurityAgent`: Threat analysis and PII masking.
    - `ComplianceAgent`: RAG-based mapping to financial regulations.
    - `RiskAgent`: Calculates financial and technical risk scores.
    - `ValidationAgent`: Final gatekeeper before human approval.
    - `SdlcAgent`: Recommends SDLC based on a weighted scoring model.
    - `DocAgent`: Generates SRS, RTM, and User Stories.

## 🚦 Getting Started

### 1. Ollama Setup
Ensure Ollama is installed and the model is pulled:
```bash
ollama pull gemma:2b # or your detected gemma model
```

### 2. Infrastructure
Start the database and cache:
```bash
docker compose up -d db redis
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
# Initialize DB
alembic upgrade head
# Start Server
uvicorn app.main:app --reload
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure
- `backend/app/api/`: REST endpoints.
- `backend/app/agents/`: Specialist AI logic.
- `backend/app/core/`: Orchestrator, RAG engine, and Security guard.
- `backend/app/models/`: SQLAlchemy database models.
- `frontend/src/`: React components and state management.
- `demo_documents/`: Sample financial policies for testing RAG.

## 🛡️ Security & Compliance
- **RBAC**: Strict role separation (Stakeholder vs Analyst vs Approver).
- **Data Privacy**: Automatic PII masking before LLM processing.
- **Prompt Guard**: Middleware to detect and block prompt injection.
- **Audit Trail**: Immutable logging of every requirement change and approval.
