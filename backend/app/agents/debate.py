"""Agent C — Adversarial Debate (Bull vs Bear + Judge).

2-round debate: Round 1 = independent arguments, Round 2 = cross-rebuttal (implicit).
Bull (creator agent) argues high, Bear (brand manager) argues low, Judge synthesizes.
"""

import asyncio
import json
import logging

from app.agents.base import BaseAgent
from app.utils.prompts import (
    DEBATE_BULL_PROMPT,
    DEBATE_BEAR_PROMPT,
    DEBATE_CROSS_REBUTTAL_PROMPT,
    DEBATE_JUDGE_PROMPT,
)

logger = logging.getLogger(__name__)


class DebateAgent(BaseAgent):
    """Runs adversarial pricing debate with Bull, Bear, and Judge roles."""

    name = "debate"
    description = "Adversarial debate between creator agent and brand manager"

    async def run(self, context: dict) -> dict:
        creator_data = context.get("creator_data", {})
        brand_info = context.get("brand_info", {})
        creator_analysis = context.get("creator_analysis", {})
        market_intel = context.get("market_intel", {})

        display_name = creator_data.get("display_name", "Unknown")
        platform = creator_data.get("platform", "youtube")
        subscriber_count = int(creator_data.get("subscriber_count", 0))
        engagement_rate = float(creator_data.get("engagement_rate", 0))
        brand_name = brand_info.get("brand_name", "Unknown Brand")
        deliverable_type = brand_info.get("deal_type", "dedicated_video")

        # Use market-adjusted price if available, fall back to creator's final price
        price_range = market_intel.get(
            "market_adjusted_price_range",
            creator_analysis.get("final_price_range", {}),
        )
        price_low = price_range.get("low", 0)
        price_mid = price_range.get("mid", 0)
        price_high = price_range.get("high", 0)

        creator_summary = json.dumps(creator_analysis, default=str)
        market_summary = json.dumps(market_intel, default=str)

        common_kwargs = dict(
            display_name=display_name,
            platform=platform,
            subscriber_count=subscriber_count,
            engagement_rate=engagement_rate,
            brand_name=brand_name,
            deliverable_type=deliverable_type,
            price_low=price_low,
            price_mid=price_mid,
            price_high=price_high,
            creator_summary=creator_summary,
            market_summary=market_summary,
        )

        # --- Round 1: Bull and Bear argue independently ---
        logger.info("DebateAgent: starting bull argument")
        bull_prompt = self.build_prompt(DEBATE_BULL_PROMPT, **common_kwargs)
        bull_result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a creator's talent agent fighting for the highest "
                        "justifiable price. Be aggressive but data-driven. "
                        "Always respond with valid JSON."
                    ),
                },
                {"role": "user", "content": bull_prompt},
            ],
            temperature=0.7,
        )

        logger.info("DebateAgent: starting bear argument")
        bear_prompt = self.build_prompt(DEBATE_BEAR_PROMPT, **common_kwargs)
        bear_result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a shrewd brand procurement manager evaluating true "
                        "market value. Be conservative and ROI-focused. "
                        "Always respond with valid JSON."
                    ),
                },
                {"role": "user", "content": bear_prompt},
            ],
            temperature=0.3,
        )

        bull_price = bull_result.get("suggested_price", price_high)
        bear_price = bear_result.get("suggested_price", price_low)
        if not isinstance(bull_price, (int, float)):
            bull_price = price_high
        if not isinstance(bear_price, (int, float)):
            bear_price = price_low

        # --- Round 2: Cross-rebuttal (Bull rebuts Bear, Bear rebuts Bull) ---
        logger.info("DebateAgent: starting cross-rebuttal round")

        bull_args_text = json.dumps(bull_result.get("arguments", []), indent=2, default=str)
        bear_args_text = json.dumps(bear_result.get("arguments", []), indent=2, default=str)

        rebuttal_common = dict(
            display_name=display_name,
            platform=platform,
            subscriber_count=subscriber_count,
            brand_name=brand_name,
            deliverable_type=deliverable_type,
            price_low=price_low,
            price_mid=price_mid,
            price_high=price_high,
        )

        bull_rebuttal_prompt = self.build_prompt(
            DEBATE_CROSS_REBUTTAL_PROMPT,
            role="创作者的经纪人（Bull方）",
            opponent_arguments=bear_args_text,
            **rebuttal_common,
        )
        bear_rebuttal_prompt = self.build_prompt(
            DEBATE_CROSS_REBUTTAL_PROMPT,
            role="品牌采购经理（Bear方）",
            opponent_arguments=bull_args_text,
            **rebuttal_common,
        )

        bull_rebuttal_task = self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a creator's talent agent rebutting the brand manager's arguments. "
                        "Be persuasive and data-driven. Always respond with valid JSON."
                    ),
                },
                {"role": "user", "content": bull_rebuttal_prompt},
            ],
            temperature=0.7,
        )
        bear_rebuttal_task = self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a brand procurement manager rebutting the creator agent's arguments. "
                        "Be analytical and ROI-focused. Always respond with valid JSON."
                    ),
                },
                {"role": "user", "content": bear_rebuttal_prompt},
            ],
            temperature=0.3,
        )

        bull_rebuttal_result, bear_rebuttal_result = await asyncio.gather(
            bull_rebuttal_task, bear_rebuttal_task
        )

        bull_rebuttals_text = json.dumps(bull_rebuttal_result.get("rebuttals", []), indent=2, default=str)
        bear_rebuttals_text = json.dumps(bear_rebuttal_result.get("rebuttals", []), indent=2, default=str)

        # --- Round 3: Judge synthesizes ---
        logger.info("DebateAgent: judge synthesizing (bull=$%.0f, bear=$%.0f)", bull_price, bear_price)

        judge_prompt = self.build_prompt(
            DEBATE_JUDGE_PROMPT,
            display_name=display_name,
            platform=platform,
            subscriber_count=subscriber_count,
            brand_name=brand_name,
            deliverable_type=deliverable_type,
            price_low=price_low,
            price_mid=price_mid,
            price_high=price_high,
            bull_price=bull_price,
            bull_arguments=bull_args_text,
            bear_price=bear_price,
            bear_arguments=bear_args_text,
            bull_rebuttals=bull_rebuttals_text,
            bear_rebuttals=bear_rebuttals_text,
        )

        judge_result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a neutral pricing expert synthesizing a debate. "
                        "Ground your analysis in the engine-computed price range. "
                        "Always respond with valid JSON."
                    ),
                },
                {"role": "user", "content": judge_prompt},
            ],
            temperature=0.4,
        )

        # Validate and fix judge output
        final_range = judge_result.get("final_price_range", {})
        walk_away = final_range.get("walk_away", price_low)
        fair_market = final_range.get("fair_market", price_mid)
        anchor_price = final_range.get("anchor_price", price_high)

        # Ensure numeric and ordered
        for val_name in ("walk_away", "fair_market", "anchor_price"):
            val = locals()[val_name]
            if not isinstance(val, (int, float)):
                locals()[val_name] = price_mid

        prices = sorted([walk_away, fair_market, anchor_price])
        walk_away, fair_market, anchor_price = prices[0], prices[1], prices[2]

        logger.info(
            "DebateAgent: done. walk_away=$%.0f, fair=$%.0f, anchor=$%.0f",
            walk_away, fair_market, anchor_price,
        )

        return {
            "bull_argument": {
                "suggested_price": bull_price,
                "arguments": bull_result.get("arguments", []),
                "preemptive_rebuttals": bull_result.get("preemptive_rebuttals", []),
            },
            "bear_argument": {
                "suggested_price": bear_price,
                "arguments": bear_result.get("arguments", []),
                "counter_arguments": bear_result.get("counter_arguments", []),
            },
            "bull_cross_rebuttal": {
                "rebuttals": bull_rebuttal_result.get("rebuttals", []),
                "reinforced_position": bull_rebuttal_result.get("reinforced_position", ""),
            },
            "bear_cross_rebuttal": {
                "rebuttals": bear_rebuttal_result.get("rebuttals", []),
                "reinforced_position": bear_rebuttal_result.get("reinforced_position", ""),
            },
            "judge_verdict": {
                "final_price_range": {
                    "walk_away": round(walk_away, 2),
                    "fair_market": round(fair_market, 2),
                    "anchor_price": round(anchor_price, 2),
                },
                "confidence": judge_result.get("confidence", 0.7),
                "uncertainty_flag": judge_result.get("uncertainty_flag", False),
                "key_factors": judge_result.get("key_factors", []),
                "bull_strongest_argument": judge_result.get("bull_strongest_argument", ""),
                "bear_strongest_argument": judge_result.get("bear_strongest_argument", ""),
                "consensus_areas": judge_result.get("consensus_areas", []),
                "judge_notes": judge_result.get("judge_notes", ""),
            },
        }
