from typing import List, Dict, Any
from src.core.orchestrator.state import ProjectState, Requirement

class DocumentationAgent:
    """
    Generates SRS, User Stories, and Traceability Matrices.
    """
    def generate_srs(self, state: ProjectState) -> str:
        srs = "# Software Requirements Specification\n\n"
        srs += "## 1. Functional Requirements\n"
        for req in state.requirements.values():
            if req.category == "Functional":
                srs += f"- {req.req_id}: {req.statement} (Source: {req.source}) [Regs: {', '.join(req.regulations)}]\n"

        srs += "\n## 2. Non-Functional Requirements\n"
        for req in state.requirements.values():
            if req.category != "Functional":
                srs += f"- {req.req_id}: {req.statement} [{req.category}]\n"

        return srs

    def generate_user_stories(self, state: ProjectState) -> List[str]:
        stories = []
        for req in state.requirements.values():
            if req.category == "Functional":
                stories.append(f"As a {req.source}, I want {req.statement} so that business goals are met.")
        return stories

    def generate_rtm(self, state: ProjectState) -> str:
        rtm = "| Req ID | Source | Regulation | Status |\n|---|---|---|---|\n"
        for req in state.requirements.values():
            rtm += f"| {req.req_id} | {req.source} | {', '.join(req.regulations)} | {req.status} |\n"
        return rtm
