"""Feature registry — every flag a plan can grant.

The registry is the single source of truth: plan payloads are validated
against it, resolution derives the visible feature set from it, and the
console renders one toggle per key. Adding a feature means adding it here;
existing plans start with it disabled until an admin enables it.
"""
from __future__ import annotations

FEATURE_KEYS: tuple[str, ...] = (
    "advanced_reporting",
    "priority_support",
    "custom_domain",
    "todos",
)

# Flags the Professional tier implied before plans became editable. Kept
# explicit so new registry keys stay opt-in for seeded defaults.
DEFAULT_PROFESSIONAL_FEATURES: dict[str, bool] = {
    "advanced_reporting": True,
    "priority_support": True,
    "custom_domain": True,
}


__all__ = ["DEFAULT_PROFESSIONAL_FEATURES", "FEATURE_KEYS"]
