/* ------------------------------------------------------------------ */
/*  API Types – mirrors backend Pydantic schemas                      */
/* ------------------------------------------------------------------ */

export interface ProviderInfo {
  id: string;
  display_name: string;
  models: string[];
  docs_url: string;
}

export interface ProviderSetup {
  provider: string;
  api_key: string;
  model?: string | null;
}

export interface ProviderResponse {
  provider: string;
  model: string | null;
  api_key_masked: string;
}

export interface TestResult {
  success: boolean;
  message: string;
}

/* ---- Creator ---- */

export interface CreatorLookupRequest {
  platform: string;
  channel_url: string;
}

export interface CreatorProfile {
  id: string;
  platform: string;
  platform_id: string;
  handle: string;
  display_name: string;
  subscriber_count: number | null;
  avg_views: number | null;
  engagement_rate: number | null;
  content_niche: string | null;
  raw_data: Record<string, unknown> | null;
  fetched_at: string | null;
}

/* ---- Analysis ---- */

export interface AnalysisRequest {
  creator_id?: string | null;
  manual_data?: Record<string, unknown> | null;
  brand_name: string;
  deal_type: string;
  usage_rights?: string;
  exclusivity?: string;
  is_first_brand_deal?: boolean;
  language?: string;
}

export interface AnalysisStatus {
  run_id: string;
  status: string;
  current_agent: string | null;
  progress: number;
}

export interface AnalysisResult {
  run_id: string;
  status: string;
  market_data: Record<string, unknown> | null;
  creator_analysis: Record<string, unknown> | null;
  brand_analysis: Record<string, unknown> | null;
  market_intel: Record<string, unknown> | null;
  debate_result: Record<string, unknown> | null;
  final_report: FinalReport | null;
  started_at: string | null;
  completed_at: string | null;
}

/* ---- Report (final_report structure) ---- */

export interface PriceRange {
  low: number;
  mid: number;
  high: number;
  currency: string;
}

export interface ContentTypePricing {
  content_type: string;
  label: string;
  price_range: PriceRange;
}

export interface NegotiationPoint {
  title: string;
  description: string;
}

export interface ContractRedFlag {
  title: string;
  description: string;
  severity: "low" | "medium" | "high";
}

export interface NegotiationScript {
  scenario: string;
  script: string;
}

export interface PackageTier {
  name: string;
  price: number;
  includes: string[];
  pitch?: string;
  duration?: string;
  savings_vs_individual?: string;
}

export interface FinalReport {
  title?: string;
  summary?: string;
  executive_summary?: string;
  price_low?: number;
  price_mid?: number;
  price_high?: number;
  currency?: string;
  pricing_rationale?: string;
  content_type_pricing?: ContentTypePricing[];
  negotiation_points?: NegotiationPoint[];
  contract_red_flags?: ContractRedFlag[];
  negotiation_scripts?: NegotiationScript[];
  package_tiers?: Record<string, PackageTier>;
  timing_advice?: string;
  market_context?: string;
  confidence_level?: string;
  confidence_score?: number;
  [key: string]: unknown;
}

/* ---- Saved Report ---- */

export interface AgentOutputs {
  creator_analysis: Record<string, unknown> | null;
  market_intel: Record<string, unknown> | null;
  market_data: Record<string, unknown> | null;
  brand_analysis: Record<string, unknown> | null;
  debate_result: Record<string, unknown> | null;
}

export interface ReportResponse {
  id: string;
  analysis_run_id: string;
  title: string;
  summary: string;
  price_low: number | null;
  price_mid: number | null;
  price_high: number | null;
  currency: string;
  full_report: FinalReport | null;
  agent_outputs: AgentOutputs | null;
  created_at: string;
}

export interface ReportList {
  id: string;
  title: string;
  summary: string;
  price_low: number | null;
  price_mid: number | null;
  price_high: number | null;
  currency: string;
  created_at: string;
}

/* ---- SSE Event ---- */

export interface SSEEvent {
  agent?: string;
  status?: string;
  done?: boolean;
  error?: string;
}

/* ---- UI-only types ---- */

export type AgentName =
  | "creator_profile"
  | "market_intel"
  | "debate"
  | "report";

export type AgentStatus = "pending" | "running" | "completed" | "failed" | "skipped";

export interface AgentStep {
  agent: AgentName;
  label: string;
  description: string;
  status: AgentStatus;
}

/* ---- Edition detection ---- */

export const EDITION = (import.meta.env.VITE_EDITION as string) || "international";
export const isCN = EDITION === "cn";

/* ---- Platforms ---- */

export type InternationalPlatform = "youtube" | "tiktok";
export type CNPlatform = "bilibili" | "douyin" | "kuaishou";
export type Platform = InternationalPlatform | CNPlatform;

/* Deal types aligned with backend pricing tables */
export type DealType =
  | "dedicated_video"
  | "integrated_mention"
  | "pre_roll_mention"
  | "shorts"
  | "community_post"
  | "livestream_mention"
  /* CN-specific deal types */
  | "bilibili_custom_video"
  | "bilibili_dynamic"
  | "bilibili_image_text"
  | "douyin_video"
  | "douyin_image"
  | "kuaishou_video"
  | "livestream_slot"
  | "livestream_clip";

export const DEAL_TYPE_LABELS: Record<DealType, string> = {
  dedicated_video: "Dedicated Video",
  integrated_mention: "Integration / Mention",
  pre_roll_mention: "Pre-roll Mention",
  shorts: "Shorts / Reels",
  community_post: "Community Post",
  livestream_mention: "Livestream Mention",
  bilibili_custom_video: "B站定制视频",
  bilibili_dynamic: "B站动态",
  bilibili_image_text: "B站图文",
  douyin_video: "抖音视频",
  douyin_image: "抖音图文",
  kuaishou_video: "快手视频",
  livestream_slot: "直播坑位",
  livestream_clip: "直播切片",
};

export const DEAL_TYPE_LABELS_INTL: Record<string, string> = {
  dedicated_video: "Dedicated Video",
  integrated_mention: "Integration / Mention",
  pre_roll_mention: "Pre-roll Mention",
  shorts: "Shorts / Reels",
  community_post: "Community Post",
  livestream_mention: "Livestream Mention",
};

export const DEAL_TYPE_LABELS_CN: Record<string, string> = {
  bilibili_custom_video: "B站定制视频",
  bilibili_dynamic: "B站动态",
  bilibili_image_text: "B站图文",
  douyin_video: "抖音视频",
  douyin_image: "抖音图文",
  kuaishou_video: "快手视频",
  livestream_slot: "直播坑位",
  livestream_clip: "直播切片",
};

/** Deal types filtered by CN platform */
export const DEAL_TYPES_BY_PLATFORM: Record<string, Record<string, string>> = {
  bilibili: {
    bilibili_custom_video: "B站定制视频",
    bilibili_dynamic: "B站动态",
    bilibili_image_text: "B站图文",
    livestream_slot: "直播坑位",
    livestream_clip: "直播切片",
  },
  douyin: {
    douyin_video: "抖音视频",
    douyin_image: "抖音图文",
    livestream_slot: "直播坑位",
    livestream_clip: "直播切片",
  },
  kuaishou: {
    kuaishou_video: "快手视频",
    livestream_slot: "直播坑位",
    livestream_clip: "直播切片",
  },
};

export type UsageRights =
  | "organic_only"
  | "brand_repost_30d"
  | "brand_repost_perpetual"
  | "whitelisting_30d"
  | "whitelisting_90d"
  | "whitelisting_perpetual"
  | "website_use"
  | "paid_ads"
  | "perpetual_all_media"
  /* CN-specific */
  | "feed_ads_30d"
  | "feed_ads_90d"
  | "livestream_loop"
  | "ecommerce_detail";

export const USAGE_RIGHTS_LABELS: Record<UsageRights, string> = {
  organic_only: "Organic Only (creator's channel)",
  brand_repost_30d: "Brand Repost (30 days)",
  brand_repost_perpetual: "Brand Repost (perpetual)",
  whitelisting_30d: "Whitelisting / Spark Ads (30 days)",
  whitelisting_90d: "Whitelisting / Spark Ads (90 days)",
  whitelisting_perpetual: "Whitelisting (perpetual)",
  website_use: "Brand Website Use",
  paid_ads: "Paid Ad Creative",
  perpetual_all_media: "All Media (perpetual)",
  feed_ads_30d: "信息流投放 (30天)",
  feed_ads_90d: "信息流投放 (90天)",
  livestream_loop: "直播间循环播放",
  ecommerce_detail: "电商详情页使用",
};

export const USAGE_RIGHTS_LABELS_INTL: Record<string, string> = {
  organic_only: "Organic Only (creator's channel)",
  brand_repost_30d: "Brand Repost (30 days)",
  brand_repost_perpetual: "Brand Repost (perpetual)",
  whitelisting_30d: "Whitelisting / Spark Ads (30 days)",
  whitelisting_90d: "Whitelisting / Spark Ads (90 days)",
  whitelisting_perpetual: "Whitelisting (perpetual)",
  website_use: "Brand Website Use",
  paid_ads: "Paid Ad Creative",
  perpetual_all_media: "All Media (perpetual)",
};

export const USAGE_RIGHTS_LABELS_CN: Record<string, string> = {
  organic_only: "仅创作者频道发布",
  brand_repost_30d: "品牌转发 (30天)",
  brand_repost_perpetual: "品牌转发 (永久)",
  feed_ads_30d: "信息流投放 (30天)",
  feed_ads_90d: "信息流投放 (90天)",
  livestream_loop: "直播间循环播放",
  ecommerce_detail: "电商详情页使用",
  perpetual_all_media: "全媒体永久使用",
};

export type Exclusivity =
  | "none"
  | "category_30d"
  | "category_90d"
  | "category_6m"
  | "category_12m"
  | "full_exclusivity_30d"
  | "full_exclusivity_90d";

export const EXCLUSIVITY_LABELS: Record<Exclusivity, string> = {
  none: "None",
  category_30d: "Category (30 days)",
  category_90d: "Category (90 days)",
  category_6m: "Category (6 months)",
  category_12m: "Category (12 months)",
  full_exclusivity_30d: "Full Exclusivity (30 days)",
  full_exclusivity_90d: "Full Exclusivity (90 days)",
};

export const EXCLUSIVITY_LABELS_CN: Record<string, string> = {
  none: "无排他",
  category_30d: "品类排他 (30天)",
  category_90d: "品类排他 (90天)",
  category_6m: "品类排他 (6个月)",
  category_12m: "品类排他 (12个月)",
  full_exclusivity_30d: "全品类排他 (30天)",
  full_exclusivity_90d: "全品类排他 (90天)",
};

/* Niche options aligned with backend CPM tables */
export const NICHE_OPTIONS = [
  "finance_investing",
  "technology",
  "business_saas",
  "health_fitness",
  "beauty_skincare",
  "food_cooking",
  "gaming",
  "lifestyle_vlog",
  "education",
  "entertainment_comedy",
  "travel",
  "parenting_family",
  "diy_crafts",
  "automotive",
  "pets_animals",
] as const;

export const NICHE_OPTIONS_CN = [
  "finance_investing",
  "technology",
  "business_saas",
  "health_fitness",
  "beauty_skincare",
  "food_cooking",
  "gaming",
  "lifestyle_vlog",
  "education",
  "entertainment_comedy",
  "travel",
  "parenting_family",
  "diy_crafts",
  "automotive",
  "pets_animals",
  "acg_anime",
  "digital_3c",
  "home_furnishing",
] as const;

export const NICHE_LABELS: Record<string, string> = {
  finance_investing: "Finance / Investing",
  technology: "Technology",
  business_saas: "Business / SaaS",
  health_fitness: "Health / Fitness",
  beauty_skincare: "Beauty / Skincare",
  food_cooking: "Food / Cooking",
  gaming: "Gaming",
  lifestyle_vlog: "Lifestyle / Vlog",
  education: "Education",
  entertainment_comedy: "Entertainment / Comedy",
  travel: "Travel",
  parenting_family: "Parenting / Family",
  diy_crafts: "DIY / Crafts",
  automotive: "Automotive",
  pets_animals: "Pets / Animals",
};

export const NICHE_LABELS_CN: Record<string, string> = {
  finance_investing: "财经/理财",
  technology: "科技",
  business_saas: "商业/企服",
  health_fitness: "健康/健身",
  beauty_skincare: "美妆/护肤",
  food_cooking: "美食/烹饪",
  gaming: "游戏",
  lifestyle_vlog: "生活/Vlog",
  education: "教育/知识",
  entertainment_comedy: "娱乐/搞笑",
  travel: "旅游",
  parenting_family: "母婴/家庭",
  diy_crafts: "手工/DIY",
  automotive: "汽车",
  pets_animals: "宠物",
  acg_anime: "ACG/动漫",
  digital_3c: "数码3C",
  home_furnishing: "家居/家装",
};

/* ---- CN-specific types ---- */

export type CityTier = "tier_1" | "new_tier_1" | "tier_2" | "tier_3" | "other";

export const CITY_TIER_LABELS: Record<CityTier, string> = {
  tier_1: "一线城市",
  new_tier_1: "新一线城市",
  tier_2: "二线城市",
  tier_3: "三线及以下",
  other: "未知",
};
