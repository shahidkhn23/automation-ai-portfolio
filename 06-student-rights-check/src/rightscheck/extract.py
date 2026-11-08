"""Get text out of a document. PDFs with a text layer and .txt/.md files for now.
Scanned letters (photos) are on the roadmap: OCR step before this one."""

from pathlib import Path


def read_document(path: str | Path) -> str:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        if not text.strip():
            raise ValueError("This PDF has no text layer (probably a scan). OCR is not supported yet.")
        return text
    return path.read_text(encoding="utf-8")
