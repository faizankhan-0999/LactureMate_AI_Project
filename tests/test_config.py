from src.config import get_model

def test_model_reads_streamlit_secret():
    assert get_model({"GEMINI_MODEL": "gemini-3.8-flash"}) == "gemini-3.8-flash"

def test_model_uses_stable_default_when_secret_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert get_model({}) == "gemini-3.8-flash"

def test_model_trims_secret_value():
    assert get_model({"GEMINI_MODEL": "  gemini-3.8-flash  "}) == "gemini-3.8-flash"
