"""Scholarship domain — re-exports bp, service, model, DTOs, and presenters."""
from __future__ import annotations

from app.scholarship.api import bp
from app.scholarship.dto import ScholarshipCreateIn, ScholarshipUpdateIn
from app.scholarship.models import Scholarship
from app.scholarship.presenters import ScholarshipOut, ScholarshipSummaryOut
from app.scholarship.services import ScholarshipService

__all__ = [
    "Scholarship",
    "ScholarshipCreateIn",
    "ScholarshipOut",
    "ScholarshipService",
    "ScholarshipSummaryOut",
    "ScholarshipUpdateIn",
    "bp",
]
