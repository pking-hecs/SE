import logging
from typing import List, Optional
from backend.app.services.gemini_service import gemini_service
from backend.app.core.orchestrator.state import RequirementSchema, AnalysisFinding
from backend.app.core.rag.engine import rag_engine

logger = logging.getLogger(__name__)

class ComplianceAgent:
    """
    Maps requirements to regulatory controls using RAG.
    """
    SYSTEM_PROMPT = (
        "You are a Financial Compliance Officer. Your task is to map requirements to approved "
        "regulatory controls. You must only use the provided evidence from the knowledge base. "
        "If no evidence is found, mark coverage as NONE."
    )

    async def analyze_compliance(self, requirement: RequirementSchema, project_id: int) -> List[AnalysisFinding]:
        # 1. Retrieve evidence from pgvector
        evidence_chunks = await rag_engine.retrieve_context(requirement.statement, project_id)
        evidence_text = "\n\n".join([c for c in evidence_chunks]) if evidence_chunks else "No approved evidence found."

        # 2. Analyze using Gemini
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "control_id": {"type": "string"},
                    "coverage": {"type": "string", "enum": ["FULL", "PARTIAL", "NONE"]},
                    "evidence_citation": {"type": "string"},
                    "gap": {"type": "string"},
                    "confidence": {"type": "number"}
                },
                "required": ["control_id", "coverage"]
            }
        }

        prompt = f"Requirement: {requirement.statement}\n\nApproved Evidence:\n{evidence_text}\n\nMap this requirement to the correct regulatory control."

        try:
            result = await gemini_service.generate_structured(prompt, schema, self.SYSTEM_PROMPT)
            findings = []
            if isinstance(result, list):
                for item in result:
                    findings.append(AnalysisFinding(
                        requirement_id=requirement.requirement_id,
                        issue_type="COMPLIANCE_GAP" if item["coverage"] != "FULL" else "COMPLIANCE_MAPPED",
                        severity="HIGH" if item["coverage"] == "NONE" else "MEDIUM",
                        description=f"Mapped to {item['control_id']}. Coverage: {item['coverage']}. Gap: {item.get('gap', 'None')}"
                    ))
            return findings
        except Exception as e:
            logger.error(f"Compliance Agent failed: {e}")
            return []

compliance_agent = ComplianceAgent()
