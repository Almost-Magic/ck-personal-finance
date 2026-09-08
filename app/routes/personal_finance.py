"""CK Personal Finance local/internal cockpit truth endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.openrouter_router import (
    openrouter_complete,
    openrouter_policy,
    select_openrouter_route,
)
from app.services.personal_finance_store import (
    APP_MODE,
    DEMO_MODE,
    POSTGRES_SCHEMA_SQL,
    WORKFLOW_IDS,
    audit_delivery,
    create_local_receipt,
    create_report_export,
    get_drilldown,
    get_persistence_snapshot,
    index_nas_sources,
    index_approved_rag_sources,
    save_user_upload,
    init_personal_finance_store,
    search_rag,
    using_postgres,
)

router = APIRouter(prefix="/personal-finance", tags=["personal-finance"])


class ReceiptRequest(BaseModel):
    decision_type: str = "weekly_review"
    context: str = "Local CK Personal Finance review action."


class ReportRequest(BaseModel):
    report_type: str = "local_review_pack"


class RagSearchRequest(BaseModel):
    query: str = "tax evidence"
    limit: int = 5


class AiRouteRequest(BaseModel):
    task_kind: str = "field_explanation"
    reasoning_level: str = "low"
    max_cost_tier: str = "expensive"


class AiCompleteRequest(BaseModel):
    prompt: str
    reasoning_level: str = "low"
    max_cost_tier: str = "expensive"
    execute: bool = False
    allow_paid_provider: bool = False
    system: str | None = None


class NasIndexRequest(BaseModel):
    max_files: int = 120
    max_chunks_per_file: int = 3


SAFE_LOCAL_WORKFLOWS = [
    ("dashboard", "Dashboard", "DONE", "public/index.html", "Calm overview, user controls, privacy boundary, and live proof panels"),
    ("accounts", "Accounts", "DONE", "app/services/personal_finance_store.py", "Personal account groups persist with source state and drilldown rows"),
    ("transactions", "Transactions", "DONE", "app/services/personal_finance_store.py", "Import rollback receipts, source confidence, and local drilldown are wired"),
    ("income", "Income", "DONE", "app/services/personal_finance_store.py", "Household income appears in report/export and scenario payloads"),
    ("expenses", "Expenses", "DONE", "app/services/personal_finance_store.py", "Bills/subscriptions are represented through reminders, scenarios, and report rows"),
    ("cashflow", "Cashflow", "DONE", "app/services/personal_finance_store.py", "Local scenarios and review-pack export show cash movement without external writes"),
    ("budget", "Budget", "DONE", "app/services/personal_finance_store.py", "Local review pack and field helpers cover budget variance and calm explanations"),
    ("savings-goals", "Savings goals", "DONE", "app/services/personal_finance_store.py", "Savings goals persist and drill into named rows"),
    ("debt-loans", "Debt and loans", "DONE", "app/services/personal_finance_store.py", "Debt plans persist with repayment scenario support"),
    ("net-worth", "Net worth", "DONE", "app/services/personal_finance_store.py", "Account groups include assets/liabilities/super and report exports link to source rows"),
    ("tax-evidence", "Tax and document evidence", "DONE", "app/services/personal_finance_store.py", "Approved source docs are indexed for local pgvector/RAG search with disclaimers"),
    ("receipts-files", "Receipts and files", "DONE", "app/services/personal_finance_store.py", "Document evidence and local receipts persist; external send remains disabled"),
    ("alerts-reminders", "Alerts and reminders", "DONE", "app/services/personal_finance_store.py", "Local reminder records exist with cadence, due date, and source refs"),
    ("reports", "Reports", "DONE", "app/services/personal_finance_store.py", "Report/export receipts are local, source-linked, and marked not sent"),
    ("scenario-planner", "Scenario planner", "DONE", "app/services/personal_finance_store.py", "Local what-if scenarios persist with inputs, outputs, and no-advice boundary"),
    ("privacy-risk", "Risk and privacy boundaries", "DONE", "app/routes/personal_finance.py", "No advice, no bank API, external AI disabled, no external write"),
    ("import-reconcile", "Import and reconcile", "DONE", "app/services/personal_finance_store.py", "Preview-only rollback receipts and source confidence are visible"),
    ("local-notes", "Local notes and decisions", "DONE", "app/services/personal_finance_store.py", "Decision receipts persist without external write"),
    ("cross-app", "Cross-app handoffs", "DONE", "app/services/personal_finance_store.py", "Draft-only handoff records exist for AMTL apps; no receiver mutation"),
    ("admin-settings", "Admin and settings", "DONE", "app/routes/personal_finance.py", "Admin proof is behind Admin/Proof and includes DB/RAG/route truth"),
    ("nas-source-indexing", "NAS source indexing", "DONE", "app/services/personal_finance_store.py", "Approved NAS roots index into Postgres/pgvector with only the two user-named path exclusions"),
    ("openrouter-live-route", "OpenRouter live route", "DONE", "app/services/openrouter_router.py", "External AI execution is disabled regardless of caller flags"),
    ("external-action-gates", "External action gates", "DONE", "app/routes/personal_finance.py", "Bank/source/write/deploy actions are explicit approval targets with receipts, not silent UI buttons"),
    ("user-csv-pdf-upload", "User CSV/PDF upload", "DONE", "app/routes/personal_finance.py", "Users can provide local CSV or PDF evidence; files are stored locally, indexed, and receipt-backed with external_send=false"),
]


BUTTONS = [
    {"id": "review-week", "label": "Create review receipt", "truth": "posts_local_decision_receipt", "status": "wired"},
    {"id": "import-preview", "label": "Show import rollback", "truth": "reads_import_rollback_receipts", "status": "wired"},
    {"id": "export-report", "label": "Create local report", "truth": "posts_local_report_export_receipt", "status": "wired"},
    {"id": "rag-search", "label": "Search evidence", "truth": "runs_local_pgvector_or_vector_fallback_search", "status": "wired"},
    {"id": "copy-privacy", "label": "Copy privacy receipt", "truth": "copies_static_local_boundary_receipt", "status": "wired"},
    {"id": "upload-csv-pdf", "label": "Upload CSV/PDF", "truth": "stores_user_file_locally_indexes_evidence_and_returns_receipt", "status": "wired"},
]


def _matrix() -> list[dict[str, str]]:
    return [
        {
            "id": row_id,
            "surface": surface,
            "status": "PARTIAL",
            "implementation_location": location,
            "evidence_path": "app/services/personal_finance_store.py",
            "test_or_browser_proof": "focused API tests, route proof, browser QA, five-loop audit",
            "gap": result,
            "exact_next_fix": "Verify the full user journey; stored records do not establish an implemented workflow.",
        }
        for row_id, surface, status, location, result in SAFE_LOCAL_WORKFLOWS
    ]


@router.get("/cockpit")
def cockpit():
    """Return the local/internal CK Personal Finance delivery truth."""

    try:
        init_personal_finance_store()
        persistence = get_persistence_snapshot()
        dependency_error = None
    except Exception as exc:
        persistence = {
            "store": APP_MODE,
            "postgres_first_required": True,
            "postgres_runtime_state": "dependency_down",
            "pgvector_contract": {
                "extension": "vector",
                "version": None,
                "embedding_column": "unavailable_until_postgres_pgvector_is_reachable",
                "rag_status": "dependency_down",
            },
            "profile": None,
            "table_counts": {"finance_document_evidence": 0},
            "savings_goals": [],
            "debt_plans": [],
            "latest_receipts": [],
            "blocked_external_actions": [
                "live_bank_connection",
                "provider_or_model_send",
                "regulated_financial_advice",
                "external_write",
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        dependency_error = "PostgreSQL/pgvector is unavailable. Check the local database service."
    matrix = _matrix()
    done = sum(1 for row in matrix if row["status"] == "DONE")
    partial = sum(1 for row in matrix if row["status"] == "PARTIAL")
    missing = sum(1 for row in matrix if row["status"] == "NOT IMPLEMENTED")
    local_complete = using_postgres() and dependency_error is None
    reason = (
        "Local records are available. Workflow completion requires independent testing; external AI is disabled."
        if local_complete
        else "Postgres/pgvector dependency is not active; CK Personal Finance has no SQLite runtime fallback."
    )
    return {
        "product": "CK Personal Finance",
        "mode": "synthetic_demo" if DEMO_MODE else "local_internal_private",
        "source_truth": {
            "active_tree": "C:/AMTL/repos/elaine-complete-record-push/Source and Brand/Finance App/The Ledger",
            "recovered_app_name": "The Ledger",
            "recovered_positioning": "Recovered finance app adapted to CK Personal Finance local/internal scope",
            "ck_personal_finance_fit": "local_records_available" if local_complete else "fallback_partial",
        },
        "claim": {
            "done_local_internal": False,
            "mani_100_allowed": False,
            "database_ready": local_complete,
            "reason": reason,
        },
        "privacy": {
            "regulated_financial_advice": "not_provided",
            "bank_api_connection": "disabled_without_explicit_approval",
            "provider_or_model_send": "external_providers_disabled",
            "external_write": False,
            "demo_data_label_required": True,
        },
        "ai_provider": openrouter_policy(),
        "database": {
            "configured_path": "redacted_postgres_dsn" if using_postgres() else "postgres_unavailable",
            "store_kind": APP_MODE,
            "postgres_required_for_serious_runtime": True,
            "postgres_truth": "pass_active_runtime" if using_postgres() and not dependency_error else "dependency_down_no_sqlite_runtime",
            "pgvector_truth": persistence["pgvector_contract"],
            "dependency_error": dependency_error,
        },
        "rag": {
            "needed_for_receipts_statements_documents": True,
            "configured": persistence["table_counts"]["finance_document_evidence"] > 1,
            "truth": persistence["pgvector_contract"]["rag_status"],
        },
        "persistence": persistence,
        "counts": {"done": done, "partial": partial, "not_implemented": missing, "total": len(matrix)},
        "matrix": matrix,
        "buttons": BUTTONS,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/actions")
def actions():
    """Return safe local actions for the browser cockpit."""

    return {
        "safe_actions": [
            "create_local_review_receipt",
            "show_import_rollback_receipts",
            "create_local_report_export",
            "search_local_rag_evidence",
            "show_local_review_policy",
            "upload_user_csv_or_pdf_local_evidence",
            "copy_privacy_boundary_receipt",
            "open_named_row_drilldown",
        ],
        "blocked_actions": [
            "regulated_financial_advice",
            "live_bank_connection",
            "external_provider_model_send",
            "source_system_write",
            "public_release_or_deploy",
        ],
        "next_best_slice": "Start with the labelled demo records, then create a review receipt or download a report.",
    }


@router.get("/beyond-local/status")
def beyond_local_status():
    return {
        "product": "CK Personal Finance",
        "status": "LOCAL_DEMO_EXTERNAL_ACTIONS_DISABLED",
        "done": ["local_records", "local_review_receipts", "local_report_download"],
        "partial": ["Full workflow and real-data deployment verification remain outstanding."],
        "missing": [],
        "blocked": [{"item": item} for item in ["live_bank_cdr_connection", "external_provider_execution", "public_deployment"]],
    }


@router.get("/persistence")
def persistence():
    return get_persistence_snapshot()


@router.get("/postgres-schema")
def postgres_schema():
    return {
        "product": "CK Personal Finance",
        "schema_sql": POSTGRES_SCHEMA_SQL.strip(),
        "credential_boundary": "No database password or secret is exposed by this endpoint.",
        "external_write": False,
    }


@router.post("/receipts")
def receipts(request: ReceiptRequest):
    return create_local_receipt(request.decision_type, request.context)


@router.get("/drilldown/{surface}")
def drilldown(surface: str):
    return get_drilldown(surface)


@router.post("/reports")
def reports(request: ReportRequest):
    return create_report_export(request.report_type)


@router.post("/rag/index")
def rag_index():
    return index_approved_rag_sources()


@router.post("/sources/nas/index")
def nas_index(request: NasIndexRequest):
    if DEMO_MODE:
        raise HTTPException(status_code=403, detail="NAS indexing is disabled in the synthetic demo.")
    return index_nas_sources(request.max_files, request.max_chunks_per_file)


@router.post("/uploads")
def upload_local_evidence(file: UploadFile = File(...)):
    suffix = (file.filename or "").lower().rsplit(".", 1)[-1]
    if suffix not in {"csv", "pdf"}:
        raise HTTPException(status_code=400, detail="Only CSV and PDF uploads are accepted.")
    try:
        return save_user_upload(file.file, file.filename or "upload", file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/rag/search")
def rag_search_get(q: str = "tax evidence", limit: int = 5):
    return search_rag(q, limit)


@router.post("/rag/search")
def rag_search_post(request: RagSearchRequest):
    return search_rag(request.query, request.limit)


@router.get("/ai/model-policy")
def ai_model_policy():
    return openrouter_policy()


@router.post("/ai/route")
def ai_route(request: AiRouteRequest):
    route = select_openrouter_route(request.reasoning_level, request.max_cost_tier)
    return {
        "provider": "local_manual",
        "task_kind": request.task_kind,
        "route": route,
        "provider_called": False,
        "external_write": False,
        "notes": "Route selection only; no model call was made.",
    }


@router.post("/ai/complete")
async def ai_complete(request: AiCompleteRequest):
    return await openrouter_complete(
        prompt=request.prompt,
        reasoning_level=request.reasoning_level,
        max_cost_tier=request.max_cost_tier,
        execute=request.execute,
        allow_paid_provider=request.allow_paid_provider,
        system=request.system,
    )


@router.post("/audit/{iteration}")
def audit(iteration: int):
    return audit_delivery(iteration)


@router.get("/health")
def personal_finance_health():
    try:
        snapshot = get_persistence_snapshot()
    except Exception:
        raise HTTPException(status_code=503, detail="Local PostgreSQL/pgvector is unavailable.")
    return {"status": "ok", "product": "CK Personal Finance", "store": snapshot["store"],
            "demo_data": snapshot["demo_data"]["present"], "pgvector": snapshot["pgvector_contract"]["version"]}
