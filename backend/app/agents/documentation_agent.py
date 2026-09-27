import logging
from typing import List, Optional, Dict, Any
from backend.app.services.gemini_service import gemini_service
from backend.app.core.orchestrator.state import RequirementSchema, ReqStatus

logger = logging.getLogger(__name__)

class DocumentationAgent:
    """
    Generates professional financial requirements artifacts.
    """
    SYSTEM_PROMPT = (
        "You are a Professional Technical Writer for the Banking sector. "
        "Your task is to transform approved requirements into formal documentation. "
        "Use a formal, precise, and unambiguous tone. Follow ISO/IEC/IEEE 29148 standards."
    )

    async def generate_srs(self, project_name: str, requirements: List[RequirementSchema]) -> str:
        # Only use approved requirements
        approved_reqs = [r for r in requirements if r.approval_status == ReqStatus.APPROVED]

        if not approved_reqs:
            return "No approved requirements available to generate SRS."

        req_text = "\n".join([f"{r.requirement_id}: {r.statement} (Priority: {r.priority})" for r in approved_reqs])

        prompt = (
            f"Generate a formal Software Requirements Specification (SRS) for project: {project_name}.\n\n"
            f"Approved Requirements:\n{req_text}\n\n"
            "The SRS should include: \n"
            "1. Introduction\n"
            "2. Overall Description\n"
            "3. Specific Requirements (grouped by category)\n"
            "4. Acceptance Criteria"
        )

        try:
            return await gemini_service.chat(prompt, self.SYSTEM_PROMPT)
        except Exception as e:
            logger.error(f"SRS Generation failed: {e}")
            return "Error generating SRS document."

    async def generate_user_stories(self, requirements: List[RequirementSchema]) -> str:
        approved_reqs = [r for r in requirements if r.approval_status == ReqStatus.APPROVED]

        req_text = "\n".join([f"{r.requirement_id}: {r.statement}" for r in approved_reqs])
        prompt = (
            f"Convert these requirements into User Stories following the format: "
            "'As a [role], I want to [goal] so that [benefit]'.\n\n"
            f"Requirements:\n{req_text}"
        )

        try:
            return await gemini_service.chat(prompt, self.SYSTEM_PROMPT)
        except Exception as e:
            logger.error(f"User Story generation failed: {e}")
            return "Error generating User Stories."

doc_agent = DocumentationAgent()
