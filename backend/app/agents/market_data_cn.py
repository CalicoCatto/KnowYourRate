"""Agent B — Market Intelligence & Comparable Deals (CN Edition).

Combines structured deal-condition calculations with LLM-powered
brand intelligence and market context for Chinese platforms.
"""

import json
import logging

from app.agents.base import BaseAgent
from app.utils.pricing_tables_cn import (
    calculate_deal_adjusted_price_cn,
    generate_package_tiers_cn,
    lookup_brand_cn,
    detect_contract_red_flags_cn,
    calculate_platform_adjusted_price,
)
from app.utils.prompts_cn import MARKET_INTEL_PROMPT_CN

logger = logging.getLogger(__name__)


class MarketIntelCNAgent(BaseAgent):
    """CN edition: analyzes deal conditions, brand intelligence, and market context."""

    name = "market_intel"
    description = "Computes CN deal adjustments and provides market intelligence"

    async def run(self, context: dict) -> dict:
        creator_data = context.get("creator_data", {})
        brand_info = context.get("brand_info", {})
        creator_analysis = context.get("creator_analysis", {})

        platform = creator_data.get("platform", "bilibili")
        niche = creator_data.get("content_niche", "lifestyle_vlog")
        subscriber_count = int(creator_data.get("subscriber_count", 0))
        avg_views = int(creator_data.get("avg_views", 0))

        brand_name = brand_info.get("brand_name", "")
        deliverable_type = brand_info.get("deal_type", "dedicated_video")
        usage_rights = brand_info.get("usage_rights", "organic_only")
        exclusivity = brand_info.get("exclusivity", "none")
        has_livestream = brand_info.get("has_livestream", False)

        # Get creator-adjusted price from Agent A
        creator_price = creator_analysis.get("final_price_range", {})
        base_range = {
            "low": creator_price.get("low", 0),
            "mid": creator_price.get("mid", 0),
            "high": creator_price.get("high", 0),
        }

        tier = creator_analysis.get("creator_profile", {}).get("tier", "中腰部UP主")

        # --- Structured calculations ---
        deal_adjusted, deal_breakdown = calculate_deal_adjusted_price_cn(
            base_range, platform, deliverable_type, usage_rights, exclusivity,
        )

        package_tiers = generate_package_tiers_cn(deal_adjusted["mid"], platform)

        # Brand lookup
        brand_intel = lookup_brand_cn(brand_name) if brand_name else None

        # Contract red flags
        red_flags = detect_contract_red_flags_cn(
            usage_rights, exclusivity,
            deal_breakdown["usage_rights_premium"],
            deal_breakdown["exclusivity_premium"],
            has_livestream=has_livestream,
        )

        # Platform official system prices
        platform_official = calculate_platform_adjusted_price(
            deal_adjusted["mid"], platform, through_official=True,
        )
        platform_private = calculate_platform_adjusted_price(
            deal_adjusted["mid"], platform, through_official=False,
        )

        # --- LLM for market context ---
        if brand_intel:
            brand_intel_section = (
                f"**已知品牌数据（来自数据库）：**\n"
                f"- 品类：{brand_intel.get('category', 'N/A')}\n"
                f"- 预算层级：{brand_intel.get('budget_tier', 'N/A')}\n"
                f"- 谈判灵活度：{brand_intel.get('negotiation_flexibility', 'N/A')}\n"
                f"- 典型CPM范围：¥{brand_intel.get('typical_cpm_cny', [0, 0])[0]}-¥{brand_intel.get('typical_cpm_cny', [0, 0])[1]}\n"
                f"- 付款可靠性：{brand_intel.get('payment_reliability', 'N/A')}\n"
                f"- 已知问题：{brand_intel.get('known_issues', '无')}\n"
            )
            brand_analysis_instruction = (
                "我们有该品牌的数据。请补充关于其赞助模式、近期活动或市场声誉的额外洞察。"
            )
        elif brand_name:
            brand_intel_section = f"**品牌 '{brand_name}' 不在我们的数据库中。**"
            brand_analysis_instruction = (
                "请根据你的知识推断该品牌可能的品类、预算层级、谈判风格和赞助模式。"
                "明确区分推断和已知事实。"
            )
        else:
            brand_intel_section = "**未提供具体品牌 — 进行一般市场分析。**"
            brand_analysis_instruction = (
                "请提供该垂类和层级的一般市场背景，不进行品牌特定分析。"
            )

        prompt = self.build_prompt(
            MARKET_INTEL_PROMPT_CN,
            platform=platform,
            content_niche=niche,
            tier=tier,
            subscriber_count=subscriber_count,
            avg_views=avg_views,
            brand_name=brand_name or "N/A",
            deliverable_type=deliverable_type,
            usage_rights=usage_rights,
            exclusivity=exclusivity,
            deal_price_low=deal_adjusted["low"],
            deal_price_mid=deal_adjusted["mid"],
            deal_price_high=deal_adjusted["high"],
            brand_intel_section=brand_intel_section,
            brand_analysis_instruction=brand_analysis_instruction,
        )

        logger.info("MarketIntelCNAgent: running market analysis")
        llm_result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一位资深的国内KOL营销策略师。"
                        "提供市场情报以补充结构化定价数据。"
                        "始终以有效的JSON格式回复。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        # Apply market adjustment (clamped to ±15%)
        market_adj_pct = llm_result.get("market_adjustment_pct", 0)
        if not isinstance(market_adj_pct, (int, float)):
            market_adj_pct = 0
        market_adj_pct = max(-15, min(15, market_adj_pct))
        market_multiplier = 1 + market_adj_pct / 100

        final_deal_price = {
            "low": round(deal_adjusted["low"] * market_multiplier, 2),
            "mid": round(deal_adjusted["mid"] * market_multiplier, 2),
            "high": round(deal_adjusted["high"] * market_multiplier, 2),
        }

        logger.info(
            "MarketIntelCNAgent: done. deal_mid=¥%.0f, final_mid=¥%.0f",
            deal_adjusted["mid"], final_deal_price["mid"],
        )

        return {
            "deal_adjusted_price_range": deal_adjusted,
            "deal_breakdown": deal_breakdown,
            "market_adjusted_price_range": final_deal_price,
            "market_adjustment": {
                "percentage": market_adj_pct,
                "reason": llm_result.get("market_adjustment_reason", ""),
            },
            "brand_intelligence": {
                "brand_name": brand_name,
                "from_database": brand_intel is not None,
                "database_info": brand_intel,
                "llm_analysis": llm_result.get("brand_intelligence", {}),
            },
            "comparable_deals_context": llm_result.get("comparable_deals_context", ""),
            "market_timing_factors": llm_result.get("market_timing_factors", []),
            "deal_structure_advice": llm_result.get("deal_structure_advice", []),
            "negotiation_tips": llm_result.get("negotiation_tips", []),
            "package_tiers": package_tiers,
            "contract_red_flags": red_flags,
            "platform_pricing": {
                "official": platform_official,
                "private": platform_private,
            },
        }
