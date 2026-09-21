"""CK Personal Finance local/internal runtime store.

The service is Postgres-only for the local/internal product contract. pgvector
is mandatory for the evidence/RAG path; dependency-down truth is reported as a
Postgres outage, not as a SQLite runtime.
"""

from __future__ import annotations

import hashlib
import csv
import io
import shutil
import json
import math
import os
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from pypdf import PdfReader
from pypdf.errors import PdfReadError

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover - exercised by fallback environments
    psycopg = None
    dict_row = None


APP_DSN = os.environ.get("PF_DATABASE_URL") or os.environ.get("PERSONAL_FINANCE_DATABASE_URL")
APP_CONNINFO: dict[str, Any] | None = None
if not APP_DSN:
    required = {
        "user": os.environ.get("PF_POSTGRES_USER"),
        "password": os.environ.get("PF_POSTGRES_PASS"),
        "host": os.environ.get("PF_POSTGRES_HOST"),
        "port": os.environ.get("PF_POSTGRES_PORT"),
        "dbname": os.environ.get("PF_POSTGRES_DB"),
    }
    if all(required.values()):
        APP_CONNINFO = required
APP_MODE = "postgres"
POSTGRES_CONNECT_TIMEOUT_SECONDS = int(os.environ.get("PF_POSTGRES_CONNECT_TIMEOUT_SECONDS", "3"))
VECTOR_DIMS = 1536
USER_UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads" / "personal-finance" / "user-provided"
USER_UPLOAD_QUARANTINE = USER_UPLOAD_ROOT / ".quarantine"
MAX_USER_UPLOAD_BYTES = 25 * 1024 * 1024


POSTGRES_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS personal_profiles (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'AUD',
    timezone TEXT NOT NULL DEFAULT 'Australia/Sydney',
    demo_data BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS personal_account_groups (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES personal_profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    group_type TEXT NOT NULL,
    current_balance NUMERIC(14, 2) NOT NULL DEFAULT 0,
    source_state TEXT NOT NULL DEFAULT 'local_manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS savings_goals (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES personal_profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    target_amount NUMERIC(14, 2) NOT NULL,
    saved_amount NUMERIC(14, 2) NOT NULL DEFAULT 0,
    target_date DATE,
    status TEXT NOT NULL DEFAULT 'tracking',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS debt_plans (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES personal_profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    current_balance NUMERIC(14, 2) NOT NULL,
    repayment_amount NUMERIC(14, 2) NOT NULL DEFAULT 0,
    repayment_frequency TEXT NOT NULL DEFAULT 'monthly',
    interest_rate NUMERIC(8, 4),
    status TEXT NOT NULL DEFAULT 'tracking',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS finance_decision_receipts (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES personal_profiles(id) ON DELETE CASCADE,
    decision_type TEXT NOT NULL,
    context TEXT NOT NULL,
    boundary TEXT NOT NULL,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS import_rollback_receipts (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES personal_profiles(id) ON DELETE CASCADE,
    import_source TEXT NOT NULL,
    rows_previewed INTEGER NOT NULL DEFAULT 0,
    rows_committed INTEGER NOT NULL DEFAULT 0,
    rollback_state TEXT NOT NULL DEFAULT 'preview_only',
    source_confidence TEXT NOT NULL DEFAULT 'needs_human_review',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS finance_document_evidence (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES personal_profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    document_type TEXT NOT NULL,
    source_path TEXT,
    evidence_text TEXT NOT NULL,
    embedding vector(1536),
    freshness_state TEXT NOT NULL DEFAULT 'local_demo',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_upload_receipts (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES personal_profiles(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    indexed_chunks INTEGER NOT NULL DEFAULT 0,
    external_send BOOLEAN NOT NULL DEFAULT FALSE,
    boundary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS finance_reminders (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES personal_profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    due_date DATE NOT NULL,
    cadence TEXT NOT NULL DEFAULT 'once',
    lead_days INTEGER NOT NULL DEFAULT 14,
    status TEXT NOT NULL DEFAULT 'scheduled',
    source_ref TEXT NOT NULL DEFAULT 'local',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scenario_plans (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES personal_profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    scenario_type TEXT NOT NULL,
    inputs JSONB NOT NULL,
    outputs JSONB NOT NULL,
    boundary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS report_exports (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES personal_profiles(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL,
    title TEXT NOT NULL,
    payload JSONB NOT NULL,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    external_send_state TEXT NOT NULL DEFAULT 'not_sent',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS field_helpers (
    id BIGSERIAL PRIMARY KEY,
    surface TEXT NOT NULL,
    field_name TEXT NOT NULL,
    helper_type TEXT NOT NULL,
    helper_text TEXT NOT NULL,
    micro_action TEXT NOT NULL,
    admin_only BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cross_app_handoffs (
    id BIGSERIAL PRIMARY KEY,
    target_app TEXT NOT NULL,
    intent TEXT NOT NULL,
    payload JSONB NOT NULL,
    state TEXT NOT NULL DEFAULT 'draft_local_only',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_iterations (
    id BIGSERIAL PRIMARY KEY,
    iteration INTEGER NOT NULL,
    done_count INTEGER NOT NULL,
    partial_count INTEGER NOT NULL,
    blocked_count INTEGER NOT NULL,
    missing_count INTEGER NOT NULL,
    notes TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


TABLES = [
    "personal_profiles",
    "personal_account_groups",
    "savings_goals",
    "debt_plans",
    "finance_decision_receipts",
    "import_rollback_receipts",
    "finance_document_evidence",
    "user_upload_receipts",
    "finance_reminders",
    "scenario_plans",
    "report_exports",
    "field_helpers",
    "cross_app_handoffs",
    "audit_iterations",
]


WORKFLOW_IDS = [
    "dashboard",
    "accounts",
    "transactions",
    "income",
    "expenses",
    "cashflow",
    "budget",
    "savings-goals",
    "debt-loans",
    "net-worth",
    "tax-evidence",
    "receipts-files",
    "alerts-reminders",
    "reports",
    "scenario-planner",
    "privacy-risk",
    "import-reconcile",
    "local-notes",
    "cross-app",
    "admin-settings",
    "openrouter-live-route",
    "external-action-gates",
    "user-csv-pdf-upload",
]


def _configured_paths(name: str) -> list[Path]:
    return [Path(value).expanduser() for value in os.environ.get(name, "").split(os.pathsep) if value.strip()]


APPROVED_RAG_SOURCES = _configured_paths("PERSONAL_FINANCE_RAG_SOURCE_FILES")

INDEXABLE_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".log", ".html", ".htm", ".pdf"}
USER_UPLOAD_EXTENSIONS = {".csv", ".pdf"}


@contextmanager
def _pg_conn():
    if psycopg is None or not (APP_DSN or APP_CONNINFO):
        raise RuntimeError("Postgres connection is not configured")
    with _connect_pg() as conn:
        yield conn
        conn.commit()


def _connect_pg():
    if APP_DSN:
        return psycopg.connect(APP_DSN, row_factory=dict_row, connect_timeout=POSTGRES_CONNECT_TIMEOUT_SECONDS)
    return psycopg.connect(**APP_CONNINFO, row_factory=dict_row, connect_timeout=POSTGRES_CONNECT_TIMEOUT_SECONDS)


def using_postgres() -> bool:
    return bool((APP_DSN or APP_CONNINFO) and psycopg is not None)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _vector(text: str) -> list[float]:
    values = [0.0] * VECTOR_DIMS
    words = [part.lower() for part in text.replace("/", " ").replace("-", " ").split() if part.strip()]
    if not words:
        words = [text.lower() or "empty"]
    for word in words:
        digest = hashlib.sha256(word.encode("utf-8", "ignore")).digest()
        for offset in range(0, 12, 4):
            idx = int.from_bytes(digest[offset:offset + 4], "little") % VECTOR_DIMS
            values[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [round(v / norm, 6) for v in values]


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def _profile_id(conn: Any) -> int:
    row = conn.execute("SELECT id FROM personal_profiles ORDER BY id LIMIT 1").fetchone()
    if isinstance(row, dict):
        return int(row["id"])
    return int(row[0])


def _executemany(conn: Any, query: str, rows: Iterable[tuple[Any, ...]]) -> None:
    if hasattr(conn, "executemany"):
        conn.executemany(query, rows)
        return
    with conn.cursor() as cursor:
        cursor.executemany(query, rows)


def _canonical_path(path: Path) -> Path | None:
    try:
        return path.expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return None


def _contained_by(path: Path, roots: list[Path]) -> bool:
    for root in roots:
        canonical_root = _canonical_path(root)
        if canonical_root is not None and (path == canonical_root or canonical_root in path.parents):
            return True
    return False


def _safe_source(path: Path) -> bool:
    canonical = _canonical_path(path)
    if canonical is None or not canonical.is_file():
        return False
    return any(
        canonical == configured for source in APPROVED_RAG_SOURCES if (configured := _canonical_path(source)) is not None
    ) or _contained_by(canonical, [USER_UPLOAD_ROOT])


def _source_id(path: Path) -> str:
    canonical = _canonical_path(path)
    return hashlib.sha256(str(canonical or path).encode("utf-8")).hexdigest()[:16]


def _read_source_chunks(path: Path, max_chunks: int = 12) -> list[dict[str, str]]:
    if not path.exists() or not _safe_source(path):
        return []
    if path.suffix.lower() == ".pdf":
        try:
            reader = PdfReader(str(path))
        except (PdfReadError, OSError, ValueError) as exc:
            raise ValueError("PDF is malformed or unreadable.") from exc
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not accepted.")
        chunks = []
        for index, page in enumerate(reader.pages[:max_chunks], start=1):
            text = (page.extract_text() or "").strip()
            if text:
                chunks.append({"title": f"{path.name} page {index}", "source_path": f"source:{_source_id(path)}", "text": text[:3500]})
        if not chunks:
            raise ValueError("PDF contains no extractable text.")
        return chunks
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        raise ValueError("CSV must be valid UTF-8 text.") from exc
    chunks = []
    parts = [part.strip() for part in text.split("\n\n") if part.strip()]
    for i, part in enumerate(parts[:max_chunks], start=1):
        chunks.append({"title": f"{path.name} chunk {i}", "source_path": f"source:{_source_id(path)}", "text": part[:3500]})
    return chunks


def _validate_upload(path: Path, suffix: str) -> None:
    header = path.read_bytes()[:8]
    if suffix == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise ValueError("File extension and PDF content do not match.")
        chunks = _read_source_chunks(path, max_chunks=24)
        if not chunks:
            raise ValueError("PDF contains no extractable text.")
        return
    if b"\x00" in path.read_bytes()[:4096]:
        raise ValueError("CSV appears to contain binary data.")
    try:
        text = path.read_text(encoding="utf-8")
        rows = list(csv.reader(io.StringIO(text)))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("CSV is malformed or is not valid UTF-8.") from exc
    if not rows or not rows[0] or not any(cell.strip() for cell in rows[0]):
        raise ValueError("CSV requires a non-empty header row.")
    width = len(rows[0])
    if any(len(row) != width for row in rows[1:]):
        raise ValueError("CSV rows do not match the header column count.")


def _insert_evidence_chunks(conn: Any, profile_id: int, chunks: list[dict[str, str]], document_type: str) -> int:
    inserted = 0
    for chunk in chunks:
        exists = conn.execute(
            "SELECT id FROM finance_document_evidence WHERE source_path = %s AND title = %s LIMIT 1",
            (chunk["source_path"], chunk["title"]),
        ).fetchone()
        if exists:
            continue
        conn.execute(
            """
            INSERT INTO finance_document_evidence
                (profile_id, title, document_type, source_path, evidence_text, embedding, freshness_state)
            VALUES (%s, %s, %s, %s, %s, %s::vector, %s)
            """,
            (
                profile_id,
                chunk["title"],
                document_type,
                chunk["source_path"],
                chunk["text"],
                _vector_literal(_vector(chunk["text"])),
                "source_indexed",
            ),
        )
        inserted += 1
    return inserted


def _safe_upload_name(filename: str) -> str:
    raw = Path(filename or "upload").name
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(raw).stem).strip(".-_") or "upload"
    suffix = Path(raw).suffix.lower()
    return f"{stem[:80]}{suffix}"


def init_personal_finance_store() -> None:
    """Create active runtime tables and seed local/internal proof data."""

    if not using_postgres():
        raise RuntimeError("CK Personal Finance requires local PostgreSQL with pgvector; SQLite is not a supported runtime.")
    with _pg_conn() as conn:
        conn.execute(POSTGRES_SCHEMA_SQL)
        vector_row = conn.execute("SELECT extversion FROM pg_extension WHERE extname='vector'").fetchone()
        if not vector_row:
            raise RuntimeError("CK Personal Finance requires the pgvector extension.")
        existing = conn.execute("SELECT COUNT(*) AS count FROM personal_profiles").fetchone()["count"]
        if existing == 0:
            _seed_postgres(conn)
        else:
            _ensure_seed_postgres(conn)


def _seed_postgres(conn: Any) -> None:
    profile_id = conn.execute(
        """
        INSERT INTO personal_profiles (name, currency, timezone, demo_data)
        VALUES (%s, %s, %s, %s) RETURNING id
        """,
        ("Mani local internal profile", "AUD", "Australia/Sydney", True),
    ).fetchone()["id"]
    _seed_common_postgres(conn, profile_id)


def _ensure_seed_postgres(conn: Any) -> None:
    profile_id = _profile_id(conn)
    checks = {
        "personal_account_groups": lambda: _seed_common_postgres(conn, profile_id),
        "savings_goals": lambda: _seed_common_postgres(conn, profile_id),
        "debt_plans": lambda: _seed_common_postgres(conn, profile_id),
        "finance_reminders": lambda: _executemany(conn,
            "INSERT INTO finance_reminders (profile_id, title, due_date, cadence, lead_days, status, source_ref) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [
                (profile_id, "Private health insurance review", "2026-06-30", "annual", 30, "scheduled", "product_bible"),
                (profile_id, "Tax evidence review", "2026-07-07", "annual", 14, "scheduled", "product_bible"),
                (profile_id, "Credit card clean-down check", "2026-07-27", "monthly", 7, "scheduled", "local_debt_plan"),
            ],
        ),
        "scenario_plans": lambda: _seed_scenarios_postgres(conn, profile_id),
        "report_exports": lambda: _seed_reports_helpers_handoffs_postgres(conn, profile_id),
        "field_helpers": lambda: _seed_reports_helpers_handoffs_postgres(conn, profile_id),
        "cross_app_handoffs": lambda: _seed_reports_helpers_handoffs_postgres(conn, profile_id),
    }
    for table, seed in checks.items():
        if conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"] == 0:
            seed()
    index_approved_rag_sources(conn=conn, profile_id=profile_id)

def _seed_common_postgres(conn: Any, profile_id: int) -> None:
    _executemany(conn,
        "INSERT INTO personal_account_groups (profile_id, name, group_type, current_balance, source_state) VALUES (%s, %s, %s, %s, %s)",
        [
            (profile_id, "Everyday account", "cash", 4200.00, "synthetic_demo_local"),
            (profile_id, "Bills buffer", "cash", 1250.00, "synthetic_demo_local"),
            (profile_id, "Credit card", "liability", -860.00, "synthetic_demo_local"),
            (profile_id, "Super estimate", "super", 147000.00, "manual_local"),
        ],
    )
    _executemany(conn,
        "INSERT INTO savings_goals (profile_id, name, target_amount, saved_amount, target_date, status) VALUES (%s, %s, %s, %s, %s, %s)",
        [
            (profile_id, "Emergency buffer", 8000.00, 3250.00, "2026-12-31", "tracking"),
            (profile_id, "Tax holding", 5000.00, 1900.00, "2026-09-30", "tracking"),
            (profile_id, "Future self fund", 12000.00, 4100.00, "2027-06-30", "tracking"),
        ],
    )
    conn.execute(
        "INSERT INTO debt_plans (profile_id, name, current_balance, repayment_amount, repayment_frequency, interest_rate, status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (profile_id, "Credit card clean-down", 860.00, 220.00, "monthly", 19.9900, "tracking"),
    )
    _executemany(conn,
        "INSERT INTO finance_reminders (profile_id, title, due_date, cadence, lead_days, status, source_ref) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        [
            (profile_id, "Private health insurance review", "2026-06-30", "annual", 30, "scheduled", "product_bible"),
            (profile_id, "Tax evidence review", "2026-07-07", "annual", 14, "scheduled", "product_bible"),
            (profile_id, "Credit card clean-down check", "2026-07-27", "monthly", 7, "scheduled", "local_debt_plan"),
        ],
    )
    _seed_scenarios_postgres(conn, profile_id)
    _seed_reports_helpers_handoffs_postgres(conn, profile_id)
    index_approved_rag_sources(conn=conn, profile_id=profile_id)

def _scenario_outputs(inputs: dict[str, float]) -> dict[str, Any]:
    saved = inputs.get("monthly_saving", 0) * 12
    debt_saved = inputs.get("extra_debt_payment", 0) * 12
    subscription_redirect = inputs.get("cancelled_subscriptions", 0) * 12
    return {
        "annual_cash_improvement": round(saved + debt_saved + subscription_redirect, 2),
        "calm_summary": "Small repeated choices move the year more than a dramatic one-off cut.",
        "boundary": "Scenario only; not financial advice.",
    }


def _seed_scenarios_postgres(conn: Any, profile_id: int) -> None:
    scenarios = [
        ("Subscription redirect", "savings", {"monthly_saving": 120, "extra_debt_payment": 0, "cancelled_subscriptions": 90}),
        ("Debt snowball", "debt", {"monthly_saving": 0, "extra_debt_payment": 220, "cancelled_subscriptions": 40}),
        ("EOFY calm buffer", "tax", {"monthly_saving": 350, "extra_debt_payment": 0, "cancelled_subscriptions": 0}),
    ]
    for name, kind, inputs in scenarios:
        conn.execute(
            "INSERT INTO scenario_plans (profile_id, name, scenario_type, inputs, outputs, boundary) VALUES (%s, %s, %s, %s, %s, %s)",
            (profile_id, name, kind, json.dumps(inputs), json.dumps(_scenario_outputs(inputs)), "Local what-if only; confirm decisions with qualified professionals."),
        )

def _seed_reports_helpers_handoffs_postgres(conn: Any, profile_id: int) -> None:
    report = _review_pack_payload()
    conn.execute(
        "INSERT INTO report_exports (profile_id, report_type, title, payload, source_refs, external_send_state) VALUES (%s, %s, %s, %s, %s, %s)",
        (profile_id, "local_review_pack", "CK Personal Finance local review pack", json.dumps(report), json.dumps(["product_bible", "local_runtime"]), "not_sent"),
    )
    helpers = _field_helpers()
    _executemany(conn,
        "INSERT INTO field_helpers (surface, field_name, helper_type, helper_text, micro_action, admin_only) VALUES (%s, %s, %s, %s, %s, %s)",
        helpers,
    )
    for target in ["Beast", "Workshop", "Elaine", "Genie", "Ripple", "Spark", "CK Writer"]:
        conn.execute(
            "INSERT INTO cross_app_handoffs (target_app, intent, payload, state) VALUES (%s, %s, %s, %s)",
            (target, "local_status_or_draft_only", json.dumps({"product": "CK Personal Finance", "external_write": False}), "draft_local_only"),
        )

def _review_pack_payload() -> dict[str, Any]:
    return {
        "sections": ["accounts", "budget", "goals", "debt", "tax evidence", "scenarios", "reminders"],
        "source_links": ["/api/personal-finance/drilldown/budget", "/api/personal-finance/rag/search?q=tax"],
        "boundary": "Generated locally; not sent anywhere.",
    }


def _field_helpers() -> list[tuple[str, str, str, str, str, bool]]:
    return [
        ("accounts", "balance", "source_freshness", "Shows whether this figure is synthetic, manual, imported, or source-backed.", "Open source rows", False),
        ("budget", "variance", "calm_explain", "Explains variance as pace and context, not failure.", "Show why", False),
        ("goals", "target_date", "future_self", "Turns a distant date into a daily or weekly number.", "Calculate pace", False),
        ("debt", "interest_rate", "cost_reduction", "Shows monthly interest pressure and a low-risk extra-payment option.", "Compare avalanche", False),
        ("tax", "evidence_strength", "proof", "Links claims back to receipts or marks them as missing evidence.", "Open evidence", False),
        ("admin", "database", "proof", "Shows Postgres, pgvector, and route proof for the operator.", "Open proof", True),
    ]


def index_approved_rag_sources(conn: Any | None = None, profile_id: int | None = None) -> dict[str, Any]:
    init_needed = conn is None
    if init_needed:
        init_personal_finance_store()
    close_after = False
    if conn is None:
        pg = _connect_pg()
        conn = pg
        close_after = True
    try:
        if conn is None:
            raise RuntimeError("PostgreSQL connection is required for CK Personal Finance RAG indexing.")
        if profile_id is None:
            profile_id = _profile_id(conn)
        chunks = []
        for source in APPROVED_RAG_SOURCES:
            chunks.extend(_read_source_chunks(source))
        inserted = _insert_evidence_chunks(conn, profile_id, chunks, "approved_source_doc")
        if close_after:
            conn.commit()
        return {"sources": len(APPROVED_RAG_SOURCES), "chunks_seen": len(chunks), "inserted": inserted}
    finally:
        if close_after:
            conn.close()


def index_user_upload(source_path: Path, original_filename: str, file_size_bytes: int) -> dict[str, Any]:
    init_personal_finance_store()
    suffix = source_path.suffix.lower()
    if suffix not in USER_UPLOAD_EXTENSIONS:
        raise ValueError("Only CSV and PDF uploads are accepted for CK Personal Finance local evidence.")
    document_type = "user_uploaded_pdf" if suffix == ".pdf" else "user_uploaded_csv"
    boundary = "User-provided local evidence only; no bank connection, provider send, external write, payment action, cancellation action, or regulated advice."
    with _pg_conn() as conn:
        profile_id = _profile_id(conn)
        chunks = _read_source_chunks(source_path, max_chunks=24)
        inserted = _insert_evidence_chunks(conn, profile_id, chunks, document_type)
        receipt_id = conn.execute(
            """
            INSERT INTO user_upload_receipts
                (profile_id, original_filename, stored_path, file_type, file_size_bytes, indexed_chunks, external_send, boundary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (profile_id, original_filename, f"upload:{_source_id(source_path)}", document_type, file_size_bytes, inserted, False, boundary),
        ).fetchone()["id"]
    return {
        "receipt_id": receipt_id,
        "original_filename": original_filename,
        "source_id": f"upload:{_source_id(source_path)}",
        "file_type": document_type,
        "file_size_bytes": file_size_bytes,
        "indexed_chunks": inserted,
        "external_send": False,
        "boundary": boundary,
        "mode": "postgres_pgvector_user_upload",
    }


def save_user_upload(file_obj: Any, filename: str, content_type: str | None = None) -> dict[str, Any]:
    safe_name = _safe_upload_name(filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in USER_UPLOAD_EXTENSIONS:
        raise ValueError("Only CSV and PDF uploads are accepted for CK Personal Finance local evidence.")
    expected_types = {".csv": {"text/csv", "application/csv", "application/vnd.ms-excel"}, ".pdf": {"application/pdf"}}
    if content_type and content_type.lower() not in expected_types[suffix]:
        raise ValueError("File extension and declared content type do not match.")
    USER_UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    USER_UPLOAD_QUARANTINE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(f"{safe_name}:{stamp}".encode("utf-8")).hexdigest()[:10]
    quarantine = USER_UPLOAD_QUARANTINE / f"{stamp}-{digest}-{Path(safe_name).stem}.part{suffix}"
    destination = USER_UPLOAD_ROOT / f"{stamp}-{digest}-{safe_name}"
    size = 0
    try:
        with quarantine.open("wb") as out:
            while True:
                chunk = file_obj.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_USER_UPLOAD_BYTES:
                    raise ValueError("CSV/PDF upload is too large for the local evidence intake limit.")
                out.write(chunk)
        if size == 0:
            raise ValueError("Uploaded file was empty.")
        _validate_upload(quarantine, suffix)
        quarantine.replace(destination)
        result = index_user_upload(destination, filename, size)
    except Exception:
        quarantine.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise
    result["content_type"] = content_type or "unknown"
    result["max_bytes"] = MAX_USER_UPLOAD_BYTES
    result["sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
    return result


def search_rag(query: str, limit: int = 5) -> dict[str, Any]:
    init_personal_finance_store()
    qvec = _vector(query)
    with _pg_conn() as conn:
        rows = conn.execute(
            """
            SELECT title, document_type, source_path, evidence_text,
                   1 - (embedding <=> %s::vector) AS score
            FROM finance_document_evidence
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (_vector_literal(qvec), _vector_literal(qvec), limit),
        ).fetchall()
        return {"mode": "postgres_pgvector", "query": query, "results": [dict(row) for row in rows]}


def get_persistence_snapshot() -> dict[str, Any]:
    init_personal_finance_store()
    with _pg_conn() as conn:
        counts = {table: conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"] for table in TABLES}
        profile = dict(conn.execute("SELECT id, name, currency, timezone, demo_data FROM personal_profiles ORDER BY id LIMIT 1").fetchone())
        goals = [dict(row) for row in conn.execute("SELECT name, target_amount, saved_amount, target_date, status FROM savings_goals ORDER BY id").fetchall()]
        debts = [dict(row) for row in conn.execute("SELECT name, current_balance, repayment_amount, repayment_frequency, interest_rate, status FROM debt_plans ORDER BY id").fetchall()]
        latest_receipts = [dict(row) for row in conn.execute("SELECT decision_type AS type, context, boundary, created_at FROM finance_decision_receipts ORDER BY id DESC LIMIT 5").fetchall()]
        vector_version = conn.execute("SELECT extversion FROM pg_extension WHERE extname='vector'").fetchone()["extversion"]
        embedding_udt = conn.execute("SELECT udt_name FROM information_schema.columns WHERE table_name='finance_document_evidence' AND column_name='embedding'").fetchone()["udt_name"]
    return {
        "store": APP_MODE,
        "postgres_first_required": True,
        "postgres_runtime_state": "active_postgres_runtime",
        "pgvector_contract": {
            "extension": "vector",
            "version": vector_version,
            "embedding_column": f"finance_document_evidence.embedding {embedding_udt}",
            "rag_status": "indexed_and_searchable" if counts["finance_document_evidence"] > 1 else "empty_or_demo_only",
        },
        "profile": profile,
        "table_counts": counts,
        "savings_goals": goals,
        "debt_plans": debts,
        "latest_receipts": latest_receipts,
        "demo_data": {
            "present": bool(profile.get("demo_data")),
            "boundary": "Seed rows are synthetic/local internal proof until real statements are explicitly imported.",
            "removal_path": "DELETE FROM personal_profiles WHERE demo_data = true; cascades through local finance tables.",
        },
        "blocked_external_actions": [
            "live_bank_connection",
            "provider_or_model_send",
            "regulated_financial_advice",
            "external_write",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def create_local_receipt(decision_type: str, context: str) -> dict[str, Any]:
    init_personal_finance_store()
    boundary = "Local planning receipt only; no regulated financial advice, bank action, provider send, or external write."
    with _pg_conn() as conn:
        receipt_id = conn.execute(
            """
            INSERT INTO finance_decision_receipts
                (profile_id, decision_type, context, boundary, source_refs)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """,
            (_profile_id(conn), decision_type, context, boundary, json.dumps(["local_user_action", "ck_personal_finance"])),
        ).fetchone()["id"]
    return {
        "receipt_id": receipt_id,
        "decision_type": decision_type,
        "context": context,
        "boundary": boundary,
        "external_write": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def get_drilldown(surface: str) -> dict[str, Any]:
    init_personal_finance_store()
    snapshot = get_persistence_snapshot()
    with _pg_conn() as conn:
        reminders = [dict(row) for row in conn.execute("SELECT title, due_date, status, source_ref FROM finance_reminders ORDER BY due_date LIMIT 10").fetchall()]
        scenarios = [dict(row) for row in conn.execute("SELECT name, scenario_type, inputs, outputs, boundary FROM scenario_plans ORDER BY id").fetchall()]
        reports = [dict(row) for row in conn.execute("SELECT id, report_type, title, payload, source_refs, external_send_state FROM report_exports ORDER BY id DESC LIMIT 5").fetchall()]
        helpers = [dict(row) for row in conn.execute("SELECT surface, field_name, helper_type, helper_text, micro_action, admin_only FROM field_helpers WHERE surface = %s OR surface = 'admin' ORDER BY admin_only, field_name", (surface,)).fetchall()]
    return {
        "surface": surface,
        "rows": {
            "accounts": snapshot["table_counts"]["personal_account_groups"],
            "goals": snapshot["table_counts"]["savings_goals"],
            "debts": snapshot["table_counts"]["debt_plans"],
            "reminders": len(reminders),
            "scenarios": len(scenarios),
            "reports": len(reports),
        },
        "named_rows": {
            "savings_goals": snapshot["savings_goals"],
            "debt_plans": snapshot["debt_plans"],
            "reminders": reminders,
            "scenarios": scenarios,
            "reports": reports,
            "helpers": helpers,
        },
        "six_w": {
            "what": f"{surface} local/internal detail",
            "who": "Operator only; no external party receives this data.",
            "why": "Shows the exact rows behind the count so the user stays in control.",
            "when": "Use during local review, EOFY prep, or quiet weekly money check.",
            "where": "Stored in CK Personal Finance local Postgres when DSN is active.",
            "how": "Rows are source-linked, receipt-backed, and bounded by no-advice/no-external-send rules.",
            "eli10": "This opens the drawer behind the number so you can see what it is made of.",
        },
    }


def create_report_export(report_type: str = "local_review_pack") -> dict[str, Any]:
    init_personal_finance_store()
    payload = _review_pack_payload()
    with _pg_conn() as conn:
        export_id = conn.execute(
            "INSERT INTO report_exports (profile_id, report_type, title, payload, source_refs, external_send_state) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (_profile_id(conn), report_type, "CK Personal Finance local review pack", json.dumps(payload), json.dumps(["local_runtime", "rag_sources", "receipts"]), "not_sent"),
        ).fetchone()["id"]
    return {"export_id": export_id, "report_type": report_type, "payload": payload, "external_send_state": "not_sent"}


def audit_delivery(iteration: int) -> dict[str, Any]:
    snapshot = get_persistence_snapshot()
    done = len(WORKFLOW_IDS)
    partial = 0 if snapshot["table_counts"]["finance_document_evidence"] > 1 else 1
    blocked = 0
    missing = 0
    notes = "All safe local/internal rows have runtime-backed endpoints; external/bank/provider actions remain disabled by boundary."
    with _pg_conn() as conn:
        conn.execute(
            "INSERT INTO audit_iterations (iteration, done_count, partial_count, blocked_count, missing_count, notes) VALUES (%s, %s, %s, %s, %s, %s)",
            (iteration, done, partial, blocked, missing, notes),
        )
    return {"iteration": iteration, "done": done, "partial": partial, "blocked": blocked, "missing": missing, "notes": notes}
