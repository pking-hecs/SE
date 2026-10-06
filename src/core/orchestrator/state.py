from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class AgentResponse:
    agent_name: str
    content: Any
    confidence: float = 1.0
    citations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class Requirement:
    req_id: str
    statement: str
    category: str = "Functional"  # Functional, Security, Privacy, Regulatory, Performance, etc.
    priority: str = "Medium"      # High, Medium, Low
    status: str = "draft"         # draft, validated, approved, rejected
    source: str = "stakeholder"
    justification: str = ""
    compliance_mapping: List[str] = field(default_factory=list)
    regulations: List[str] = field(default_factory=list)
    risk_level: str = "Medium"
    confidence_score: float = 0.90
    acceptance_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    approval_status: str = "pending"

    def __post_init__(self):
        if not self.regulations and self.compliance_mapping:
            self.regulations = list(self.compliance_mapping)
        elif not self.compliance_mapping and self.regulations:
            self.compliance_mapping = list(self.regulations)

class ProjectState:
    def __init__(self, project_id: str, user_prompt: str = ""):
        self.project_id = project_id
        self.initial_prompt = user_prompt
        self.stakeholder_role = "Business Analyst"
        self.domain = "Digital Banking"
        self.current_phase = "INTERVIEWING"  # INTERVIEWING, ANALYZING, DOCUMENTING, APPROVED
        self.requirements_baseline: Dict[str, Requirement] = {}
        self.chat_history: List[Dict[str, str]] = []
        self.audit_trail: List[Dict[str, Any]] = []
        self.sdlc_recommendation: Optional[str] = None
        self.sdlc_workflow: List[str] = []
        self.final_srs: Optional[str] = None
        self.rtm: Optional[str] = None
        self.risk_register: List[Dict[str, Any]] = []
        self.clarifications: List[str] = []
        self.conflicts: List[str] = []
        self.approved_baseline: bool = False
        self.interview_turn: int = 0
        self.answered_topics: List[str] = []
        self.created_at = datetime.now().isoformat()

    @property
    def requirements(self) -> Dict[str, Requirement]:
        return self.requirements_baseline

    @requirements.setter
    def requirements(self, value: Dict[str, Requirement]):
        self.requirements_baseline = value

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
            "initial_prompt": self.initial_prompt,
            "domain": self.domain,
            "stakeholder_role": self.stakeholder_role,
            "current_phase": self.current_phase,
            "requirements": {k: v.__dict__ for k, v in self.requirements_baseline.items()},
            "chat_history": self.chat_history,
            "audit_trail": self.audit_trail,
            "sdlc": self.sdlc_recommendation,
            "sdlc_workflow": self.sdlc_workflow,
            "srs": self.final_srs,
            "rtm": self.rtm,
            "risk_register": self.risk_register,
            "clarifications": self.clarifications,
            "conflicts": self.conflicts,
            "approved_baseline": self.approved_baseline,
            "interview_turn": self.interview_turn,
            "answered_topics": self.answered_topics,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectState":
        """Rebuild a usable session from a database snapshot."""
        state = cls(data.get("project_id", ""), data.get("initial_prompt", ""))
        for key in (
            "domain", "stakeholder_role", "current_phase", "chat_history",
            "audit_trail", "sdlc_workflow", "final_srs", "rtm", "risk_register",
            "clarifications", "conflicts", "approved_baseline", "interview_turn",
            "answered_topics", "created_at",
        ):
            snapshot_key = {"final_srs": "srs", "sdlc_recommendation": "sdlc"}.get(key, key)
            if snapshot_key in data:
                setattr(state, key, data[snapshot_key])

        state.sdlc_recommendation = data.get("sdlc")
        for req_id, req_data in (data.get("requirements") or {}).items():
            if not isinstance(req_data, dict):
                continue
            allowed = set(Requirement.__dataclass_fields__)
            values = {k: v for k, v in req_data.items() if k in allowed}
            values.setdefault("req_id", req_data.get("req_id") or req_id)
            try:
                state.requirements_baseline[req_id] = Requirement(**values)
            except TypeError:
                continue
        return state
