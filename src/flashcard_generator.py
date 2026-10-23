"""Flashcard and revision-sheet helpers."""
def generate_flashcards(service, source_text: str, count: int = 12, source_pages: list[int] | None = None):
    data = service.generate_json(f"Create {count} useful lecture flashcards. Return JSON {{\"flashcards\":[{{\"term\":string,\"answer\":string,\"example\":string,\"topic\":string,\"source_pages\":integer[]}}]}}. Use only supported source page numbers; otherwise []. Pages: {source_pages or []}. Source:\n{source_text}")
    cards = data.get("flashcards") if isinstance(data, dict) else None
    if not isinstance(cards, list) or not cards: raise ValueError("Flashcard response is invalid.")
    for card in cards:
        if not isinstance(card, dict) or not all(k in card for k in ("term", "answer", "topic", "source_pages")): raise ValueError("A flashcard is incomplete.")
        if not isinstance(card["source_pages"], list): raise ValueError("Flashcard source_pages must be a list.")
    return cards

def generate_revision_sheet(service, source_text: str, source_pages: list[int] | None = None) -> str:
    return service.generate(f"Create a concise last-minute revision sheet of the lecture's most important definitions, formulas, differences, concepts and reminders. Cite only evidenced original PDF pages; do not invent content. Pages available: {source_pages or []}. Source:\n{source_text}")
