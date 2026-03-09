import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalysisRun(Base):
    """Represents a single analysis pipeline execution."""

    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    creator_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("creators.id", ondelete="SET NULL"),
        nullable=True,
    )
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    deal_type: Mapped[str] = mapped_column(String(100), nullable=False, default="sponsored_video")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    current_agent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    creator_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    brand_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    debate_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    final_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
    )
