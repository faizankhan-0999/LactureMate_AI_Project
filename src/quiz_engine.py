"""Pure quiz-scoring logic, independent of Streamlit session state."""
from __future__ import annotations

def score_quiz(questions: list[dict], answers: dict[int, str]) -> dict:
    if not questions: return {"total": 0, "answered": 0, "correct": 0, "incorrect": 0, "percentage": 0.0, "incorrect_indices": []}
    correct_indices = [i for i, q in enumerate(questions) if answers.get(i) == q.get("correct_answer")]
    answered = sum(i in answers for i in range(len(questions)))
    incorrect = [i for i in range(len(questions)) if i in answers and i not in correct_indices]
    correct = len(correct_indices)
    return {"total": len(questions), "answered": answered, "correct": correct, "incorrect": len(incorrect), "percentage": round(correct / len(questions) * 100, 1), "incorrect_indices": incorrect}

def restart_quiz_state() -> dict:
    return {"answers": {}, "submitted": False, "current_index": 0, "result": None}
