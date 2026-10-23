"""Gemini API wrapper using the official google-genai SDK."""
from __future__ import annotations
import json, time
from .config import DEFAULT_MODEL, get_api_key

class GeminiServiceError(RuntimeError): pass

class GeminiService:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL, client=None, max_retries: int = 2):
        self.api_key = api_key
        self.model = model
        self.client = client
        self.max_retries = max(0, int(max_retries))

    def _client(self):
        if self.client is not None: return self.client
        key = self.api_key or get_api_key()
        if not key: raise GeminiServiceError("Gemini API key is missing. Add GEMINI_API_KEY to Streamlit Secrets or your local environment.")
        try:
            from google import genai
            self.client = genai.Client(api_key=key)
            return self.client
        except Exception as exc:
            raise GeminiServiceError("Could not initialize Gemini. Check that google-genai is installed and the API key is valid.") from exc

    def generate(self, prompt: str, *, json_mode: bool = False) -> str:
        client = self._client()
        config = {"temperature": 0.3}
        if json_mode: config["response_mime_type"] = "application/json"
        last = None
        for attempt in range(self.max_retries + 1):
            try:
                response = client.models.generate_content(model=self.model, contents=prompt, config=config)
                text = getattr(response, "text", None)
                if not text or not str(text).strip(): raise GeminiServiceError("Gemini returned an empty response. Please retry.")
                return str(text).strip()
            except GeminiServiceError: raise
            except Exception as exc:
                last = exc
                message = str(exc).lower()
                if any(x in message for x in ("api key", "unauthenticated", "permission denied", "403")):
                    raise GeminiServiceError("Gemini authentication failed. Verify the API key and model access.") from exc
                if any(x in message for x in ("quota", "429", "resource_exhausted")):
                    raise GeminiServiceError("Gemini usage quota or rate limit was reached. Wait and try again, or check your API plan.") from exc
                if attempt < self.max_retries: time.sleep(0.4 * (attempt + 1))
        raise GeminiServiceError("Gemini request failed after retries. Check your connection and service status.") from last

    def generate_json(self, prompt: str):
        raw = self.generate(prompt, json_mode=True)
        try: return json.loads(raw)
        except json.JSONDecodeError:
            # Bounded repair attempt; do not expose malformed data as if valid.
            repaired = self.generate("Return only valid JSON matching the request. Repair this response without adding unsupported facts:\n" + raw, json_mode=True)
            try: return json.loads(repaired)
            except json.JSONDecodeError as exc: raise GeminiServiceError("Gemini returned invalid JSON after one repair attempt. Please retry.") from exc
