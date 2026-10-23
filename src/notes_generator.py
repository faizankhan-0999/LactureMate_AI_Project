"""Prompt construction and note-generation helpers."""
STUDY_MODES = {
 "Simple Explanation": "Explain in easy English, define unfamiliar terms, use step-by-step explanations and simple analogies while preserving technical accuracy.",
 "Detailed University Notes": "Produce comprehensive undergraduate notes with definitions, concept relationships, examples, formulas, classifications, applications, comparisons, limitations and glossary where relevant.",
 "Exam-Focused Revision": "Create concise exam revision notes emphasizing key definitions, formulas, differences, recall points and likely practice areas. Do not claim to predict the actual exam."
}

def build_notes_prompt(source_text: str, mode: str = "Detailed University Notes", source_pages: list[int] | None = None) -> str:
    if mode not in STUDY_MODES: raise ValueError(f"Unsupported study mode: {mode}")
    pages = ", ".join(map(str, source_pages or [])) or "not reliably identified"
    return f"""You are an experienced university teacher. Create accurate study notes based primarily on the lecture source below.
Study mode: {mode}. Instructions: {STUDY_MODES[mode]}
Rules: preserve important terminology and formulas; do not invent source claims or citations; attach original PDF page references only when evidenced in source text; label any supplementary explanation as 'Supplementary explanation'; flag ambiguity instead of guessing. Adapt sections to subject and do not force irrelevant content. Include a title, overview, learning objectives, main topics/subtopics, definitions, explanations, examples, formulas where relevant, comparisons, common mistakes, key takeaways, revision summary and glossary where useful.
Available original pages: {pages}
LECTURE SOURCE:
{source_text}
"""

def generate_notes(service, source_text: str, mode: str = "Detailed University Notes", source_pages: list[int] | None = None) -> str:
    return service.generate(build_notes_prompt(source_text, mode, source_pages))
