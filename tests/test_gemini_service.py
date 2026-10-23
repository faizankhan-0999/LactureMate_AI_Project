import json
import pytest
from types import SimpleNamespace
from src.gemini_service import GeminiService, GeminiServiceError

class Models:
    def __init__(self, responses): self.responses=iter(responses); self.calls=0
    def generate_content(self, **kwargs):
        self.calls+=1; item=next(self.responses)
        if isinstance(item,Exception): raise item
        return SimpleNamespace(text=item)
class Client:
    def __init__(self,responses): self.models=Models(responses)

def test_missing_key():
    with pytest.raises(GeminiServiceError,match="missing"): GeminiService(api_key=None,client=None).generate("hi")
def test_mock_success(): assert GeminiService(client=Client(["hello"])).generate("hi") == "hello"
def test_json_repair():
    service=GeminiService(client=Client(["{bad", '{"ok": true}']))
    assert service.generate_json("json") == {"ok":True}
def test_auth_failure():
    service=GeminiService(client=Client([RuntimeError("403 permission denied")]),max_retries=0)
    with pytest.raises(GeminiServiceError,match="authentication"): service.generate("x")
def test_quota_failure():
    service=GeminiService(client=Client([RuntimeError("429 quota exceeded")]),max_retries=0)
    with pytest.raises(GeminiServiceError,match="quota"): service.generate("x")



def test_model_not_found_has_actionable_message():
    service = GeminiService(client=Client([RuntimeError("404 NOT_FOUND model not found")]), max_retries=2)
    with pytest.raises(GeminiServiceError, match="model.*unavailable"):
        service.generate("x")
    assert service.client.models.calls == 1


def test_unknown_error_includes_diagnostic():
    service = GeminiService(client=Client([RuntimeError("unexpected request parameter foo")]), max_retries=2)
    with pytest.raises(GeminiServiceError, match="unexpected request parameter foo"):
        service.generate("x")
    assert service.client.models.calls == 1


def test_transient_error_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("src.gemini_service.time.sleep", lambda _: None)
    service = GeminiService(client=Client([RuntimeError("503 service unavailable"), "ok"]), max_retries=1)
    assert service.generate("x") == "ok"
    assert service.client.models.calls == 2
