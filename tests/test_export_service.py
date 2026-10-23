from src.export_service import notes_to_markdown, questions_to_markdown, mcqs_to_markdown, flashcards_to_markdown

def test_notes_export_unicode(): assert "Résumé" in notes_to_markdown("Résumé", "Café — formula λ")
def test_question_export():
    out=questions_to_markdown([{"question":"Define data.","type":"Short","topic":"Basics","difficulty":"Easy","source_pages":[2],"suggested_answer":"Information."}])
    assert "Suggested answer" in out and "2" in out
def test_mcq_export():
    q={"question":"Q?","options":{"A":"a","B":"b","C":"c","D":"d"},"correct_answer":"B","explanation":"Because","difficulty":"Easy","topic":"T","source_pages":[]}
    assert "**Correct answer:** B" in mcqs_to_markdown([q])
def test_flashcard_export(): assert "Answer" in flashcards_to_markdown([{"term":"X","answer":"Y","topic":"T","source_pages":[]}])
