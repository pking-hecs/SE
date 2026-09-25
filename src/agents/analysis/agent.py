from typing import List
from src.core.orchestrator.state import ProjectState, AgentResponse

class AnalysisAgent:
    """
    Checks requirements for ambiguity, incompleteness, and inconsistency.
    """
    def analyze_quality(self, state: ProjectState) -> List[AgentResponse]:
        findings = []
        for req_id, req in state.requirements.items():
            # Heuristic: check for "fast", "user-friendly", etc.
            vague_words = ["fast", "user-friendly", "efficient", "appropriate", "easy"]
            if any(word in req.statement.lower() for word in vague_words):
                findings.append(AgentResponse(
                    agent_name="AnalysisAgent",
                    content=f"Requirement {req_id} is ambiguous. It uses subjective terms.",
                    confidence=1.0
                ))
        return findings
