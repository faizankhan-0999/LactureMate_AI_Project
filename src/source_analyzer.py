"""Multi-stage, page-aware analysis for longer lecture documents."""
from __future__ import annotations
from .lecture_chunker import LectureChunk


def analyze_chunks(service, chunks: list[LectureChunk], mode: str = "Detailed University Notes") -> str:
    """Summarize every chunk with its page references, then assemble a study context.

    Raises on any failed chunk rather than silently pretending the lecture was fully covered.
    """
    if not chunks:
        raise ValueError("No extractable lecture chunks are available to analyze.")
    summaries = []
    failures = []
    for chunk in chunks:
        pages = ", ".join(map(str, chunk.source_pages)) or "uncertain"
        prompt = (
            "Analyze this university lecture section for later study-guide synthesis. "
            "Preserve definitions, formulas, examples, distinctions, and technical terms. "
            "Do not add facts not supported by this section. Label ambiguity. "
            "Return a compact but comprehensive structured summary. Keep the given original PDF page references.\n"
            f"Study mode: {mode}\nOriginal PDF pages: {pages}\nSection {chunk.chunk_id}:\n{chunk.text}"
        )
        try:
            summary = service.generate(prompt)
            summaries.append(f"[ANALYSIS OF ORIGINAL PDF PAGES {pages}; CHUNK {chunk.chunk_id}]\n{summary}")
        except Exception as exc:
            failures.append((chunk.chunk_id, pages, str(exc)))
    if failures:
        details = "; ".join(f"chunk {cid} (pages {pages})" for cid, pages, _ in failures)
        raise RuntimeError(f"Lecture analysis incomplete: failed {details}. Retry after checking the API. No complete-coverage claim is made.")
    return "\n\n".join(summaries)
