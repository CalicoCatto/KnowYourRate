import asyncio
import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.api.deps import get_db, get_llm_client
from app.llm.provider import LLMClient
from app.models.analysis_run import AnalysisRun
from app.models.creator import Creator
from app.schemas.analysis import AnalysisRequest, AnalysisResult, AnalysisStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory progress tracking for SSE (per run_id)
_progress_store: dict[str, list[dict]] = {}


async def _run_analysis(
    run_id: str,
    creator_data: dict,
    brand_name: str,
    deal_type: str,
    language: str,
    llm_client: LLMClient,
    db_url: str,
) -> None:
    """Execute the agent pipeline in the background."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

    engine_kwargs: dict = {}
    if db_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    bg_engine = create_async_engine(db_url, **engine_kwargs)
    bg_session_factory = async_sessionmaker(bg_engine, class_=AsyncSession, expire_on_commit=False)

    async with bg_session_factory() as session:
        run = await session.get(AnalysisRun, run_id)
        if not run:
            logger.error("Analysis run %s not found", run_id)
            return

        try:
            run.status = "running"
            await session.commit()

            def on_progress(agent_name: str, status: str) -> None:
                _progress_store.setdefault(run_id, []).append(
                    {"agent": agent_name, "status": status}
                )

            orchestrator = AgentOrchestrator(llm_client=llm_client, language=language)
            result = await orchestrator.run_pipeline(
                creator_data=creator_data,
                brand_info={"brand_name": brand_name, "deal_type": deal_type},
                on_progress=on_progress,
            )

            run.market_data = result.get("market_data")
            run.creator_analysis = result.get("creator_analysis")
            run.brand_analysis = result.get("brand_analysis")
            run.debate_result = result.get("debate_result")
            run.final_report = result.get("final_report")
            run.status = "completed"

            from datetime import datetime, timezone
            run.completed_at = datetime.now(timezone.utc)
            await session.commit()

        except Exception as e:
            logger.exception("Analysis run %s failed", run_id)
            run.status = "failed"
            run.error_message = str(e)
            await session.commit()
        finally:
            _progress_store.setdefault(run_id, []).append(
                {"agent": "pipeline", "status": run.status}
            )
            await bg_engine.dispose()


@router.post("/run", response_model=AnalysisStatus)
async def start_analysis(
    body: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> AnalysisStatus:
    """Start the agent pipeline in a background task."""
    creator_data: dict = {}

    if body.creator_id:
        creator = await db.get(Creator, str(body.creator_id))
        if not creator:
            raise HTTPException(status_code=404, detail="Creator not found")
        creator_data = {
            "platform": creator.platform,
            "handle": creator.handle,
            "display_name": creator.display_name,
            "subscriber_count": creator.subscriber_count,
            "avg_views": creator.avg_views,
            "engagement_rate": creator.engagement_rate,
            "content_niche": creator.content_niche,
            "raw_data": creator.raw_data,
        }
    elif body.manual_data:
        creator_data = body.manual_data
    else:
        raise HTTPException(
            status_code=400,
            detail="Either creator_id or manual_data is required",
        )

    run = AnalysisRun(
        creator_id=str(body.creator_id) if body.creator_id else None,
        brand_name=body.brand_name,
        deal_type=body.deal_type,
        status="pending",
    )
    db.add(run)
    await db.commit()

    from app.config import get_settings
    db_url = get_settings().DATABASE_URL

    background_tasks.add_task(
        _run_analysis,
        run_id=str(run.id),
        creator_data=creator_data,
        brand_name=body.brand_name,
        deal_type=body.deal_type,
        language=body.language,
        llm_client=llm_client,
        db_url=db_url,
    )

    return AnalysisStatus(
        run_id=run.id,
        status="pending",
        current_agent=None,
        progress=0.0,
    )


@router.get("/{run_id}/status")
async def stream_status(run_id: UUID) -> StreamingResponse:
    """SSE endpoint streaming agent progress updates."""

    async def event_stream():
        sent = 0
        max_wait = 600  # 10 minutes timeout
        elapsed = 0.0

        while elapsed < max_wait:
            events = _progress_store.get(str(run_id), [])
            while sent < len(events):
                event = events[sent]
                data = json.dumps(event)
                yield f"data: {data}\n\n"
                sent += 1

                # Only close the stream when the whole pipeline finishes
                if event.get("agent") == "pipeline" and event.get("status") in ("completed", "failed"):
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    return

            await asyncio.sleep(0.5)
            elapsed += 0.5

        yield f"data: {json.dumps({'error': 'timeout'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/{run_id}/result", response_model=AnalysisResult)
async def get_result(
    run_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalysisResult:
    """Return the completed analysis result."""
    run = await db.get(AnalysisRun, str(run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    if run.status == "pending" or run.status == "running":
        raise HTTPException(status_code=202, detail="Analysis still in progress")

    if run.status == "failed":
        raise HTTPException(status_code=500, detail=f"Analysis failed: {run.error_message}")

    return AnalysisResult(
        run_id=run.id,
        status=run.status,
        market_data=run.market_data,
        creator_analysis=run.creator_analysis,
        brand_analysis=run.brand_analysis,
        debate_result=run.debate_result,
        final_report=run.final_report,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )
