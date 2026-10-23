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

def test_source_pages_must_exist_in_source():
    with pytest.raises(ValidationError, match="not present"):
        validate_mcqs(sample(), expected_count=1, source_pages=[2, 3])


def test_duplicate_options_rejected():
    d = sample()
    d["questions"][0]["options"]["D"] = d["questions"][0]["options"]["C"]
    with pytest.raises(ValidationError, match="duplicate answer options"):
        validate_mcqs(d)


def test_source_pages_must_be_actual_integers_not_booleans():
    d = sample()
    d["questions"][0]["source_pages"] = [True]
    with pytest.raises(ValidationError, match="invalid source pages"):
        validate_mcqs(d)


def test_schema_failure_gets_one_correction_attempt():
    class FakeService:
        def __init__(self): self.calls = 0
        def generate_json(self, prompt):
            self.calls += 1
            if self.calls == 1:
                return {"questions": []}
            base = sample()["questions"][0]
            return {"questions": [dict(base, question=f"Question {i}?") for i in range(1, 6)]}
    service = FakeService()
    from src.question_generator import generate_mcqs
    result = generate_mcqs(service, "lecture text", 5, [1])
    assert len(result) == 5
    assert service.calls == 2
