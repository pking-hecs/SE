# Agentic AI for Financial Requirements Engineering

An autonomous, collaborative multi-agent AI system designed to automate requirement gathering, analysis, and SDLC identification in the highly regulated financial sector.

## 🚀 Project Overview
Gathering requirements in banking and finance is typically manual, time-consuming, and prone to regulatory omissions. This system uses a team of specialized AI agents to interact with stakeholders, analyze conversations, detect ambiguities, and ensure every requirement is mapped to financial regulations.

## 🛠️ Core Features
- **Multi-Agent Orchestration:** 13 specialized agents (Coordinator, Compliance, Risk, SDLC Selection, etc.) collaborating via a hub-and-spoke model.
- **Retrieval-Augmented Generation (RAG):** Grounding all requirements in an authorized **Financial Knowledge Base (FKB)** to eliminate hallucinations and ensure regulatory adherence.
- **Security & Privacy:** Integrated PII masking (emails, account numbers) and prompt-injection guards to protect sensitive financial data.
- **Automated Artifacts:** Generation of professional **Software Requirements Specifications (SRS)**, User Stories, and Requirements Traceability Matrices (RTM).
- **Intelligent SDLC Selection:** A decision engine that recommends the best development model (Agile, V-Model, Spiral, etc.) based on risk, stability, and regulatory criticality.
- **Human-in-the-Loop (HITL):** Mandatory approval gates for critical regulatory and architectural decisions.

## 📁 Project Structure
- `src/core/`: The "Brain" (RAG engine, SDLC engine, Orchestrator state, Security guards).
- `src/agents/`: The "Workers" (Interaction, Extraction, Analysis, Compliance, Documentation agents).
- `docs/`: Full technical specifications, architecture designs, and stakeholder maps.
- `src/main.py`: The main entry point to run the end-to-end pipeline.

## 🏃 How to Run
### Prerequisites
- Python 3.10+

### Execution (PowerShell)
```powershell
$env:PYTHONPATH = (Get-Location).Path
python src/main.py
```

### Execution (Git Bash)
```bash
export PYTHONPATH=$(pwd) && python src/main.py
```

## 📊 Expected Results
Upon running, the system will:
1. Mask sensitive data from stakeholder input.
2. Extract structured requirements.
3. Map requirements to regulatory codes (e.g., `[KB-REG-001]`).
4. Recommend a justified SDLC model.
5. Request human sign-off for the project baseline.
6. Generate a final SRS preview.
