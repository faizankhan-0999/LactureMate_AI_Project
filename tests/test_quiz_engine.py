from src.quiz_engine import score_quiz, restart_quiz_state

def test_score():
    qs=[{"correct_answer":"A"},{"correct_answer":"C"},{"correct_answer":"B"}]
    result=score_quiz(qs,{0:"A",1:"B"})
    assert result["correct"] == 1 and result["incorrect"] == 1
    assert result["percentage"] == 33.3 and result["incorrect_indices"] == [1]
def test_empty_quiz(): assert score_quiz([],{})["percentage"] == 0.0
def test_restart(): assert restart_quiz_state() == {"answers":{},"submitted":False,"current_index":0,"result":None}
