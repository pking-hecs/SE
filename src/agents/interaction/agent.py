from src.core.orchestrator.state import ProjectState, AgentResponse
from src.core.rag.engine import FinancialRAG

class InteractionAgent:
    """
    Conducts adaptive interviews with stakeholders.
    """
    def __init__(self, rag_engine: FinancialRAG):
        self.rag = rag_engine

    def conduct_interview(self, state: ProjectState, stakeholder_role: str, input_text: str) -> AgentResponse:
        """
        Processes stakeholder input and determines if follow-up is needed.
        """
        # 1. Ground the conversation in knowledge if needed
        rag_result = self.rag.generate_grounded_response(input_text, None)

        # 2. Determine if response is vague or incomplete (Simulated logic)
        if len(input_text.split()) < 5:
            response_text = "Your response is too brief. Could you please elaborate on the business rules associated with this requirement?"
            confidence = 0.6
        else:
            response_text = f"I have captured this. Based on {stakeholder_role} perspective, I've noted the need. {rag_result['response']}"
            confidence = 0.9

        return AgentResponse(
            agent_name="InteractionAgent",
            content=response_text,
            confidence=confidence,
            citations=rag_result['citations']
        )
