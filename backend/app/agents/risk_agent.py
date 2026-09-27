import logging
from typing import List
from backend.app.services.gemini_service import gemini_service
from backend.app.core.orchestrator.state import RequirementSchema, AnalysisFinding

logger = logging.getLogger(__name__)

class RiskAgent:
    """
    Evaluates financial, technical, and security risk of requirements.
    """
    SYSTEM_PROMPT = (
        "You are a Financial Risk Manager. Evaluate the following requirement for "
        "likelihood of failure and impact on the business. Provide a risk score (1-10)."
    )

    async def evaluate_risk(self, requirement: RequirementSchema) -> AnalysisFinding:
        schema = {
            "type": "object",
            "properties": {
                "likelihood": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                "impact": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                "score": {"type": "integer", "minimum": 1, "maximum": 10},
                "mitigation": {"type": "string"}
            },
            "required": ["likelihood", "impact", "score"]
        }

        prompt = f"Evaluate risk for: {requirement.statement}"

        try:
            result = await gemini_service.generate_structured(prompt, schema, self.SYSTEM_PROMPT)

            return AnalysisFinding(
                requirement_id=requirement.requirement_id,
                issue_type="RISK_ASSESSMENT",
                severity="HIGH" if result["score"] > 7 else "MEDIUM" if result["score"] > 4 else "LOW",
                description=f"Risk Score: {result['score']}. Impact: {result['impact']}, Likelihood: {result['likelihood']}. Mitigation: {result.get('mitigation', 'N/A')}"
            )
        except Exception as e:
            logger.error(f"Risk Agent failed: {e}")
            return AnalysisFinding(
                requirement_id=requirement.requirement_id,
                issue_type="RISK_ERROR",
                severity="MEDIUM",
                description="Risk analysis failed to execute."
            )

risk_agent = RiskAgent()
