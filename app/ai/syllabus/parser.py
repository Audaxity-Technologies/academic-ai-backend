import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from threading import Lock
from zipfile import BadZipFile, ZipFile

logger = logging.getLogger(__name__)
MAX_BYTES = 50 * 1024 * 1024
MAX_PAGES = 250
FORMATS = {".pdf", ".docx", ".txt"}
DOCLING_LOCK = Lock()


class SyllabusParser:
    def validate(self, path: Path) -> None:
        if path.suffix.lower() not in FORMATS:
            raise ValueError("Choose a PDF, DOCX, or UTF-8 TXT document")
        if not path.is_file() or not path.stat().st_size:
            raise ValueError("The syllabus file is empty or missing")
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("Syllabus files must be at most 50 MiB")
        if path.suffix.lower() == ".pdf":
            with self.open_pdf(path):
                pass
        elif path.suffix.lower() == ".docx":
            try:
                with ZipFile(path) as archive:
                    if "word/document.xml" not in archive.namelist():
                        raise ValueError("The file is not a Word document")
                    if sum(entry.file_size for entry in archive.infolist()) > 100 * 1024 * 1024:
                        raise ValueError("The expanded Word document is too large")
                    if any(entry.flag_bits & 1 for entry in archive.infolist()):
                        raise ValueError("The Word document is encrypted")
            except BadZipFile as exc:
                raise ValueError("The Word document is unreadable") from exc

    def open_pdf(self, path):
        import pymupdf

        try:
            pdf = pymupdf.open(path, filetype="pdf")
        except (RuntimeError, ValueError) as exc:
            raise ValueError("The PDF is unreadable or corrupt") from exc
        if not pdf.is_pdf or pdf.needs_pass or not 1 <= pdf.page_count <= MAX_PAGES:
            pdf.close()
            raise ValueError(f"Provide an unencrypted PDF with 1–{MAX_PAGES} pages")
        return pdf

    def parse_document(self, file_path: str | Path, *, native_pdf: bool = False) -> dict:
        path = Path(file_path)
        self.validate(path)
        kind = path.suffix.lower()[1:]
        if native_pdf and kind != "pdf":
            raise ValueError("Native PDF extraction requires a PDF input.")
        warnings = []
        ocr_pages = []
        source_pages = []
        if kind == "txt":
            pages = [path.read_text(encoding="utf-8-sig")]
        elif kind == "docx":
            pages = [self._docling(path).export_to_markdown()]
            warnings.append("Word documents have no fixed physical page references.")
        else:
            with self.open_pdf(path) as pdf:
                mixed_provenance = set()
                if native_pdf:
                    pages = [page.get_text(sort=True) for page in pdf]
                    warnings.append("Used native PDF text extraction. Review table layout and reading order.")
                else:
                    try:
                        document = self._docling(path)
                        pages = [document.export_to_markdown(page_no=i)
                                 for i in range(1, len(pdf) + 1)]
                        for item, _ in document.iterate_items():
                            item_pages = {ref.page_no for ref in getattr(item, "prov", [])}
                            if len(item_pages) > 1:
                                mixed_provenance.update(item_pages)
                    except Exception:
                        logger.warning("Docling extraction failed, using PDF fallback", exc_info=True)
                        warnings.append("Docling was unavailable or failed. Fallback layout may need review.")
                        pages = [self._fallback(page) for page in pdf]

                for index, page in enumerate(pdf):
                    native = page.get_text(sort=True).strip()
                    source_pages.append(native)
                    if native and index + 1 in mixed_provenance:
                        pages[index] = self._fallback(page)
                        warnings.append(f"Recovered physical page {index + 1} from cross-page layout content.")
                    layout_text = re.sub(r"<!--\s*image\s*-->", "", pages[index]).strip()
                    if native and not layout_text:
                        pages[index] = self._fallback(page)
                        warnings.append(f"Recovered native text omitted by layout extraction on page {index + 1}.")
                    images = page.get_image_info()
                    if not images:
                        continue
                    from pymupdf import Rect

                    largest_image = max((Rect(image["bbox"]) & page.rect).get_area() for image in images)
                    if len(native) >= 40 and largest_image < page.rect.get_area() * 0.65:
                        continue
                    if len(native) >= 250:
                        continue
                    try:
                        textpage = page.get_textpage_ocr(
                            full=True, dpi=200, tessdata=os.getenv("TESSDATA_PREFIX")
                        )
                        recovered = page.get_text(textpage=textpage, sort=True).strip()
                        if len(recovered) > max(10, len(native) + 10):
                            pages[index] = recovered
                            source_pages[index] = recovered
                            ocr_pages.append(index + 1)
                        else:
                            warnings.append(f"OCR found no additional text on page {index + 1}.")
                    except (RuntimeError, ValueError):
                        warnings.append(f"Page {index + 1} may need OCR. Configure TESSDATA_PREFIX.")
        records = [
            {"page_number": i, "text": re.sub(r"<!--\s*image\s*-->", "", text).strip()}
            for i, text in enumerate(pages, 1)
        ]
        empty = [page["page_number"] for page in records if not page["text"]]
        if len(empty) == len(records):
            raise ValueError("No readable syllabus text. For scans, configure OCR and retry.")
        if empty:
            warnings.append(f"No readable content on pages {empty}.")
        return {
            "format": kind,
            "pages": records,
            "source_pages": source_pages or pages,
            "raw_text": "\n\n".join(
                f"[Page {page['page_number']}]\n{page['text']}" for page in records
            ),
            "warnings": warnings,
            "empty_pages": empty,
            "ocr_pages": ocr_pages,
        }

    @staticmethod
    def _docling(path):
        with DOCLING_LOCK:
            result = docling_converter().convert(path)
        if result.status.value != "success":
            raise RuntimeError("Docling could not extract the entire document")
        return result.document

    @staticmethod
    def _fallback(page):
        text = page.get_text(sort=True)
        tables = page.find_tables().tables
        if tables:
            text += "\n" + "\n".join(table.to_markdown() for table in tables)
        return text



@lru_cache(maxsize=1)
def docling_converter():
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    options = PdfPipelineOptions(do_ocr=False, do_table_structure=True)
    converter = DocumentConverter(format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=options)
    })
    return converter
