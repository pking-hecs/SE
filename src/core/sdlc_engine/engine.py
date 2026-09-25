from typing import List, Dict, Any, Tuple
from src.core.orchestrator.state import ProjectState

class SDLCEngine:
    """
    Analyzes project characteristics to recommend an SDLC model.
    """
    def extract_factors(self, state: ProjectState) -> Dict[str, Any]:
        # Analysis logic based on the requirement set
        factors = {
            "stability": "Low" if len(state.requirements) < 5 else "High",
            "regulatory_criticality": "Critical" if any(len(r.regulations) > 0 for r in state.requirements.values()) else "Standard",
            "complexity": "High" if len(state.requirements) > 10 else "Low",
            "risk": "High" if any("security" in r.statement.lower() for r in state.requirements.values()) else "Low"
        }
        return factors

    def recommend_model(self, factors: Dict[str, Any]) -> Tuple[str, str, float]:
        # Decision Logic
        if factors["regulatory_criticality"] == "Critical" and factors["risk"] == "High":
            return "V-Model", "High regulatory risk and safety requirements demand strict verification.", 0.92
        elif factors["stability"] == "Low":
            return "Agile", "Unstable requirements suggest an iterative approach.", 0.85
        elif factors["risk"] == "High":
            return "Spiral", "High technical risk requires prototyping and risk analysis.", 0.80
        else:
            return "Waterfall", "Stable requirements and low risk allow a sequential approach.", 0.70

    def generate_workflow(self, model: str) -> List[str]:
        workflows = {
            "V-Model": ["Requirements Analysis", "System Design", "Architecture Design", "Module Design", "Coding", "Unit Testing", "Integration Testing", "System Testing", "Acceptance Testing"],
            "Agile": ["Backlog Grooming", "Sprint Planning", "Development", "Daily Standup", "Sprint Review", "Sprint Retrospective"],
            "Spiral": ["Identification", "Risk Analysis", "Engineering", "Evaluation"],
            "Waterfall": ["Requirements", "Analysis", "Design", "Implementation", "Testing", "Deployment", "Maintenance"]
        }
        return workflows.get(model, ["Standard SDLC Phases"])
