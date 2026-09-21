"""Focused CK Personal Finance recovery layer tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from server import app


def test_personal_finance_cockpit_keeps_completion_honest():
    client = TestClient(app)
    client.headers.update({"Origin": "http://testserver"})
    response = client.get("/api/personal-finance/cockpit")
    assert response.status_code == 200
    data = response.json()

    assert data["product"] == "CK Personal Finance"
    assert data["database"]["store_kind"] == "postgres"
    assert data["claim"]["preview_local_internal"] is False
    assert data["claim"]["acceptance_evidence_complete"] is False
    assert data["database"]["postgres_truth"] == "pass_active_runtime"
    assert data["rag"]["configured"] is False
    assert data["rag"]["truth"] == "empty_or_demo_only"
    assert data["privacy"]["regulated_financial_advice"] == "not_provided"
    assert data["privacy"]["bank_api_connection"] == "disabled_without_explicit_approval"
    assert data["ai_provider"]["provider_call_allowed"] is False
    assert data["ai_provider"]["provider"] is None
    assert data["ai_provider"]["default_execution"] == "disabled_by_policy"
    assert data["database"]["postgres_required_for_serious_runtime"] is True
    assert data["persistence"]["table_counts"]["savings_goals"] >= 1
    assert data["persistence"]["table_counts"]["finance_reminders"] >= 1
    assert data["persistence"]["table_counts"]["scenario_plans"] >= 1
    assert data["counts"]["total"] >= 22


def test_personal_finance_matrix_has_required_surfaces():
    client = TestClient(app)
    client.headers.update({"Origin": "http://testserver"})
    rows = client.get("/api/personal-finance/cockpit").json()["matrix"]
    row_ids = {row["id"] for row in rows}

    required = {
        "dashboard",
        "accounts",
        "transactions",
        "cashflow",
        "budget",
        "tax-evidence",
        "import-reconcile",
        "privacy-risk",
        "cross-app",
    }
    assert required.issubset(row_ids)
    assert all(row["status"] == "PREVIEW" for row in rows)
    assert all(row["exact_next_fix"] for row in rows)


def test_personal_finance_persistence_and_postgres_contract_are_visible():
    client = TestClient(app)
    client.headers.update({"Origin": "http://testserver"})
    persistence = client.get("/api/personal-finance/persistence").json()
    schema = client.get("/api/personal-finance/postgres-schema").json()

    assert persistence["postgres_first_required"] is True
    assert persistence["pgvector_contract"]["extension"] == "vector"
    assert persistence["demo_data"]["present"] is True
    assert "CREATE EXTENSION IF NOT EXISTS vector" in schema["schema_sql"]
    assert schema["credential_boundary"].startswith("No database password")


def test_personal_finance_actions_are_local_and_blocked_where_needed():
    client = TestClient(app)
    client.headers.update({"Origin": "http://testserver"})
    data = client.get("/api/personal-finance/actions").json()

    assert "copy_privacy_boundary_receipt" in data["safe_actions"]
    assert "route_ai_task_through_openrouter_policy" in data["safe_actions"]
    assert "upload_user_csv_or_pdf_local_evidence" in data["safe_actions"]
    assert "live_bank_connection" in data["blocked_actions"]
    assert "regulated_financial_advice" in data["blocked_actions"]
    assert "public_release_or_deploy" in data["blocked_actions"]


def test_personal_finance_external_ai_is_disabled_before_network(monkeypatch):
    client = TestClient(app)
    client.headers.update({"Origin": "http://testserver"})

    def fail_network(*args, **kwargs):
        raise AssertionError("network client must not be constructed")

    monkeypatch.setattr("socket.create_connection", fail_network)
    policy = client.get("/api/personal-finance/ai/model-policy").json()
    assert policy["provider"] is None
    assert policy["provider_call_allowed"] is False
    assert policy["default_execution"] == "disabled_by_policy"
    assert "OPENROUTER_API_KEY" not in str(policy)

    route = client.post(
        "/api/personal-finance/ai/route",
        json={"task_kind": "scenario_planner", "reasoning_level": "high", "max_cost_tier": "modest"},
    )
    assert route.status_code == 200
    assert route.json()["provider"] is None
    assert route.json()["provider_called"] is False

    completion = client.post(
        "/api/personal-finance/ai/complete",
        json={
            "prompt": "Explain a budget variance calmly.",
            "reasoning_level": "low",
            "max_cost_tier": "free",
            "execute": True,
            "allow_paid_provider": True,
        },
    )
    assert completion.status_code == 403
    detail = completion.json()["detail"]
    assert detail["state"] == "disabled_by_policy"
    assert detail["provider_called"] is False


def test_personal_finance_receipts_create_local_only_records():
    client = TestClient(app)
    client.headers.update({"Origin": "http://testserver"})
    response = client.post(
        "/api/personal-finance/receipts",
        json={"decision_type": "test_review", "context": "Focused test receipt"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["receipt_id"] > 0
    assert data["external_write"] is False
    assert "no regulated financial advice" in data["boundary"]


def test_personal_finance_user_csv_pdf_uploads_are_local_receipted():
    client = TestClient(app)
    client.headers.update({"Origin": "http://testserver"})

    csv_response = client.post(
        "/api/personal-finance/uploads",
        files={"file": ("budget.csv", b"date,description,amount\n2026-06-28,Coffee,4.50\n", "text/csv")},
    )
    assert csv_response.status_code == 200
    csv_data = csv_response.json()
    assert csv_data["receipt_id"] > 0
    assert csv_data["file_type"] == "user_uploaded_csv"
    assert csv_data["external_send"] is False
    assert csv_data["indexed_chunks"] >= 1
    assert "no bank connection" in csv_data["boundary"].lower()
    assert csv_data["source_id"].startswith("upload:")
    assert "stored_path" not in csv_data

    pdf_response = client.post(
        "/api/personal-finance/uploads",
        files={"file": ("bill.pdf", b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n", "application/pdf")},
    )
    assert pdf_response.status_code == 400
    assert any(text in pdf_response.json()["detail"].lower() for text in ("malformed", "unreadable", "extractable text"))

    blocked = client.post(
        "/api/personal-finance/uploads",
        files={"file": ("notes.txt", b"not accepted", "text/plain")},
    )
    assert blocked.status_code == 400


def test_personal_finance_rag_drilldown_reports_and_audit_are_wired():
    client = TestClient(app)
    client.headers.update({"Origin": "http://testserver"})

    rag = client.get("/api/personal-finance/rag/search", params={"q": "tax evidence", "limit": 2}).json()
    assert rag["mode"] == "postgres_pgvector"
    assert len(rag["results"]) >= 1

    drilldown = client.get("/api/personal-finance/drilldown/budget").json()
    assert drilldown["rows"]["reminders"] >= 1
    assert drilldown["six_w"]["what"].startswith("budget")
    assert drilldown["six_w"]["eli10"]

    report = client.post("/api/personal-finance/reports", json={"report_type": "local_review_pack"}).json()
    assert report["export_id"] > 0
    assert report["external_send_state"] == "not_sent"

    audit = client.post("/api/personal-finance/audit/5").json()
    assert audit["done"] >= 23
    assert audit["blocked"] == 0
    assert audit["missing"] == 0


def test_personal_finance_beyond_local_status_is_preview_and_nas_index_is_removed():
    client = TestClient(app)
    client.headers.update({"Origin": "http://testserver"})

    status = client.get("/api/personal-finance/beyond-local/status").json()
    assert status["status"] == "PREVIEW_LOCAL_WITH_EXTERNAL_TARGET_BLOCKERS"
    assert "approved_nas_source_indexing_endpoint" not in status["preview"]
    assert status["partial"] == []
    assert status["missing"] == []
    assert any(row["item"] == "live_bank_cdr_connection" for row in status["blocked"])

    response = client.post(
        "/api/personal-finance/sources/nas/index",
        json={"max_files": 1, "max_chunks_per_file": 1},
    )
    assert response.status_code in {404, 405}
