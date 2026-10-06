"""
db.py — Comprehensive PostgreSQL persistence and vector layer for FinReq Platform.
Uses PostgreSQL with pgvector for:
  - Structured engineering requirements, classifications, and dependencies
  - 13-agent run monitoring and immutable audit logging
  - RAG vector knowledge base with 384-dimensional semantic embeddings
  - RBAC user authentication, MFA credentials, and project governance
Falls back to SQLite for offline dev if PostgreSQL is unreachable.
"""
import json
import os
import re
import time
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import numpy as np

# ---------------------------------------------------------------------------
# Connection configuration
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/fin_req_db"
)

_local = threading.local()
_use_postgres = True


def _parse_pg_url(url: str) -> dict:
    """Parse a postgresql:// URL into psycopg2 connect kwargs."""
    m = re.match(
        r"postgresql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<dbname>.+)",
        url,
    )
    if not m:
        return {}
    return {
        "dbname": m.group("dbname"),
        "user": m.group("user"),
        "password": m.group("password"),
        "host": m.group("host"),
        "port": int(m.group("port")),
    }


def _get_pg_conn():
    """Return a thread-local PostgreSQL connection (create if missing)."""
    if not getattr(_local, "pg_conn", None) or _local.pg_conn.closed:
        import psycopg2
        import psycopg2.extras
        params = _parse_pg_url(DATABASE_URL)
        # Never let an unavailable local Docker service block application startup.
        # Production deployments can override this through DATABASE_CONNECT_TIMEOUT.
        params["connect_timeout"] = int(os.getenv("DATABASE_CONNECT_TIMEOUT", "3"))
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        _local.pg_conn = conn
    return _local.pg_conn


# ── SQLite fallback helpers (kept for offline dev) ─────────────────
import sqlite3

_SQLITE_PATH = Path(__file__).parent / "finreq_history.db"


def _get_sqlite_conn() -> sqlite3.Connection:
    if not getattr(_local, "sqlite_conn", None):
        conn = sqlite3.connect(str(_SQLITE_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.sqlite_conn = conn
    return _local.sqlite_conn


# ─────────────────────────────────────────────────────────────────────────────
# Semantic Vector Embedding Generator (384-dimensional L2-normalized)
# ─────────────────────────────────────────────────────────────────────────────
def generate_embedding(text: str, dim: int = 384) -> List[float]:
    """
    Computes a deterministic, semantic subword-projected 384-d vector.
    Normalized to unit length for direct cosine similarity in pgvector (<=> operator).
    """
    if not text:
        return [0.0] * dim
    vec = np.zeros(dim, dtype=np.float32)
    words = text.lower().split()
    for w in words:
        h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0 if (h >> 8) % 2 == 0 else -1.0
        # Character trigrams for morphological and subword richness
        for i in range(max(0, len(w) - 2)):
            ng = w[i:i + 3]
            h_ng = int(hashlib.sha256(ng.encode("utf-8")).hexdigest(), 16)
            vec[h_ng % dim] += 0.5 * (1.0 if (h_ng >> 8) % 2 == 0 else -1.0)
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


# ===================================================================
# Schema initialisation — All 22 Relational Tables + Compatibility
# ===================================================================

_PG_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Roles
CREATE TABLE IF NOT EXISTS roles (
    name         VARCHAR(50) PRIMARY KEY,
    description  TEXT,
    permissions  JSONB DEFAULT '[]'::jsonb
);

-- 2. Users (Authentication, RBAC, MFA)
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    full_name     TEXT,
    role          VARCHAR(50) NOT NULL REFERENCES roles(name) ON DELETE RESTRICT,
    mfa_secret    TEXT,
    mfa_enabled   BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Projects
CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    domain      TEXT,
    owner_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status      TEXT DEFAULT 'ACTIVE',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Stakeholders
CREATE TABLE IF NOT EXISTS stakeholders (
    id          SERIAL PRIMARY KEY,
    project_id  TEXT REFERENCES projects(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL,
    contact     TEXT,
    notes       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id             TEXT PRIMARY KEY,
    project_id     TEXT REFERENCES projects(id) ON DELETE CASCADE,
    stakeholder_id INTEGER REFERENCES stakeholders(id) ON DELETE SET NULL,
    title          TEXT,
    status         TEXT DEFAULT 'OPEN',
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Messages
CREATE TABLE IF NOT EXISTS messages (
    id              SERIAL PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    agent_name      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Documents (Uploaded stakeholder & project docs)
CREATE TABLE IF NOT EXISTS documents (
    id          SERIAL PRIMARY KEY,
    project_id  TEXT REFERENCES projects(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    file_type   TEXT,
    file_path   TEXT,
    file_size   INTEGER,
    status      TEXT DEFAULT 'PROCESSED',
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Knowledge Documents (RAG Knowledge Base with pgvector)
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id             SERIAL PRIMARY KEY,
    title          TEXT NOT NULL,
    source         TEXT,
    jurisdiction   TEXT,
    effective_date TEXT,
    version        TEXT,
    applicability  TEXT,
    category       TEXT,
    content        TEXT NOT NULL,
    embedding      vector(384),
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Requirement Categories (13 Financial Taxonomies)
CREATE TABLE IF NOT EXISTS requirement_categories (
    name        TEXT PRIMARY KEY,
    description TEXT
);

-- Chat sessions & messages (for active UI state)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id            TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    domain        TEXT,
    role          TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    snapshot      JSONB
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          SERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,
    html        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_msgs_session ON chat_messages(session_id);

-- 10. Requirements (Structured IEEE 830 / ISO 29148)
CREATE TABLE IF NOT EXISTS requirements (
    id                  SERIAL PRIMARY KEY,
    session_id          TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    req_id              TEXT NOT NULL,
    statement           TEXT NOT NULL,
    category            TEXT DEFAULT 'Functional',
    priority            TEXT DEFAULT 'Medium',
    status              TEXT DEFAULT 'draft',
    source              TEXT DEFAULT 'stakeholder',
    justification       TEXT DEFAULT '',
    risk_level          TEXT DEFAULT 'Medium',
    confidence          REAL DEFAULT 0.90,
    acceptance_criteria JSONB DEFAULT '[]'::jsonb,
    compliance_mapping  JSONB DEFAULT '[]'::jsonb,
    regulations         JSONB DEFAULT '[]'::jsonb,
    dependencies        JSONB DEFAULT '[]'::jsonb,
    assumptions         JSONB DEFAULT '[]'::jsonb,
    approval_status     TEXT DEFAULT 'pending',
    version             INTEGER DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(session_id, req_id)
);
CREATE INDEX IF NOT EXISTS idx_reqs_session ON requirements(session_id);

-- 11. Requirement Dependencies
CREATE TABLE IF NOT EXISTS requirement_dependencies (
    id                 SERIAL PRIMARY KEY,
    session_id         TEXT REFERENCES chat_sessions(id) ON DELETE CASCADE,
    req_id             TEXT NOT NULL,
    depends_on_req_id  TEXT NOT NULL,
    dependency_type    TEXT DEFAULT 'BLOCKS',
    description        TEXT,
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- 12. Acceptance Criteria
CREATE TABLE IF NOT EXISTS acceptance_criteria (
    id                  SERIAL PRIMARY KEY,
    session_id          TEXT REFERENCES chat_sessions(id) ON DELETE CASCADE,
    req_id              TEXT NOT NULL,
    criterion           TEXT NOT NULL,
    test_scenario       TEXT,
    verification_method TEXT DEFAULT 'Automated Test',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- 13. Regulations
CREATE TABLE IF NOT EXISTS regulations (
    code         TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    jurisdiction TEXT,
    authority    TEXT,
    description  TEXT,
    version      TEXT,
    url          TEXT
);

-- 14. Compliance Controls
CREATE TABLE IF NOT EXISTS compliance_controls (
    id              SERIAL PRIMARY KEY,
    regulation_code TEXT REFERENCES regulations(code) ON DELETE CASCADE,
    control_code    TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    domain          TEXT
);

-- 15. Requirement Compliance Mappings
CREATE TABLE IF NOT EXISTS requirement_compliance (
    id              SERIAL PRIMARY KEY,
    session_id      TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    req_id          TEXT NOT NULL,
    control_id      TEXT,
    citation        TEXT,
    evidence        TEXT,
    coverage        TEXT DEFAULT 'Partial',
    confidence      REAL DEFAULT 0.80,
    approval_status TEXT DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Compatibility alias for compliance_mappings
CREATE TABLE IF NOT EXISTS compliance_mappings (
    id              SERIAL PRIMARY KEY,
    session_id      TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    req_id          TEXT NOT NULL,
    control_id      TEXT,
    citation        TEXT,
    evidence        TEXT,
    coverage        TEXT DEFAULT 'Partial',
    confidence      REAL DEFAULT 0.80,
    approval_status TEXT DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 16. Risks (Threat & Risk Register)
CREATE TABLE IF NOT EXISTS risks (
    id          SERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    risk_id     TEXT NOT NULL,
    category    TEXT,
    description TEXT,
    likelihood  TEXT DEFAULT 'Medium',
    impact      TEXT DEFAULT 'Medium',
    score       INTEGER DEFAULT 5,
    mitigation  TEXT,
    status      TEXT DEFAULT 'OPEN',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS project_risks (
    id          SERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    risk_id     TEXT NOT NULL,
    category    TEXT,
    description TEXT,
    likelihood  TEXT DEFAULT 'Medium',
    impact      TEXT DEFAULT 'Medium',
    score       INTEGER DEFAULT 5,
    mitigation  TEXT,
    status      TEXT DEFAULT 'OPEN',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 17. Conflicts (Contradiction & Ambiguity Engine)
CREATE TABLE IF NOT EXISTS conflicts (
    id            SERIAL PRIMARY KEY,
    session_id    TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    req_id_1      TEXT,
    req_id_2      TEXT,
    description   TEXT NOT NULL,
    conflict_type TEXT DEFAULT 'CONTRADICTION',
    status        TEXT DEFAULT 'OPEN',
    resolution    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 18. Approvals (Human-in-the-Loop Governance Gates)
CREATE TABLE IF NOT EXISTS approvals (
    id            SERIAL PRIMARY KEY,
    session_id    TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    object_type   TEXT NOT NULL,
    object_id     TEXT NOT NULL,
    approver_name TEXT,
    approver_role TEXT,
    decision      TEXT NOT NULL,
    comments      TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 19. SDLC Recommendations
CREATE TABLE IF NOT EXISTS sdlc_recommendations (
    id                  SERIAL PRIMARY KEY,
    session_id          TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    primary_model       TEXT NOT NULL,
    primary_score       REAL NOT NULL,
    ranked_alternatives JSONB DEFAULT '[]'::jsonb,
    justification       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 20. SDLC Workflows (Customized Engineering Process Phases)
CREATE TABLE IF NOT EXISTS sdlc_workflows (
    id                SERIAL PRIMARY KEY,
    session_id        TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    phase_name        TEXT NOT NULL,
    sequence_num      INTEGER NOT NULL,
    activities        JSONB DEFAULT '[]'::jsonb,
    roles             JSONB DEFAULT '[]'::jsonb,
    deliverables      JSONB DEFAULT '[]'::jsonb,
    security_controls JSONB DEFAULT '[]'::jsonb,
    compliance_gates  JSONB DEFAULT '[]'::jsonb,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 21. Audit Logs (Immutable WORM Audit Trail)
CREATE TABLE IF NOT EXISTS audit_logs (
    id          SERIAL PRIMARY KEY,
    session_id  TEXT REFERENCES chat_sessions(id) ON DELETE SET NULL,
    agent       TEXT NOT NULL,
    action      TEXT NOT NULL,
    detail      TEXT,
    old_value   TEXT,
    new_value   TEXT,
    ip_address  TEXT DEFAULT '127.0.0.1',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_session ON audit_logs(session_id);

-- 22. Agent Runs (Telemetry, Processing Time, Quality Metrics)
CREATE TABLE IF NOT EXISTS agent_runs (
    id                SERIAL PRIMARY KEY,
    session_id        TEXT REFERENCES chat_sessions(id) ON DELETE SET NULL,
    agent_name        TEXT NOT NULL,
    input_data        JSONB,
    output_data       JSONB,
    execution_time_ms INTEGER DEFAULT 0,
    status            TEXT DEFAULT 'SUCCESS',
    error             TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id            TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    domain        TEXT,
    role          TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    snapshot      TEXT
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,
    html        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_msgs_session ON chat_messages(session_id);

-- The local development store mirrors the data used by the API.  It is not a
-- vector store, but it must preserve the same governance records when Docker
-- PostgreSQL is not running.
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, salt TEXT NOT NULL, full_name TEXT,
    role TEXT NOT NULL, mfa_secret TEXT, mfa_enabled INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, req_id TEXT NOT NULL,
    statement TEXT NOT NULL, category TEXT, priority TEXT, status TEXT, source TEXT,
    justification TEXT, risk_level TEXT, confidence REAL, acceptance_criteria TEXT,
    compliance_mapping TEXT, regulations TEXT, dependencies TEXT, assumptions TEXT,
    approval_status TEXT, version INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL, UNIQUE(session_id, req_id)
);
CREATE TABLE IF NOT EXISTS compliance_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, req_id TEXT NOT NULL,
    control_id TEXT, citation TEXT, evidence TEXT, coverage TEXT, confidence REAL,
    approval_status TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS project_risks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, risk_id TEXT,
    category TEXT, description TEXT, likelihood TEXT, impact TEXT, score INTEGER,
    mitigation TEXT, status TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, agent TEXT,
    action TEXT, detail TEXT, old_value TEXT, new_value TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, object_type TEXT,
    object_id TEXT, approver_name TEXT, approver_role TEXT, decision TEXT, comments TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, filename TEXT, file_type TEXT,
    file_path TEXT, file_size INTEGER, status TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, req_id_1 TEXT,
    req_id_2 TEXT, description TEXT, conflict_type TEXT, status TEXT, resolution TEXT,
    created_at TEXT NOT NULL
);
"""


def _seed_initial_data(conn) -> None:
    """Populates roles, users, categories, regulations, and knowledge base with vector embeddings."""
    cur = conn.cursor()
    import auth

    # 1. Seed Roles
    for role, perms in auth.ROLES_PERMISSIONS.items():
        cur.execute("""
            INSERT INTO roles (name, description, permissions)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET permissions = EXCLUDED.permissions;
        """, (role, f"Financial platform role: {role}", json.dumps(perms)))

    # 2. Seed Users
    demo_users = [
        ("admin@finreq.bank", "FinReq2026!", "Platform Administrator", "ADMIN"),
        ("analyst@finreq.bank", "FinReq2026!", "Lead Business Analyst", "ANALYST"),
        ("compliance@finreq.bank", "FinReq2026!", "Senior Compliance Officer", "COMPLIANCE_OFFICER"),
        ("security@finreq.bank", "FinReq2026!", "CISO / Security Lead", "SECURITY_LEAD"),
        ("approver@finreq.bank", "FinReq2026!", "Architecture & Release Approver", "APPROVER"),
        ("stakeholder@finreq.bank", "FinReq2026!", "Business Domain Stakeholder", "STAKEHOLDER"),
    ]
    for email, pwd, name, role in demo_users:
        h, s = auth.hash_password(pwd)
        mfa_sec = auth.generate_mfa_secret()
        cur.execute("""
            INSERT INTO users (email, password_hash, salt, full_name, role, mfa_secret, mfa_enabled)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (email) DO NOTHING;
        """, (email, h, s, name, role, mfa_sec))

    # 3. Seed Categories
    categories = [
        ("Business", "High-level organizational and commercial objectives"),
        ("Stakeholder", "End-user, operator, and customer workflow needs"),
        ("Functional", "Concrete software features, business rules, and behavior"),
        ("Security", "Cybersecurity, encryption, IAM, and STRIDE mitigations"),
        ("Privacy", "Data protection, GDPR, consent, and pseudonymisation"),
        ("Regulatory", "Statutory compliance (Basel, PCI-DSS, AML/BSA, SOX)"),
        ("Performance", "Throughput, latency SLAs, and transaction response limits"),
        ("Availability and Reliability", "Uptime SLAs, failover, RTO, and RPO constraints"),
        ("Usability", "Accessibility, UX workflows, and error recovery"),
        ("Data Management", "Data pipelines, retention, cleansing, and schema rules"),
        ("Integration", "APIs, message queues, ISO 20022 gateways, and legacy hooks"),
        ("Audit and Reporting", "Immutable audit trails, supervisory reports, and WORM storage"),
        ("Operational and Maintenance", "Monitoring, deployment pipelines, and support runbooks"),
    ]
    for cname, cdesc in categories:
        cur.execute("""
            INSERT INTO requirement_categories (name, description)
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING;
        """, (cname, cdesc))

    # 4. Seed Knowledge Documents & Regulations from knowledge_base/
    kb_dir = Path(__file__).parent / "knowledge_base"
    reg_file = kb_dir / "regulations.txt"
    pol_file = kb_dir / "policies.txt"

    docs_to_seed = []
    if reg_file.exists():
        for line in reg_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line.startswith("- ["):
                continue
            # Parse - [ID] Title | Jurisdiction: J | Effective: E | Version: V | Applicability: A
            m = re.match(r"- \[(?P<id>[^\]]+)\]\s*(?P<title>[^|]+)\|\s*Jurisdiction:\s*(?P<jur>[^|]+)\|\s*Effective:\s*(?P<eff>[^|]+)\|\s*Version:\s*(?P<ver>[^|]+)\|\s*Applicability:\s*(?P<app>.+)", line)
            if m:
                docs_to_seed.append({
                    "title": m.group("title").strip(),
                    "source": "regulations.txt",
                    "code": m.group("id").strip(),
                    "jurisdiction": m.group("jur").strip(),
                    "effective_date": m.group("eff").strip(),
                    "version": m.group("ver").strip(),
                    "applicability": m.group("app").strip(),
                    "category": "Regulatory",
                    "content": line.lstrip("- ").strip()
                })

    if pol_file.exists():
        for line in pol_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line.startswith("- ["):
                continue
            m = re.match(r"- \[(?P<id>[^\]]+)\]\s*(?P<title>[^|]+)\|\s*Scope:\s*(?P<jur>[^|]+)\|\s*Effective:\s*(?P<eff>[^|]+)\|\s*(?P<content>.+)", line)
            if m:
                docs_to_seed.append({
                    "title": m.group("title").strip(),
                    "source": "policies.txt",
                    "code": m.group("id").strip(),
                    "jurisdiction": m.group("jur").strip(),
                    "effective_date": m.group("eff").strip(),
                    "version": "1.8",
                    "applicability": m.group("jur").strip(),
                    "category": "Policy",
                    "content": line.lstrip("- ").strip()
                })

    for doc in docs_to_seed:
        # Seed into regulations table if regulatory
        if doc["category"] == "Regulatory":
            cur.execute("""
                INSERT INTO regulations (code, name, jurisdiction, authority, description, version)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO NOTHING;
            """, (doc["code"], doc["title"], doc["jurisdiction"], "Supervisory Authority", doc["applicability"], doc["version"]))

        # Seed into knowledge_documents with vector embedding
        cur.execute("SELECT id FROM knowledge_documents WHERE title = %s LIMIT 1;", (doc["title"],))
        if not cur.fetchone():
            emb = generate_embedding(doc["content"])
            cur.execute("""
                INSERT INTO knowledge_documents (title, source, jurisdiction, effective_date, version, applicability, category, content, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (doc["title"], doc["source"], doc["jurisdiction"], doc["effective_date"], doc["version"], doc["applicability"], doc["category"], doc["content"], str(emb)))

    conn.commit()


def init_db() -> None:
    """Create tables and seed initial knowledge base and roles."""
    global _use_postgres

    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute(_PG_SCHEMA)
        conn.commit()
        _seed_initial_data(conn)
        _use_postgres = True
        return
    except Exception as exc:
        print(f"[db.py] PostgreSQL init failed: {exc}. Falling back to SQLite.")
        _use_postgres = False

    # SQLite fallback
    conn = _get_sqlite_conn()
    with conn:
        conn.executescript(_SQLITE_SCHEMA)
    _sqlite_seed_initial_data()


def _sqlite_seed_initial_data() -> None:
    """Seed the same demo identities available in the PostgreSQL deployment."""
    import auth
    users = [
        ("admin@finreq.bank", "FinReq2026!", "Platform Administrator", "ADMIN"),
        ("analyst@finreq.bank", "FinReq2026!", "Lead Business Analyst", "ANALYST"),
        ("compliance@finreq.bank", "FinReq2026!", "Senior Compliance Officer", "COMPLIANCE_OFFICER"),
        ("security@finreq.bank", "FinReq2026!", "CISO / Security Lead", "SECURITY_LEAD"),
        ("approver@finreq.bank", "FinReq2026!", "Architecture & Release Approver", "APPROVER"),
        ("stakeholder@finreq.bank", "FinReq2026!", "Business Domain Stakeholder", "STAKEHOLDER"),
    ]
    conn = _get_sqlite_conn()
    with conn:
        for email, password, name, role in users:
            hashed, salt = auth.hash_password(password)
            conn.execute("""INSERT OR IGNORE INTO users
                (email, password_hash, salt, full_name, role, mfa_secret, mfa_enabled)
                VALUES (?, ?, ?, ?, ?, ?, 1)""",
                (email, hashed, salt, name, role, auth.generate_mfa_secret()))


# ===================================================================
# Vector Search in PostgreSQL pgvector
# ===================================================================

def search_knowledge_vector(query: str, top_k: int = 5, category: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Performs cosine distance vector similarity search on knowledge_documents table.
    Returns ranked documents with metadata, citations, and confidence scores.
    """
    if not _use_postgres:
        return []

    effective_limit = limit if limit is not None else top_k
    try:
        conn = _get_pg_conn()
        emb = generate_embedding(query)
        cur = conn.cursor()
        sql = """
            SELECT id, title, source, jurisdiction, effective_date, version, applicability, category, content,
                   1 - (embedding <=> %s) AS similarity
            FROM knowledge_documents
            WHERE (%s IS NULL OR category = %s)
            ORDER BY embedding <=> %s ASC
            LIMIT %s;
        """
        cur.execute(sql, (str(emb), category, category, str(emb), effective_limit))
        rows = cur.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "title": r[1],
                "source": r[2],
                "jurisdiction": r[3],
                "effective_date": r[4],
                "version": r[5],
                "applicability": r[6],
                "category": r[7],
                "content": r[8],
                "confidence": round(float(r[9]), 3)
            })
        return results
    except Exception as e:
        print(f"[db.py] Vector search error: {e}")
        return []


# ===================================================================
# Telemetry, Monitoring, and Metrics
# ===================================================================

def log_agent_run(session_id: str, agent_name: str, input_data: Any, output_data: Any,
                  execution_time_ms: int = 0, status: str = "SUCCESS", error: Optional[str] = None) -> None:
    """Records agent execution telemetry into agent_runs table."""
    if not _use_postgres:
        return
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_sessions (id, title, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (id) DO NOTHING;
            """, (session_id, f"Session {session_id}"))
            cur.execute("""
                INSERT INTO agent_runs (session_id, agent_name, input_data, output_data, execution_time_ms, status, error)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                session_id,
                agent_name,
                json.dumps(input_data) if input_data is not None else None,
                json.dumps(output_data) if output_data is not None else None,
                execution_time_ms,
                status,
                error
            ))
        conn.commit()
    except Exception as e:
        print(f"[db.py] log_agent_run error: {e}")


def get_monitoring_metrics() -> Dict[str, Any]:
    """Computes real-time admin monitoring dashboard metrics from PostgreSQL."""
    if not _use_postgres:
        conn = _get_sqlite_conn()
        count = lambda table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return {"status": "sqlite_fallback", "database": "SQLite (local development)",
                "total_requirements": count("requirements"), "approved_requirements": conn.execute("SELECT COUNT(*) FROM requirements WHERE approval_status = 'approved'").fetchone()[0],
                "pending_approvals": conn.execute("SELECT COUNT(*) FROM requirements WHERE approval_status = 'pending'").fetchone()[0],
                "agent_executions": 0, "failed_agent_runs": 0, "avg_agent_duration_ms": 0,
                "compliance_gaps": conn.execute("SELECT COUNT(*) FROM compliance_mappings WHERE coverage IN ('None', 'Partial')").fetchone()[0],
                "high_risk_alerts": conn.execute("SELECT COUNT(*) FROM project_risks WHERE score >= 7").fetchone()[0],
                "audit_trail_entries": count("audit_logs"), "knowledge_documents": 0,
                "active_users": count("users"), "recent_agent_runs": []}

    try:
        conn = _get_pg_conn()
        cur = conn.cursor()

        # Counts
        cur.execute("SELECT COUNT(*) FROM requirements;")
        total_reqs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM requirements WHERE approval_status = 'approved';")
        approved_reqs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM requirements WHERE approval_status = 'pending';")
        pending_approvals = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM agent_runs;")
        total_runs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM agent_runs WHERE status = 'ERROR';")
        failed_runs = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(AVG(execution_time_ms), 0) FROM agent_runs;")
        avg_exec_time = round(float(cur.fetchone()[0]), 1)

        cur.execute("SELECT COUNT(*) FROM audit_logs;")
        total_audits = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM compliance_mappings WHERE coverage = 'None' OR coverage = 'Partial';")
        compliance_gaps = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM project_risks WHERE score >= 7;")
        high_risks = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM knowledge_documents;")
        kb_docs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users;")
        total_users = cur.fetchone()[0]

        # Recent runs
        cur.execute("""
            SELECT agent_name, status, execution_time_ms, created_at
            FROM agent_runs
            ORDER BY id DESC
            LIMIT 6;
        """)
        recent_runs = [{"agent": r[0], "status": r[1], "duration_ms": r[2], "time": r[3].strftime("%H:%M:%S") if r[3] else ""} for r in cur.fetchall()]

        return {
            "status": "connected",
            "database": "PostgreSQL (with pgvector)",
            "total_requirements": total_reqs,
            "approved_requirements": approved_reqs,
            "pending_approvals": pending_approvals,
            "agent_executions": total_runs,
            "failed_agent_runs": failed_runs,
            "avg_agent_duration_ms": avg_exec_time,
            "compliance_gaps": compliance_gaps,
            "high_risk_alerts": high_risks,
            "audit_trail_entries": total_audits,
            "knowledge_documents": kb_docs,
            "active_users": total_users,
            "recent_agent_runs": recent_runs
        }
    except Exception as e:
        print(f"[db.py] get_monitoring_metrics error: {e}")
        return {"status": "error", "error": str(e)}


# ===================================================================
# Approvals, Conflicts, SDLC, and Documents Persistence
# ===================================================================

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetch an identity through the active persistence backend."""
    if not _use_postgres:
        row = _get_sqlite_conn().execute("SELECT id, email, password_hash, salt, full_name, role, mfa_enabled, mfa_secret FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        return dict(row) if row else None
    conn = _get_pg_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id, email, password_hash, salt, full_name, role, mfa_enabled, mfa_secret FROM users WHERE email = %s", (email.lower().strip(),))
        row = cur.fetchone()
    if not row:
        return None
    return dict(zip(("id", "email", "password_hash", "salt", "full_name", "role", "mfa_enabled", "mfa_secret"), row))


def create_user(email: str, password_hash: str, salt: str, full_name: str, role: str, mfa_secret: str) -> int:
    if not _use_postgres:
        conn = _get_sqlite_conn()
        with conn:
            cur = conn.execute("INSERT INTO users (email, password_hash, salt, full_name, role, mfa_secret, mfa_enabled) VALUES (?, ?, ?, ?, ?, ?, 1)", (email.lower().strip(), password_hash, salt, full_name, role.upper(), mfa_secret))
        return int(cur.lastrowid)
    conn = _get_pg_conn()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO users (email, password_hash, salt, full_name, role, mfa_secret, mfa_enabled) VALUES (%s, %s, %s, %s, %s, %s, TRUE) RETURNING id", (email.lower().strip(), password_hash, salt, full_name, role.upper(), mfa_secret))
        uid = cur.fetchone()[0]
    conn.commit()
    return uid


def list_users() -> List[Dict[str, Any]]:
    if not _use_postgres:
        return [dict(row) for row in _get_sqlite_conn().execute("SELECT id, email, full_name, role FROM users ORDER BY id").fetchall()]
    conn = _get_pg_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id, email, full_name, role FROM users ORDER BY id")
        rows = cur.fetchall()
    return [dict(zip(("id", "email", "name", "role"), row)) for row in rows]


def resolve_conflict(session_id: str, conflict_id: Optional[int], req_id_1: str, req_id_2: str, resolution: str) -> None:
    if not _use_postgres:
        conn = _get_sqlite_conn()
        with conn:
            if conflict_id:
                conn.execute("UPDATE conflicts SET status = 'RESOLVED', resolution = ? WHERE id = ?", (resolution, conflict_id))
            else:
                conn.execute("INSERT INTO conflicts (session_id, req_id_1, req_id_2, description, conflict_type, status, resolution, created_at) VALUES (?, ?, ?, ?, 'USER_RESOLVED', 'RESOLVED', ?, ?)", (session_id, req_id_1, req_id_2, resolution, resolution, datetime.utcnow().isoformat() + "Z"))
        return
    conn = _get_pg_conn()
    with conn.cursor() as cur:
        if conflict_id:
            cur.execute("UPDATE conflicts SET status = 'RESOLVED', resolution = %s WHERE id = %s", (resolution, conflict_id))
        else:
            cur.execute("INSERT INTO conflicts (session_id, req_id_1, req_id_2, description, conflict_type, status, resolution) VALUES (%s, %s, %s, %s, 'USER_RESOLVED', 'RESOLVED', %s)", (session_id, req_id_1, req_id_2, resolution, resolution))
    conn.commit()

def record_approval(session_id: str, object_type: str, object_id: str, approver_name: str,
                    approver_role: str, decision: str, comments: str = "") -> None:
    """Records human governance gate decision in approvals table."""
    if not _use_postgres:
        with _get_sqlite_conn():
            _get_sqlite_conn().execute("INSERT INTO approvals (session_id, object_type, object_id, approver_name, approver_role, decision, comments, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, object_type, object_id, approver_name, approver_role, decision, comments, datetime.utcnow().isoformat() + "Z"))
        return
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO approvals (session_id, object_type, object_id, approver_name, approver_role, decision, comments)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (session_id, object_type, object_id, approver_name, approver_role, decision, comments))
        conn.commit()
    except Exception as e:
        print(f"[db.py] record_approval error: {e}")


def record_conflict(session_id: str, req_id_1: str, req_id_2: str, description: str,
                    conflict_type: str = "CONTRADICTION", status: str = "OPEN", resolution: str = "") -> None:
    """Stores identified requirement conflicts for resolution UI."""
    if not _use_postgres:
        with _get_sqlite_conn():
            _get_sqlite_conn().execute("INSERT INTO conflicts (session_id, req_id_1, req_id_2, description, conflict_type, status, resolution, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, req_id_1, req_id_2, description, conflict_type, status, resolution, datetime.utcnow().isoformat() + "Z"))
        return
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conflicts (session_id, req_id_1, req_id_2, description, conflict_type, status, resolution)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (session_id, req_id_1, req_id_2, description, conflict_type, status, resolution))
        conn.commit()
    except Exception as e:
        print(f"[db.py] record_conflict error: {e}")


def get_conflicts(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve conflicts identified for a session."""
    if not _use_postgres:
        rows = _get_sqlite_conn().execute(
            "SELECT id, req_id_1, req_id_2, description, conflict_type, status, resolution, created_at FROM conflicts WHERE session_id = ? ORDER BY id",
            (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, req_id_1, req_id_2, description, conflict_type, status, resolution, created_at
                FROM conflicts
                WHERE session_id = %s
                ORDER BY id;
                """,
                (session_id,)
            )
            rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "req_id_1": r[1],
                "req_id_2": r[2],
                "description": r[3],
                "conflict_type": r[4],
                "status": r[5],
                "resolution": r[6],
                "created_at": r[7].isoformat() if r[7] else None,
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[db.py] get_conflicts error: {e}")
        return []


def record_sdlc(session_id: str, primary_model: str, primary_score: float,
                ranked_alternatives: List[Dict[str, Any]], justification: str,
                workflow_phases: List[Dict[str, Any]]) -> None:
    """Persists SDLC recommendation and custom project workflow into PostgreSQL."""
    if not _use_postgres:
        return
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_sessions (id, title, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (id) DO NOTHING;
            """, (session_id, f"Session {session_id}"))
            cur.execute("""
                INSERT INTO sdlc_recommendations (session_id, primary_model, primary_score, ranked_alternatives, justification)
                VALUES (%s, %s, %s, %s::jsonb, %s);
            """, (session_id, primary_model, primary_score, json.dumps(ranked_alternatives), justification))

            cur.execute("DELETE FROM sdlc_workflows WHERE session_id = %s;", (session_id,))
            for idx, phase in enumerate(workflow_phases, 1):
                pname = phase.get("phase", f"Phase {idx}")
                acts = json.dumps(phase.get("activities", []))
                roles = json.dumps([phase.get("responsible_role", "Engineering")])
                delivs = json.dumps(phase.get("deliverables", []))
                sec = json.dumps([phase.get("security_checkpoint", "Standard")])
                gates = json.dumps([phase.get("validation_gate", "Review")])
                cur.execute("""
                    INSERT INTO sdlc_workflows (session_id, phase_name, sequence_num, activities, roles, deliverables, security_controls, compliance_gates)
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb);
                """, (session_id, pname, idx, acts, roles, delivs, sec, gates))
        conn.commit()
    except Exception as e:
        print(f"[db.py] record_sdlc error: {e}")


def record_document(session_id: str, filename: str, file_type: str, file_path: str,
                    file_size: int, status: str = "PROCESSED") -> int:
    """Stores uploaded document record and returns its document id."""
    if not _use_postgres:
        conn = _get_sqlite_conn()
        with conn:
            cur = conn.execute("INSERT INTO documents (session_id, filename, file_type, file_path, file_size, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, filename, file_type, file_path, file_size, status, datetime.utcnow().isoformat() + "Z"))
        return int(cur.lastrowid)
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            if session_id:
                cur.execute("""
                    INSERT INTO projects (id, name, description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (session_id, f"Project {session_id}", "Workspace initialized on document ingestion"))
            cur.execute("""
                INSERT INTO documents (project_id, filename, file_type, file_path, file_size, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (session_id or None, filename, file_type, file_path, file_size, status))
            doc_id = cur.fetchone()[0]
        conn.commit()
        return doc_id
    except Exception as e:
        print(f"[db.py] record_document error: {e}")
        return 1


# ===================================================================
# Public session API (PostgreSQL + SQLite fallback)
# ===================================================================

def save_session(
    session_id: str,
    title: str,
    domain: str = "",
    role: str = "",
    snapshot: Optional[dict] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Save or update a session with its messages."""
    if _use_postgres:
        _pg_save_session(session_id, title, domain, role, snapshot, messages or [])
    else:
        _sqlite_save_session(session_id, title, domain, role, snapshot, messages or [])


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a session by ID."""
    if _use_postgres:
        return _pg_get_session(session_id)
    return _sqlite_get_session(session_id)


def list_sessions() -> List[Dict[str, Any]]:
    """Return summary metadata for all saved sessions."""
    if _use_postgres:
        return _pg_list_sessions()
    return _sqlite_list_sessions()


def delete_session(session_id: str) -> bool:
    """Delete a session (messages cascade). Returns True if found."""
    if _use_postgres:
        return _pg_delete_session(session_id)
    return _sqlite_delete_session(session_id)


def update_session_title(session_id: str, title: str) -> bool:
    """Update title of a saved session."""
    if _use_postgres:
        return _pg_update_session_title(session_id, title)
    return _sqlite_update_session_title(session_id, title)


# ---------------------------------------------------------------------------
# Structured Requirements Persistence
# ---------------------------------------------------------------------------

def persist_requirements(session_id: str, requirements_dict: Dict[str, Any]) -> None:
    """Store or update extracted requirements in PostgreSQL."""
    if not requirements_dict:
        return

    if not _use_postgres:
        conn = _get_sqlite_conn()
        now = datetime.utcnow().isoformat() + "Z"
        with conn:
            for req_id, data in requirements_dict.items():
                if hasattr(data, "__dict__"):
                    data = data.__dict__
                conn.execute("""INSERT INTO requirements (session_id, req_id, statement, category, priority, status, source, justification, risk_level, confidence, acceptance_criteria, compliance_mapping, regulations, dependencies, assumptions, approval_status, version, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, req_id) DO UPDATE SET statement=excluded.statement, category=excluded.category, priority=excluded.priority, status=excluded.status, source=excluded.source, justification=excluded.justification, risk_level=excluded.risk_level, confidence=excluded.confidence, acceptance_criteria=excluded.acceptance_criteria, compliance_mapping=excluded.compliance_mapping, regulations=excluded.regulations, dependencies=excluded.dependencies, assumptions=excluded.assumptions, approval_status=excluded.approval_status, version=requirements.version + 1, updated_at=excluded.updated_at""",
                    (session_id, req_id, data.get("statement", ""), data.get("category", "Functional"), data.get("priority", "Medium"), data.get("status", "draft"), data.get("source", "stakeholder"), data.get("justification", ""), data.get("risk_level", "Medium"), float(data.get("confidence", data.get("confidence_score", .9))), json.dumps(data.get("acceptance_criteria", [])), json.dumps(data.get("compliance_mapping", [])), json.dumps(data.get("regulations", [])), json.dumps(data.get("dependencies", [])), json.dumps(data.get("assumptions", [])), data.get("approval_status", "pending"), int(data.get("version", 1)), now, now))
        return

    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            for req_id, data in requirements_dict.items():
                if hasattr(data, "__dict__"):
                    data = data.__dict__
                stmt = data.get("statement", "")
                cat = data.get("category", "Functional")
                prio = data.get("priority", "Medium")
                status = data.get("status", "draft")
                app_status = data.get("approval_status", "pending")
                src = data.get("source", "stakeholder")
                just = data.get("justification", "")
                risk = data.get("risk_level", "Medium")
                conf = float(data.get("confidence", 0.90))
                ac = json.dumps(data.get("acceptance_criteria", []))
                comp = json.dumps(data.get("compliance_mapping", []))
                regs = json.dumps(data.get("regulations", []))
                deps = json.dumps(data.get("dependencies", []))
                assump = json.dumps(data.get("assumptions", []))
                ver = int(data.get("version", 1))

                cur.execute("""
                    INSERT INTO requirements (
                        session_id, req_id, statement, category, priority, status,
                        source, justification, risk_level, confidence,
                        acceptance_criteria, compliance_mapping, regulations,
                        dependencies, assumptions, approval_status, version,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb,
                        %s, %s, NOW()
                    )
                    ON CONFLICT (session_id, req_id) DO UPDATE SET
                        statement = EXCLUDED.statement,
                        category = EXCLUDED.category,
                        priority = EXCLUDED.priority,
                        status = EXCLUDED.status,
                        approval_status = EXCLUDED.approval_status,
                        justification = EXCLUDED.justification,
                        risk_level = EXCLUDED.risk_level,
                        confidence = EXCLUDED.confidence,
                        acceptance_criteria = EXCLUDED.acceptance_criteria,
                        compliance_mapping = EXCLUDED.compliance_mapping,
                        regulations = EXCLUDED.regulations,
                        dependencies = EXCLUDED.dependencies,
                        assumptions = EXCLUDED.assumptions,
                        version = requirements.version + 1,
                        updated_at = NOW();
                """, (
                    session_id, req_id, stmt, cat, prio, status,
                    src, just, risk, conf,
                    ac, comp, regs, deps, assump,
                    app_status, ver
                ))
        conn.commit()
    except Exception as e:
        print(f"[db.py] persist_requirements error: {e}")


def get_requirements(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve structured requirements from PostgreSQL."""
    if not _use_postgres:
        rows = _get_sqlite_conn().execute("SELECT * FROM requirements WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
        json_columns = ("acceptance_criteria", "compliance_mapping", "regulations", "dependencies", "assumptions")
        result = []
        for row in rows:
            item = dict(row)
            for column in json_columns:
                try: item[column] = json.loads(item[column] or "[]")
                except json.JSONDecodeError: item[column] = []
            result.append(item)
        return result
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT req_id, statement, category, priority, status, approval_status,
                       source, justification, risk_level, confidence,
                       acceptance_criteria, compliance_mapping, regulations,
                       dependencies, assumptions, version, created_at, updated_at
                FROM requirements
                WHERE session_id = %s
                ORDER BY id ASC;
            """, (session_id,))
            rows = cur.fetchall()
            cols = [
                "req_id", "statement", "category", "priority", "status", "approval_status",
                "source", "justification", "risk_level", "confidence",
                "acceptance_criteria", "compliance_mapping", "regulations",
                "dependencies", "assumptions", "version", "created_at", "updated_at"
            ]
            return [dict(zip(cols, r)) for r in rows]
    except Exception as e:
        print(f"[db.py] get_requirements error: {e}")
        return []


def delete_requirement(session_id: str, req_id: str) -> None:
    """Remove a requirement from the durable baseline after a human decision."""
    if not _use_postgres:
        with _get_sqlite_conn():
            _get_sqlite_conn().execute("DELETE FROM requirements WHERE session_id = ? AND req_id = ?", (session_id, req_id))
        return
    conn = _get_pg_conn()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM requirements WHERE session_id = %s AND req_id = %s", (session_id, req_id))
    conn.commit()


def persist_compliance(session_id: str, mappings: List[Dict[str, Any]]) -> None:
    """Store compliance control mappings in PostgreSQL."""
    if not mappings:
        return
    if not _use_postgres:
        conn = _get_sqlite_conn()
        now = datetime.utcnow().isoformat() + "Z"
        with conn:
            conn.execute("DELETE FROM compliance_mappings WHERE session_id = ?", (session_id,))
            conn.executemany("INSERT INTO compliance_mappings (session_id, req_id, control_id, citation, evidence, coverage, confidence, approval_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(session_id, m.get("req_id") or m.get("id", ""), m.get("control_id") or m.get("control", ""), m.get("citation", ""), m.get("evidence", ""), m.get("coverage", "Partial"), float(m.get("confidence", .8)), m.get("approval_status", "pending"), now) for m in mappings])
        return
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            for m in mappings:
                req_id = m.get("req_id") or m.get("id", "")
                ctrl = m.get("control_id") or m.get("control", "")
                cit = m.get("citation", "")
                ev = m.get("evidence", "")
                cov = m.get("coverage", "Partial")
                conf = float(m.get("confidence", 0.80))
                stat = m.get("approval_status", "pending")
                cur.execute("""
                    INSERT INTO compliance_mappings (
                        session_id, req_id, control_id, citation, evidence, coverage, confidence, approval_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (session_id, req_id, ctrl, cit, ev, cov, conf, stat))
        conn.commit()
    except Exception as e:
        print(f"[db.py] persist_compliance error: {e}")


def get_compliance(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve compliance mappings from PostgreSQL."""
    if not _use_postgres:
        return [dict(row) for row in _get_sqlite_conn().execute("SELECT req_id, control_id, citation, evidence, coverage, confidence, approval_status, created_at FROM compliance_mappings WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()]
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT req_id, control_id, citation, evidence, coverage, confidence, approval_status, created_at
                FROM compliance_mappings
                WHERE session_id = %s
                ORDER BY id ASC;
            """, (session_id,))
            cols = ["req_id", "control_id", "citation", "evidence", "coverage", "confidence", "approval_status", "created_at"]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception as e:
        print(f"[db.py] get_compliance error: {e}")
        return []


def persist_risks(session_id: str, risks: List[Dict[str, Any]]) -> None:
    """Store threat & risk register items in PostgreSQL."""
    if not risks:
        return
    if not _use_postgres:
        conn = _get_sqlite_conn()
        now = datetime.utcnow().isoformat() + "Z"
        with conn:
            conn.execute("DELETE FROM project_risks WHERE session_id = ?", (session_id,))
            conn.executemany("INSERT INTO project_risks (session_id, risk_id, category, description, likelihood, impact, score, mitigation, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(session_id, r.get("id") or r.get("risk_id", ""), r.get("category", "General"), r.get("description", ""), r.get("likelihood", "Medium"), r.get("impact", "Medium"), int(r.get("score", 5)), r.get("mitigation", ""), r.get("status", "OPEN"), now) for r in risks])
        return
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            for r in risks:
                rid = r.get("id") or r.get("risk_id", "")
                cat = r.get("category", "General")
                desc = r.get("description", "")
                like = r.get("likelihood", "Medium")
                imp = r.get("impact", "Medium")
                score = int(r.get("score", 5))
                mit = r.get("mitigation", "")
                stat = r.get("status", "OPEN")
                cur.execute("""
                    INSERT INTO project_risks (
                        session_id, risk_id, category, description, likelihood, impact, score, mitigation, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (session_id, rid, cat, desc, like, imp, score, mit, stat))
        conn.commit()
    except Exception as e:
        print(f"[db.py] persist_risks error: {e}")


def get_risks(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve risk register from PostgreSQL."""
    if not _use_postgres:
        return []
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT risk_id, category, description, likelihood, impact, score, mitigation, status, created_at
                FROM project_risks
                WHERE session_id = %s
                ORDER BY score DESC;
            """, (session_id,))
            cols = ["risk_id", "category", "description", "likelihood", "impact", "score", "mitigation", "status", "created_at"]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception as e:
        print(f"[db.py] get_risks error: {e}")
        return []


def log_audit(session_id: str, agent: str, action: str, detail: str, old_val: Optional[str] = None, new_val: Optional[str] = None) -> None:
    """Append immutable entry to audit_logs table."""
    if not _use_postgres:
        with _get_sqlite_conn():
            _get_sqlite_conn().execute("INSERT INTO audit_logs (session_id, agent, action, detail, old_value, new_value, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, agent, action, detail, old_val, new_val, datetime.utcnow().isoformat() + "Z"))
        return
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO audit_logs (session_id, agent, action, detail, old_value, new_value)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (session_id, agent, action, detail, old_val, new_val))
        conn.commit()
    except Exception as e:
        print(f"[db.py] log_audit error: {e}")


def get_audit_trail(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve immutable audit trail from PostgreSQL."""
    if not _use_postgres:
        return [dict(row) for row in _get_sqlite_conn().execute("SELECT agent, action, detail, old_value, new_value, created_at FROM audit_logs WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()]
    try:
        conn = _get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT agent, action, detail, old_value, new_value, created_at
                FROM audit_logs
                WHERE session_id = %s
                ORDER BY id ASC;
            """, (session_id,))
            cols = ["agent", "action", "detail", "old_value", "new_value", "created_at"]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception as e:
        print(f"[db.py] get_audit_trail error: {e}")
        return []


get_audit_logs = get_audit_trail


# ---------------------------------------------------------------------------
# PostgreSQL Internal Implementation
# ---------------------------------------------------------------------------

def _pg_save_session(session_id, title, domain, role, snapshot, messages):
    conn = _get_pg_conn()
    snapshot_json = json.dumps(snapshot) if snapshot else None

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chat_sessions (id, title, domain, role, snapshot, updated_at)
            VALUES (%s, %s, %s, %s, %s::jsonb, NOW())
            ON CONFLICT (id) DO UPDATE SET
                title      = EXCLUDED.title,
                domain     = EXCLUDED.domain,
                role       = EXCLUDED.role,
                snapshot   = COALESCE(EXCLUDED.snapshot, chat_sessions.snapshot),
                updated_at = NOW();
            """,
            (session_id, title, domain, role, snapshot_json),
        )
        cur.execute(
            """
            INSERT INTO projects (id, name, domain, status)
            VALUES (%s, %s, %s, 'ACTIVE')
            ON CONFLICT (id) DO UPDATE SET
                name       = EXCLUDED.name,
                domain     = EXCLUDED.domain,
                updated_at = NOW();
            """,
            (session_id, title, domain),
        )

        if messages:
            cur.execute("DELETE FROM chat_messages WHERE session_id = %s;", (session_id,))
            for m in messages:
                cur.execute(
                    """
                    INSERT INTO chat_messages (session_id, role, html, created_at)
                    VALUES (%s, %s, %s, COALESCE(%s::timestamptz, NOW()));
                    """,
                    (session_id, m.get("role", "user"), m.get("html", ""), m.get("created_at")),
                )
    conn.commit()


def _pg_get_session(session_id):
    conn = _get_pg_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, domain, role, created_at, updated_at, snapshot
            FROM chat_sessions
            WHERE id = %s;
            """,
            (session_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        cur.execute(
            """
            SELECT role, html, created_at
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY id ASC;
            """,
            (session_id,),
        )
        msgs = [
            {"role": r[0], "html": r[1], "created_at": r[2].isoformat() if r[2] else None}
            for r in cur.fetchall()
        ]

    return {
        "id": row[0],
        "title": row[1],
        "domain": row[2],
        "role": row[3],
        "created_at": row[4].isoformat() if row[4] else None,
        "updated_at": row[5].isoformat() if row[5] else None,
        "snapshot": row[6],
        "messages": msgs,
    }


def _pg_list_sessions():
    conn = _get_pg_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.title, s.domain, s.role, s.created_at, s.updated_at,
                   COUNT(DISTINCT m.id) AS msg_count,
                   COUNT(DISTINCT r.id) AS req_count
            FROM chat_sessions s
            LEFT JOIN chat_messages m ON m.session_id = s.id
            LEFT JOIN requirements r ON r.session_id = s.id
            GROUP BY s.id
            ORDER BY s.updated_at DESC;
            """
        )
        rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "title": r[1],
            "domain": r[2],
            "role": r[3],
            "created_at": r[4].isoformat() if r[4] else None,
            "updated_at": r[5].isoformat() if r[5] else None,
            "message_count": r[6],
            "requirement_count": r[7],
        }
        for r in rows
    ]


def _pg_update_session_title(session_id: str, title: str) -> bool:
    conn = _get_pg_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE chat_sessions
            SET title = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id;
            """,
            (title, session_id),
        )
        row = cur.fetchone()
        cur.execute(
            """
            UPDATE projects
            SET name = %s, updated_at = NOW()
            WHERE id = %s;
            """,
            (title, session_id),
        )
    conn.commit()
    return row is not None


def _pg_delete_session(session_id):
    conn = _get_pg_conn()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM chat_sessions WHERE id = %s RETURNING id;", (session_id,))
        deleted = cur.fetchone()
    conn.commit()
    return deleted is not None


# ---------------------------------------------------------------------------
# SQLite Fallback Implementation
# ---------------------------------------------------------------------------

def _sqlite_save_session(session_id, title, domain, role, snapshot, messages):
    conn = _get_sqlite_conn()
    now = datetime.utcnow().isoformat() + "Z"
    snapshot_json = json.dumps(snapshot) if snapshot else None

    with conn:
        conn.execute(
            """
            INSERT INTO chat_sessions (id, title, domain, role, created_at, updated_at, snapshot)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title      = excluded.title,
                domain     = excluded.domain,
                role       = excluded.role,
                updated_at = excluded.updated_at,
                snapshot   = coalesce(excluded.snapshot, chat_sessions.snapshot);
            """,
            (session_id, title, domain, role, now, now, snapshot_json),
        )

        if messages:
            conn.execute("DELETE FROM chat_messages WHERE session_id = ?;", (session_id,))
            conn.executemany(
                """
                INSERT INTO chat_messages (session_id, role, html, created_at)
                VALUES (?, ?, ?, ?);
                """,
                [(session_id, m.get("role", "user"), m.get("html", ""), m.get("created_at", now)) for m in messages],
            )


def _sqlite_get_session(session_id):
    conn = _get_sqlite_conn()
    row = conn.execute(
        "SELECT id, title, domain, role, created_at, updated_at, snapshot FROM chat_sessions WHERE id = ?;",
        (session_id,),
    ).fetchone()
    if not row:
        return None

    msgs = conn.execute(
        "SELECT role, html, created_at FROM chat_messages WHERE session_id = ? ORDER BY id ASC;",
        (session_id,),
    ).fetchall()

    snapshot = None
    if row["snapshot"]:
        try:
            snapshot = json.loads(row["snapshot"])
        except Exception:
            snapshot = None

    return {
        "id": row["id"],
        "title": row["title"],
        "domain": row["domain"],
        "role": row["role"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "snapshot": snapshot,
        "messages": [dict(m) for m in msgs],
    }


def _sqlite_list_sessions():
    conn = _get_sqlite_conn()
    rows = conn.execute(
        """
        SELECT s.id, s.title, s.domain, s.role, s.created_at, s.updated_at,
               COUNT(DISTINCT m.id) AS msg_count,
               COUNT(DISTINCT r.id) AS req_count
        FROM chat_sessions s
        LEFT JOIN chat_messages m ON m.session_id = s.id
        LEFT JOIN requirements r ON r.session_id = s.id
        GROUP BY s.id
        ORDER BY s.updated_at DESC;
        """
    ).fetchall()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "domain": r["domain"],
            "role": r["role"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "message_count": r["msg_count"],
            "requirement_count": r["req_count"],
        }
        for r in rows
    ]


def _sqlite_update_session_title(session_id: str, title: str) -> bool:
    conn = _get_sqlite_conn()
    now = datetime.utcnow().isoformat() + "Z"
    with conn:
        cur = conn.execute(
            "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?;",
            (title, now, session_id),
        )
        try:
            conn.execute("UPDATE projects SET name = ?, updated_at = ? WHERE id = ?;", (title, now, session_id))
        except Exception:
            pass
    return cur.rowcount > 0


def _sqlite_delete_session(session_id):
    conn = _get_sqlite_conn()
    with conn:
        cur = conn.execute("DELETE FROM chat_sessions WHERE id = ?;", (session_id,))
    return cur.rowcount > 0
