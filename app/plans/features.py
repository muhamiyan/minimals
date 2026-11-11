"""Feature registry — every flag a plan can grant.

The registry is the single source of truth: plan payloads are validated
against it, resolution derives the visible feature set from it, and the
console renders one toggle per key, grouped by category. Adding a feature
means adding it here; existing plans start with it disabled until an
admin enables it.
"""
from __future__ import annotations

# Category -> feature keys, in display order. Categories are presentational
# groupings for the plan editor; they carry no behavior.
FEATURE_CATEGORIES: dict[str, tuple[str, ...]] = {
    "insights": ("advanced_reporting",),
    "support": ("priority_support",),
    "platform": ("custom_domain",),
    "productivity": ("todo",),
}

FEATURE_KEYS: tuple[str, ...] = tuple(
    key for keys in FEATURE_CATEGORIES.values() for key in keys
)

# Flags the Professional tier implied before plans became editable. Kept
# explicit so new registry keys stay opt-in for seeded defaults.
DEFAULT_PROFESSIONAL_FEATURES: dict[str, bool] = {
    "advanced_reporting": True,
    "priority_support": True,
    "custom_domain": True,
}


__all__ = [
    "DEFAULT_PROFESSIONAL_FEATURES",
    "FEATURE_CATEGORIES",
    "FEATURE_KEYS",
]
