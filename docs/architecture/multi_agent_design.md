# Multi-Agent Architecture Specification

## 1. Overview
The system employs a collaborative multi-agent architecture to automate the requirements engineering process for the financial sector. A central **Coordinator Agent** manages the workflow, ensuring that requirements are extracted, validated, classified, and mapped to regulatory standards before an SDLC is recommended.

## 2. Agent Definitions & Responsibilities

| Agent | Role | Core Responsibility | Interaction |
| :--- | :--- | :--- | :--- |
| **Coordinator Agent** | Orchestrator | Manages execution order and shared context. | Root $\rightarrow$ All Agents |
| **Stakeholder Interaction Agent** | Interviewer | Conducts adaptive interviews to gather raw inputs. | User $\leftrightarrow$ Coordinator |
| **Requirement Extraction Agent** | Parser | Transforms unstructured text into raw requirements. | Input $\rightarrow$ Coordinator |
| **Clarification Agent** | Quality Analyst | Detects ambiguity and asks follow-up questions. | Coordinator $\leftrightarrow$ User |
| **Classification Agent** | Taxonomist | Categorizes requirements (Functional, Security, etc.). | Extractor $\rightarrow$ Coordinator |
| **Conflict-Detection Agent** | Auditor | Identifies contradictions or duplicates. | Classifier $\rightarrow$ Coordinator |
| **Compliance Agent** | Regulatory Expert | Maps requirements to GDPR, PCI-DSS, Basel III. | Classifier $\rightarrow$ Coordinator |
| **Security & Privacy Agent** | Cyber Guard | Identifies threats and privacy control needs. | Classifier $\rightarrow$ Coordinator |
| **Risk-Analysis Agent** | Risk Manager | Assesses business and technical risks. | Compliance $\rightarrow$ Coordinator |
| **SDLC Selection Agent** | Architect | Recommends the optimal SDLC model (V-Model, Agile, etc.). | Risk/Reqs $\rightarrow$ Coordinator |
| **Documentation Agent** | Technical Writer | Generates SRS, User Stories, and Traceability Matrix. | All Agents $\rightarrow$ User |
| **Validation Agent** | Verifier | Ensures completeness and evidence-based output. | Documentation $\rightarrow$ Coordinator |
| **Human-Approval Agent** | Gatekeeper | Routes critical decisions to authorized personnel. | Coordinator $\rightarrow$ Human |

## 3. Interaction Workflow (The Pipeline)

1. **Initiation**: The `Coordinator Agent` receives a project idea.
2. **Extraction & Analysis**: The `Requirement Extraction Agent` and `Classification Agent` process the input.
3. **Regulatory Grounding**: The `Compliance Agent` uses RAG to map requirements to financial laws.
4. **Strategic Selection**: The `SDLC Selection Agent` analyzes the risk profile to choose the model (e.g., Waterfall for fixed laws, Agile for mobile apps).
5. **Artifact Generation**: The `Documentation Agent` compiles all findings into a formal SRS.
6. **Human-in-the-Loop**: The `Human-Approval Agent` presents the output to the user for final sign-off.

## 4. Shared Context & State
All agents communicate via a **Shared Context Object** (the `result` dictionary in `orchestrator.py`), which ensures that the SDLC agent knows exactly what the Compliance agent discovered.
