import json
import logging

from app.agents.base import BaseAgent
from app.utils.prompts import DEBATE_PROMPT

logger = logging.getLogger(__name__)


class DebateAgent(BaseAgent):
    """Dual-persona debate to find the pricing sweet spot."""

    name = "debate"
    description = "Simulates brand-vs-creator negotiation to find optimal pricing"

    async def run(self, context: dict) -> dict:
        """Run the negotiation debate between brand and creator personas."""
        creator = context.get("creator_data", {})
        brand_info = context.get("brand_info", {})
        market_data = context.get("market_data", {})
        creator_analysis = context.get("creator_analysis", {})
        brand_analysis = context.get("brand_analysis", {})

        prompt = self.build_prompt(
            DEBATE_PROMPT,
            display_name=creator.get("display_name", "Unknown"),
            platform=creator.get("platform", "unknown"),
            subscriber_count=creator.get("subscriber_count", 0),
            engagement_rate=creator.get("engagement_rate", 0),
            brand_name=brand_info.get("brand_name", "Unknown Brand"),
            deal_type=brand_info.get("deal_type", "sponsored_video"),
            rate_low=market_data.get("rate_low", 0),
            rate_mid=market_data.get("rate_mid", 0),
            rate_high=market_data.get("rate_high", 0),
            market_summary=json.dumps(market_data, default=str),
            creator_summary=json.dumps(creator_analysis, default=str),
            brand_summary=json.dumps(brand_analysis, default=str),
        )

        logger.info("DebateAgent: starting negotiation simulation")
        result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert negotiation simulator. Argue both sides fairly "
                        "and find a realistic pricing sweet spot. Always respond with valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        logger.info(
            "DebateAgent: debate complete, sweet_spot=%s",
            result.get("sweet_spot", {}).get("rate"),
        )
        return result
