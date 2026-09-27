from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, Float, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    APPROVER = "APPROVER"
    STAKEHOLDER = "STAKEHOLDER"

class ReqStatus(enum.Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ReqCategory(enum.Enum):
    BUSINESS = "BUSINESS"
    FUNCTIONAL = "FUNCTIONAL"
    SECURITY = "SECURITY"
    PRIVACY = "PRIVACY"
    REGULATORY = "REGULATORY"
    PERFORMANCE = "PERFORMANCE"
    # ... add others as per prompt

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.STAKEHOLDER)
    created_at = Column(DateTime, server_default=func.now())

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String, nullable=False)
    file_path = Column(String)
    doc_type = Column(String) # e.g., REGULATION, POLICY
    status = Column(String, default="UPLOADED")
    created_at = Column(DateTime, server_default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    content = Column(Text, nullable=False)
    embedding = Column(Text) # Simplified; in real use we use pgvector Vector type
    page_number = Column(Integer)

class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    req_id = Column(String, index=True) # e.g., FR-ONB-001
    statement = Column(Text, nullable=False)
    category = Column(SQLEnum(ReqCategory))
    priority = Column(String) # HIGH, MEDIUM, LOW
    status = Column(SQLEnum(ReqStatus), default=ReqStatus.DRAFT)
    source_stakeholder = Column(String)
    business_justification = Column(Text)
    confidence = Column(Float)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

class RequirementEvidence(Base):
    __tablename__ = "requirement_evidence"
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"))
    citation = Column(String)
    evidence_text = Column(Text)

class ComplianceMapping(Base):
    __tablename__ = "compliance_mappings"
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    control_id = Column(String)
    source_doc_id = Column(Integer, ForeignKey("documents.id"))
    mapping_reason = Column(Text)
    coverage = Column(String) # FULL, PARTIAL, NONE
    approval_status = Column(String, default="PENDING")

class SecurityFinding(Base):
    __tablename__ = "security_findings"
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    finding = Column(Text)
    severity = Column(String)
    mitigation = Column(Text)

class ProjectRisk(Base):
    __tablename__ = "project_risks"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=True)
    description = Column(Text)
    likelihood = Column(String)
    impact = Column(String)
    score = Column(Integer)
    mitigation = Column(Text)
    status = Column(String, default="OPEN")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    object_type = Column(String)
    object_id = Column(Integer)
    old_value = Column(Text)
    new_value = Column(Text)
    timestamp = Column(DateTime, server_default=func.now())
