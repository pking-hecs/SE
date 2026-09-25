from src.core.orchestrator.state import ProjectState, AgentResponse

class HumanApprovalAgent:
    """
    Routes critical decisions to authorized personnel.
    """
    def __init__(self):
        self.pending_approvals = []

    def request_approval(self, item_id: str, content: str, role_required: str) -> bool:
        print(f"[APPROVAL REQUIRED] Role: {role_required} | Item: {item_id}")
        print(f"Content: {content}")
        # In a real system, this would be a Web UI. Here we simulate approval.
        return True

    def verify_baseline(self, state: ProjectState) -> bool:
        if not state.requirements:
            return False
        return self.request_approval("PROJECT_BASELINE", "Final SRS for Approval", "Project Manager")
