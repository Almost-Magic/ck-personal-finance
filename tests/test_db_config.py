from pathlib import Path


def test_personal_finance_has_no_default_database_password():
    service = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "services"
        / "personal_finance_store.py"
    ).read_text(encoding="utf-8")
    assert 'os.environ.get("PF_POSTGRES_PASS",' not in service
    assert '"password": os.environ.get("PF_POSTGRES_PASS")' in service
    assert '"amtl"' not in service.split("APP_MODE", 1)[0]
