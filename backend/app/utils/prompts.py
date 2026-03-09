"""Prompt templates for all agents in the analysis pipeline.

Each template uses {variable} placeholders that are filled in by the agents
at runtime via str.format().
"""

MARKET_DATA_PROMPT = """\
You are an expert influencer marketing analyst specializing in pricing benchmarks.

Analyze the current market rates for influencer sponsorships with the following context:

**Creator Profile:**
- Platform: {platform}
- Subscriber/Follower Count: {subscriber_count}
- Average Views per Video: {avg_views}
- Engagement Rate: {engagement_rate}%
- Content Niche: {content_niche}

**Deal Type:** {deal_type}

Provide a detailed market analysis including:
1. **Tier Classification**: What tier is this creator (nano, micro, mid-tier, macro, mega)?
2. **Market Rate Ranges**: What are typical rates for this tier and niche for the specified deal type?
3. **Niche Premium/Discount**: Does this niche command higher or lower rates than average?
4. **Platform-Specific Factors**: Any platform-specific pricing considerations.
5. **Current Market Trends**: Relevant trends affecting pricing in this space.

Return your analysis as a JSON object with keys:
- tier: string
- rate_low: number (USD)
- rate_mid: number (USD)
- rate_high: number (USD)
- niche_multiplier: number (1.0 = average)
- market_trends: list of strings
- reasoning: string
"""

CREATOR_PROFILE_PROMPT = """\
You are an expert talent evaluator for influencer marketing.

Analyze this creator's market position and value proposition:

**Creator Data:**
- Platform: {platform}
- Display Name: {display_name}
- Handle: {handle}
- Subscribers/Followers: {subscriber_count}
- Average Views: {avg_views}
- Engagement Rate: {engagement_rate}%
- Content Niche: {content_niche}
- Additional Data: {raw_data}

Evaluate:
1. **Content Quality Signal**: Based on engagement rate and view-to-subscriber ratio, how strong is their content?
2. **Audience Value**: How valuable is this creator's audience for brand partnerships?
3. **Growth Trajectory**: Any signals about whether they're growing, stable, or declining?
4. **Unique Selling Points**: What makes this creator valuable to brands?
5. **Negotiation Leverage**: How much pricing power does this creator likely have?

Return your analysis as a JSON object with keys:
- content_quality_score: number (1-10)
- audience_value_score: number (1-10)
- growth_signal: string (growing/stable/declining)
- unique_selling_points: list of strings
- negotiation_leverage: string (low/medium/high)
- recommended_premium: number (percentage above/below market average)
- reasoning: string
"""

BRAND_STRATEGY_PROMPT = """\
You are a brand marketing strategist with deep knowledge of influencer marketing budgets.

Analyze the likely negotiation approach for this brand deal:

**Brand:** {brand_name}
**Deal Type:** {deal_type}
**Creator Tier:** {creator_tier}
**Creator Niche:** {content_niche}

Consider:
1. **Brand Category**: What category does this brand likely fall into? What's their typical marketing budget?
2. **Budget Expectations**: What would this brand typically allocate for influencer marketing?
3. **Negotiation Patterns**: How do brands in this category typically negotiate?
4. **Contract Terms**: What terms/clauses should the creator expect and watch out for?
5. **Value Proposition**: What does the brand likely value most from this partnership?

Return your analysis as a JSON object with keys:
- brand_category: string
- estimated_budget_range: object with low and high (USD)
- negotiation_style: string (aggressive/moderate/flexible)
- common_contract_traps: list of strings
- value_priorities: list of strings
- recommended_approach: string
- reasoning: string
"""

DEBATE_PROMPT = """\
You are simulating a negotiation between two expert personas to find the optimal pricing sweet spot.

**Context:**
- Creator: {display_name} ({platform}, {subscriber_count} subscribers, {engagement_rate}% engagement)
- Brand: {brand_name}
- Deal Type: {deal_type}
- Market Rate Range: ${rate_low} - ${rate_high} (mid: ${rate_mid})

**Market Analysis Summary:** {market_summary}
**Creator Analysis Summary:** {creator_summary}
**Brand Analysis Summary:** {brand_summary}

Now simulate a structured negotiation:

**PERSONA 1 - Brand Procurement Manager:**
Argue for the lowest reasonable rate. Consider brand ROI, market comparables, budget constraints.

**PERSONA 2 - Creator's Talent Agent:**
Argue for the highest justifiable rate. Consider creator's unique value, audience quality, content quality.

After both sides present their arguments, find the **pricing sweet spot** that both sides could accept.

Return your analysis as a JSON object with keys:
- brand_argument: object with proposed_rate (number), key_points (list of strings)
- creator_argument: object with proposed_rate (number), key_points (list of strings)
- sweet_spot: object with rate (number), reasoning (string)
- contract_red_flags: list of strings (things the creator should watch out for)
- negotiation_tips: list of strings
"""

REPORT_PROMPT = """\
You are a professional influencer marketing consultant preparing a pricing strategy report.

{language_instruction}

**Creator:** {display_name} ({platform})
**Brand:** {brand_name}
**Deal Type:** {deal_type}

**Analysis Data:**
- Market Data: {market_data}
- Creator Analysis: {creator_analysis}
- Brand Strategy: {brand_analysis}
- Negotiation Debate: {debate_result}

Generate a comprehensive pricing strategy report with:

1. **Executive Summary**: Brief overview of the recommendation
2. **Recommended Price Range**:
   - Low (minimum acceptable): justified rate
   - Mid (target rate): optimal rate to aim for
   - High (aspirational): maximum justifiable rate
3. **Negotiation Strategy**: Step-by-step approach for the creator
4. **Key Talking Points**: What to emphasize when negotiating
5. **Contract Checklist**: Terms to negotiate, red flags to avoid
6. **Market Context**: How this rate compares to the market

Return as a JSON object with keys:
- title: string
- summary: string
- price_low: number
- price_mid: number
- price_high: number
- currency: string (default "USD")
- negotiation_strategy: list of strings (ordered steps)
- talking_points: list of strings
- contract_checklist: list of objects with item (string) and priority (high/medium/low)
- market_context: string
- confidence_level: string (low/medium/high)
- reasoning: string
"""
