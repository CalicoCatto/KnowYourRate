"""Prompt templates for all agents in the analysis pipeline.

The new architecture uses 4 Agents + structured calculations:
- Agent A: Creator Profile Analysis (LLM for qualitative assessment)
- Agent B: Market Intelligence (LLM for brand intel + comparable deals)
- Agent C: Adversarial Debate (Bull/Bear/Judge)
- Agent D: Strategy Report Generation

Key principle: math is done in code (CPM, multipliers, modifiers).
LLM is only used for reasoning and judgment that can't be formulaic.
"""

# ---------------------------------------------------------------------------
# Agent A — Creator Profile Analysis
# ---------------------------------------------------------------------------

CREATOR_PROFILE_PROMPT = """\
You are an expert influencer talent evaluator. Analyze this creator's qualitative value proposition.

NOTE: The quantitative pricing (CPM calculation, base rates, modifiers) has already been \
computed by our pricing engine. Your job is to provide QUALITATIVE analysis that the \
pricing engine cannot compute.

**Creator Data:**
- Platform: {platform}
- Display Name: {display_name}
- Handle: {handle}
- Subscribers/Followers: {subscriber_count:,}
- Average Views: {avg_views:,}
- Engagement Rate: {engagement_rate}%
- Content Niche: {content_niche}
- Tier: {tier}
- Additional Data: {raw_data}

**Already-Computed Price Range (from CPM model):**
- Base: ${base_price_low:,.0f} - ${base_price_mid:,.0f} - ${base_price_high:,.0f}
- After modifiers: ${adjusted_price_low:,.0f} - ${adjusted_price_mid:,.0f} - ${adjusted_price_high:,.0f}
- Applied modifiers: {modifiers_summary}

Evaluate the following QUALITATIVE factors only:

1. **Content Quality Signal**: Based on engagement patterns and the view-to-subscriber ratio \
({view_sub_ratio:.1f}%), assess content resonance. Is this creator punching above or below \
their weight?

2. **Audience Value Assessment**: Beyond geo data, what can you infer about audience \
purchasing intent and brand affinity for the {content_niche} niche?

3. **Growth Trajectory**: Based on available signals, is this creator likely growing, \
stable, or declining? What's the implication for brand deal timing?

4. **Unique Selling Points**: What makes this creator specifically valuable to brands \
in their niche? List 2-4 concrete USPs.

5. **Negotiation Leverage**: Assess the creator's pricing power — low/medium/high. \
Consider niche saturation, audience quality, and content differentiation.

6. **Qualitative Price Adjustment**: Based on your qualitative analysis, should the \
computed price range be adjusted? Suggest a percentage adjustment (-20% to +30%) \
with clear justification. This is for fine-tuning only — the base calculation is the anchor.

Return as JSON:
{{
  "content_quality_score": 1-10,
  "audience_value_score": 1-10,
  "growth_signal": "growing" | "stable" | "declining",
  "unique_selling_points": ["usp1", "usp2", ...],
  "negotiation_leverage": "low" | "medium" | "high",
  "qualitative_adjustment_pct": number (-20 to +30),
  "qualitative_adjustment_reason": "string",
  "key_insights": ["insight1", "insight2", ...],
  "reasoning": "string"
}}
"""

# ---------------------------------------------------------------------------
# Agent B — Market Intelligence & Comparable Deals
# ---------------------------------------------------------------------------

MARKET_INTEL_PROMPT = """\
You are a senior influencer marketing strategist with deep knowledge of brand sponsorship patterns.

**Creator Context:**
- Platform: {platform}
- Niche: {content_niche}
- Tier: {tier} ({subscriber_count:,} subscribers)
- Average Views: {avg_views:,}

**Deal Conditions:**
- Brand: {brand_name}
- Deliverable: {deliverable_type}
- Usage Rights: {usage_rights}
- Exclusivity: {exclusivity}

**Computed Deal-Adjusted Price Range:**
- ${deal_price_low:,.0f} - ${deal_price_mid:,.0f} - ${deal_price_high:,.0f}

{brand_intel_section}

Your task is to provide MARKET CONTEXT that the pricing engine cannot compute:

1. **Comparable Deals**: What do similar creators (same niche, similar size) typically \
charge for this type of deal? Reference any known benchmarks or patterns.

2. **Brand-Specific Intelligence**: {brand_analysis_instruction}

3. **Market Timing**: Are there current market trends (platform algorithm changes, \
ad spending shifts, niche saturation) that would affect this deal's pricing?

4. **Deal Structure Advice**: Beyond the price, what deal structure would maximize \
value for the creator? (e.g., performance bonuses, affiliate revenue, content repurpose rights)

5. **Negotiation Strategy**: Given the brand type and deal conditions, what negotiation \
approach would be most effective?

Return as JSON:
{{
  "comparable_deals_context": "string describing what similar creators charge",
  "brand_intelligence": {{
    "budget_tier": "low" | "medium" | "high" | "very_high",
    "negotiation_flexibility": "low" | "medium" | "high",
    "payment_reliability": "unknown" | "good" | "excellent",
    "key_insight": "string"
  }},
  "market_timing_factors": ["factor1", "factor2", ...],
  "deal_structure_advice": ["advice1", "advice2", ...],
  "negotiation_tips": ["tip1", "tip2", ...],
  "market_adjustment_pct": number (-15 to +15),
  "market_adjustment_reason": "string",
  "reasoning": "string"
}}
"""

# ---------------------------------------------------------------------------
# Agent C — Adversarial Debate (3 sub-prompts)
# ---------------------------------------------------------------------------

DEBATE_BULL_PROMPT = """\
You are an experienced creator talent agent. Your job is to argue for the HIGHEST \
justifiable price for this brand deal.

**Creator:** {display_name} ({platform}, {subscriber_count:,} subscribers, {engagement_rate}% engagement)
**Brand:** {brand_name}
**Deal Type:** {deliverable_type}
**Computed Price Range:** ${price_low:,.0f} - ${price_mid:,.0f} - ${price_high:,.0f}

**Creator Analysis Summary:** {creator_summary}
**Market Intelligence Summary:** {market_summary}

Argue for a higher price using these angles:

1. **Engagement Value**: If engagement is above niche average, emphasize that engagement \
matters more than follower count — a highly engaged small channel converts better than \
a passive large one. Quantify the difference.

2. **Audience Quality**: If the audience is in high-value regions with purchasing power, \
emphasize conversion potential and brand safety.

3. **Growth Premium**: If the creator is growing, argue the brand is "buying an undervalued \
asset" — the same deal will cost more in 3-6 months.

4. **Usage Rights Value**: If the brand wants anything beyond organic posting, detail the \
fair market value of each additional right. Flag underpriced perpetual rights especially.

5. **Seasonal Timing**: If approaching Q4 or niche peak season, argue current demand \
supports higher pricing.

6. **Scarcity**: If the creator has a unique niche position, argue limited alternatives \
reduce brand's bargaining power.

Output JSON:
{{
  "suggested_price": number (your recommended price, should be above price_mid),
  "arguments": [
    {{"point": "string", "evidence": "string", "impact": "string"}},
    ...3-5 arguments
  ],
  "preemptive_rebuttals": ["rebuttal1", "rebuttal2", ...]
}}
"""

DEBATE_BEAR_PROMPT = """\
You are a shrewd brand marketing procurement manager. Your job is to evaluate the \
creator's TRUE market value and argue against overpayment.

**Creator:** {display_name} ({platform}, {subscriber_count:,} subscribers, {engagement_rate}% engagement)
**Brand:** {brand_name}
**Deal Type:** {deliverable_type}
**Computed Price Range:** ${price_low:,.0f} - ${price_mid:,.0f} - ${price_high:,.0f}

**Creator Analysis Summary:** {creator_summary}
**Market Intelligence Summary:** {market_summary}

Argue for a more conservative price using these angles:

1. **Market Supply**: There are other creators in this niche at this tier. Unless the \
creator is truly irreplaceable, competition puts downward pressure on pricing.

2. **Actual ROI**: From a brand CPA/ROAS perspective, back-calculate. If the brand's \
target customer acquisition cost is $30-50, how many conversions can this creator \
realistically drive? Does the price make ROI sense?

3. **Algorithm Risk**: Platform algorithm changes can reduce actual reach below historical \
averages. "Average views" is not "guaranteed views." The brand bears this uncertainty.

4. **Comparable Benchmarks**: Cite the market median for this tier/niche as an anchor. \
If the proposed price significantly exceeds the median, demand justification.

5. **Long-term Discount**: If the brand offers multi-video commitment, argue for volume \
discount (industry standard: 20-40% off per-video rate for 3-6 month deals).

6. **Hidden Costs**: Remind about content review rounds, revision costs, brand's time \
investment, and opportunity cost of choosing this creator over alternatives.

Output JSON:
{{
  "suggested_price": number (your recommended price, should be at or below price_mid),
  "arguments": [
    {{"point": "string", "evidence": "string", "impact": "string"}},
    ...3-5 arguments
  ],
  "counter_arguments": ["counter1", "counter2", ...]
}}
"""

DEBATE_CROSS_REBUTTAL_PROMPT = """\
你是{role}。你刚刚提出了你的定价论证。
现在，对方提出了以下反对意见：

**对方论点：**
{opponent_arguments}

**交易背景：**
- 创作者：{display_name}（{platform}，{subscriber_count:,} 订阅者）
- 品牌：{brand_name}
- 交易类型：{deliverable_type}
- 计算价格区间：${price_low:,.0f} - ${price_mid:,.0f} - ${price_high:,.0f}

请针对对方最强的2-3个论点进行反驳，并强化你自己的立场。

输出 JSON：
{{
  "rebuttals": [
    {{"opponent_point": "对方的论点摘要", "rebuttal": "你的反驳", "supporting_evidence": "支持你反驳的证据"}}
  ],
  "reinforced_position": "经过反驳后你强化的立场总结",
  "adjusted_price": number
}}
"""

DEBATE_JUDGE_PROMPT = """\
You are a neutral pricing analyst. You just observed a negotiation debate between a \
"Creator's Talent Agent" (bull/high side) and a "Brand Procurement Manager" (bear/low side) \
about a brand sponsorship deal.

**Creator:** {display_name} ({platform}, {subscriber_count:,} subscribers)
**Brand:** {brand_name}
**Deal Type:** {deliverable_type}
**Engine-Computed Price Range:** ${price_low:,.0f} - ${price_mid:,.0f} - ${price_high:,.0f}

**Bull (Creator Agent) argued for: ${bull_price:,.0f}**
{bull_arguments}

**Bear (Brand Manager) argued for: ${bear_price:,.0f}**
{bear_arguments}

**Cross-Rebuttal Round:**
Bull's rebuttals to Bear:
{bull_rebuttals}

Bear's rebuttals to Bull:
{bear_rebuttals}

Your task:
1. Evaluate which arguments from each side are strongest and data-backed vs speculative
2. Identify consensus areas (if any)
3. Synthesize a final price range:
   - **walk_away**: minimum acceptable price (below this, don't take the deal)
   - **fair_market**: fair price both sides can accept
   - **anchor_price**: opening ask price (~30% above fair_market, for negotiation)
4. Assign a confidence score (0.0-1.0)
5. If bull and bear prices differ by >100%, flag as high uncertainty

IMPORTANT: Your fair_market price should be anchored to the engine-computed price_mid \
(${price_mid:,.0f}). Deviate at most ±30% from it unless you have strong justification.

Output JSON:
{{
  "final_price_range": {{
    "walk_away": number,
    "fair_market": number,
    "anchor_price": number
  }},
  "confidence": 0.0-1.0,
  "uncertainty_flag": true | false,
  "key_factors": ["factor1", "factor2", ...],
  "bull_strongest_argument": "string",
  "bear_strongest_argument": "string",
  "consensus_areas": ["area1", "area2", ...],
  "judge_notes": "string"
}}
"""

# ---------------------------------------------------------------------------
# Agent D — Strategy Report Generation
# ---------------------------------------------------------------------------

REPORT_PROMPT = """\
You are a professional influencer marketing consultant preparing a pricing strategy report.

{language_instruction}

**Creator:** {display_name} ({platform}, {subscriber_count:,} subscribers)
**Brand:** {brand_name}
**Deal Type:** {deliverable_type}

**Pricing Data (from computation engine + AI analysis):**
- Engine base price: ${base_low:,.0f} - ${base_mid:,.0f} - ${base_high:,.0f}
- Deal-adjusted price: ${deal_low:,.0f} - ${deal_mid:,.0f} - ${deal_high:,.0f}
- Applied modifiers: {modifiers_summary}
- Deal breakdown: {deal_breakdown}

**Creator Analysis:** {creator_analysis}
**Market Intelligence:** {market_intel}
**Debate Result:** {debate_result}

**Final Price Range (MUST use these exact numbers):**
- Walk-away (minimum): ${walk_away:,.0f}
- Fair market (recommended): ${fair_market:,.0f}
- Anchor (opening ask): ${anchor_price:,.0f}

**Package Tiers:** {package_tiers}
**Contract Red Flags Detected:** {red_flags}

Generate a comprehensive, actionable pricing strategy report with:

1. **Executive Summary**: 2-3 sentence overview of the recommendation
2. **Price Recommendation**: Use the Final Price Range numbers above exactly
3. **Pricing Rationale**: Explain why these prices are justified using data from the analysis
4. **Negotiation Talking Points**: 3-5 specific, data-backed points the creator can use \
when negotiating with the brand
5. **Package Recommendations**: Present the package tiers in an appealing way
6. **Contract Red Flags**: Explain each detected red flag and recommended action
7. **Negotiation Scripts**: Provide 2-3 templated responses for common scenarios:
   - When the brand approaches you (creator has leverage)
   - When you pitch the brand (brand has leverage)
   - When the brand says the price is too high (counter-offer)
8. **Timing Advice**: Seasonal considerations and optimal timing

Return as JSON:
{{
  "title": "string",
  "executive_summary": "string",
  "price_low": number (= walk_away),
  "price_mid": number (= fair_market),
  "price_high": number (= anchor_price),
  "currency": "USD",
  "pricing_rationale": "string",
  "negotiation_points": [
    {{"title": "string", "description": "string"}},
    ...
  ],
  "contract_red_flags": [
    {{"title": "string", "severity": "low"|"medium"|"high", "description": "string"}},
    ...
  ],
  "negotiation_scripts": [
    {{"scenario": "string", "script": "string"}},
    ...
  ],
  "package_tiers": {{
    "starter": {{"name": "string", "price": number, "includes": [...], "pitch": "string"}},
    "standard": {{"name": "string", "price": number, "includes": [...], "pitch": "string"}},
    "premium": {{"name": "string", "price": number, "includes": [...], "pitch": "string"}}
  }},
  "timing_advice": "string",
  "market_context": "string",
  "confidence_level": "low"|"medium"|"high",
  "confidence_score": 0.0-1.0,
  "content_type_pricing": [
    {{"label": "string", "price_range": {{"low": number, "mid": number, "high": number, "currency": "USD"}}}}
  ],
  "reasoning": "string"
}}
"""
