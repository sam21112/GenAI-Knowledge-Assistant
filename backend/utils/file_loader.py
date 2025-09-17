# backend/utils/file_loader.py
import fitz  # PyMuPDF

def parse_pdf_text(path: str, max_pages: int = None) -> str:
    """
    Read a PDF and return plain text. Requires PyMuPDF (package: pymupdf).
    """
    parts = []
    with fitz.open(path) as doc:
        for i, page in enumerate(doc):
            if max_pages is not None and i >= max_pages:
                break
            parts.append(page.get_text("text"))
    return "\n".join(parts).strip()


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200):
    """
    Optional helper: yield overlapping chunks for embedding.
    """
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunks.append(text[start:end])
        if end == n:
            break
        start = end - overlap if end - overlap > start else end
    return chunks
