from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.orchestrator import AgentOrchestrator
import uvicorn
import os
import json
from datetime import datetime
from typing import Dict
from src.core.orchestrator.state import ProjectState

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = AgentOrchestrator()

# In-memory session store
sessions: Dict[str, ProjectState] = {}

class SessionStartRequest(BaseModel):
    prompt: str

class ChatRequest(BaseModel):
    project_id: str
    message: str

class ApprovalRequest(BaseModel):
    project_id: str
    section: str
    content: str
    status: str # "approved", "rejected", "modified"
    comments: str = ""

@app.post("/session/start")
async def start_session(request: SessionStartRequest):
    try:
        project_id = f"PROJ_{int(datetime.now().timestamp())}"
        state = ProjectState(project_id, request.prompt)
        sessions[project_id] = state

        # Initial analysis to seed the requirements
        result = await orchestrator.process_request_async(state, request.prompt)

        return {
            "status": "success",
            "project_id": project_id,
            "initial_analysis": result,
            "current_phase": state.current_phase
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/chat")
async def session_chat(request: ChatRequest):
    if request.project_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[request.project_id]
    try:
        # Interaction loop: Agent processes message and updates state
        response = await orchestrator.handle_interaction(state, request.message)

        return {
            "status": "success",
            "response": response,
            "current_phase": state.current_phase,
            "requirements": state.requirements_baseline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/approve")
async def approve_section(request: ApprovalRequest):
    if request.project_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[request.project_id]
    state.log_event("Human-Approval Agent", "Approval", f"Section {request.section} marked as {request.status}. Comments: {request.comments}")

    return {"status": "success", "message": f"Section {request.section} {request.status}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
