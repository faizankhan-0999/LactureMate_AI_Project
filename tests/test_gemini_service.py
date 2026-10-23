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
    with pytest.raises(GeminiServiceError,match="denied access"): service.generate("x")
def test_quota_failure():
    service=GeminiService(client=Client([RuntimeError("429 quota exceeded")]),max_retries=0)
    with pytest.raises(GeminiServiceError,match="quota"): service.generate("x")

def test_invalid_request_is_not_retried():
    error = RuntimeError("400 INVALID_ARGUMENT: unsupported response setting")
    error.status_code = 400
    client = Client([error])
    service = GeminiService(client=client, max_retries=2)
    with pytest.raises(GeminiServiceError, match="rejected the request"):
        service.generate("safe prompt")
    assert client.models.calls == 1


def test_transient_server_error_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("src.gemini_service.time.sleep", lambda _seconds: None)
    error = RuntimeError("503 service unavailable")
    error.status_code = 503
    client = Client([error, "success"])
    assert GeminiService(client=client, max_retries=1).generate("hello") == "success"
    assert client.models.calls == 2


def test_transient_retry_limit_is_bounded(monkeypatch):
    monkeypatch.setattr("src.gemini_service.time.sleep", lambda _seconds: None)
    errors = []
    for _ in range(5):
        err = RuntimeError("503 service unavailable")
        err.status_code = 503
        errors.append(err)
    client = Client(errors)
    with pytest.raises(GeminiServiceError, match="temporarily"):
        GeminiService(client=client, max_retries=1).generate("hello")
    assert client.models.calls == 2


def test_model_not_found_is_actionable_and_not_retried():
    error = RuntimeError("404 model not found")
    error.status_code = 404
    client = Client([error])
    with pytest.raises(GeminiServiceError, match="model was not found"):
        GeminiService(client=client, model="bad-model", max_retries=2).generate("hello")
    assert client.models.calls == 1


def test_invalid_json_after_repair_is_actionable():
    service = GeminiService(client=Client(["not json", "still not json"]), max_retries=0)
    with pytest.raises(GeminiServiceError, match="malformed JSON"):
        service.generate_json("json please")
