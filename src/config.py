"""Central configuration and safe API-key lookup."""
from __future__ import annotations
import os

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_UPLOAD_MB = int(os.getenv("LECTUREMATE_MAX_UPLOAD_MB", "25"))
CHUNK_CHARS = int(os.getenv("LECTUREMATE_CHUNK_CHARS", "18000"))
CHUNK_OVERLAP_CHARS = int(os.getenv("LECTUREMATE_CHUNK_OVERLAP_CHARS", "800"))


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
