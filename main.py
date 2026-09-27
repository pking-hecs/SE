import warnings
warnings.filterwarnings("ignore")
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
import uvicorn
import uuid
from datetime import datetime
from src.core.orchestrator.state import ProjectState, Requirement
from agents.orchestrator import AgentOrchestrator

app = FastAPI(title="FinReq AI Platform", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = AgentOrchestrator()
sessions: Dict[str, ProjectState] = {}

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

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "FinReq AI Platform",
        "agents_count": 13,
        "domains_supported": 8,
        "version": "2.0.0"
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
async def start_session(request: SessionStartRequest):
    try:
        project_id = f"PROJ_{uuid.uuid4().hex[:10].upper()}"
        state = ProjectState(project_id, request.prompt)
        state.domain = request.domain or "Digital Banking & Payment Systems"
        state.stakeholder_role = request.stakeholder_role or "Business Analyst"
        sessions[project_id] = state

        result = await orchestrator.process_request_async(
            state,
            request.prompt,
            domain=request.domain,
            stakeholder_role=request.stakeholder_role
        )

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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/chat")
async def session_chat(request: ChatRequest):
    if request.project_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[request.project_id]
    if request.stakeholder_role:
        state.stakeholder_role = request.stakeholder_role
    try:
        response = await orchestrator.handle_interaction(state, request.message)
        return {
            "status": "success",
            "response": response,
            "current_phase": state.current_phase,
            "requirements": {k: v.__dict__ for k, v in state.requirements_baseline.items()},
            "audit_trail": state.audit_trail
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/approve")
async def approve_section(request: ApprovalRequest):
    if request.project_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[request.project_id]
    if request.status not in {"approved", "rejected", "modified"}:
        raise HTTPException(status_code=422, detail="status must be approved, rejected, or modified")

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
            state.log_event("Human-Approval Agent", "Requirement Decision", f"Req {target_k} marked as {request.status}. Note: {request.comments or 'Stakeholder sign-off'}")
            return {
                "status": "success",
                "message": f"Requirement {target_k} marked {request.status}",
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

    state.log_event("Human-Approval Agent", "Section Approval", f"Section '{request.section}' marked as '{request.status}'. Remarks: {request.comments or 'None'}")
    return {
        "status": "success",
        "message": f"Section {request.section} marked {request.status}",
        "requirements": {k: v.__dict__ for k, v in state.requirements_baseline.items()},
        "audit_trail": state.audit_trail
    }

@app.post("/session/requirement/remove")
@app.delete("/session/requirement/remove")
async def remove_requirement(request: ReqRemoveRequest):
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
    return {
        "status": "success",
        "message": f"Requirement {request.req_id} removed successfully",
        "remaining_count": len(state.requirements_baseline),
        "requirements": {k: v.__dict__ for k, v in state.requirements_baseline.items()},
        "audit_trail": state.audit_trail
    }

@app.post("/session/requirement/update")
async def update_requirement(request: ReqUpdateRequest):
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
    return {"status": "success", "requirement": req.__dict__}

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

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
