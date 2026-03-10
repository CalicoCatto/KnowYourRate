"""Agent A — Creator Profile Analysis (CN Edition).

Combines structured CPM calculation with qualitative LLM assessment.
Uses additive modifier system instead of multiplicative.
"""

import logging

from app.agents.base import BaseAgent
from app.utils.pricing_tables_cn import (
    calculate_base_price_cn,
    calculate_all_modifiers_cn,
    classify_tier_cn,
    calculate_confidence_cn,
    get_cpm_confidence_cn,
    calculate_vf_ratio_modifier,
    NICHE_AVG_ENGAGEMENT_CN,
    NICHE_DISPLAY_NAMES_CN,
)
from app.utils.prompts_cn import CREATOR_PROFILE_PROMPT_CN

logger = logging.getLogger(__name__)


class CreatorProfileCNAgent(BaseAgent):
    """CN edition: analyzes creator data with additive modifier system."""

    name = "creator_profile"
    description = "Computes base pricing from CN CPM tables and evaluates creator quality"

    async def run(self, context: dict) -> dict:
        creator = context.get("creator_data", {})
        platform = creator.get("platform", "bilibili")
        subscriber_count = int(creator.get("subscriber_count", 0))
        avg_views = int(creator.get("avg_views", 0))
        engagement_rate = float(creator.get("engagement_rate", 0))
        niche = creator.get("content_niche", "lifestyle_vlog")
        display_name = creator.get("display_name", "Unknown")
        handle = creator.get("handle", "")
        raw_data = creator.get("raw_data", {})
        monthly_growth = creator.get("monthly_growth_rate")

        # Platform-specific signals
        coin_rate = float(creator.get("coin_rate", 0))
        favorite_rate = float(creator.get("favorite_rate", 0))
        completion_rate = float(creator.get("completion_rate", 0))
        share_rate = float(creator.get("share_rate", 0))
        revisit_rate = float(creator.get("revisit_rate", 0))
        live_viewer_follower_ratio = float(creator.get("live_viewer_follower_ratio", 0))
        audience_city_distribution = creator.get("audience_city_distribution")

        # --- Structured calculations ---
        tier = classify_tier_cn(platform, subscriber_count)
        base_price = calculate_base_price_cn(platform, niche, avg_views)

        total_modifier, modifiers = calculate_all_modifiers_cn(
            engagement_rate=engagement_rate,
            platform=platform,
            niche=niche,
            avg_views=avg_views,
            followers=subscriber_count,
            monthly_growth_rate=monthly_growth,
            audience_city_distribution=audience_city_distribution,
            coin_rate=coin_rate,
            favorite_rate=favorite_rate,
            completion_rate=completion_rate,
            share_rate=share_rate,
            revisit_rate=revisit_rate,
            live_viewer_follower_ratio=live_viewer_follower_ratio,
        )

        adjusted_price = {
            "low": round(base_price["low"] * total_modifier, 2),
            "mid": round(base_price["mid"] * total_modifier, 2),
            "high": round(base_price["high"] * total_modifier, 2),
        }

        vf_ratio, _ = calculate_vf_ratio_modifier(avg_views, subscriber_count, platform)

        modifiers_summary = "; ".join(
            f"{k}: Δ{v['delta']:+.3f} ({v['reason']})" for k, v in modifiers.items()
        )

        has_api_data = bool(raw_data)
        cpm_confidence = get_cpm_confidence_cn(platform, niche)
        confidence = calculate_confidence_cn(
            has_api_data=has_api_data,
            has_engagement=engagement_rate > 0,
            has_city_tier=audience_city_distribution is not None,
            has_growth=monthly_growth is not None,
            has_brand_intel=False,
            cpm_confidence=cpm_confidence,
        )

        # --- LLM qualitative assessment ---
        prompt = self.build_prompt(
            CREATOR_PROFILE_PROMPT_CN,
            platform=platform,
            display_name=display_name,
            handle=handle,
            subscriber_count=subscriber_count,
            avg_views=avg_views,
            engagement_rate=engagement_rate,
            content_niche=niche,
            tier=tier,
            vf_ratio=vf_ratio,
            raw_data=raw_data or "N/A",
            base_price_low=base_price["low"],
            base_price_mid=base_price["mid"],
            base_price_high=base_price["high"],
            adjusted_price_low=adjusted_price["low"],
            adjusted_price_mid=adjusted_price["mid"],
            adjusted_price_high=adjusted_price["high"],
            modifiers_summary=modifiers_summary,
        )

        logger.info("CreatorProfileCNAgent: running qualitative analysis for %s", display_name)
        llm_result = await self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一位资深的国内KOL商业价值评估专家。"
                        "提供定性分析以补充结构化定价数据。"
                        "始终以有效的JSON格式回复。"
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
            "CreatorProfileCNAgent: done. tier=%s, base_mid=¥%.0f, final_mid=¥%.0f",
            tier, base_price["mid"], final_adjusted["mid"],
        )

        # --- Display fields ---
        niche_display = NICHE_DISPLAY_NAMES_CN.get(niche, niche)

        niche_avg = NICHE_AVG_ENGAGEMENT_CN.get(platform, {}).get(niche, 4.0)
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
                "vf_ratio": vf_ratio,
                "top_geo": None,  # CN uses city tiers, not country
                "growth_rate": monthly_growth,
                "growth_trend": growth_trend,
                "channel_age": channel_age,
            },
            "base_price_range": {
                "low": round(base_price["low"], 2),
                "mid": round(base_price["mid"], 2),
                "high": round(base_price["high"], 2),
                "currency": "CNY",
            },
            "applied_modifiers": modifiers,
            "total_modifier": total_modifier,
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
            "cpm_confidence": cpm_confidence,
            "data_quality_flags": _build_data_flags_cn(
                has_api_data, engagement_rate, audience_city_distribution,
                monthly_growth, vf_ratio, platform,
            ),
        }


def _build_data_flags_cn(
    has_api_data: bool,
    engagement_rate: float,
    audience_city_distribution: dict | None,
    monthly_growth: float | None,
    vf_ratio: float,
    platform: str,
) -> list[str]:
    flags = []
    if not has_api_data:
        flags.append("manual_data_entry")
    if engagement_rate <= 0:
        flags.append("engagement_rate_missing")
    if audience_city_distribution is None:
        flags.append("city_tier_data_missing")
    if monthly_growth is None:
        flags.append("growth_data_missing")
    from app.utils.pricing_tables_cn import VF_RATIO_BENCHMARKS
    bench = VF_RATIO_BENCHMARKS.get(platform, {})
    if vf_ratio < bench.get("poor", 0.1):
        flags.append("low_vf_ratio_possible_fake_followers")
    return flags
