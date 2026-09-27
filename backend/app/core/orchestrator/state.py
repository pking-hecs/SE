from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class ReqStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ReqCategory(str, Enum):
    BUSINESS = "BUSINESS"
    FUNCTIONAL = "FUNCTIONAL"
    SECURITY = "SECURITY"
    PRIVACY = "PRIVACY"
    REGULATORY = "REGULATORY"
    PERFORMANCE = "PERFORMANCE"
    AVAILABILITY = "AVAILABILITY"
    RELIABILITY = "RELIABILITY"
    USABILITY = "USABILITY"
    DATA_MANAGEMENT = "DATA_MANAGEMENT"
    INTEGRATION = "INTEGRATION"
    AUDIT_REPORTING = "AUDIT_REPORTING"
    OPERATIONS = "OPERATIONS"

class RequirementSchema(BaseModel):
    requirement_id: str = Field(..., description="Unique ID like FR-ONB-001")
    statement: str = Field(..., description="The actual requirement text")
    categories: List[ReqCategory] = Field(default_factory=list)
    priority: str = Field("MEDIUM", description="HIGH, MEDIUM, or LOW")
    source: str = Field(..., description="Source stakeholder or document")
    business_justification: str = Field(..., description="Why is this needed?")
    dependencies: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    applicable_regulations: List[str] = Field(default_factory=list)
    risk_level: str = Field("LOW", description="HIGH, MEDIUM, or LOW")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    approval_status: ReqStatus = ReqStatus.DRAFT

class AnalysisFinding(BaseModel):
    requirement_id: str
    issue_type: str = Field(..., description="AMBIGUITY, INCONSISTENCY, DUPLICATION, etc.")
    severity: str = Field("MEDIUM")
    description: str
    suggested_question: Optional[str] = None

class ProjectState(BaseModel):
    project_id: int
    current_phase: str = "INTERVIEW"
    raw_inputs: List[str] = Field(default_factory=list)
    requirements: List[RequirementSchema] = Field(default_factory=list)
    findings: List[AnalysisFinding] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
