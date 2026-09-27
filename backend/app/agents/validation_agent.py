import logging
from typing import List, Optional
from backend.app.core.orchestrator.state import RequirementSchema, AnalysisFinding, ReqStatus

logger = logging.getLogger(__name__)

class ValidationAgent:
    """
    Final gatekeeper that ensures requirements meet the 'Definition of Ready'.
    """
    def __init__(self):
        # Criteria for a requirement to be 'VALIDATED'
        self.mandatory_fields = ["statement", "categories", "priority", "source", "business_justification"]

    async def validate(self, requirement: RequirementSchema) -> bool:
        # 1. Check mandatory fields
        for field in self.mandatory_fields:
            if not getattr(requirement, field):
                logger.info(f"Validation failed for {requirement.requirement_id}: Missing {field}")
                return False

        # 2. Check for minimum length/quality
        if len(requirement.statement) < 10:
            return False

        # 3. Check for confidence score
        if requirement.confidence < 0.7:
            logger.info(f"Validation failed for {requirement.requirement_id}: Confidence too low ({requirement.confidence})")
            return False

        return True

validation_agent = ValidationAgent()
