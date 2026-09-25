from typing import List
from src.core.orchestrator.state import ProjectState, AgentResponse
from src.core.rag.engine import FinancialRAG

class ComplianceAgent:
    """
    Maps requirements to financial regulations and policies.
    """
    def __init__(self, rag_engine: FinancialRAG):
        self.rag = rag_engine

    def map_compliance(self, state: ProjectState) -> List[AgentResponse]:
        results = []
        for req_id, req in state.requirements.items():
            # Ground the requirement against FKB
            compliance_result = self.rag.generate_grounded_response(req.statement, None)

            if compliance_result['confidence'] > 0.5:
                req.regulations.extend(compliance_result['citations'])
                results.append(AgentResponse(
                    agent_name="ComplianceAgent",
                    content=f"Requirement {req_id} mapped to {compliance_result['citations']}",
                    confidence=compliance_result['confidence'],
                    citations=compliance_result['citations']
                ))
        return results
