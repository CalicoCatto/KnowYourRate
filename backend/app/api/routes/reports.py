from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.analysis_run import AnalysisRun
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportList, ReportResponse

router = APIRouter()


@router.get("", response_model=list[ReportList])
async def list_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ReportList]:
    """List all saved reports."""
    result = await db.execute(
        select(Report).order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return [
        ReportList(
            id=r.id,
            title=r.title,
            summary=r.summary,
            price_low=r.price_low,
            price_mid=r.price_mid,
            price_high=r.price_high,
            currency=r.currency,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Get a single report by ID."""
    report = await db.get(Report, str(report_id))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse(
        id=report.id,
        analysis_run_id=report.analysis_run_id,
        title=report.title,
        summary=report.summary,
        price_low=report.price_low,
        price_mid=report.price_mid,
        price_high=report.price_high,
        currency=report.currency,
        full_report=report.full_report,
        agent_outputs=report.agent_outputs,
        created_at=report.created_at,
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Delete a report."""
    report = await db.get(Report, str(report_id))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await db.delete(report)
    return {"status": "deleted"}


@router.post("", response_model=ReportResponse)
async def create_report(
    body: ReportCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Save a report from a completed analysis run."""
    run = await db.get(AnalysisRun, str(body.analysis_run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    if run.status != "completed":
        raise HTTPException(status_code=400, detail="Analysis run is not completed")

    # Check for existing report for this run
    existing = await db.execute(
        select(Report).where(Report.analysis_run_id == str(body.analysis_run_id))
    )
    existing_report = existing.scalar_one_or_none()
    if existing_report:
        return ReportResponse(
            id=existing_report.id,
            analysis_run_id=existing_report.analysis_run_id,
            title=existing_report.title,
            summary=existing_report.summary,
            price_low=existing_report.price_low,
            price_mid=existing_report.price_mid,
            price_high=existing_report.price_high,
            currency=existing_report.currency,
            full_report=existing_report.full_report,
            agent_outputs=existing_report.agent_outputs,
            created_at=existing_report.created_at,
        )

    final = run.final_report or {}

    # Collect all agent outputs for the detailed view
    agent_outputs = {
        "creator_analysis": run.creator_analysis,
        "market_intel": run.market_data,
        "market_data": run.market_data,
        "brand_analysis": run.brand_analysis,
        "debate_result": run.debate_result,
    }

    report = Report(
        analysis_run_id=str(body.analysis_run_id),
        title=body.title or final.get("title", "Untitled Report"),
        summary=body.summary or final.get("summary", ""),
        price_low=body.price_low or final.get("price_low"),
        price_mid=body.price_mid or final.get("price_mid"),
        price_high=body.price_high or final.get("price_high"),
        currency=body.currency or final.get("currency", "USD"),
        full_report=run.final_report,
        agent_outputs=agent_outputs,
    )
    db.add(report)
    await db.flush()

    return ReportResponse(
        id=report.id,
        analysis_run_id=report.analysis_run_id,
        title=report.title,
        summary=report.summary,
        price_low=report.price_low,
        price_mid=report.price_mid,
        price_high=report.price_high,
        currency=report.currency,
        full_report=report.full_report,
        agent_outputs=report.agent_outputs,
        created_at=report.created_at,
    )
