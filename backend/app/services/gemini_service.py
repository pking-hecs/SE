import os
import json
import logging
import warnings
warnings.filterwarnings("ignore")
import google.generativeai as genai
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Service to interact with AI API.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.error("AI_API_KEY is not set. Please update your .env file.")

        genai.configure(api_key=self.api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest").replace("models/", "")
        self.model = genai.GenerativeModel(model_name)

    async def health_check(self) -> bool:
        try:
            # Basic check: try to generate a tiny response
            response = self.model.generate_content("ping")
            return True
        except Exception as e:
            logger.error(f"AI engine health check failed: {e}")
            return False

    async def chat(self, prompt: str, system_prompt: str = "You are a professional financial analyst.") -> str:
        try:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"AI engine chat error: {e}")
            raise e

    async def generate_structured(self, prompt: str, schema: dict, system_prompt: str = "") -> dict:
        """
        Requests a JSON response from AI engine.
        """
        json_prompt = (
            f"{system_prompt}\n\n"
            f"Task: {prompt}\n\n"
            f"IMPORTANT: You must return the result as a strict JSON object matching this schema: {json.dumps(schema)}. "
            f"Do not include markdown formatting like ```json. Return ONLY the JSON string."
        )

        try:
            response = self.model.generate_content(
                json_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"AI structured generation error: {e}")
            # Fallback: try to clean the response if it returned markdown
            try:
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                return json.loads(text)
            except:
                raise ValueError(f"AI failed to return valid JSON: {e}")

gemini_service = GeminiService()
