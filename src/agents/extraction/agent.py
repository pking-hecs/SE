from src.core.orchestrator.state import ProjectState, Requirement, AgentResponse

class ExtractionAgent:
    """
    Transforms Natural Language inputs into structured Requirement objects.
    """
    def extract(self, state: ProjectState, text: str, source: str) -> AgentResponse:
        # In a real app, this would be an LLM call with a JSON-mode prompt using the schema from docs/architecture/extraction_specification.md

        # Simulated extraction
        req_id = f"FR-{len(state.requirements)+1:03d}"
        extracted_req = Requirement(
            req_id=req_id,
            statement=text if "shall" in text else f"The system shall {text}",
            category="Functional",
            source=source,
            confidence_score=0.9
        )

        state.add_requirement(extracted_req)

        return AgentResponse(
            agent_name="ExtractionAgent",
            content=extracted_req,
            confidence=0.9
        )
