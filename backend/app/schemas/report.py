from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ReportCreate(BaseModel):
    """Request to create a report from an analysis run."""

    analysis_run_id: UUID
    title: str | None = None
    summary: str | None = None
    price_low: Decimal | None = None
    price_mid: Decimal | None = None
    price_high: Decimal | None = None
    currency: str | None = None


class ReportResponse(BaseModel):
    """Full report response."""

    id: str
    analysis_run_id: str
    title: str
    summary: str
    price_low: Decimal | None = None
    price_mid: Decimal | None = None
    price_high: Decimal | None = None
    currency: str
    full_report: dict | None = None
    created_at: datetime


class ReportList(BaseModel):
    """Summary report for list view."""

    id: str
    title: str
    summary: str
    price_low: Decimal | None = None
    price_mid: Decimal | None = None
    price_high: Decimal | None = None
    currency: str
    created_at: datetime
