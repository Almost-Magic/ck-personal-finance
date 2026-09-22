from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "app/routes/personal_finance.py",
    ROOT / "public/index.html",
]
TEXT = "\n".join(path.read_text(encoding="utf-8") for path in FILES)


def test_incomplete_wrappers_are_labelled_as_previews():
    assert "DONE_LOCAL_INTERNAL_" not in TEXT
    assert '"status": "BEYOND_LOCAL_IMPLEMENTED' not in TEXT
    assert "PREVIEW_LOCAL_WITH_EXTERNAL_TARGET_BLOCKERS" in TEXT
    assert "Private workspace preview" in TEXT


def test_nas_indexing_claims_do_not_return_in_preview_copy():
    assert "NAS source indexing" not in TEXT
    assert "approved by Mani" not in TEXT
