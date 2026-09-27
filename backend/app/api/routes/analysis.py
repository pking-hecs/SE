from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from backend.app.core.orchestrator.state import ProjectState, RequirementSchema, AnalysisFinding
from backend.app.core.orchestrator.coordinator import coordinator_agent
from backend.app.core.auth import auth_handler
from fastapi.security import OAuth2PasswordBearer
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

router = APIRouter(prefix="/projects", tags=["Requirement Engineering"])

class ChatMessage(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    requirements: List[RequirementSchema]
    findings: List[AnalysisFinding]

@router.post("/{project_id}/chat", response_model=AnalysisResponse)
async def project_chat(project_id: int, message: ChatMessage, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth_handler.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Initialize state (In real use, load from Redis/DB)
    state = ProjectState(project_id=project_id)

    # Process via Coordinator
    updated_state = await coordinator_agent.process_inputs(state, message.text)

    return AnalysisResponse(
        requirements=updated_state.requirements,
        findings=updated_state.findings
    )
