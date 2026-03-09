import asyncio
import logging
from collections.abc import Callable

from app.agents.brand_strategy import BrandStrategyAgent
from app.agents.creator_profile import CreatorProfileAgent
from app.agents.debate import DebateAgent
from app.agents.market_data import MarketDataAgent
from app.agents.report import ReportAgent
from app.llm.provider import LLMClient

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
        Execute the full analysis pipeline:
          Phase 1: Market data, creator profile, brand strategy (parallel)
          Phase 2: Debate agent
          Phase 3: Report agent

        Args:
            creator_data: Creator profile information.
            brand_info: Brand name and deal type.
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
            "deal_type": brand_info.get("deal_type", "sponsored_video"),
        }

        # Phase 1: Parallel analysis
        logger.info("Pipeline Phase 1: starting parallel analysis agents")
        market_agent = MarketDataAgent(self.llm_client, self.language)
        creator_agent = CreatorProfileAgent(self.llm_client, self.language)
        brand_agent = BrandStrategyAgent(self.llm_client, self.language)

        progress("market_data", "running")
        progress("creator_profile", "running")
        progress("brand_strategy", "running")

        market_result, creator_result, brand_result = await asyncio.gather(
            market_agent.run(context),
            creator_agent.run(context),
            brand_agent.run(context),
        )

        progress("market_data", "completed")
        progress("creator_profile", "completed")
        progress("brand_strategy", "completed")

        context["market_data"] = market_result
        context["creator_analysis"] = creator_result
        context["brand_analysis"] = brand_result

        # Phase 2: Debate
        logger.info("Pipeline Phase 2: starting debate agent")
        debate_agent = DebateAgent(self.llm_client, self.language)
        progress("debate", "running")
        debate_result = await debate_agent.run(context)
        progress("debate", "completed")

        context["debate_result"] = debate_result

        # Phase 3: Final report
        logger.info("Pipeline Phase 3: generating final report")
        report_agent = ReportAgent(self.llm_client, self.language)
        progress("report", "running")
        final_report = await report_agent.run(context)
        progress("report", "completed")

        return {
            "market_data": market_result,
            "creator_analysis": creator_result,
            "brand_analysis": brand_result,
            "debate_result": debate_result,
            "final_report": final_report,
        }
