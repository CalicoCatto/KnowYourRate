"""Agent B — Market Intelligence & Comparable Deals.

Combines structured deal-condition calculations (code) with LLM-powered
brand intelligence and market context analysis.
"""

import json
import logging

from app.agents.base import BaseAgent
from app.utils.pricing_tables import (
    calculate_deal_adjusted_price,
    generate_package_tiers,
    lookup_brand,
    detect_contract_red_flags,
)
from app.utils.prompts import MARKET_INTEL_PROMPT

logger = logging.getLogger(__name__)


class MarketIntelAgent(BaseAgent):
    """Analyzes deal conditions, brand intelligence, and market context."""

    name = "market_intel"
    description = "Computes deal adjustments and provides market intelligence"

    async def run(self, context: dict) -> dict:
        creator_data = context.get("creator_data", {})
        brand_info = context.get("brand_info", {})
        creator_analysis = context.get("creator_analysis", {})

        platform = creator_data.get("platform", "youtube")
        niche = creator_data.get("content_niche", "lifestyle_vlog")
        subscriber_count = int(creator_data.get("subscriber_count", 0))
        avg_views = int(creator_data.get("avg_views", 0))

        brand_name = brand_info.get("brand_name", "")
        deliverable_type = brand_info.get("deal_type", "dedicated_video")
        usage_rights = brand_info.get("usage_rights", "organic_only")
        exclusivity = brand_info.get("exclusivity", "none")

        # Get the creator-adjusted price range from Agent A
        creator_price = creator_analysis.get("final_price_range", {})
        base_range = {
            "low": creator_price.get("low", 0),
            "mid": creator_price.get("mid", 0),
            "high": creator_price.get("high", 0),
        }

        tier = creator_analysis.get("creator_profile", {}).get("tier", "micro")

        # --- Structured calculations ---
        deal_adjusted, deal_breakdown = calculate_deal_adjusted_price(
            base_range, platform, deliverable_type, usage_rights, exclusivity,
        )

        package_tiers = generate_package_tiers(deal_adjusted["mid"], platform)

        # Brand lookup from known database
        brand_intel = lookup_brand(brand_name) if brand_name else None

        # Contract red flags detection
        red_flags = detect_contract_red_flags(
            usage_rights, exclusivity,
            deal_breakdown["usage_rights_premium"],
            deal_breakdown["exclusivity_premium"],
        )

        # --- LLM for market context & brand intelligence ---
        if brand_intel:
            brand_intel_section = (
                f"**Known Brand Data (from our database):**\n"
                f"- Category: {brand_intel['category']}\n"
                f"- Budget Tier: {brand_intel['budget_tier']}\n"
                f"- Negotiation Flexibility: {brand_intel['negotiation_flexibility']}\n"
                f"- Typical CPM Range: ${brand_intel['typical_cpm_range'][0]}-${brand_intel['typical_cpm_range'][1]}\n"
                f"- Payment Reliability: {brand_intel['payment_reliability']}\n"
                f"- Known Issues: {brand_intel.get('known_issues') or 'None'}\n"
            )
            brand_analysis_instruction = (
                "We have data on this brand. Supplement with any additional insights "
                "about their sponsorship patterns, recent campaigns, or market reputation."
            )
        elif brand_name:
            brand_intel_section = f"**Brand '{brand_name}' is NOT in our database.**"
            brand_analysis_instruction = (
                "Infer the brand's likely category, budget tier, negotiation style, "
                "and sponsorship patterns from your knowledge. Be explicit about what "
                "is inference vs known fact."
            )
        else:
            brand_intel_section = "**No specific brand provided — general market analysis.**"
            brand_analysis_instruction = (
                "Provide general market context for this niche and tier without "
                "brand-specific analysis."
            )

        prompt = self.build_prompt(
            MARKET_INTEL_PROMPT,
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

        logger.info("MarketIntelAgent: running market analysis")
        llm_result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior influencer marketing strategist. "
                        "Provide market intelligence to complement structured pricing data. "
                        "Always respond with valid JSON."
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
            "MarketIntelAgent: done. deal_mid=$%.0f, final_mid=$%.0f",
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
        }
