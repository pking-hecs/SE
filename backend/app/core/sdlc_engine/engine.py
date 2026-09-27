import logging
from typing import List, Dict, Any
from backend.app.core.config import settings
from backend.app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

class SdlcEngine:
    """
    Deterministic SDLC Selection Engine.
    Uses weighted scoring based on project characteristics.
    """
    MODELS = {
        "AGILE": {"stability": 0.2, "criticality": 0.1, "risk": 0.2, "complexity": 0.2, "change_freq": 0.3},
        "V_MODEL": {"stability": 0.4, "criticality": 0.3, "risk": 0.1, "complexity": 0.1, "change_freq": 0.1},
        "SPIRAL": {"stability": 0.1, "criticality": 0.2, "risk": 0.4, "complexity": 0.2, "change_freq": 0.1},
        "WATERFALL": {"stability": 0.5, "criticality": 0.2, "risk": 0.1, "complexity": 0.1, "change_freq": 0.1}
    }

    async def analyze(self, characteristics: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates scores for each SDLC model.
        Characteristics should be normalized (0.0 to 1.0).
        """
        scores = {}
        for model, weights in self.MODELS.items():
            score = sum(characteristics.get(k, 0.5) * weights[k] for k in weights)
            scores[model] = round(score, 2)

        best_model = max(scores, key=scores.get)

        # Generate rationale using LLM
        rationale_prompt = (
            f"The project has characteristics: {characteristics}. "
            f"The recommended SDLC is {best_model} with a score of {scores[best_model]}. "
            "Explain why this model is the best fit for a financial project with these traits."
        )

        try:
            rationale = await gemini_service.chat(rationale_prompt, "You are an SDLC Advisor.")
        except Exception as e:
            logger.error(f"SDLC Rationale generation failed: {e}")
            rationale = "Based on weighted scoring of stability, risk, and criticality."

        return {
            "recommended_model": best_model,
            "scores": scores,
            "rationale": rationale
        }

sdlc_engine = SdlcEngine()
