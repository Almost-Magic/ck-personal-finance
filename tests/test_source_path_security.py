from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PERSONAL_SERVICE = (ROOT / "app/services/personal_finance_store.py").read_text(encoding="utf-8")
PERSONAL_ROUTES = (ROOT / "app/routes/personal_finance.py").read_text(encoding="utf-8")


def test_source_paths_come_from_deployment_configuration():
    combined = PERSONAL_SERVICE
    assert "C:/Users/Mani" not in combined
    assert "\\\\NAS1" not in combined
    assert "\\\\NAS2" not in combined
    assert "resolve(strict=True)" in combined
    assert "canonical_root in path.parents" in combined


def test_nas_indexing_is_not_exposed_or_claimed():
    combined = PERSONAL_SERVICE + PERSONAL_ROUTES
    assert "index_nas_sources" not in combined
    assert 'sources/nas/index' not in combined
    assert "approved by Mani" not in combined
    assert "mani_approved" not in combined


def test_client_payloads_use_opaque_source_ids_not_machine_paths():
    assert '"source_path": str(path)' not in PERSONAL_SERVICE
    assert '"stored_path": str(source_path)' not in PERSONAL_SERVICE
