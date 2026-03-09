from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    """Request to start an analysis pipeline."""

    creator_id: UUID | None = None
    manual_data: dict | None = None
    brand_name: str
    deal_type: str = "sponsored_video"
    language: str = "en"


class AnalysisStatus(BaseModel):
    """Current status of an analysis run."""

    run_id: str
    status: str
    current_agent: str | None = None
    progress: float = 0.0


class AnalysisResult(BaseModel):
    """Completed analysis result."""

    run_id: str
    status: str
    market_data: dict | None = None
    creator_analysis: dict | None = None
    brand_analysis: dict | None = None
    debate_result: dict | None = None
    final_report: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
