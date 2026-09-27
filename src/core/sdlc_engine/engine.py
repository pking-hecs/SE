from typing import List, Dict, Any, Tuple
from src.core.orchestrator.state import ProjectState

class SDLCEngine:
    """
    Analyzes project characteristics to recommend an SDLC model.
    """
    def extract_factors(self, state: ProjectState) -> Dict[str, Any]:
        requirements = list(state.requirements_baseline.values())
        factors = {
            "stability": "Low" if len(requirements) < 5 else "High",
            "regulatory_criticality": "Critical" if any(r.category == "Compliance" for r in requirements) else "Standard",
            "complexity": "High" if len(requirements) > 10 else "Low",
            "risk": "High" if any(r.risk_level == "High" or "security" in r.statement.lower() for r in requirements) else "Low"
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
            "Waterfall": ["Requirements", "Analysis", "Design", "Implementation", "Testing", "Deployment", "Maintenance"],
            "DevSecOps": ["Backlog and threat review", "Secure design", "Build and code review", "Automated security and quality tests", "Compliance evidence review", "Controlled release", "Monitoring and incident response"],
            "Agile–V-Model hybrid": ["Requirements and traceability", "Sprint planning", "Threat modelling and design review", "Secure implementation", "Unit and integration verification", "System and acceptance validation", "Compliance approval", "Controlled deployment and monitoring"],
        }
        return workflows.get(model, ["Standard SDLC Phases"])
