from pathlib import Path
from io import BytesIO

import pytest

from app.services.personal_finance_store import _validate_upload


def test_csv_requires_matching_shape_and_text(tmp_path):
    valid = tmp_path / "valid.csv"
    valid.write_text("date,amount\n2026-09-21,4.50\n", encoding="utf-8")
    _validate_upload(valid, ".csv")
    malformed = tmp_path / "bad.csv"
    malformed.write_text("date,amount\n2026-09-21\n", encoding="utf-8")
    with pytest.raises(ValueError, match="column count"):
        _validate_upload(malformed, ".csv")


def test_pdf_rejects_extension_spoof(tmp_path):
    fake = tmp_path / "fake.pdf"
    fake.write_text("not a PDF", encoding="utf-8")
    with pytest.raises(ValueError, match="do not match"):
        _validate_upload(fake, ".pdf")


def test_textless_pdf_is_rejected(tmp_path):
    fake = tmp_path / "empty.pdf"
    fake.write_bytes(b"%PDF-1.4\n%%EOF")
    with pytest.raises(ValueError, match="malformed|unreadable|extractable"):
        _validate_upload(fake, ".pdf")



def test_quarantined_pdf_keeps_pdf_suffix_and_is_actually_parsed(tmp_path, monkeypatch):
    from app.services import personal_finance_store as store

    monkeypatch.setattr(store, "USER_UPLOAD_ROOT", tmp_path / "uploads")
    monkeypatch.setattr(store, "USER_UPLOAD_QUARANTINE", tmp_path / "uploads" / ".quarantine")
    malformed_ascii_pdf = BytesIO(b"%PDF-1.4\nthis is not a valid PDF\n%%EOF")
    with pytest.raises(ValueError, match="malformed|unreadable|extractable"):
        store.save_user_upload(malformed_ascii_pdf, "statement.pdf", "application/pdf")
    assert not [path for path in tmp_path.rglob("*") if path.is_file()]
