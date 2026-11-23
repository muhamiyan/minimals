"""Shared webhook signature helper — HMAC-SHA256 over raw body bytes.

Provider-agnostic: any third-party webhook that signs its payload with
``hmac(secret, body)`` hex-encoded can use this. Callers decide the HTTP
outcome (401 vs 500); this module only returns ``True``/``False``.
"""

from __future__ import annotations

import hashlib
import hmac


def verify_signature(body: bytes, signature: str | None, secret: str | None) -> bool:
    """Return ``True`` iff ``signature`` is the hex HMAC-SHA256 of ``body``."""
    if not signature or not secret:
        return False
    key = secret.encode("utf-8")
    digest = hmac.new(key=key, msg=body, digestmod=hashlib.sha256)
    return hmac.compare_digest(digest.hexdigest(), signature)


__all__ = ["verify_signature"]
