"""Chunk extracted page text without losing original page provenance."""
from __future__ import annotations
from dataclasses import dataclass
from .pdf_processor import PageText

@dataclass
class LectureChunk:
    chunk_id: int
    text: str
    source_pages: list[int]


def chunk_pages(pages: list[PageText], max_chars: int = 18000, overlap_chars: int = 800) -> list[LectureChunk]:
    if max_chars < 100: raise ValueError("max_chars must be at least 100.")
    if overlap_chars < 0 or overlap_chars >= max_chars: raise ValueError("overlap_chars must be between 0 and max_chars.")
    chunks, current, page_refs = [], "", []
    for page in pages:
        text = page.text.strip()
        if not text: continue
        piece = f"[PDF page {page.page_number}]\n{text}"
        if current and len(current) + len(piece) + 2 > max_chars:
            chunks.append(LectureChunk(len(chunks)+1, current, sorted(set(page_refs))))
            overlap = current[-overlap_chars:] if overlap_chars else ""
            current = overlap
            page_refs = page_refs[-1:] if overlap else []
        # Split oversized single pages into manageable pieces.
        while len(piece) > max_chars:
            room = max_chars - len(current) - 2
            if room > 0:
                current += ("\n\n" if current else "") + piece[:room]
                page_refs.append(page.page_number)
                chunks.append(LectureChunk(len(chunks)+1, current, sorted(set(page_refs))))
                current = current[-overlap_chars:] if overlap_chars else ""
                page_refs = [page.page_number] if current else []
                piece = piece[room:]
            else:
                chunks.append(LectureChunk(len(chunks)+1, current, sorted(set(page_refs))))
                current, page_refs = "", []
        if current and len(current) + len(piece) + 2 > max_chars:
            chunks.append(LectureChunk(len(chunks)+1, current, sorted(set(page_refs))))
            current = current[-overlap_chars:] if overlap_chars else ""
            page_refs = [page.page_number] if current else []
        current += ("\n\n" if current else "") + piece
        page_refs.append(page.page_number)
    if current.strip(): chunks.append(LectureChunk(len(chunks)+1, current, sorted(set(page_refs))))
    return chunks
