# Implementation Plan: Transition to 13-Agent Collaborative Architecture

## 1. Overview
Transition the current 4-agent linear pipeline to a sophisticated 13-agent collaborative platform. The system will move from a "single request-response" model to an "interactive stateful session" model, allowing for iterative stakeholder interviews, clarification loops, and multi-stage approval gates.

## 2. Phased Implementation Strategy

### Phase 1: Core Infrastructure & State Management (Foundation)
- **Shared Context Evolution**: Upgrade `ProjectState` to support session-based persistence, requirement versioning, and agent-specific audit logs.
- **Coordinator Agent**: Implement the `CoordinatorAgent` to act as the primary state machine and routing logic.
- **API Refactor**: Update `main.py` to support session-based endpoints (`/start_session`, `/chat`, `/get_state`) instead of a single `/analyze` endpoint.

### Phase 2: Interaction & Requirement Refinement (The Interview Loop)
- **Frontend Overhaul**: Modify `index.html` and `script.js` to support a chat-like interface that handles different states (Interviewing, Clarifying, Reviewing).
- **Interaction & Clarification Agents**: Implement `InteractionAgent` (for initial intake) and `ClarificationAgent` (for resolving ambiguities found by the Analysis/Conflict agents).
- **Extraction & Classification Agents**: Implement agents to transform chat history into structured `Requirement` objects and categorize them.

### Phase 3: Analysis & Risk Assessment (The Quality Gate)
- **Conflict Detection Agent**: Implement logic to identify contradictory requirements.
- **Compliance, Security, & Risk Agents**: Implement a parallel analysis tier to map requirements to financial regulations and identify project-level risks.
- **Validation Agent**: Implement a final check to ensure all requirements are grounded, non-conflicting, and compliant.

### Phase 4: Synthesis & Approval (The Final Output)
- **SDLC Selection Agent**: Refine the existing SDLC logic to take inputs from the Risk and Compliance agents.
- **Documentation Agent**: Upgrade the SRS generation to use the refined, validated requirements baseline.
- **Human-Approval Agent**: Implement the "Approval Gate" logic, allowing humans to approve/reject specific requirements before the final SRS is locked.

## 3. Proposed Shared Context (`ProjectState`)
The state must be a centralized object managed by the Coordinator.

```python
@dataclass
class ProjectState:
    project_id: str
    session_id: str
    current_phase: str  # INTERVIEW, CLARIFICATION, ANALYSIS, APPROVAL, FINALIZATION
    
    # Structured Data
    requirements: Dict[str, Requirement]  # req_id -> Requirement object
    global_constraints: List[str]         # High-level project boundaries
    stakeholder_profiles: List[Dict]     # Roles and their specific concerns
    
    # Analysis Results
    conflicts: List[Dict]                # identified contradictions
    compliance_gaps: List[Dict]          # missing regulatory mappings
    risk_matrix: List[Dict]              # identified risks and mitigations
    
    # Workflow State
    history: List[AgentResponse]         # Full audit trail of all agent interactions
    pending_clarifications: List[str]    # Questions the user needs to answer
    approval_status: Dict[str, str]     # req_id -> "approved" | "rejected" | "pending"
    
    # Final Outputs
    selected_sdlc: Optional[str]
    final_srs_document: Optional[str]
```

## 4. Agent Breakdown & Prompts

| Agent | Primary Responsibility | Key Prompt Focus |
| :--- | :--- | :--- |
| **Coordinator** | Session management & routing | "Analyze the current ProjectState and determine which agent is next in the workflow. If ambiguities exist, route to ClarificationAgent." |
| **Interaction** | Stakeholder interviewing | "Act as a lead business analyst. Conduct an adaptive interview to uncover functional and non-functional requirements. Be conversational but thorough." |
| **Extraction** | Text $\rightarrow$ Structured Req | "Parse the conversation history and extract atomic requirements. Assign each a unique ID and a draft category." |
| **Clarification**| Resolving ambiguity | "Review the ambiguities identified by the AnalysisAgent. Formulate precise, non-leading questions for the user to resolve them." |
| **Classification**| Categorization | "Classify requirements into: Functional, Non-Functional, Security, or Technical Constraints. Justify the classification." |
| **Conflict-Det.** | Contradiction detection | "Compare all extracted requirements. Identify any two or more statements that are logically incompatible or contradictory." |
| **Compliance** | Regulatory mapping | "Map requirements to GDPR, PCI-DSS, and Basel III. Flag any requirement that violates these regulations." |
| **Security** | Threat modeling | "Analyze requirements for security vulnerabilities. Suggest specific security controls (e.g., OAuth2, AES-256) for each." |
| **Risk** | Project risk analysis | "Identify operational, financial, and technical risks associated with these requirements. Assign a risk level (Low/Med/High)." |
| **SDLC** | Model selection | "Based on risk level, compliance needs, and requirement stability, select the optimal SDLC (Waterfall, Agile, Spiral, etc.)." |
| **Documentation**| SRS Generation | "Synthesize the validated requirements, selected SDLC, and compliance mappings into a professional Software Requirements Specification." |
| **Validation** | Final consistency check | "Perform a final audit. Ensure no conflicts remain and all high-risk items have mitigations." |
| **Human-Approval**| Approval management | "Present requirements to the human stakeholder. Track approvals and modifications. Lock the baseline once all critical items are signed off." |

## 5. System Changes

### `main.py` (FastAPI)
- **Shift to Session-based API**:
    - `POST /session/start`: Initializes `ProjectState` and returns `session_id`.
    - `POST /session/chat`: Takes `session_id` and `message`. Routes to `Coordinator` $\rightarrow$ `Agent` $\rightarrow$ `Coordinator`.
    - `GET /session/state`: Returns the current state (requirements list, current phase).
    - `POST /session/approve`: Updates the `approval_status` in the shared context.
- **State Persistence**: Replace simple JSON logs with a lightweight session store (e.g., a dictionary in memory for dev, or SQLite for production).

### `index.html` / `script.js` (Frontend)
- **Stateful UI**: 
    - Add a "Project Status" indicator (e.g., "Phase: Requirement Extraction").
    - Implement a side panel showing the "Current Requirement Baseline" that updates in real-time as agents extract data.
    - Add "Approval" buttons next to requirements in the side panel.
- **Iterative Chat**: Update `sendMessage` to handle multi-turn conversations and display specific "Clarification Questions" as highlighted call-outs.

## 6. Critical Files for Implementation
- `src/core/orchestrator/state.py` (The Shared Context)
- `agents/orchestrator.py` (The Coordinator logic)
- `main.py` (The session-based API)
- `static/script.js` (The interactive frontend)
- `src/agents/` (New agent implementations)
EOF`
