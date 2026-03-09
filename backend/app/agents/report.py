"""Agent D — Strategy Report Generation.

Synthesizes all previous agent outputs into a user-friendly pricing report.
The prices are ALREADY computed — this agent's job is presentation and narrative.
"""

import json
import logging

from app.agents.base import BaseAgent
from app.utils.prompts import REPORT_PROMPT

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """Generates the final comprehensive pricing strategy report."""

    name = "report"
    description = "Produces the final pricing report with negotiation strategy"

    async def run(self, context: dict) -> dict:
        creator_data = context.get("creator_data", {})
        brand_info = context.get("brand_info", {})
        creator_analysis = context.get("creator_analysis", {})
        market_intel = context.get("market_intel", {})
        debate_result = context.get("debate_result", {})

        display_name = creator_data.get("display_name", "Unknown")
        platform = creator_data.get("platform", "youtube")
        subscriber_count = int(creator_data.get("subscriber_count", 0))
        brand_name = brand_info.get("brand_name", "Unknown Brand")
        deliverable_type = brand_info.get("deal_type", "dedicated_video")

        # Extract computed prices
        base_range = creator_analysis.get("base_price_range", {})
        deal_range = market_intel.get("deal_adjusted_price_range", {}) if market_intel else {}
        deal_breakdown = market_intel.get("deal_breakdown", {}) if market_intel else {}
        modifiers = creator_analysis.get("applied_modifiers", {})
        package_tiers = market_intel.get("package_tiers", {}) if market_intel else {}
        red_flags = market_intel.get("contract_red_flags", []) if market_intel else []

        # Final prices from debate judge (or fall back to deal-adjusted / creator prices)
        judge = debate_result.get("judge_verdict", {}) if debate_result else {}
        final_range = judge.get("final_price_range", {})

        # Fallback chain: judge → market-adjusted → deal-adjusted → creator final
        fallback_range = (
            market_intel.get("market_adjusted_price_range")
            or deal_range
            or creator_analysis.get("final_price_range", {})
        )

        walk_away = final_range.get("walk_away") or fallback_range.get("low", 0)
        fair_market = final_range.get("fair_market") or fallback_range.get("mid", 0)
        anchor_price = final_range.get("anchor_price") or fallback_range.get("high", 0)

        modifiers_summary = json.dumps(modifiers, default=str)
        deal_breakdown_str = json.dumps(deal_breakdown, default=str)
        package_str = json.dumps(package_tiers, default=str)
        red_flags_str = json.dumps(red_flags, default=str)

        language_instruction = ""
        if self.language and self.language != "en":
            language_instruction = (
                f"IMPORTANT: Write the entire report in the language with code '{self.language}'. "
                f"All text, headings, and descriptions should be in that language. "
                f"Only keep technical terms, brand names, and currency in English."
            )

        prompt = self.build_prompt(
            REPORT_PROMPT,
            language_instruction=language_instruction,
            display_name=display_name,
            platform=platform,
            subscriber_count=subscriber_count,
            brand_name=brand_name,
            deliverable_type=deliverable_type,
            base_low=base_range.get("low", 0),
            base_mid=base_range.get("mid", 0),
            base_high=base_range.get("high", 0),
            deal_low=deal_range.get("low", walk_away),
            deal_mid=deal_range.get("mid", fair_market),
            deal_high=deal_range.get("high", anchor_price),
            modifiers_summary=modifiers_summary,
            deal_breakdown=deal_breakdown_str,
            creator_analysis=json.dumps(creator_analysis, default=str),
            market_intel=json.dumps(market_intel, default=str) if market_intel else "N/A (fast track)",
            debate_result=json.dumps(debate_result, default=str) if debate_result else "N/A (fast track)",
            walk_away=walk_away,
            fair_market=fair_market,
            anchor_price=anchor_price,
            package_tiers=package_str,
            red_flags=red_flags_str,
        )

        logger.info("ReportAgent: generating final report")
        result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional influencer marketing consultant. "
                        "Generate a thorough, actionable pricing strategy report. "
                        "Use the EXACT price numbers provided — do not invent different prices. "
                        "Always respond with valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        # Enforce the computed prices regardless of what LLM returns
        result["price_low"] = round(walk_away, 2)
        result["price_mid"] = round(fair_market, 2)
        result["price_high"] = round(anchor_price, 2)
        result["currency"] = "USD"

        logger.info("ReportAgent: done. confidence=%s", result.get("confidence_level"))
        return result
