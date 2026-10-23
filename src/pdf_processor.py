"""PDF extraction with original page references and coverage reporting."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from io import BytesIO
from pypdf import PdfReader

@dataclass
class PageText:
    page_number: int
    text: str
    char_count: int
    status: str

@dataclass
class PDFResult:
    filename: str
    total_pages: int
    pages: list[PageText]
    extracted_pages: int
    low_text_pages: list[int]
    failed_pages: list[int]
    encrypted: bool = False

    @property
    def full_text(self) -> str:
        return "\n\n".join(f"[PDF page {p.page_number}]\n{p.text}" for p in self.pages if p.text.strip())

    @property
    def coverage(self) -> dict:
        eligible = self.total_pages - len(self.low_text_pages)
        return {"total_pages": self.total_pages, "pages_with_text": self.extracted_pages,
                "low_or_empty_text_pages": self.low_text_pages, "failed_pages": self.failed_pages,
                "eligible_pages": max(0, eligible), "all_pages_extractable": not self.low_text_pages and not self.failed_pages,
                "notes": "Scanned/image-only pages may require OCR; OCR is not performed by this app." if self.low_text_pages else "Text extraction completed for all pages."}


def extract_pdf(file_bytes: bytes, filename: str = "lecture.pdf", low_text_threshold: int = 30) -> PDFResult:
    if not isinstance(file_bytes, (bytes, bytearray)) or not file_bytes:
        raise ValueError("The uploaded PDF is empty.")
    try:
        reader = PdfReader(BytesIO(file_bytes), strict=False)
    except Exception as exc:
        raise ValueError("This file could not be read as a valid PDF.") from exc
    if reader.is_encrypted:
        try:
            if reader.decrypt("") == 0:
                raise ValueError("This PDF is password-protected. Upload an unlocked PDF.")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("This PDF is password-protected. Upload an unlocked PDF.") from exc
    pages, low, failed = [], [], []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
            status = "text" if len(text) >= low_text_threshold else "low_text"
            if status == "low_text": low.append(index)
            pages.append(PageText(index, text, len(text), status))
        except Exception:
            failed.append(index)
            pages.append(PageText(index, "", 0, "failed"))
    if not pages:
        raise ValueError("The PDF contains no pages.")
    if not any(p.text.strip() for p in pages):
        raise ValueError("No selectable text was found. This may be a scanned PDF; OCR is not included.")
    return PDFResult(filename, len(pages), pages, sum(bool(p.text.strip()) for p in pages), low, failed, reader.is_encrypted)
