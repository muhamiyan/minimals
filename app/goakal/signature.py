"""Goakal webhook signature — re-exported from the shared helper.

Kept so ``app.goakal.signature`` remains a stable import path for callers
that already use it; new code should import from
``framework.infra.webhook_signature`` directly.
"""

from __future__ import annotations

from framework.infra.webhook_signature import verify_signature

__all__ = ["verify_signature"]
