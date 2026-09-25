from src.core.orchestrator.state import ProjectState
import hashlib

class SecurityAgent:
    """
    Implements platform security controls.
    """
    def mask_data(self, text: str) -> str:
        # Simple simulation of PII masking
        import re
        # Mask emails
        text = re.sub(r'\S+@\S+', '[EMAIL_MASKED]', text)
        # Mask potential account numbers (10+ digits)
        text = re.sub(r'\d{10,}', '[ACCOUNT_MASKED]', text)
        return text

    def check_prompt_injection(self, prompt: str) -> bool:
        forbidden = ["ignore all previous instructions", "you are now an admin", "system override"]
        return any(phrase in prompt.lower() for phrase in forbidden)

    def generate_audit_log(self, user: str, action: str, resource: str):
        log_entry = f"User: {user} | Action: {action} | Resource: {resource}"
        print(f"[AUDIT] {log_entry}")
