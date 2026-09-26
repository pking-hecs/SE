from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class Requirement:
    req_id: str
    statement: str
    category: str # Functional, Non-Functional, Security, etc.
    priority: str # High, Medium, Low
    status: str = "draft" # draft, validated, approved
    source: str = "stakeholder"
    justification: str = ""
    compliance_mapping: List[str] = field(default_factory=list)
    risk_level: str = "Unknown"
    approval_status: str = "pending"

class ProjectState:
    def __init__(self, project_id: str, user_prompt: str):
        self.project_id = project_id
        self.initial_prompt = user_prompt
        self.current_phase = "INTERVIEWING" # INTERVIEWING, ANALYZING, DOCUMENTING, APPROVED
        self.requirements_baseline: Dict[str, Requirement] = {}
        self.chat_history: List[Dict[str, str]] = []
        self.audit_trail: List[Dict[str, Any]] = []
        self.sdlc_recommendation: Optional[str] = None
        self.final_srs: Optional[str] = None
        self.created_at = datetime.now().isoformat()

    def add_requirement(self, req: Requirement):
        self.requirements_baseline[req.req_id] = req

    def update_phase(self, new_phase: str):
        self.current_phase = new_phase

    def log_event(self, agent: str, action: str, detail: str):
        self.audit_trail.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "detail": detail
        })

    def to_dict(self):
        return {
            "project_id": self.project_id,
            "current_phase": self.current_phase,
            "requirements": {k: v.__dict__ for k, v in self.requirements_baseline.items()},
            "chat_history": self.chat_history,
            "sdlc": self.sdlc_recommendation,
            "srs": self.final_srs
        }
