from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from backend.app.core.auth import auth_handler
from fastapi.security import OAuth2PasswordBearer
from backend.app.models.schema import Requirement, ReqStatus, Base
from backend.app.agents.documentation_agent import doc_agent
from backend.app.core.sdlc_engine.engine import sdlc_engine
from backend.app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class ApprovalRequest(BaseModel):
    status: ReqStatus

class SdlcChars(BaseModel):
    stability: float
    criticality: float
    risk: float
    complexity: float
    change_freq: float

router = APIRouter(prefix="/projects", tags=["Approvals & Artifacts"])

@router.patch("/requirements/{req_id}/approve", response_model=None)
async def approve_requirement(req_id: int, request: ApprovalRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth_handler.decode_token(token)
    if not payload or payload["role"] not in ["APPROVER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions to approve")

    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    req.status = request.status
    db.commit()
    return {"status": "success", "new_status": req.status}

@router.post("/{project_id}/sdlc/analyze")
async def analyze_sdlc(project_id: int, chars: SdlcChars, token: str = Depends(oauth2_scheme)):
    payload = auth_handler.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return await sdlc_engine.analyze(chars.dict())

@router.get("/{project_id}/artifacts/srs")
async def generate_srs(project_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth_handler.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # In real use, fetch project name and approved requirements from DB
    # For now, using a mock a list of approved requirements
    from backend.app.core.orchestrator.state import RequirementSchema
    mock_reqs = [
        RequirementSchema(requirement_id="FR-001", statement="System must support MFA", categories=["SECURITY"], priority="HIGH", source="Admin", business_justification="Compliance", approval_status=ReqStatus.APPROVED),
    ]

    return {"content": await doc_agent.generate_srs("Demo Project", mock_reqs)}
