import json
import logging

from app.agents.base import BaseAgent
from app.utils.prompts import REPORT_PROMPT

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """Generates the final pricing strategy report."""

    name = "report"
    description = "Produces the final pricing report with negotiation strategy"

    async def run(self, context: dict) -> dict:
        """Generate the final comprehensive pricing report."""
        creator = context.get("creator_data", {})
        brand_info = context.get("brand_info", {})
        market_data = context.get("market_data", {})
        creator_analysis = context.get("creator_analysis", {})
        brand_analysis = context.get("brand_analysis", {})
        debate_result = context.get("debate_result", {})

        language_instruction = ""
        if self.language and self.language != "en":
            language_instruction = (
                f"IMPORTANT: Write the entire report in the language with code '{self.language}'. "
                f"All text, headings, and descriptions should be in that language. "
                f"Only keep technical terms and brand names in English."
            )

        prompt = self.build_prompt(
            REPORT_PROMPT,
            language_instruction=language_instruction,
            display_name=creator.get("display_name", "Unknown"),
            platform=creator.get("platform", "unknown"),
            brand_name=brand_info.get("brand_name", "Unknown Brand"),
            deal_type=brand_info.get("deal_type", "sponsored_video"),
            market_data=json.dumps(market_data, default=str),
            creator_analysis=json.dumps(creator_analysis, default=str),
            brand_analysis=json.dumps(brand_analysis, default=str),
            debate_result=json.dumps(debate_result, default=str),
        )

        logger.info("ReportAgent: generating final report")
        result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional influencer marketing consultant. "
                        "Generate a thorough, actionable pricing strategy report. "
                        "Always respond with valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        logger.info("ReportAgent: report generated, confidence=%s", result.get("confidence_level"))
        return result
