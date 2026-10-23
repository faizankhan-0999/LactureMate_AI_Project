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
