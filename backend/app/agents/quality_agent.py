import logging
from typing import List, Optional
from backend.app.services.gemini_service import gemini_service
from backend.app.core.orchestrator.state import RequirementSchema, AnalysisFinding

logger = logging.getLogger(__name__)

class QualityAgent:
    """
    Detects ambiguity, incompleteness, and duplication in requirements.
    """
    SYSTEM_PROMPT = (
        "You are a Senior Quality Assurance Analyst for Financial Systems. "
        "Review the following requirements for ambiguity, inconsistency, and testability. "
        "Identify gaps and suggest specific questions to clarify the requirements."
    )

    async def analyze(self, requirements: List[RequirementSchema]) -> List[AnalysisFinding]:
        if not requirements:
            return []

        # Prepare the requirements text for the LLM
        req_text = "\n".join([f"[{r.requirement_id}] {r.statement}" for r in requirements])

        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "requirement_id": {"type": "string"},
                    "issue_type": {"type": "string", "enum": ["AMBIGUITY", "INCONSISTENCY", "DUPLICATION", "INCOMPLETENESS"]},
                    "severity": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                    "description": {"type": "string"},
                    "suggested_question": {"type": "string"}
                },
                "required": ["requirement_id", "issue_type", "description"]
            }
        }

        prompt = f"Analyze these requirements for quality issues:\n\n{req_text}"

        try:
            result = await gemini_service.generate_structured(prompt, schema, self.SYSTEM_PROMPT)
            return [AnalysisFinding(**item) for item in result] if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Quality Agent failed: {e}")
            return []

quality_agent = QualityAgent()
