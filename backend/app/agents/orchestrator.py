"""Orchestrator — manages the multi-agent pipeline with complexity routing.

Pipeline:
  Router → decides fast_track or full_pipeline
  fast_track:    Agent A (creator profile) → Agent D (report)
  full_pipeline: Agent A ‖ Agent B (parallel) → Agent C (debate) → Agent D (report)
"""

import asyncio
import logging
from collections.abc import Callable

from app.agents.creator_profile import CreatorProfileAgent
from app.agents.market_data import MarketIntelAgent
from app.agents.debate import DebateAgent
from app.agents.report import ReportAgent
from app.llm.provider import LLMClient
from app.utils.pricing_tables import route_complexity

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates the multi-agent analysis pipeline."""

    def __init__(self, llm_client: LLMClient, language: str = "en") -> None:
        self.llm_client = llm_client
        self.language = language

    async def run_pipeline(
        self,
        creator_data: dict,
        brand_info: dict,
        on_progress: Callable[[str, str], None] | None = None,
    ) -> dict:
        """
        Execute the analysis pipeline with complexity routing.

        Args:
            creator_data: Creator profile information.
            brand_info: Brand name, deal type, usage rights, exclusivity.
            on_progress: Callback invoked as (agent_name, status).

        Returns:
            Dict with all agent outputs keyed by stage name.
        """

        def progress(agent: str, status: str) -> None:
            if on_progress:
                on_progress(agent, status)

        context = {
            "creator_data": creator_data,
            "brand_info": brand_info,
        }

        # --- Route complexity ---
        niche = creator_data.get("content_niche", "lifestyle_vlog")
        route = route_complexity(
            brand_name=brand_info.get("brand_name"),
            exclusivity=brand_info.get("exclusivity", "none"),
            usage_rights=brand_info.get("usage_rights", "organic_only"),
            niche=niche,
            is_first_brand_deal=brand_info.get("is_first_brand_deal", False),
        )
        logger.info("Pipeline routing: %s", route)

        # --- Phase 1: Creator Profile (always runs) ---
        logger.info("Pipeline Phase 1: Creator Profile Agent")
        creator_agent = CreatorProfileAgent(self.llm_client, self.language)
        progress("creator_profile", "running")

        if route == "full_pipeline":
            # In full pipeline, Agent A runs first (Agent B needs its output)
            creator_result = await creator_agent.run(context)
            progress("creator_profile", "completed")
            context["creator_analysis"] = creator_result

            # --- Phase 2: Market Intel (parallel-ready, but depends on A) ---
            logger.info("Pipeline Phase 2: Market Intelligence Agent")
            market_agent = MarketIntelAgent(self.llm_client, self.language)
            progress("market_intel", "running")
            market_result = await market_agent.run(context)
            progress("market_intel", "completed")
            context["market_intel"] = market_result

            # --- Phase 3: Debate ---
            logger.info("Pipeline Phase 3: Adversarial Debate Agent")
            debate_agent = DebateAgent(self.llm_client, self.language)
            progress("debate", "running")
            debate_result = await debate_agent.run(context)
            progress("debate", "completed")
            context["debate_result"] = debate_result

        else:
            # Fast track: only Agent A
            creator_result = await creator_agent.run(context)
            progress("creator_profile", "completed")
            context["creator_analysis"] = creator_result

            # Skip market_intel and debate — mark as skipped
            progress("market_intel", "skipped")
            progress("debate", "skipped")

        # --- Final Phase: Report Generation ---
        logger.info("Pipeline Final Phase: Report Agent")
        report_agent = ReportAgent(self.llm_client, self.language)
        progress("report", "running")
        final_report = await report_agent.run(context)
        progress("report", "completed")

        return {
            "route": route,
            "creator_analysis": creator_result,
            "market_intel": context.get("market_intel"),
            "debate_result": context.get("debate_result"),
            "final_report": final_report,
        }
