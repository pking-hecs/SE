import logging
from typing import List, Optional
from backend.app.services.gemini_service import gemini_service
from backend.app.core.orchestrator.state import RequirementSchema, ReqCategory
from backend.app.core.security.guard import security_guard

logger = logging.getLogger(__name__)

class ExtractionAgent:
    """
    Converts conversations/documents into structured requirements.
    """
    SYSTEM_PROMPT = (
        "You are a Financial Requirements Engineer. Your task is to extract structured requirements "
        "from the provided text. Each requirement must be precise, testable, and mapped to a category. "
        "If the text is too vague to create a requirement, do not invent one."
    )

    async def extract(self, text: str) -> List[RequirementSchema]:
        # 1. Mask PII first
        safe_text = security_guard.mask_pii(text)

        # 2. Define the schema for Gemini
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "requirement_id": {"type": "string"},
                    "statement": {"type": "string"},
                    "categories": {"type": "array", "items": {"type": "string"}},
                    "priority": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                    "source": {"type": "string"},
                    "business_justification": {"type": "string"},
                    "confidence": {"type": "number"}
                },
                "required": ["requirement_id", "statement", "categories", "priority", "source"]
            }
        }

        prompt = f"Extract requirements from the following text:\n\n{safe_text}"

        try:
            # Use structured generation from Gemini
            result = await gemini_service.generate_structured(prompt, schema, self.SYSTEM_PROMPT)

            # Map raw JSON to Pydantic objects
            requirements = []
            if isinstance(result, list):
                for item in result:
                    requirements.append(RequirementSchema(**item))

            return requirements
        except Exception as e:
            logger.error(f"Extraction Agent failed: {e}")
            return []

extraction_agent = ExtractionAgent()
