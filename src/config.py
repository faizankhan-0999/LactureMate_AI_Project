"""Central configuration and safe API-key/model lookup."""
from __future__ import annotations
import os

# Use a current stable Gemini Flash model by default. A Streamlit Secret can override it.
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
MAX_UPLOAD_MB = int(os.getenv("LECTUREMATE_MAX_UPLOAD_MB", "25"))
CHUNK_CHARS = int(os.getenv("LECTUREMATE_CHUNK_CHARS", "9000"))
CHUNK_OVERLAP_CHARS = int(os.getenv("LECTUREMATE_CHUNK_OVERLAP_CHARS", "300"))


def get_model(secrets_obj=None) -> str:
    """Read GEMINI_MODEL from Streamlit Secrets first, then environment/default."""
    if secrets_obj is not None:
        try:
            value = secrets_obj.get("GEMINI_MODEL")
            if value and str(value).strip():
                return str(value).strip()
        except Exception:
            pass
    value = os.getenv("GEMINI_MODEL", "")
    return value.strip() or "gemini-3.8-flash"


def get_api_key(secrets_obj=None) -> str | None:
    """Read the API key from Streamlit secrets, then environment variables."""
    if secrets_obj is not None:
        try:
            value = secrets_obj.get("GEMINI_API_KEY")
            if value:
                return str(value).strip()
        except Exception:
            pass
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
