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

export interface FinalReport {
  title?: string;
  summary?: string;
  price_low?: number;
  price_mid?: number;
  price_high?: number;
  currency?: string;
  content_type_pricing?: ContentTypePricing[];
  negotiation_points?: NegotiationPoint[];
  contract_red_flags?: ContractRedFlag[];
  market_context?: string;
  executive_summary?: string;
  [key: string]: unknown;
}

/* ---- Saved Report ---- */

export interface AgentOutputs {
  market_data: Record<string, unknown> | null;
  creator_analysis: Record<string, unknown> | null;
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
  | "market_data"
  | "creator_profile"
  | "brand_strategy"
  | "debate"
  | "report";

export type AgentStatus = "pending" | "running" | "completed" | "failed";

export interface AgentStep {
  agent: AgentName;
  label: string;
  description: string;
  status: AgentStatus;
}

export type Platform = "youtube" | "tiktok";

export type DealType =
  | "dedicated_video"
  | "integration"
  | "short_form"
  | "story_reel"
  | "podcast_mention";

export const DEAL_TYPE_LABELS: Record<DealType, string> = {
  dedicated_video: "Dedicated Video",
  integration: "Integration / Mention",
  short_form: "Short-Form (Shorts / Reels)",
  story_reel: "Story / Reel",
  podcast_mention: "Podcast Mention",
};

export const NICHE_OPTIONS = [
  "gaming",
  "tech",
  "beauty",
  "fashion",
  "food",
  "travel",
  "fitness",
  "education",
  "entertainment",
  "music",
  "finance",
  "lifestyle",
  "news",
  "sports",
  "other",
] as const;
