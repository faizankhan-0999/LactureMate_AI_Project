"""Validated exam question and MCQ generation."""
from __future__ import annotations
import json

class ValidationError(ValueError): pass

def build_mcq_prompt(source_text: str, count: int = 10, source_pages: list[int] | None = None) -> str:
    if count not in (5, 10, 15, 20, 30): raise ValueError("MCQ count must be 5, 10, 15, 20, or 30.")
    return f"Create {count} distinct lecture-based MCQs, balanced across the source topics. Return JSON object {{\"questions\":[...]}}. Each item must have question, options (object with exactly A,B,C,D), correct_answer (A/B/C/D), explanation, difficulty (Easy/Medium/Hard), topic, source_pages (array of original integer PDF page numbers or empty array). Exactly one best answer. No unsupported citations. Source pages available: {source_pages or 'not specified'}. Source:\n{source_text}"

def validate_mcqs(data, expected_count: int | None = None) -> list[dict]:
    if isinstance(data, str):
        try: data = json.loads(data)
        except json.JSONDecodeError as exc: raise ValidationError("MCQ response is not valid JSON.") from exc
    questions = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(questions, list) or not questions: raise ValidationError("MCQ response must contain a non-empty questions list.")
    if expected_count is not None and len(questions) != expected_count: raise ValidationError(f"Expected {expected_count} MCQs, received {len(questions)}.")
    seen, valid = set(), []
    for i, item in enumerate(questions, 1):
        if not isinstance(item, dict): raise ValidationError(f"Question {i} must be an object.")
        for key in ("question", "options", "correct_answer", "explanation", "difficulty", "topic", "source_pages"):
            if key not in item: raise ValidationError(f"Question {i} is missing {key}.")
        if not isinstance(item["question"], str) or not item["question"].strip(): raise ValidationError(f"Question {i} has empty text.")
        opts = item["options"]
        if not isinstance(opts, dict) or set(opts) != {"A", "B", "C", "D"} or not all(str(opts[k]).strip() for k in "ABCD"):
            raise ValidationError(f"Question {i} must have four non-empty options A-D.")
        if item["correct_answer"] not in ("A", "B", "C", "D"): raise ValidationError(f"Question {i} has an invalid answer key.")
        if item["difficulty"] not in ("Easy", "Medium", "Hard"): raise ValidationError(f"Question {i} has invalid difficulty.")
        if not isinstance(item["source_pages"], list) or any(not isinstance(p, int) or p < 1 for p in item["source_pages"]): raise ValidationError(f"Question {i} has invalid source pages.")
        key = item["question"].strip().casefold()
        if key in seen: raise ValidationError("Duplicate MCQ questions were detected.")
        seen.add(key); valid.append(item)
    return valid

def generate_mcqs(service, source_text: str, count: int = 10, source_pages: list[int] | None = None):
    return validate_mcqs(service.generate_json(build_mcq_prompt(source_text, count, source_pages)), expected_count=count)

def generate_exam_questions(service, source_text: str, count: int = 10, source_pages: list[int] | None = None):
    prompt = f"Create {count} lecture-based short/long/conceptual/application questions. Return JSON {{\"questions\":[{{\"question\":string,\"type\":string,\"topic\":string,\"difficulty\":\"Easy|Medium|Hard\",\"source_pages\":integer[],\"suggested_answer\":string}}]}}. Do not predict the actual exam. Only cite evidenced original pages. Pages available: {source_pages or []}. Source:\n{source_text}"
    data = service.generate_json(prompt)
    questions = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(questions, list) or not questions: raise ValidationError("Question response is missing a questions list.")
    for i, q in enumerate(questions, 1):
        if not isinstance(q, dict) or not all(k in q for k in ("question", "type", "topic", "difficulty", "source_pages", "suggested_answer")):
            raise ValidationError(f"Question {i} is incomplete.")
        if q["difficulty"] not in ("Easy", "Medium", "Hard"): raise ValidationError(f"Question {i} has invalid difficulty.")
        if any(not isinstance(p, int) or p < 1 for p in q["source_pages"]): raise ValidationError(f"Question {i} has invalid source pages.")
    return questions
