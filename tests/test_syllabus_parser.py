import os
import sys
from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from app.ai.syllabus import cli, structurer
from app.ai.syllabus.parser import SyllabusParser


@pytest.fixture
def fixture_pdf(tmp_path):
    path = tmp_path / "syllabus.pdf"
    pdf = Canvas(str(path))
    pdf.drawString(50, 750, "UNIT III: DATABASE DESIGN")
    pdf.drawString(50, 730, "3.2 Normalization")
    pdf.drawString(50, 710, "3.2.1 First Normal Form")
    pdf.showPage()
    pdf.drawString(50, 750, "Concurrency")
    pdf.drawString(50, 730, "Locking")
    pdf.drawString(50, 710, "References: Database System Concepts")
    pdf.save()
    return path


@pytest.fixture
def use_fallback(monkeypatch):
    def unavailable(_):
        raise ImportError("Force fallback in ordinary tests")
    monkeypatch.setattr(SyllabusParser, "_docling", staticmethod(unavailable))


def test_multipage_extraction_and_cli(fixture_pdf, use_fallback, monkeypatch, tmp_path):
    client = Mock()
    monkeypatch.setattr(structurer, "llm_client", client)
    client.generate_content.return_value = {"subject_name": "Database Systems", "units": [
        {"title": "Database Design", "number": "III", "pages": [1], "topics": [
            {"title": "Normalization", "number": "3.2", "pages": [1], "subtopics": [
                {"title": "First Normal Form", "number": "3.2.1", "pages": [1]}
            ]}
        ]},
        {"title": "Concurrency", "pages": [2], "topics": [{"title": "Locking", "pages": [2]}]},
    ]}
    out = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["cli", "--input", str(fixture_pdf), "--output-dir", str(out)])
    assert cli.main() == 0
    markdown = (out / "parsed_syllabus.md").read_text(encoding="utf-8")
    assert "III Database Design" in markdown and "  - 3.2.1 First Normal Form" in markdown
    assert "Database System Concepts" not in markdown
    assert "[Page 2]" in (out / "extracted_preview.txt").read_text(encoding="utf-8")
    report = structurer.ParsingReport.model_validate_json((out / "parsing_report.json").read_text())
    assert (report.pages_processed, report.units, report.topics, report.subtopics) == (2, 2, 2, 1)
    assert report.needs_review


def test_fallback_preserves_tables(use_fallback, tmp_path):
    path = tmp_path / "table.pdf"
    table = Table([["Module", "Topic"], ["III", "Normalization"]])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, "black")]))
    SimpleDocTemplate(str(path)).build([table])
    result = SyllabusParser().parse_document(path)
    assert "|Module|Topic|" in result["pages"][0]["text"].replace(" ", "")
    assert "Normalization" in result["raw_text"]


@pytest.mark.parametrize("content", [b"", b"%PDF-1.7 corrupt"])
def test_reject_unreadable_pdf(tmp_path, content):
    path = tmp_path / "invalid.pdf"
    path.write_bytes(content)
    with pytest.raises(ValueError):
        SyllabusParser().parse_document(path)


def test_duplicates_invalid_page_and_malformed_schema():
    hierarchy = structurer.SyllabusHierarchy.model_validate({"units": [
        {"title": "Databases", "topics": [{"title": "Locking"}, {"title": "locking"}]},
    ]})
    assert "Duplicate sibling title" in structurer.inspect_hierarchy(hierarchy, 1)[0][0]
    hierarchy.units[0].topics[0].pages = [2]
    with pytest.raises(ValueError, match="outside"):
        structurer.inspect_hierarchy(hierarchy, 1)
    with pytest.raises(ValidationError):
        structurer.SyllabusHierarchy.model_validate({"units": [{"title": " ", "topics": []}]})


@pytest.mark.skipif(not os.getenv("TESSDATA_PREFIX"), reason="Requires configured Tesseract language data")
@pytest.mark.parametrize("mixed", [False, True])
def test_scanned_pdf_with_ocr(tmp_path, use_fallback, fixture_pdf, mixed):
    import pymupdf

    path = tmp_path / "scanned.pdf"
    with pymupdf.open(fixture_pdf) as native, pymupdf.open() as scanned:
        for index, source in enumerate(native):
            if mixed and index == 0:
                scanned.insert_pdf(native, from_page=0, to_page=0)
                continue
            page = scanned.new_page(width=source.rect.width, height=source.rect.height)
            page.insert_image(page.rect, pixmap=source.get_pixmap(dpi=160))
        scanned.save(path)
    result = SyllabusParser().parse_document(path)
    assert result["ocr_pages"] == ([2] if mixed else [1, 2])
    assert "Normalization" in result["raw_text"]


@pytest.mark.skipif(os.getenv("AUDAXITY_DOCLING_INTEGRATION") != "1",
                    reason="Opt-in download of Docling layout models")
def test_docling_pdf_layout(fixture_pdf):
    result = SyllabusParser().parse_document(fixture_pdf)
    assert "Normalization" in result["pages"][0]["text"]
    assert "Locking" in result["pages"][1]["text"]
    assert not any("Docling was unavailable" in warning for warning in result["warnings"])



def test_encrypted_pdf(tmp_path, fixture_pdf):
    import pymupdf

    encrypted = tmp_path / "encrypted.pdf"
    with pymupdf.open(fixture_pdf) as doc:
        doc.save(encrypted, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="private")
    with pytest.raises(ValueError, match="unencrypted"):
        SyllabusParser().parse_document(encrypted)


def test_docx_uses_document_body(tmp_path):
    from docx import Document

    word = Document()
    word.add_heading("Unit III", 1)
    word.add_paragraph("Normalization")
    path = tmp_path / "syllabus.docx"
    word.save(path)
    assert "Normalization" in SyllabusParser().parse_document(path)["raw_text"]


def test_reference_anchors_use_physical_page_text():
    hierarchy = structurer.SyllabusHierarchy.model_validate({"units": [
        {"title": "Database Design", "pages": [1], "topics": [
            {"title": "Locking", "pages": [1, 2]},
            {"title": "Invented topic", "pages": [1]},
        ]},
    ]})
    warnings = structurer.ground_page_references(hierarchy, {
        "format": "pdf", "source_pages": ["Database Design", "Locking"],
    })
    assert hierarchy.units[0].topics[0].pages == [2]
    assert hierarchy.units[0].topics[1].pages == []
    assert len(warnings) == 2
