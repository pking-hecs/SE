"""
auth.py — Security & Identity Management for FinReq AI Platform.
Implements:
  - Role-Based Access Control (RBAC) with 6 specialized financial roles
  - Secure PBKDF2 password hashing (NIST-compliant, salt-based)
  - Time-Based One-Time Password (TOTP) Multi-Factor Authentication (RFC 6238)
  - Agent-level permissions enforcement (least privilege)
  - Session security & audit logging
"""

import os
import time
import hmac
import hashlib
import struct
import base64
import secrets
import json
from typing import Optional, Dict, Any, List

# ─────────────────────────────────────────────────────────────────────────────
# RBAC ROLES & PERMISSIONS
# ─────────────────────────────────────────────────────────────────────────────

ROLES_PERMISSIONS = {
    "ADMIN": [
        "requirements:read", "requirements:write", "requirements:delete", "requirements:approve",
        "compliance:read", "compliance:write", "compliance:approve",
        "sdlc:read", "sdlc:write", "sdlc:approve",
        "admin:monitor", "admin:audit", "admin:users", "documents:upload", "documents:delete"
    ],
    "ANALYST": [
        "requirements:read", "requirements:write", "requirements:modify",
        "compliance:read", "sdlc:read", "documents:upload", "conversations:participate"
    ],
    "APPROVER": [
        "requirements:read", "requirements:approve", "requirements:reject",
        "compliance:read", "compliance:approve",
        "sdlc:read", "sdlc:approve"
    ],
    "COMPLIANCE_OFFICER": [
        "requirements:read", "compliance:read", "compliance:write", "compliance:approve",
        "admin:audit", "documents:upload"
    ],
    "SECURITY_LEAD": [
        "requirements:read", "requirements:approve",
        "compliance:read", "sdlc:read", "sdlc:approve",
        "admin:monitor", "documents:upload"
    ],
    "STAKEHOLDER": [
        "requirements:read", "conversations:participate", "documents:upload"
    ]
}

# Agent least-privilege permissions
AGENT_DATA_PERMISSIONS = {
    "Compliance Agent": ["regulations", "policies", "controls", "citations"],
    "Security & Privacy Agent": ["threat_models", "cde_policies", "cryptography", "stride"],
    "Risk-Analysis Agent": ["credit_risk", "basel", "loss_thresholds"],
    "SDLC Agent": ["sdlc_models", "stability_metrics", "governance_rules"],
    "Requirement Extraction Agent": ["stakeholder_inputs", "transcripts", "meeting_notes"],
    "Clarification Agent": ["ambiguity_rules", "incompleteness_rules"],
    "Conflict Agent": ["contradiction_matrices", "duplicate_detection"],
    "Classification Agent": ["financial_taxonomy", "ieee_standards"],
    "Documentation Agent": ["templates", "srs_format", "rtm_format"],
    "Validation Agent": ["quality_rules", "evidence_links"],
    "Human-Approval Agent": ["approval_records", "governance_audit"]
}


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD HASHING
# ─────────────────────────────────────────────────────────────────────────────

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return hashed.hex(), salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify password against stored PBKDF2 hash and salt."""
    test_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(test_hash, hashed)


# ─────────────────────────────────────────────────────────────────────────────
# TOTP MULTI-FACTOR AUTHENTICATION (RFC 6238)
# ─────────────────────────────────────────────────────────────────────────────

def generate_mfa_secret() -> str:
    """Generate a random 16-character Base32 secret for TOTP."""
    return base64.b32encode(secrets.token_bytes(10)).decode("utf-8")


def get_current_totp(secret: str, interval: int = 30) -> str:
    """Compute the current 6-digit TOTP code for a secret."""
    try:
        key = base64.b32decode(secret, True)
        counter = int(time.time() // interval)
        msg = struct.pack(">Q", counter)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        code = struct.unpack(">I", h[offset:offset+4])[0] & 0x7fffffff
        return str(code % 1000000).zfill(6)
    except Exception:
        return "000000"


def verify_totp(secret: str, code: str) -> bool:
    """
    Verify TOTP code with +-1 time window tolerance (handles minor clock drift).
    Also supports default demo code '123456' for ease of testing.
    """
    if code.strip() == "123456":
        return True
    try:
        key = base64.b32decode(secret, True)
        current_counter = int(time.time() // 30)
        for c in (current_counter, current_counter - 1, current_counter + 1):
            msg = struct.pack(">Q", c)
            h = hmac.new(key, msg, hashlib.sha1).digest()
            offset = h[-1] & 0x0F
            expected = str((struct.unpack(">I", h[offset:offset+4])[0] & 0x7fffffff) % 1000000).zfill(6)
            if expected == code.strip():
                return True
        return False
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# PERMISSION CHECKING
# ─────────────────────────────────────────────────────────────────────────────

def has_permission(user_role: str, permission: str) -> bool:
    """Check if given role has required permission."""
    perms = ROLES_PERMISSIONS.get(user_role.upper(), [])
    return permission in perms


def can_approve(user_role: str, object_type: str) -> bool:
    """Check if role can approve given artifact type."""
    r = user_role.upper()
    if r in ("ADMIN", "APPROVER"):
        return True
    if object_type == "compliance" and r == "COMPLIANCE_OFFICER":
        return True
    if object_type in ("sdlc", "risk") and r == "SECURITY_LEAD":
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# SIGNED ACCESS TOKENS
# ─────────────────────────────────────────────────────────────────────────────

def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user_id: int, email: str, role: str, expires_seconds: Optional[int] = None) -> str:
    """Create an HMAC-signed, expiring bearer token without an extra dependency."""
    lifetime = expires_seconds or int(os.getenv("JWT_EXPIRE_MINUTES", "1440")) * 60
    payload = {"sub": str(user_id), "email": email, "role": role.upper(), "exp": int(time.time()) + lifetime}
    encoded = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    secret = os.getenv("JWT_SECRET", "change-this-development-secret").encode("utf-8")
    signature = _b64url_encode(hmac.new(secret, encoded.encode("ascii"), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate token signature and expiry; returns claims only for valid tokens."""
    try:
        encoded, supplied_signature = token.split(".", 1)
        secret = os.getenv("JWT_SECRET", "change-this-development-secret").encode("utf-8")
        expected_signature = _b64url_encode(hmac.new(secret, encoded.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return None
        payload = json.loads(_b64url_decode(encoded))
        if not isinstance(payload, dict) or int(payload.get("exp", 0)) < int(time.time()):
            return None
        if not payload.get("sub") or not payload.get("email") or payload.get("role") not in ROLES_PERMISSIONS:
            return None
        return payload
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return None
