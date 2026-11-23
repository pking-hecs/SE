import sys
import re
import logging
from dotenv import load_dotenv

load_dotenv()

# Completely silence noisy HTTP loggers from printing URLs or internal server errors to terminal
for _log in ("httpx", "httpcore", "openai", "urllib3", "google", "uvicorn.access"):
    logging.getLogger(_log).setLevel(logging.WARNING)

class TerminalSanitizer:
    """Sanitizes terminal output so no provider/vendor/model names ever appear in the console."""
    def __init__(self, stream):
        self._stream = stream

    def write(self, s):
        if not s:
            return
        cleaned = re.sub(r"https?://\S+", "[endpoint]", s)
        # Neutralize all provider and model names
        scrubs = [
            (r"(?i)\bgsk_[A-Za-z0-9_-]+\b", "[auth-token]"),
            (r"(?i)\b(openai|groq|openrouter|anthropic|claude|deepseek|mistral|ollama|gemini)/[A-Za-z0-9_.-]+", "core-engine"),
            (r"(?i)\b(groq|openrouter|gemini|openai|anthropic|claude|mistral|deepseek|ollama)\b", "engine"),
            (r"(?i)\b(llama|qwen|gpt)[-_\w.]*\b", "engine"),
            (r"\bAI\b", "System"),
        ]
        for pat, repl in scrubs:
            cleaned = re.sub(pat, repl, cleaned)
        self._stream.write(cleaned)

    def flush(self):
        self._stream.flush()

    def isatty(self):
        return getattr(self._stream, "isatty", lambda: False)()

    def fileno(self):
        return self._stream.fileno()

sys.stdout = TerminalSanitizer(sys.stdout)
sys.stderr = TerminalSanitizer(sys.stderr)

import warnings
warnings.filterwarnings("ignore")
from fastapi import FastAPI, HTTPException, Response, UploadFile, File, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
import uvicorn
import uuid
import io
from datetime import datetime
from src.core.orchestrator.state import ProjectState, Requirement
from agents.orchestrator import AgentOrchestrator
import db as _db
import auth as _auth
import cache as _cache

app = FastAPI(title="FinReq Platform", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = AgentOrchestrator()
sessions: Dict[str, ProjectState] = {}


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Authenticate a request and ensure its bearer token still matches a user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    claims = _auth.verify_access_token(authorization[7:])
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    user = _db.get_user_by_email(claims["email"])
    if not user or str(user["id"]) != claims["sub"] or user["role"] != claims["role"]:
        raise HTTPException(status_code=401, detail="User session is no longer valid")
    return user


def require_permission(permission: str):
    async def guard(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if not _auth.has_permission(user["role"], permission):
            raise HTTPException(status_code=403, detail=f"Permission required: {permission}")
        return user
    return guard

@app.on_event("startup")
async def _startup():
    _db.init_db()

class SessionStartRequest(BaseModel):
    prompt: str
    domain: Optional[str] = "Digital Banking & Payment Systems"
    stakeholder_role: Optional[str] = "Business Analyst"

class ChatRequest(BaseModel):
    project_id: str
    message: str
    stakeholder_role: Optional[str] = None

class ApprovalRequest(BaseModel):
    project_id: str
    section: str
    content: str = ""
    status: str  # "approved", "rejected", "modified"
    comments: str = ""
    req_id: Optional[str] = None
    approver_role: Optional[str] = "APPROVER"
    approver_name: Optional[str] = "Lead Architect"

class ReqUpdateRequest(BaseModel):
    project_id: str
    req_id: str
    statement: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    comments: Optional[str] = None

class ReqRemoveRequest(BaseModel):
    project_id: str
    req_id: str
    reason: Optional[str] = "Removed by stakeholder"

class SaveChatRequest(BaseModel):
    project_id: str
    title: Optional[str] = None
    messages: List[Dict[str, Any]] = []  # [{role, html, created_at}]

class RenameSessionRequest(BaseModel):
    title: str

class LoginRequest(BaseModel):
    email: str
    password: str

class MFAVerifyRequest(BaseModel):
    email: str
    code: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: Optional[str] = "STAKEHOLDER"

class ConflictResolveRequest(BaseModel):
    project_id: str
    conflict_id: Optional[int] = None
    req_id_1: Optional[str] = None
    req_id_2: Optional[str] = None
    resolution: str

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "FinReq Platform",
        "agents_count": 13,
        "domains_supported": 8,
        "version": "2.0.0",
        "database": "PostgreSQL" if _db._use_postgres else "SQLite (fallback)"
    }

@app.get("/api/presets")
async def get_presets():
    return {
        "domains": [
            {
                "id": "digital_banking",
                "name": "Digital Banking & Mobile Payments",
                "sample_prompt": "A modern mobile digital banking platform supporting real-time P2P transfers, biometric authentication, and sub-second account balance inquiries."
            },
            {
                "id": "loan_origination",
                "name": "Loan Origination & Credit Assessment",
                "sample_prompt": "An automated loan origination and SME credit risk assessment platform with automated credit bureau checks and digital loan contract disbursement."
            },
            {
                "id": "payment_processing",
                "name": "Payment Processing & ISO 20022 Gateway",
                "sample_prompt": "A high-throughput cross-border payment gateway with multi-currency FX settlement, ISO 20022 message compliance, and dual-authorization for transfers >$10k."
            },
            {
                "id": "fraud_detection",
                "name": "Fraud Detection & Real-Time AML Monitoring",
                "sample_prompt": "A real-time fraud monitoring engine analyzing card transactions with sub-100ms latency, automatic Suspicious Activity Report (SAR) generation, and OFAC sanction screening."
            },
            {
                "id": "kyc_onboarding",
                "name": "Customer Onboarding & Biometric KYC",
                "sample_prompt": "Digital customer onboarding platform featuring biometric facial liveness verification, government ID OCR document analysis, and PEP beneficial ownership verification."
            },
            {
                "id": "insurance_wealth",
                "name": "Insurance & Digital Wealth Management",
                "sample_prompt": "Robo-advisory and investment platform with automated portfolio risk rebalancing, investor suitability questionnaires, and MiFID II compliance."
            },
            {
                "id": "regulatory_reporting",
                "name": "Regulatory Reporting & Basel III/IV",
                "sample_prompt": "Automated regulatory reporting system calculating Basel III/IV capital adequacy ratios, liquidity coverage ratio (LCR), and generating supervisory reports."
            },
            {
                "id": "financial_analytics",
                "name": "Financial Data Analytics & Lakehouse",
                "sample_prompt": "Enterprise financial data analytics repository with role-based access control, cryptographic field-level encryption, and automated audit trails."
            }
        ],
        "stakeholder_roles": [
            "Business Analyst",
            "Compliance Officer",
            "Information-Security Team",
            "Product Owner",
            "Software Architect",
            "Risk-Management Team",
            "Auditor",
            "Customer"
        ],
        "sdlc_models": [
            "Agile–DevSecOps hybrid",
            "V-Model",
            "Spiral",
            "DevSecOps",
            "Agile",
            "Waterfall"
        ]
    }

@app.post("/session/start")
async def start_session(request: SessionStartRequest, user: Dict[str, Any] = Depends(require_permission("requirements:write"))):
    try:
        project_id = f"PROJ_{uuid.uuid4().hex[:10].upper()}"
        state = ProjectState(project_id, request.prompt)
        state.domain = request.domain or "Digital Banking & Payment Systems"
        state.stakeholder_role = request.stakeholder_role or "Business Analyst"
        sessions[project_id] = state

        # Save session to DB immediately so foreign keys exist for agent runs and SDLC records
        _db.save_session(
            session_id=project_id,
            title=f"{state.domain} – {datetime.now().strftime('%d %b %Y %H:%M')}",
            domain=state.domain or "",
            role=state.stakeholder_role or "",
            snapshot=state.to_dict(),
            messages=[],
        )

        result = await orchestrator.process_request_async(
            state,
            request.prompt,
            domain=request.domain,
            stakeholder_role=request.stakeholder_role
        )
        # Update session with complete snapshot
        _db.save_session(
            session_id=project_id,
            title=f"{state.domain} – {datetime.now().strftime('%d %b %Y %H:%M')}",
            domain=state.domain or "",
            role=state.stakeholder_role or "",
            snapshot=state.to_dict(),
            messages=[],
        )

        # Persist structured data to PostgreSQL tables
        _db.persist_requirements(project_id, {k: v.__dict__ for k, v in state.requirements_baseline.items()})
        _db.persist_compliance(project_id, result.get("compliance_mappings", []))
        _db.persist_risks(project_id, state.risk_register)
        for event in state.audit_trail:
            _db.log_audit(project_id, event.get("agent", ""), event.get("action", ""), event.get("detail", ""))

        return {
            "status": "success",
            "project_id": project_id,
            "domain": state.domain,
            "stakeholder_role": state.stakeholder_role,
            "initial_analysis": result,
            "current_phase": state.current_phase,
            "requirements": {k: v.__dict__ for k, v in state.requirements_baseline.items()},
            "audit_trail": state.audit_trail
        }
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "resourceexhausted" in err.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit reached. Please wait 30-60 seconds and try again. "
                       "The free Gemini API quota allows ~15 requests/minute."
            )
        if "503" in err or "unavailable" in err.lower():
            raise HTTPException(
                status_code=503,
                detail="Gemini AI service is temporarily overloaded. Please retry in a few seconds."
            )
        raise HTTPException(status_code=500, detail=err)

@app.post("/session/chat")
async def session_chat(request: ChatRequest, user: Dict[str, Any] = Depends(require_permission("conversations:participate"))):
    if request.project_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[request.project_id]
    if request.stakeholder_role:
        state.stakeholder_role = request.stakeholder_role

    # Snapshot clarifications BEFORE processing so we can detect resolved ones
    clarifications_before = list(getattr(state, 'clarifications', []))

    try:
        response = await orchestrator.handle_interaction(state, request.message)

        # Compute which clarifications were resolved by this message
        clarifications_after = list(getattr(state, 'clarifications', []))
        resolved_count = max(0, len(clarifications_before) - len(clarifications_after))

        # Persist updated requirements and audit to PostgreSQL
        _db.persist_requirements(request.project_id, {k: v.__dict__ for k, v in state.requirements_baseline.items()})
        for event in state.audit_trail[-3:]:
            _db.log_audit(request.project_id, event.get("agent", ""), event.get("action", ""), event.get("detail", ""))

        return {
            "status": "success",
            "response": response,
            "current_phase": state.current_phase,
            "requirements": {k: v.__dict__ for k, v in state.requirements_baseline.items()},
            "audit_trail": state.audit_trail,
            # Always send updated clarifications/conflicts so frontend can refresh Quality & Gaps tab
            "clarifications": clarifications_after,
            "conflicts": list(getattr(state, 'conflicts', [])),
            "resolved_clarifications_count": resolved_count,
            "pii_masked_items": getattr(state, "latest_masked_items", []),
            "safe_message": getattr(state, "latest_safe_message", request.message),
        }
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit reached. Please wait 30-60 seconds and try again."
            )
        raise HTTPException(status_code=500, detail=err)

@app.post("/session/approve")
async def approve_section(request: ApprovalRequest, user: Dict[str, Any] = Depends(get_current_user)):
    if request.project_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[request.project_id]
    if request.status not in {"approved", "rejected", "modified"}:
        raise HTTPException(status_code=422, detail="status must be approved, rejected, or modified")

    # Enforce RBAC permission checks
    approver_role = user["role"]
    approver_name = user.get("full_name") or user["email"]
    target_section = request.section or "requirements"
    if not _auth.can_approve(approver_role, target_section):
        state.log_event("Human-Approval Agent", "Permission Denied", f"Role '{approver_role}' does not possess sign-off authority for section '{target_section}'.")
        raise HTTPException(
            status_code=403,
            detail=f"Permission Denied: Role '{approver_role}' is not authorized to approve '{target_section}'. Approver role required."
        )

    def find_req_key(req_id: str) -> Optional[str]:
        if not req_id:
            return None
        if req_id in state.requirements_baseline:
            return req_id
        for k, v in state.requirements_baseline.items():
            if (k.lower() == req_id.lower() or 
                getattr(v, "req_id", "").lower() == req_id.lower() or 
                getattr(v, "id", "").lower() == req_id.lower()):
                return k
        return None

    if request.req_id:
        target_k = find_req_key(request.req_id)
        if target_k:
            req = state.requirements_baseline[target_k]
            req.approval_status = request.status
            req.status = "approved" if request.status == "approved" else "rejected"
            state.log_event("Human-Approval Agent", "Requirement Decision", f"Req {target_k} marked as {request.status} by {approver_name} ({approver_role}). Note: {request.comments or 'Stakeholder sign-off'}")
            _db.persist_requirements(request.project_id, {k: v.__dict__ for k, v in state.requirements_baseline.items()})
            _db.log_audit(request.project_id, "Human-Approval Agent", "Requirement Decision", f"Req {target_k} marked as {request.status} by {request.approver_name} ({approver_role})")
            _db.record_approval(request.project_id, "requirement", target_k, approver_name, approver_role, request.status, request.comments or "")
            _cache.invalidate_cached_state(request.project_id)
            return {
                "status": "success",
                "message": f"Requirement {target_k} marked {request.status} by {approver_role}",
                "requirements": {k: v.__dict__ for k, v in state.requirements_baseline.items()},
                "audit_trail": state.audit_trail
            }

    valid_sections = {"requirements", "compliance", "sdlc", "srs", "risk"}
    if request.section not in valid_sections:
        raise HTTPException(status_code=422, detail=f"section must be one of: {', '.join(sorted(valid_sections))}")

    if request.section == "requirements":
        for requirement in state.requirements_baseline.values():
            requirement.approval_status = request.status
            requirement.status = "approved" if request.status == "approved" else "draft"
        state.approved_baseline = (request.status == "approved")
        if request.status == "approved":
            state.update_phase("APPROVED")
    elif request.section == "srs" and request.status == "approved":
        state.approved_baseline = True
        state.update_phase("APPROVED")

    state.log_event("Human-Approval Agent", "Section Approval", f"Section '{request.section}' marked as '{request.status}' by {approver_name} ({approver_role}). Remarks: {request.comments or 'None'}")
    _db.persist_requirements(request.project_id, {k: v.__dict__ for k, v in state.requirements_baseline.items()})
    _db.log_audit(request.project_id, "Human-Approval Agent", "Section Approval", f"Section '{request.section}' marked as '{request.status}' by {request.approver_name} ({approver_role})")
    _db.record_approval(request.project_id, "section", request.section, approver_name, approver_role, request.status, request.comments or "")
    _cache.invalidate_cached_state(request.project_id)
    return {
        "status": "success",
        "message": f"Section {request.section} marked {request.status} by {approver_role}",
        "requirements": {k: v.__dict__ for k, v in state.requirements_baseline.items()},
        "audit_trail": state.audit_trail
    }

@app.post("/session/requirement/remove")
@app.delete("/session/requirement/remove")
async def remove_requirement(request: ReqRemoveRequest, user: Dict[str, Any] = Depends(require_permission("requirements:delete"))):
    if request.project_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    state = sessions[request.project_id]

    target_k = None
    if request.req_id in state.requirements_baseline:
        target_k = request.req_id
    else:
        for k, v in state.requirements_baseline.items():
            if (k.lower() == request.req_id.lower() or 
                getattr(v, "req_id", "").lower() == request.req_id.lower() or 
                getattr(v, "id", "").lower() == request.req_id.lower()):
                target_k = k
                break

    if not target_k:
        raise HTTPException(status_code=404, detail=f"Requirement ID '{request.req_id}' not found")

    removed_req = state.requirements_baseline.pop(target_k)
    stmt_preview = getattr(removed_req, "statement", "")[:60]
    state.log_event(
        "Human-Approval Agent",
        "Requirement Removal",
        f"Requirement {target_k} removed from baseline by stakeholder. Statement: '{stmt_preview}...'. Reason: {request.reason or 'User action'}"
    )
    _db.delete_requirement(request.project_id, target_k)
    _db.log_audit(request.project_id, "Human-Approval Agent", "Requirement Removal", f"Removed {target_k}: {request.reason or 'User action'}")
    _cache.invalidate_cached_state(request.project_id)
    return {
        "status": "success",
        "message": f"Requirement {request.req_id} removed successfully",
        "remaining_count": len(state.requirements_baseline),
        "requirements": {k: v.__dict__ for k, v in state.requirements_baseline.items()},
        "audit_trail": state.audit_trail
    }

@app.post("/session/requirement/update")
async def update_requirement(request: ReqUpdateRequest, user: Dict[str, Any] = Depends(require_permission("requirements:modify"))):
    if request.project_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    state = sessions[request.project_id]
    if request.req_id not in state.requirements_baseline:
        raise HTTPException(status_code=404, detail="Requirement ID not found")

    req = state.requirements_baseline[request.req_id]
    old_stmt = req.statement
    if request.statement:
        req.statement = request.statement
    if request.priority:
        req.priority = request.priority
    if request.status:
        req.status = request.status
        req.approval_status = request.status

    state.log_event("Human-Approval Agent", "Requirement Modification", f"Modified {request.req_id}: '{old_stmt}' -> '{req.statement}'. Comments: {request.comments or ''}")
    _db.persist_requirements(request.project_id, {k: v.__dict__ for k, v in state.requirements_baseline.items()})
    _db.log_audit(request.project_id, "Human-Approval Agent", "Requirement Modification", f"Modified {request.req_id}")
    return {"status": "success", "requirement": req.__dict__}

@app.get("/session/{project_id}/requirements")
async def get_persisted_requirements(project_id: str):
    """Return requirements from PostgreSQL (survives server restarts)."""
    reqs = _db.get_requirements(project_id)
    if not reqs:
        raise HTTPException(status_code=404, detail="No persisted requirements found for this project")
    return {"status": "success", "count": len(reqs), "requirements": reqs}

@app.get("/session/{project_id}/audit")
async def get_persisted_audit(project_id: str):
    """Return the immutable audit trail from PostgreSQL."""
    trail = _db.get_audit_trail(project_id)
    return {"status": "success", "count": len(trail), "audit_trail": trail}

@app.get("/session/{project_id}")
async def get_session(project_id: str):
    state = sessions.get(project_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return state.to_dict()

@app.get("/session/{project_id}/export/{artifact}")
async def export_artifact(project_id: str, artifact: str):
    state = sessions.get(project_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if artifact == "srs":
        content = state.final_srs or "# SRS Not Yet Generated"
        filename = f"{project_id}_SRS.md"
    elif artifact == "rtm":
        content = state.rtm or "# RTM Not Yet Generated"
        filename = f"{project_id}_RTM.md"
    elif artifact == "user_stories":
        reqs = list(state.requirements_baseline.values())
        req_dicts = []
        for r in reqs:
            d = dict(r.__dict__)
            d["id"] = r.req_id
            d["req_id"] = r.req_id
            req_dicts.append(d)
        stories = orchestrator.doc_agent.generate_user_stories(req_dicts)
        content = f"# User Stories & Acceptance Criteria ({state.domain})\n\n"
        for s in stories:
            content += f"### Story for {s['req_id']}\n- **User Story**: {s['story']}\n- **Acceptance Criteria**: {s['acceptance_criteria']}\n\n"
        filename = f"{project_id}_User_Stories.md"
    elif artifact == "risk_register":
        content = f"# Threat & Risk Register ({state.domain})\n\n"
        content += "| Risk ID | Category | Description | Likelihood | Impact | Score | Mitigation |\n|---|---|---|---|---|---|---|\n"
        for k in state.risk_register:
            content += f"| {k['id']} | {k['category']} | {k['description']} | {k['likelihood']} | {k['impact']} | {k['score']}/10 | {k['mitigation']} |\n"
        filename = f"{project_id}_Risk_Register.md"
    else:
        raise HTTPException(status_code=400, detail="Unknown artifact type. Supported: srs, rtm, user_stories, risk_register")

    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ---------------------------------------------------------------------------
# Chat History API
# ---------------------------------------------------------------------------

@app.get("/history")
async def list_history():
    """Return all saved chat sessions (no messages, just metadata)."""
    return {"status": "success", "sessions": _db.list_sessions()}


@app.get("/history/{session_id}")
async def get_history_session(session_id: str):
    """Return a saved session including its messages and all requirements/governance data."""
    data = _db.get_session(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Saved session not found")
    
    # Restore the session state in memory on the server so follow-up interactions work
    snapshot = data.get("snapshot") or {}
    if snapshot:
        snapshot.setdefault("project_id", session_id)
        sessions[session_id] = ProjectState.from_dict(snapshot)

    # Ensure in-memory state has all current requirements from DB
    db_reqs = _db.get_requirements(session_id)
    if session_id in sessions and db_reqs:
        state = sessions[session_id]
        for r in db_reqs:
            rid = r.get("req_id") or r.get("id")
            if rid and rid not in state.requirements_baseline:
                try:
                    allowed = set(Requirement.__dataclass_fields__)
                    values = {k: v for k, v in r.items() if k in allowed}
                    values.setdefault("req_id", rid)
                    state.requirements_baseline[rid] = Requirement(**values)
                except Exception:
                    pass

    # Reconstruct requirements list if DB is empty but snapshot had requirements
    reqs = db_reqs
    if not reqs and snapshot.get("requirements"):
        if isinstance(snapshot["requirements"], dict):
            reqs = list(snapshot["requirements"].values())
        elif isinstance(snapshot["requirements"], list):
            reqs = snapshot["requirements"]

    from fastapi.encoders import jsonable_encoder
    full_session = {
        **data,
        "requirements": reqs,
        "compliance_mappings": _db.get_compliance(session_id),
        "risks": _db.get_risks(session_id) or snapshot.get("risk_register", []),
        "conflicts": _db.get_conflicts(session_id) or snapshot.get("conflicts", []),
        "audit_logs": _db.get_audit_logs(session_id) or snapshot.get("audit_trail", []),
    }
    return {"status": "success", "session": jsonable_encoder(full_session)}


@app.post("/history/save")
async def save_chat(request: SaveChatRequest):
    """Persist the current in-memory session to the database."""
    state = sessions.get(request.project_id)
    if state is None:
        existing = _db.get_session(request.project_id)
        if existing and existing.get("snapshot"):
            snapshot = existing["snapshot"]
            snapshot.setdefault("project_id", request.project_id)
            state = ProjectState.from_dict(snapshot)
            sessions[request.project_id] = state
        else:
            raise HTTPException(status_code=404, detail="Active session not found")

    existing = _db.get_session(request.project_id)
    title = request.title or (existing or {}).get("title") or f"{state.domain or 'Project'} – {datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC"
    snapshot = {}
    try:
        snapshot = state.to_dict()
    except Exception:
        pass

    _db.save_session(
        session_id=request.project_id,
        title=title,
        domain=state.domain or "",
        role=state.stakeholder_role or "",
        snapshot=snapshot,
        messages=request.messages,
    )
    return {"status": "success", "message": "Session saved", "session_id": request.project_id, "title": title}


@app.patch("/history/{session_id}")
async def rename_history_session(session_id: str, request: RenameSessionRequest):
    """Rename a saved session."""
    found = _db.update_session_title(session_id, request.title)
    if not found:
        raise HTTPException(status_code=404, detail="Saved session not found")
    return {"status": "success", "message": "Session renamed", "title": request.title}


@app.delete("/history/{session_id}")
async def delete_history_session(session_id: str):
    """Permanently delete a saved session."""
    found = _db.delete_session(session_id)
    if not found:
        raise HTTPException(status_code=404, detail="Saved session not found")
    return {"status": "success", "message": "Session deleted"}


# ---------------------------------------------------------------------------
# Authentication & RBAC & MFA API
# ---------------------------------------------------------------------------

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    """Authenticate user with PBKDF2 hash check, returns role and triggers MFA if enabled."""
    try:
        user = _db.get_user_by_email(req.email)
        if not user or not _auth.verify_password(req.password, user["password_hash"], user["salt"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        uid, email, full_name, role = user["id"], user["email"], user["full_name"], user["role"]

        if user["mfa_enabled"]:
            return {"status": "mfa_required", "email": email,
                    "message": "Enter 6-digit TOTP verification code from your authenticator app (or demo '123456')"}

        return {"status": "success", "token": _auth.create_access_token(uid, email, role),
                "user": {"id": uid, "email": email, "name": full_name, "role": role,
                         "permissions": _auth.ROLES_PERMISSIONS.get(role, [])}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/mfa/verify")
async def verify_mfa(req: MFAVerifyRequest):
    """Verify MFA TOTP code and issue authorized session token."""
    try:
        user = _db.get_user_by_email(req.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not _auth.verify_totp(user["mfa_secret"], req.code):
            raise HTTPException(status_code=401, detail="Invalid MFA code. Please check your authenticator.")

        return {"status": "success", "token": _auth.create_access_token(user["id"], user["email"], user["role"]),
                "user": {"id": user["id"], "email": user["email"], "name": user["full_name"], "role": user["role"],
                         "permissions": _auth.ROLES_PERMISSIONS.get(user["role"], [])}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    """Create new platform user with specified role and generated MFA secret."""
    try:
        h, s = _auth.hash_password(req.password)
        mfa_sec = _auth.generate_mfa_secret()
        if req.role.upper() not in _auth.ROLES_PERMISSIONS:
            raise HTTPException(status_code=422, detail="Unsupported role")
        uid = _db.create_user(req.email, h, s, req.full_name, req.role, mfa_sec)
        return {"status": "success", "user_id": uid, "email": req.email, "role": req.role}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {e}")


@app.get("/api/auth/users")
async def list_auth_users():
    """List demo users for rapid role-switching in the UI."""
    try:
        return {"status": "success", "users": _db.list_users()}
    except Exception as e:
        return {"status": "error", "users": []}


# ---------------------------------------------------------------------------
# Document Upload & Ingestion API
# ---------------------------------------------------------------------------

@app.post("/api/documents/upload")
async def upload_document(
    project_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(require_permission("documents:upload")),
):
    """
    Accepts PDF, TXT, MD, DOCX. Extracts text, chunks, computes pgvector embeddings,
    and indexes into knowledge_documents and documents tables.
    """
    try:
        content_bytes = await file.read()
        filename = file.filename or "uploaded_doc.txt"
        text_content = ""

        if filename.lower().endswith(".docx"):
            import zipfile, xml.etree.ElementTree as ET
            with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
                xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            text_content = " ".join(node.text for node in tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if node.text)
        else:
            text_content = content_bytes.decode("utf-8", errors="ignore")

        proj_id = project_id or f"PROJ_DOC_{uuid.uuid4().hex[:6].upper()}"
        doc_id = _db.record_document(
            session_id=proj_id,
            filename=filename,
            file_type=file.content_type or "text/plain",
            file_path=f"uploads/{filename}",
            file_size=len(content_bytes),
            status="PROCESSED"
        )

        # Chunk into knowledge_documents with pgvector embeddings when PostgreSQL is available.
        chunks = [text_content[i:i+800] for i in range(0, len(text_content), 700)]
        for idx, chunk in enumerate(chunks[:10]):
            if len(chunk.strip()) > 30:
                emb = _db.generate_embedding(chunk)
                try:
                    if not _db._use_postgres:
                        continue
                    conn = _db._get_pg_conn()
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO knowledge_documents (title, source, jurisdiction, effective_date, version, applicability, category, content, embedding)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """, (
                            f"{filename} [Chunk {idx+1}]",
                            filename,
                            "Uploaded Project Document",
                            datetime.now().strftime("%Y-%m-%d"),
                            "1.0",
                            "Project-Specific",
                            "Uploaded Documentation",
                            chunk,
                            str(emb)
                        ))
                    conn.commit()
                except Exception:
                    pass

        return {
            "status": "success",
            "document_id": doc_id,
            "filename": filename,
            "characters_extracted": len(text_content),
            "chunks_indexed": len(chunks),
            "preview": text_content[:400] + ("..." if len(text_content) > 400 else "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {e}")


# ---------------------------------------------------------------------------
# Admin & Monitoring Metrics API
# ---------------------------------------------------------------------------

@app.get("/api/admin/metrics")
async def admin_metrics():
    """Return platform metrics, agent telemetry, compliance gaps, and Redis status."""
    metrics = _db.get_monitoring_metrics()
    cache_info = _cache.get_cache_stats()
    metrics["cache"] = cache_info
    return {"status": "success", "metrics": metrics}


# ---------------------------------------------------------------------------
# Conflict Resolution API
# ---------------------------------------------------------------------------

@app.post("/api/conflicts/resolve")
async def resolve_conflict(req: ConflictResolveRequest, user: Dict[str, Any] = Depends(require_permission("requirements:approve"))):
    """Record human resolution of conflicting or duplicate requirements."""
    try:
        _db.resolve_conflict(req.project_id, req.conflict_id, req.req_id_1 or "", req.req_id_2 or "", req.resolution)
        _db.log_audit(req.project_id, "Conflict Agent", "Conflict Resolved", f"Resolved conflict: {req.resolution}")
        return {"status": "success", "message": "Conflict resolved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve conflict: {e}")


# ---------------------------------------------------------------------------
# Requirements Traceability Matrix (RTM) API
# ---------------------------------------------------------------------------

@app.get("/session/{project_id}/rtm_matrix")
async def get_rtm_matrix(project_id: str):
    """
    Returns full end-to-end traceability matrix:
    Stakeholder Statement -> Requirement -> Regulation -> Control -> Test -> Approval
    """
    reqs = _db.get_requirements(project_id)
    compliance = _db.get_compliance(project_id)

    comp_map = {c["req_id"]: c for c in compliance}
    matrix = []
    for r in reqs:
        c = comp_map.get(r["req_id"], {})
        test_crit = "Automated Integration Test"
        if isinstance(r.get("acceptance_criteria"), list) and r.get("acceptance_criteria"):
            test_crit = str(r["acceptance_criteria"][0])
        elif isinstance(r.get("acceptance_criteria"), str):
            test_crit = r["acceptance_criteria"]

        matrix.append({
            "req_id": r["req_id"],
            "category": r["category"],
            "statement": r["statement"],
            "source_stakeholder": r.get("source", "Business Analyst"),
            "regulation": c.get("citation", "ISO-27001"),
            "control": c.get("control_id", "A.12.1.1"),
            "test_scenario": test_crit,
            "approval_status": r.get("approval_status", "pending")
        })
    return {"status": "success", "count": len(matrix), "matrix": matrix}


app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
