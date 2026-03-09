import logging

from app.agents.base import BaseAgent
from app.utils.prompts import BRAND_STRATEGY_PROMPT

logger = logging.getLogger(__name__)


class BrandStrategyAgent(BaseAgent):
    """Analyzes brand's likely budget and negotiation patterns."""

    name = "brand_strategy"
    description = "Evaluates brand negotiation patterns and budget expectations"

    async def run(self, context: dict) -> dict:
        """Analyze brand strategy and negotiation approach."""
        creator = context.get("creator_data", {})
        brand_info = context.get("brand_info", {})
        market_data = context.get("market_data", {})

        prompt = self.build_prompt(
            BRAND_STRATEGY_PROMPT,
            brand_name=brand_info.get("brand_name", "Unknown Brand"),
            deal_type=brand_info.get("deal_type", "sponsored_video"),
            creator_tier=market_data.get("tier", "mid-tier"),
            content_niche=creator.get("content_niche", "general"),
        )

        logger.info("BrandStrategyAgent: analyzing brand strategy for %s", brand_info.get("brand_name"))
        result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": "You are a brand marketing strategist. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        logger.info(
            "BrandStrategyAgent: analysis complete, style=%s",
            result.get("negotiation_style"),
        )
        return result
