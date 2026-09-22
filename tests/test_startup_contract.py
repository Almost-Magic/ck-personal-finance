from pathlib import Path


def test_runtime_manifest_is_postgres_only():
    manifest = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = manifest.read_text(encoding="utf-8")
    assert "psycopg[binary]" in text
    assert "aiosqlite" not in text


def test_startup_does_not_swallow_personal_finance_database_failure():
    server = (Path(__file__).resolve().parents[1] / "server.py").read_text(encoding="utf-8")
    assert "init_personal_finance_store()" in server
    assert "dependency-down startup" not in server
