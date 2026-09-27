import logging
from typing import List, Optional
from backend.app.services.ollama_service import ollama_service
from backend.app.core.orchestrator.state import RequirementSchema, AnalysisFinding
from backend.app.core.security.guard import security_guard

logger = logging.getLogger(__name__)

class ConflictAgent:
    """
    Detects contradictions between multiple requirements.
    """
    SYSTEM_PROMPT = (
        "You are a Financial Conflict Resolution Expert. Your task is to analyze a set of "
        "requirements and identify any direct or indirect contradictions. "
        "Example: Req A says 'No OTP for low value' and Req B says 'OTP for all transactions'."
    )

    async def detect_conflicts(self, requirements: List[RequirementSchema]) -> List[AnalysisFinding]:
        if len(requirements) < 2:
            return []

        req_text = "\n".join([f"[{r.requirement_id}] {r.statement}" for r in requirements])

        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "requirement_ids": {"type": "array", "items": {"type": "string"}},
                    "issue_type": {"type": "string", "const": "CONFLICT"},
                    "severity": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                    "description": {"type": "string"},
                    "resolution_suggestion": {"type": "string"}
                },
                "required": ["requirement_ids", "description"]
            }
        }

        prompt = f"Analyze these requirements for conflicts:\n\n{req_text}"

        try:
            result = await ollama_service.generate_structured(prompt, schema, self.SYSTEM_PROMPT)
            # Map to AnalysisFinding for consistency
            findings = []
            if isinstance(result, list):
                for item in result:
                    findings.append(AnalysisFinding(
                        requirement_id=", ".join(item["requirement_ids"]),
                        issue_type="CONFLICT",
                        severity=item.get("severity", "MEDIUM"),
                        description=item["description"],
                        suggested_question=item.get("resolution_suggestion")
                    ))
            return findings
        except Exception as e:
            logger.error(f"Conflict Agent failed: {e}")
            return []

conflict_agent = ConflictAgent()
