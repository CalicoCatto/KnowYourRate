"""Agent A — Creator Profile Analysis.

Combines structured CPM calculation (code) with qualitative LLM assessment.
This is the foundation of the pricing system.
"""

import logging

from app.agents.base import BaseAgent
from app.utils.pricing_tables import (
    calculate_base_price,
    apply_all_modifiers,
    classify_tier,
    calculate_confidence,
    NICHE_AVG_ENGAGEMENT,
    NICHE_DISPLAY_NAMES,
)
from app.utils.prompts import CREATOR_PROFILE_PROMPT

logger = logging.getLogger(__name__)


class CreatorProfileAgent(BaseAgent):
    """Analyzes creator data: structured pricing + qualitative LLM assessment."""

    name = "creator_profile"
    description = "Computes base pricing from CPM tables and evaluates creator quality"

    async def run(self, context: dict) -> dict:
        creator = context.get("creator_data", {})
        platform = creator.get("platform", "youtube")
        subscriber_count = int(creator.get("subscriber_count", 0))
        avg_views = int(creator.get("avg_views", 0))
        engagement_rate = float(creator.get("engagement_rate", 0))
        niche = creator.get("content_niche", "lifestyle_vlog")
        top_geo = creator.get("top_audience_country")
        monthly_growth = creator.get("monthly_growth_rate")
        display_name = creator.get("display_name", "Unknown")
        handle = creator.get("handle", "")
        raw_data = creator.get("raw_data", {})
        avg_watch_time_pct = creator.get("avg_watch_time_pct")
        like_ratio = creator.get("like_ratio")

        # --- Structured calculations (no LLM needed) ---
        tier = classify_tier(platform, subscriber_count)
        base_price = calculate_base_price(platform, niche, avg_views)
        adjusted_price, modifiers = apply_all_modifiers(
            base_price, engagement_rate, platform, niche, top_geo, monthly_growth,
            avg_watch_time_pct=avg_watch_time_pct, like_ratio=like_ratio,
        )

        view_sub_ratio = (avg_views / subscriber_count * 100) if subscriber_count > 0 else 0
        modifiers_summary = "; ".join(
            f"{k}: {v['value']}x ({v['reason']})" for k, v in modifiers.items()
        )

        has_api_data = bool(raw_data)
        confidence = calculate_confidence(
            has_api_data=has_api_data,
            has_engagement=engagement_rate > 0,
            has_geo=top_geo is not None,
            has_growth=monthly_growth is not None,
            has_brand_intel=False,
        )

        # --- LLM qualitative assessment ---
        prompt = self.build_prompt(
            CREATOR_PROFILE_PROMPT,
            platform=platform,
            display_name=display_name,
            handle=handle,
            subscriber_count=subscriber_count,
            avg_views=avg_views,
            engagement_rate=engagement_rate,
            content_niche=niche,
            tier=tier,
            raw_data=raw_data or "N/A",
            base_price_low=base_price["low"],
            base_price_mid=base_price["mid"],
            base_price_high=base_price["high"],
            adjusted_price_low=adjusted_price["low"],
            adjusted_price_mid=adjusted_price["mid"],
            adjusted_price_high=adjusted_price["high"],
            modifiers_summary=modifiers_summary,
            view_sub_ratio=view_sub_ratio,
        )

        logger.info("CreatorProfileAgent: running qualitative analysis for %s", display_name)
        llm_result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert influencer talent evaluator. "
                        "Provide qualitative analysis to complement the structured pricing data. "
                        "Always respond with valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        # Apply qualitative adjustment (clamped to -20% to +30%)
        qual_adj_pct = llm_result.get("qualitative_adjustment_pct", 0)
        if not isinstance(qual_adj_pct, (int, float)):
            qual_adj_pct = 0
        qual_adj_pct = max(-20, min(30, qual_adj_pct))
        qual_multiplier = 1 + qual_adj_pct / 100

        final_adjusted = {
            "low": round(adjusted_price["low"] * qual_multiplier, 2),
            "mid": round(adjusted_price["mid"] * qual_multiplier, 2),
            "high": round(adjusted_price["high"] * qual_multiplier, 2),
        }

        logger.info(
            "CreatorProfileAgent: done. tier=%s, base_mid=$%.0f, final_mid=$%.0f",
            tier, base_price["mid"], final_adjusted["mid"],
        )

        # --- Compute display fields ---
        niche_display = NICHE_DISPLAY_NAMES.get(niche, niche)

        niche_avg = NICHE_AVG_ENGAGEMENT.get(platform, {}).get(niche, 3.5)
        eng_vs_avg = ((engagement_rate / niche_avg) - 1) * 100 if niche_avg > 0 else 0
        engagement_vs_niche_avg = f"+{eng_vs_avg:.0f}%" if eng_vs_avg >= 0 else f"{eng_vs_avg:.0f}%"

        if monthly_growth is not None:
            if monthly_growth > 10:
                growth_trend = f"快速增长期（月增长率 {monthly_growth:.1f}%）"
            elif monthly_growth > 3:
                growth_trend = f"上升期（月增长率 {monthly_growth:.1f}%）"
            elif monthly_growth >= 0:
                growth_trend = f"稳定期（月增长率 {monthly_growth:.1f}%）"
            else:
                growth_trend = f"下降期（月增长率 {monthly_growth:.1f}%）"
        else:
            growth_trend = None

        channel_age_months = creator.get("channel_age_months")
        channel_age = f"{channel_age_months}个月" if channel_age_months else None

        return {
            "creator_profile": {
                "platform": platform,
                "tier": tier,
                "niche": niche,
                "niche_display": niche_display,
                "display_name": display_name,
                "handle": handle,
                "subscribers": subscriber_count,
                "avg_views": avg_views,
                "engagement_rate": engagement_rate,
                "engagement_vs_niche_avg": engagement_vs_niche_avg,
                "view_sub_ratio": round(view_sub_ratio, 1),
                "top_geo": top_geo,
                "growth_rate": monthly_growth,
                "growth_trend": growth_trend,
                "channel_age": channel_age,
            },
            "base_price_range": {
                "low": round(base_price["low"], 2),
                "mid": round(base_price["mid"], 2),
                "high": round(base_price["high"], 2),
                "currency": "USD",
            },
            "applied_modifiers": modifiers,
            "adjusted_price_range": {
                "low": round(adjusted_price["low"], 2),
                "mid": round(adjusted_price["mid"], 2),
                "high": round(adjusted_price["high"], 2),
            },
            "qualitative_adjustment": {
                "percentage": qual_adj_pct,
                "reason": llm_result.get("qualitative_adjustment_reason", ""),
            },
            "final_price_range": final_adjusted,
            "llm_analysis": {
                "content_quality_score": llm_result.get("content_quality_score"),
                "audience_value_score": llm_result.get("audience_value_score"),
                "growth_signal": llm_result.get("growth_signal"),
                "unique_selling_points": llm_result.get("unique_selling_points", []),
                "negotiation_leverage": llm_result.get("negotiation_leverage"),
                "key_insights": llm_result.get("key_insights", []),
            },
            "confidence_score": confidence,
            "data_quality_flags": _build_data_flags(has_api_data, engagement_rate, top_geo, monthly_growth),
        }


def _build_data_flags(
    has_api_data: bool,
    engagement_rate: float,
    top_geo: str | None,
    monthly_growth: float | None,
) -> list[str]:
    flags = []
    if not has_api_data:
        flags.append("manual_data_entry")
    if engagement_rate <= 0:
        flags.append("engagement_rate_missing")
    if top_geo is None:
        flags.append("geo_data_missing")
    if monthly_growth is None:
        flags.append("growth_data_missing")
    return flags
