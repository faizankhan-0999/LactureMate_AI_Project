import pytest
from src.notes_generator import build_notes_prompt, STUDY_MODES

def test_modes_change_prompt():
    prompts=[build_notes_prompt("lecture text",mode,[1,2]) for mode in STUDY_MODES]
    assert len(set(prompts)) == 3
    assert all("PDF page" not in p or "lecture text" in p for p in prompts)

def test_invalid_mode_rejected():
    with pytest.raises(ValueError): build_notes_prompt("text","Unknown")
