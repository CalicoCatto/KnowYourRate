import logging

from app.agents.base import BaseAgent
from app.utils.prompts import MARKET_DATA_PROMPT

logger = logging.getLogger(__name__)


class MarketDataAgent(BaseAgent):
    """Analyzes market rates for the creator's niche and tier."""

    name = "market_data"
    description = "Analyzes influencer market pricing benchmarks"

    async def run(self, context: dict) -> dict:
        """Analyze market rates based on creator profile data."""
        creator = context.get("creator_data", {})

        prompt = self.build_prompt(
            MARKET_DATA_PROMPT,
            platform=creator.get("platform", "unknown"),
            subscriber_count=creator.get("subscriber_count", 0),
            avg_views=creator.get("avg_views", 0),
            engagement_rate=creator.get("engagement_rate", 0),
            content_niche=creator.get("content_niche", "general"),
            deal_type=context.get("deal_type", "sponsored_video"),
        )

        logger.info("MarketDataAgent: analyzing market rates")
        result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert influencer marketing pricing analyst. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        logger.info("MarketDataAgent: analysis complete, tier=%s", result.get("tier"))
        return result
