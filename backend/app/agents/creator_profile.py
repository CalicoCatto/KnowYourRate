import logging

from app.agents.base import BaseAgent
from app.utils.prompts import CREATOR_PROFILE_PROMPT

logger = logging.getLogger(__name__)


class CreatorProfileAgent(BaseAgent):
    """Analyzes a creator's market position from their channel data."""

    name = "creator_profile"
    description = "Evaluates creator's value proposition and market position"

    async def run(self, context: dict) -> dict:
        """Analyze creator's profile and market position."""
        creator = context.get("creator_data", {})

        prompt = self.build_prompt(
            CREATOR_PROFILE_PROMPT,
            platform=creator.get("platform", "unknown"),
            display_name=creator.get("display_name", "Unknown"),
            handle=creator.get("handle", ""),
            subscriber_count=creator.get("subscriber_count", 0),
            avg_views=creator.get("avg_views", 0),
            engagement_rate=creator.get("engagement_rate", 0),
            content_niche=creator.get("content_niche", "general"),
            raw_data=creator.get("raw_data", {}),
        )

        logger.info("CreatorProfileAgent: analyzing creator profile")
        result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert talent evaluator for influencer marketing. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        logger.info(
            "CreatorProfileAgent: analysis complete, leverage=%s",
            result.get("negotiation_leverage"),
        )
        return result
