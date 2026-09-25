import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Requirement:
    req_id: str
    statement: str
    category: str
    source: str
    justification: str = ""
    priority: str = "Medium"
    dependencies: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    regulations: List[str] = field(default_factory=list)
    risk_level: str = "Low"
    confidence_score: float = 0.0
    status: str = "Draft"

@dataclass
class AgentResponse:
    agent_name: str
    content: Any
    confidence: float
    citations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ProjectState:
    """Maintains the shared context across the agentic workflow."""
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.requirements: Dict[str, Requirement] = {}
        self.stakeholder_inputs: List[Dict[str, Any]] = []
        self.compliance_mappings: List[Dict[str, Any]] = []
        self.sdlc_factors: Dict[str, Any] = {}
        self.approved_baseline: bool = False
        self.history: List[AgentResponse] = []

    def add_requirement(self, req: Requirement):
        self.requirements[req.req_id] = req

    def log_agent_action(self, response: AgentResponse):
        self.history.append(response)
