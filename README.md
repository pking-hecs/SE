# FinReq — Autonomous Financial Requirements Engineering Platform

## 🚀 Overview
**FinReq** is an autonomous, multi-agent AI system designed for requirements engineering in the banking and financial services sector. It transforms unstructured stakeholder prompts, interviews, and regulatory policy documents into atomic, IEEE 830/29148-compliant software specifications, BDD acceptance criteria, grounded compliance mappings, STRIDE threat models, and MCDA-ranked SDLC workflows.

---

## 🛠️ Tech Stack
- **Backend**: FastAPI, Python 3.10+, Pydantic v2, Uvicorn
- **Frontend**: Vanilla JavaScript (ES2020), HTML5, CSS3 with Custom Design Tokens & Floating Capsule Navigation
- **AI & LLM Orchestration**: Google Gemini (`google-generativeai` / `google.genai`), multi-provider candidate failover
- **Grounding & RAG**: `FinancialRAG` (TF-IDF cosine similarity over regulatory knowledge base) with optional PostgreSQL `pgvector` semantic search
- **Security & Identity**: Role-Based Access Control (RBAC, 6 financial personas), PBKDF2 password hashing (100k iterations), RFC 6238 TOTP Multi-Factor Authentication (MFA), HMAC-SHA256 signed access tokens, and pre-inference PII masking
- **Database & State**: PostgreSQL (22 relational tables) with seamless SQLite WAL fallback (`finreq_history.db`), Redis state caching with in-memory fallback

---

## 🏗️ 13 Autonomous Specialist Agents
FinReq employs a **Coordinator–Specialist Architecture** orchestrated in [`agents/orchestrator.py`](agents/orchestrator.py):

| # | Agent | Primary Responsibility |
|---|---|---|
| **0** | **Security Guard** | Pre-flight PII scanner & regex sanitizer (redacts Card Numbers, SSNs, Accounts, Emails). |
| **1** | **Interaction Agent** | Adaptive stakeholder interview engine; asks context-aware clarification questions. |
| **2** | **Extraction Agent** | Decomposes raw natural language into atomic requirements using RFC 2119 keywords (`SHALL`/`MUST`). |
| **3** | **Clarification Agent** | Identifies ambiguous metrics, missing SLAs, and unquantified non-functional bounds. |
| **4** | **Classification Agent** | Categorizes requirements across 13 financial taxonomy dimensions (Functional, Regulatory, Security, Core Banking, etc.). |
| **5** | **Conflict Agent** | Detects semantic contradictions and duplicate requirements across the baseline. |
| **6** | **Compliance Agent** | RAG-grounded mapping to GDPR, PCI-DSS v4.0, Basel III/IV, MiFID II, and AML regulations. |
| **7** | **Security & Privacy Agent** | STRIDE threat modeling (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation of Privilege). |
| **8** | **Risk Agent** | Assesses systemic, operational, and credit risk with Likelihood × Impact scoring. |
| **9** | **SDLC Selection Agent** | Multi-Criteria Decision Analysis (MCDA) ranking of Agile-DevSecOps, V-Model, Spiral, and Waterfall. |
| **10** | **Documentation Agent** | Synthesizes IEEE 830/29148 Software Requirements Specifications (SRS), BDD Gherkin User Stories, and RTM. |
| **11** | **Validation Agent** | Quality gatekeeper ensuring completeness, acceptance criteria coverage, and audit readiness. |
| **12** | **Human-Approval Agent** | Enforces governance sign-off checkpoints and writes immutable audit trail entries. |

---

## 📁 Project Structure

```
.
├── main.py                     # FastAPI core server & REST API (18 endpoints)
├── auth.py                     # RBAC permissions, PBKDF2 hashing, TOTP MFA, HMAC tokens
├── db.py                       # PostgreSQL + SQLite persistence & RAG vector interface
├── cache.py                    # Redis caching layer & sliding-window rate limiter
├── requirements.txt            # Python dependencies
├── .env.example                # Template for environment configuration
│
├── agents/                     # Specialist Agent Implementations
│   ├── orchestrator.py         # AgentOrchestrator pipeline coordinator
│   └── specialists.py          # 13 Specialist Agent classes, LLMCaller & FinancialRAG
│
├── src/core/                   # Core Data Models & RAG Engine
│   ├── orchestrator/
│   │   └── state.py            # ProjectState & Requirement dataclasses
│   └── rag/
│       └── engine.py           # FinancialRAG TF-IDF & vector retrieval engine
│
├── static/                     # Web Application UI (Served by FastAPI at /)
│   ├── index.html              # Single Page Application layout & modal templates
│   ├── style.css               # Luxury dark theme, floating capsule navigation & tab dock
│   └── script.js               # Frontend state management, real-time rendering & API client
│
├── knowledge_base/             # Authoritative Financial Knowledge Base (FKB)
│   ├── regulations.txt         # Statutory articles: GDPR, PCI-DSS, Basel III/IV, AML/BSA
│   └── policies.txt            # Internal institutional banking & governance rules
│
├── finreq_history.db           # SQLite WAL database for persistent sessions
├── test_history_feature.py     # Test suite for session persistence & workspace restore
└── test_platform_e2e.py        # End-to-End verification suite across all 13 modules
```

---

## 🚦 Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 2. Environment Setup
```bash
# Clone the repository
git clone <repo-url>
cd SE

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your Google Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. Run the Application
Start the FastAPI server:
```bash
python3 main.py
# or using uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser and navigate to:
```
http://localhost:8000
```

---

## 🔐 Demo Credentials & Roles

| Role | Email | Password | Demo MFA Code | Capabilities |
|---|---|---|---|---|
| **Compliance Officer** | `compliance@finbank.com` | `admin123` | `123456` | Review & approve compliance baselines, view audit trail |
| **Security Lead** | `security@finbank.com` | `admin123` | `123456` | Approve SDLC model, threat mitigations, risk register |
| **Business Analyst** | `analyst@finbank.com` | `admin123` | `123456` | Extract requirements, submit prompts, chat, edit statements |

---

## 🧪 Running Automated Tests

To verify that all endpoints, auth, RAG, and persistence are operating correctly:

```bash
# Test session saving, loading, and renaming
python3 test_history_feature.py

# Run complete End-to-End verification across all 13 modules
python3 test_platform_e2e.py
```

---

## 📜 Key Endpoints

- `POST /session/start` — Triggers complete 13-agent extraction & analysis pipeline
- `POST /session/chat` — Contextual follow-up conversation within an active project
- `POST /session/approve` — Role-authorized sign-off on requirements, compliance, or SDLC
- `GET /session/{id}/rtm_matrix` — Returns full Requirements Traceability Matrix
- `GET /session/{id}/export/{artifact}` — Downloads markdown exports (`srs`, `rtm`, `user_stories`, `risk_register`)
- `GET /history` & `POST /history/save` — Workspace persistence and session management
- `GET /api/admin/metrics` — Live telemetry on database, agent runs, and cache health
