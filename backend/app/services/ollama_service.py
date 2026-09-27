import httpx
import json
import logging
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaService:
    """
    Service to interact with local Ollama installation.
    """
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def chat(self, prompt: str, system_prompt: str = "You are a professional financial analyst.") -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise e

    async def generate_structured(self, prompt: str, schema: dict, system_prompt: str = "") -> dict:
        """
        Requests a JSON response from Ollama.
        Note: Gemma/Llama models may require explicit instruction to return JSON.
        """
        full_prompt = f"{prompt}\n\nReturn the result as a strict JSON object matching this schema: {json.dumps(schema)}"
        response_text = await self.chat(full_prompt, system_prompt)

        try:
            # Clean potential markdown wrapping
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Ollama JSON decode error: {e}. Response: {response_text}")
            raise ValueError(f"LLM failed to return valid JSON: {e}")

ollama_service = OllamaService()
