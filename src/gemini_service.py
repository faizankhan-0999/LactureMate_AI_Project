"""Gemini API wrapper using the official google-genai SDK."""
from __future__ import annotations

import json
import os
import re
import time

from .config import DEFAULT_MODEL, get_api_key


class GeminiServiceError(RuntimeError):
    """A safe, user-readable Gemini API error."""


class GeminiService:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL, client=None, max_retries: int = 2):
        self.api_key = api_key
        self.model = model
        self.client = client
        self.max_retries = max(0, int(max_retries))

    def _client(self):
        if self.client is not None:
            return self.client
        key = self.api_key or get_api_key()
        if not key:
            raise GeminiServiceError(
                "Gemini API key is missing. Add GEMINI_API_KEY to Streamlit Secrets "
                "or your local environment."
            )
        try:
            from google import genai
            self.client = genai.Client(api_key=key)
            return self.client
        except Exception as exc:
            raise GeminiServiceError(
                "Could not initialize Gemini. Install the requirements and verify "
                "that GEMINI_API_KEY is configured correctly."
            ) from exc

    def _friendly_error(self, exc: Exception) -> tuple[str, bool]:
        """Return a useful message and whether retrying may help."""
        message = str(exc)
        lowered = message.lower()
        status = str(getattr(exc, "code", "") or getattr(exc, "status_code", ""))

        if any(term in lowered for term in (
            "api key", "api_key_invalid", "unauthenticated", "permission denied",
            "invalid api key", " 401", " 403", "forbidden",
        )) or status in {"401", "403"}:
            return (
                "Gemini authentication failed. In Streamlit Cloud, open your app's "
                "Settings → Secrets and check that GEMINI_API_KEY is correct. "
                "Create a replacement key in Google AI Studio if needed, then reboot the app.",
                False,
            )

        if any(term in lowered for term in (
            "quota", "resource_exhausted", "rate limit", " 429",
        )) or status == "429":
            return (
                "Gemini API quota or rate limit reached. Check your API usage and "
                "quota settings, wait a little, and try again.",
                False,
            )

        if any(term in lowered for term in (
            "model not found", "not_found", "unknown model", "unsupported model",
        )) or status == "404":
            return (
                f"The Gemini model '{self.model}' is unavailable to this API key. "
                "The app defaults to 'gemini-flash-latest'. If GEMINI_MODEL is set "
                "in Streamlit Secrets or environment variables, remove that override "
                "or replace it with a model enabled for your account.",
                False,
            )

        if any(term in lowered for term in (
            "too many tokens", "token limit", "context length", "request too large",
            "payload too large", "input is too long",
        )) or (status in {"413", "400"} and any(
            term in lowered for term in ("token", "too large", "invalid argument", "request")
        )):
            return (
                "Gemini rejected the request because it may be too large or contain an "
                "invalid parameter. Try generating from a smaller lecture section and "
                "check that the selected model supports JSON output.",
                False,
            )

        transient = (
            "timeout", "timed out", "connection", "network", "dns", "ssl",
            "temporarily unavailable", " 500", " 502", " 503", " 504",
            "internal server error", "service unavailable", "server disconnected",
        )
        if any(term in lowered for term in transient) or status in {"408", "500", "502", "503", "504"}:
            return (
                "Gemini is temporarily unreachable or returned a server error. Check "
                "your internet connection and Google's API status, then retry.",
                True,
            )

        # Include a short diagnostic for unexpected SDK/API errors, while redacting keys.
        detail = re.sub(r"\s+", " ", message).strip()[:240]
        key = self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if key:
            detail = detail.replace(key, "[REDACTED]")
        if not detail:
            detail = "No additional error details were provided by the SDK."
        return (
            f"Gemini request failed ({type(exc).__name__}). Details: {detail} "
            f"Model: {self.model}. Verify the model name, API key access, and request size.",
            False,
        )

    def generate(self, prompt: str, *, json_mode: bool = False) -> str:
        client = self._client()
        config = {"temperature": 0.3}
        if json_mode:
            config["response_mime_type"] = "application/json"

        for attempt in range(self.max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=self.model, contents=prompt, config=config
                )
                text = getattr(response, "text", None)
                if not text or not str(text).strip():
                    raise GeminiServiceError(
                        "Gemini returned an empty response. The model may have blocked "
                        "the response or reached an output limit. Please retry."
                    )
                return str(text).strip()
            except GeminiServiceError:
                raise
            except Exception as exc:
                friendly, retryable = self._friendly_error(exc)
                if not retryable or attempt >= self.max_retries:
                    raise GeminiServiceError(friendly) from exc
                # Short exponential backoff; permanent client errors are not retried.
                time.sleep(0.5 * (2 ** attempt))

        raise GeminiServiceError("Gemini request failed. Please retry.")

    def generate_json(self, prompt: str):
        raw = self.generate(prompt, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            repaired = self.generate(
                "Return only valid JSON matching the original request. Repair this "
                "response without adding unsupported facts:\n" + raw,
                json_mode=True,
            )
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as exc:
                raise GeminiServiceError(
                    "Gemini returned invalid JSON after one repair attempt. Please retry."
                ) from exc
