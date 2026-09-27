import logging
import re
from typing import List
from backend.app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SecurityGuard")

class SecurityGuard:
    """
    SecurityGuard handles PII masking and prompt injection detection.
    """
    def __init__(self):
        # Basic PII patterns
        self.pii_patterns = {
            "EMAIL": r"[\w\.-]+@[\w\.-]+\.\w+",
            "PHONE": r"\b\d{10,12}\b",
            "ACCOUNT": r"\b\d{8,20}\b",
            "SSN": r"\b\d{3}-\d{2}-\d{4}\b"
        }

        # Basic prompt injection patterns
        self.injection_patterns = [
            r"ignore previous instructions",
            r"system prompt",
            r"you are now a",
            r"bypass",
            r"reveal your secret"
        ]

    def mask_pii(self, text: str) -> str:
        """Masks sensitive financial information."""
        masked_text = text
        for label, pattern in self.pii_patterns.items():
            masked_text = re.sub(pattern, f"[{label}_REDACTED]", masked_text)
        return masked_text

    def detect_injection(self, text: str) -> bool:
        """Checks if text contains potential prompt injection attempts."""
        for pattern in self.injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Prompt injection detected: {pattern}")
                return True
        return False

security_guard = SecurityGuard()
