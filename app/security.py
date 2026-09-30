import os
import secrets
from typing import Optional

from fastapi import Header, HTTPException


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Only callers that know DOCX_API_KEY (the qr-certificates server) get in."""
    expected = os.environ.get("DOCX_API_KEY", "")
    # Fail closed: without a configured key, nobody gets in.
    if not expected:
        raise HTTPException(status_code=503, detail="Server not configured")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
