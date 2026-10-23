"""Download formatting utilities."""
from __future__ import annotations

def notes_to_markdown(title: str, notes: str) -> str:
    return f"# {title.strip() or 'Lecture Notes'}\n\n{notes.strip()}\n"

def questions_to_markdown(questions: list[dict], include_answers: bool = True) -> str:
    out = ["# Practice Questions", ""]
    for i, q in enumerate(questions, 1):
        out += [f"## {i}. {q.get('question','')}", f"- Type: {q.get('type','Practice')}", f"- Topic: {q.get('topic','Not specified')}", f"- Difficulty: {q.get('difficulty','Not specified')}"]
        pages = q.get("source_pages", [])
        out.append(f"- Source pages: {', '.join(map(str, pages)) if pages else 'Not reliably identified'}")
        if include_answers and q.get("suggested_answer"): out.append(f"\n**Suggested answer:** {q['suggested_answer']}")
        out.append("")
    return "\n".join(out)

def mcqs_to_markdown(questions: list[dict], include_answers: bool = True) -> str:
    out = ["# Multiple-Choice Questions", ""]
    for i, q in enumerate(questions, 1):
        out += [f"## {i}. {q['question']}"]
        out += [f"- {letter}. {q['options'][letter]}" for letter in "ABCD"]
        out += [f"- Difficulty: {q['difficulty']} | Topic: {q['topic']}"]
        pages = q.get("source_pages", [])
        out.append(f"- Source pages: {', '.join(map(str, pages)) if pages else 'Not reliably identified'}")
        if include_answers: out += [f"**Correct answer:** {q['correct_answer']}", f"**Explanation:** {q['explanation']}"]
        out.append("")
    return "\n".join(out)

def flashcards_to_markdown(cards: list[dict]) -> str:
    return "# Flashcards\n\n" + "\n\n".join(f"## {i}. {c['term']}\n**Answer:** {c['answer']}\n" + (f"**Example:** {c['example']}\n" if c.get('example') else "") + f"**Topic:** {c.get('topic','Not specified')}\n**Source pages:** {', '.join(map(str,c.get('source_pages',[]))) or 'Not reliably identified'}" for i,c in enumerate(cards,1)) + "\n"
