"""Standalone PostgreSQL fixtures; never connect to an application database."""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["FINANCE_ENV"] = "test"
os.environ["FINANCE_AUTH_MODE"] = "disabled"


@pytest.fixture(scope="session", autouse=True)
def isolated_database(tmp_path_factory):
    database_url = os.environ.get("TEST_DATABASE_URL", "")
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"} or parsed.path != "/finance_test":
        raise RuntimeError("TEST_DATABASE_URL must point to the dedicated PostgreSQL finance_test database.")
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1", "postgres"}:
        raise RuntimeError("A local dedicated PostgreSQL test database is required.")
    schema = "cockpit_test_" + uuid4().hex
    patch = pytest.MonkeyPatch()
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    patch.setenv("PF_DATABASE_URL", database_url)
    patch.setenv("PERSONAL_FINANCE_DATABASE_URL", database_url)
    patch.setenv("PGOPTIONS", f"-c search_path={schema},public")
    from app.services import personal_finance_store as store
    patch.setattr(store, "APP_DSN", database_url)
    patch.setattr(store, "APP_CONNINFO", None)
    patch.setattr(store, "APPROVED_RAG_SOURCES", [])
    upload_root = tmp_path_factory.mktemp("cockpit-uploads")
    patch.setattr(store, "USER_UPLOAD_ROOT", upload_root)
    patch.setattr(store, "USER_UPLOAD_QUARANTINE", upload_root / ".quarantine")
    try:
        yield
    finally:
        patch.undo()
        with psycopg.connect(database_url, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
