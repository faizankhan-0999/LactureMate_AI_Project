import pytest
from src.question_generator import validate_mcqs, ValidationError, build_mcq_prompt

def sample():
    return {"questions":[{"question":"What is a variable?","options":{"A":"A named storage location","B":"A loop","C":"A compiler","D":"A file"},"correct_answer":"A","explanation":"A variable stores a value.","difficulty":"Easy","topic":"Programming","source_pages":[1]}]}

def test_valid_mcq(): assert validate_mcqs(sample(),1)[0]["correct_answer"] == "A"
def test_four_options_required():
    d=sample(); d["questions"][0]["options"].pop("D")
    with pytest.raises(ValidationError): validate_mcqs(d)
def test_invalid_answer_rejected():
    d=sample(); d["questions"][0]["correct_answer"]="E"
    with pytest.raises(ValidationError): validate_mcqs(d)
def test_duplicate_questions_rejected():
    d=sample(); d["questions"].append(dict(d["questions"][0]))
    with pytest.raises(ValidationError): validate_mcqs(d)
def test_count_prompt():
    with pytest.raises(ValueError): build_mcq_prompt("x", 7)
