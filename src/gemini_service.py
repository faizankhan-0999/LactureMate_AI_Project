"""Safe, diagnosable Gemini API wrapper using Google's official google-genai SDK."""
from __future__ import annotations

import json
import logging
import re
import time
import traceback
from typing import Any

from .config import DEFAULT_MODEL, get_api_key

logger = logging.getLogger(__name__)


class GeminiServiceError(RuntimeError):
    """Actionable, user-safe Gemini failure."""


def _status_code(exc: Exception) -> int | None:
    value = getattr(exc, "status_code", None)
    if value is None:
        value = getattr(exc, "code", None)
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_detail(exc: Exception) -> str:
    """Return a short diagnostic without logging prompts, credentials, or payloads."""
    detail = str(getattr(exc, "message", "") or str(exc) or type(exc).__name__)
    detail = re.sub(r"(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]", detail)
    detail = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_API_KEY]", detail)
    detail = re.sub(r"\s+", " ", detail).strip()
    # Avoid accidentally logging a server's echoed request or a long response body.
    return detail[:240] or type(exc).__name__


def _classify_error(exc: Exception) -> tuple[str, str, bool]:
    """Return (category, user-facing advice, retryable)."""
    status = _status_code(exc)
    message = _safe_detail(exc).lower()
    name = type(exc).__name__.lower()

    if any(term in message for term in ("api key not valid", "invalid api key", "unauthenticated", "authentication")) or status == 401:
        return "authentication", "Gemini rejected the API key. Check that GEMINI_API_KEY is correct and active.", False
    if status == 403 or any(term in message for term in ("permission denied", "permission_denied", "not authorized", "access denied")):
        return "permission", "Gemini denied access. Check that this API key has Gemini API access and that the configured model is available to your account.", False
    if status == 404 or any(term in message for term in ("model not found", "not found for api version", "unsupported model", "model is not supported")):
        return "model_unavailable", "The configured Gemini model was not found or is unavailable to this API key. Check GEMINI_MODEL and account access.", False
    if status == 429 or any(term in message for term in ("resource_exhausted", "rate limit", "too many requests", "quota")):
        if "quota" in message or "billing" in message or "limit: 0" in message:
            return "quota", "Gemini quota appears exhausted. Check the API project's quota/billing status, then try again when quota is available.", False
        return "rate_limit", "Gemini is rate-limiting requests. Wait briefly, then retry.", True
    if status == 400 or any(term in message for term in ("invalid argument", "invalid_argument", "bad request", "request payload")):
        if "model" in message and any(term in message for term in ("unsupported", "not found", "invalid")):
            return "model_unavailable", "The configured Gemini model is not supported for this request or API version. Verify the model name and access.", False
        return "invalid_request", "Gemini rejected the request. The request settings or response format may be unsupported; check the server diagnostic for the API error details.", False
    if status is not None and status >= 500:
        return "service_error", "Gemini is temporarily having a service problem. Wait a moment and retry.", True
    if any(term in name for term in ("timeout", "connecterror", "connectionerror", "networkerror")) or any(term in message for term in ("timed out", "timeout", "connection reset", "name or service not known", "temporary failure in name resolution", "network is unreachable")):
        return "network", "A network timeout or connection problem interrupted the Gemini request. Check the connection and retry.", True
    return "request_error", "The Gemini request failed for an unclassified reason. Check the server logs for the diagnostic category and HTTP status, then retry if appropriate.", False


class GeminiService:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL, client=None, max_retries: int = 2):
        self.api_key = api_key
        self.model = (model or "").strip()
        self.client = client
        self.max_retries = max(0, min(int(max_retries), 3))

    def _client(self):
        if self.client is not None:
            return self.client
        key = self.api_key or get_api_key()
        if not key:
            raise GeminiServiceError("Gemini API key is missing. Add GEMINI_API_KEY to Streamlit Secrets or your local environment.")
        if not self.model:
            raise GeminiServiceError("Gemini model is not configured. Set GEMINI_MODEL to a supported model identifier.")
        try:
            from google import genai
        except ImportError as exc:
            logger.error("Gemini SDK unavailable: package=google-genai; exception_type=%s", type(exc).__name__)
            raise GeminiServiceError("The google-genai package is not installed. Install the project's requirements.txt and restart the app.") from exc
        try:
            self.client = genai.Client(api_key=key)
            return self.client
        except Exception as exc:
            category, advice, _ = _classify_error(exc)
            logger.error("Gemini client initialization failed: category=%s exception_type=%s status=%s detail=%s\ntraceback_frames=%s", category, type(exc).__name__, _status_code(exc), _safe_detail(exc), "".join(traceback.format_tb(exc.__traceback__)))
            raise GeminiServiceError(f"Could not initialize the Gemini client. {advice}") from exc

    def generate(self, prompt: str, *, json_mode: bool = False) -> str:
        client = self._client()
        if not isinstance(prompt, str) or not prompt.strip():
            raise GeminiServiceError("Cannot send an empty prompt to Gemini.")
        config: dict[str, Any] = {"temperature": 0.2, "max_output_tokens": 12288}
        if json_mode:
            config["response_mime_type"] = "application/json"
        for attempt in range(self.max_retries + 1):
            try:
                # Official google-genai SDK call pattern.
                response = client.models.generate_content(model=self.model, contents=prompt, config=config)
                text = getattr(response, "text", None)
                if not text or not str(text).strip():
                    raise GeminiServiceError("Gemini returned no text. The response may have been blocked or truncated; retry or reduce the requested output size.")
                return str(text).strip()
            except GeminiServiceError:
                raise
            except Exception as exc:
                category, advice, retryable = _classify_error(exc)
                status = _status_code(exc)
                logger.error(
                    "Gemini generate_content failed: category=%s exception_type=%s status=%s model=%s attempt=%s/%s detail=%s",
                    category, type(exc).__name__, status, self.model, attempt + 1, self.max_retries + 1,
                    _safe_detail(exc) + "\ntraceback_frames=" + "".join(traceback.format_tb(exc.__traceback__)),
                )
                if not retryable or attempt >= self.max_retries:
                    raise GeminiServiceError(f"{advice} (diagnostic: {category}{f', HTTP {status}' if status is not None else ''}; see server logs for details.)") from exc
                # Bounded exponential backoff. SDK-level retries may also apply.
                time.sleep(min(0.5 * (2 ** attempt), 2.0))
        raise GeminiServiceError("Gemini request ended unexpectedly.")

    def generate_json(self, prompt: str):
        raw = self.generate(prompt, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as original_exc:
            logger.warning("Gemini returned malformed JSON; attempting one bounded repair. model=%s", self.model)
            repair_prompt = (
                "Repair the following model output into valid JSON only. Preserve its existing facts; do not add content. "
                "Return no Markdown fences or commentary.\n\n" + raw
            )
            repaired = self.generate(repair_prompt, json_mode=True)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as exc:
                logger.error("Gemini JSON repair failed: exception_type=%s model=%s", type(exc).__name__, self.model)
                raise GeminiServiceError("Gemini returned malformed JSON, and one repair attempt did not fix it. Regenerate the MCQs.") from original_exc
