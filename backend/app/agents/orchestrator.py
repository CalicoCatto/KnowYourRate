"""Orchestrator — manages the multi-agent pipeline with complexity routing.

Pipeline:
  Router → decides fast_track or full_pipeline
  fast_track:    Agent A (creator profile) → Agent D (report)
  full_pipeline: Agent A ‖ Agent B (parallel) → Agent C (debate) → Agent D (report)

Supports both international and CN editions via EDITION env var.
"""

import asyncio
import logging
from collections.abc import Callable

from app.edition import is_cn
from app.agents.debate import DebateAgent
from app.llm.provider import LLMClient

logger = logging.getLogger(__name__)


def _load_agents():
    """Load agent classes based on current edition."""
    if is_cn():
        from app.agents.creator_profile_cn import CreatorProfileCNAgent as ProfileAgent
        from app.agents.market_data_cn import MarketIntelCNAgent as MarketAgent
        from app.agents.report_cn import ReportCNAgent as ReportAgentCls
        from app.utils.pricing_tables_cn import route_complexity_cn as route_fn
    else:
        from app.agents.creator_profile import CreatorProfileAgent as ProfileAgent
        from app.agents.market_data import MarketIntelAgent as MarketAgent
        from app.agents.report import ReportAgent as ReportAgentCls
        from app.utils.pricing_tables import route_complexity as route_fn
    return ProfileAgent, MarketAgent, ReportAgentCls, route_fn


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

        ProfileAgent, MarketAgent, ReportAgentCls, route_fn = _load_agents()

        context = {
            "creator_data": creator_data,
            "brand_info": brand_info,
        }

        # --- Data Validator (CN only) ---
        data_quality = None
        if is_cn():
            from app.utils.pricing_tables_cn import validate_input_data_cn
            data_quality = validate_input_data_cn(
                platform=creator_data.get("platform", "bilibili"),
                followers=int(creator_data.get("subscriber_count", 0)),
                avg_views=int(creator_data.get("avg_views", 0)) or None,
                engagement_rate=float(creator_data.get("engagement_rate", 0)) or None,
                niche=creator_data.get("content_niche"),
            )
            context["data_quality"] = data_quality
            if data_quality.get("warnings") or data_quality.get("anomalies"):
                logger.info(
                    "Data Validator: warnings=%s, anomalies=%s, degradation=%s",
                    data_quality.get("warnings", []),
                    data_quality.get("anomalies", []),
                    data_quality.get("degradation_level"),
                )

        # --- Route complexity ---
        niche = creator_data.get("content_niche", "lifestyle_vlog")
        if is_cn():
            route = route_fn(
                brand_name=brand_info.get("brand_name"),
                exclusivity=brand_info.get("exclusivity", "none"),
                usage_rights=brand_info.get("usage_rights", "organic_only"),
                niche=niche,
                is_first_brand_deal=brand_info.get("is_first_brand_deal", False),
                has_livestream=brand_info.get("has_livestream", False),
                num_platforms=brand_info.get("num_platforms", 1),
            )
            # Data quality can force fast_track
            if data_quality and data_quality.get("degradation_level") == "minimal":
                route = "fast_track"
                logger.info("Data quality too low, forcing fast_track")
        else:
            route = route_fn(
                brand_name=brand_info.get("brand_name"),
                exclusivity=brand_info.get("exclusivity", "none"),
                usage_rights=brand_info.get("usage_rights", "organic_only"),
                niche=niche,
                is_first_brand_deal=brand_info.get("is_first_brand_deal", False),
            )
        logger.info("Pipeline routing: %s (edition=%s)", route, "cn" if is_cn() else "international")

        # --- Phase 1: Creator Profile (always runs) ---
        logger.info("Pipeline Phase 1: Creator Profile Agent")
        creator_agent = ProfileAgent(self.llm_client, self.language)
        progress("creator_profile", "running")

        if route == "full_pipeline":
            # In full pipeline, Agent A runs first (Agent B needs its output)
            creator_result = await creator_agent.run(context)
            progress("creator_profile", "completed")
            context["creator_analysis"] = creator_result

            # --- Phase 2: Market Intel (parallel-ready, but depends on A) ---
            logger.info("Pipeline Phase 2: Market Intelligence Agent")
            market_agent = MarketAgent(self.llm_client, self.language)
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
        report_agent = ReportAgentCls(self.llm_client, self.language)
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
