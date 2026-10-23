"""Multi-stage, page-aware analysis with bounded recovery and useful diagnostics."""
from __future__ import annotations
import logging
from .lecture_chunker import LectureChunk

logger = logging.getLogger(__name__)


def _looks_like_size_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(term in message for term in (
        "too many tokens", "token limit", "maximum context", "context length",
        "request too large", "payload too large", "input too long", "content too long",
        "request size", "invalid_argument", "invalid argument", "http 400",
    ))


def _split_chunk(chunk: LectureChunk) -> tuple[LectureChunk, LectureChunk] | None:
    text = chunk.text
    if len(text) < 3500:
        return None
    midpoint = len(text) // 2
    # Prefer a paragraph/line boundary close to the midpoint to avoid cutting concepts.
    candidates = [text.rfind("\n\n", 0, midpoint + 500), text.find("\n\n", midpoint)]
    candidates = [p for p in candidates if p >= int(len(text) * 0.30) and p <= int(len(text) * 0.70)]
    cut = min(candidates, key=lambda p: abs(p - midpoint)) if candidates else midpoint
    left, right = text[:cut].strip(), text[cut:].strip()
    if not left or not right:
        return None
    return (
        LectureChunk(chunk.chunk_id, left, list(chunk.source_pages)),
        LectureChunk(chunk.chunk_id, right, list(chunk.source_pages)),
    )


def analyze_chunks(service, chunks: list[LectureChunk], mode: str = "Detailed University Notes") -> str:
    """Analyze all chunks. On likely input-size failures, split and retry boundedly.

    Raises on any remaining failure rather than silently claiming full coverage. The
    exception includes the safe service diagnostic so the user can fix keys/quota/model
    problems without guessing.
    """
    if not chunks:
        raise ValueError("No extractable lecture chunks are available to analyze.")
    summaries: list[str] = []
    failures: list[tuple[int, str, str]] = []

    def analyze_one(chunk: LectureChunk, depth: int = 0) -> None:
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
            return
        except Exception as exc:
            logger.warning("Lecture chunk analysis failed: chunk=%s pages=%s chars=%s error=%s", chunk.chunk_id, pages, len(chunk.text), str(exc)[:300])
            # Only split for likely request/context-size failures, at most twice.
            split = _split_chunk(chunk) if depth < 2 and _looks_like_size_error(exc) else None
            if split:
                logger.info("Retrying oversized lecture chunk as smaller sections: chunk=%s depth=%s", chunk.chunk_id, depth + 1)
                analyze_one(split[0], depth + 1)
                analyze_one(split[1], depth + 1)
                return
            failures.append((chunk.chunk_id, pages, str(exc)[:500] or type(exc).__name__))

    for chunk in chunks:
        analyze_one(chunk)

    if failures:
        cid, pages, reason = failures[0]
        other_count = len(failures) - 1
        extra = f" {other_count} additional chunk(s) also failed." if other_count else ""
        raise RuntimeError(
            f"Lecture analysis incomplete: chunk {cid} (PDF pages {pages}) failed. "
            f"Actual error: {reason}.{extra} No complete-coverage claim is made. "
            "Use the diagnostic in this message to check the API key, model access, quota, or connection."
        )
    return "\n\n".join(summaries)
