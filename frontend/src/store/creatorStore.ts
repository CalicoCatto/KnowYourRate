import { create } from "zustand";
import type { Platform, CreatorProfile, DealType, UsageRights, Exclusivity, CityTier } from "@/types";

const CN_MANUAL_PLATFORMS = ["tiktok", "douyin", "kuaishou"];

const DEFAULT_DEAL_TYPE: Record<string, DealType> = {
  youtube: "dedicated_video",
  tiktok: "dedicated_video",
  bilibili: "bilibili_custom_video",
  douyin: "douyin_video",
  kuaishou: "kuaishou_video",
};

interface CreatorState {
  platform: Platform | null;
  channelUrl: string;
  profile: CreatorProfile | null;
  fetchError: string | null;
  useManual: boolean;
  manualHandle: string;
  manualName: string;
  manualFollowers: string;
  manualAvgViews: string;
  manualEngagement: string;
  manualNiche: string;
  brandName: string;
  dealType: DealType;
  usageRights: UsageRights;
  exclusivity: Exclusivity;
  isFirstBrandDeal: boolean;
  /* CN-specific fields */
  manualCoinRate: string;
  manualFavoriteRate: string;
  manualCompletionRate: string;
  manualShareRate: string;
  manualRevisitRate: string;
  manualCityTier: CityTier;
  manualMcnStatus: string;
  hasLivestream: boolean;
  numPlatforms: number;

  setPlatform: (p: Platform | null) => void;
  setChannelUrl: (v: string) => void;
  setProfile: (p: CreatorProfile | null) => void;
  setFetchError: (e: string | null) => void;
  setUseManual: (v: boolean) => void;
  setManualHandle: (v: string) => void;
  setManualName: (v: string) => void;
  setManualFollowers: (v: string) => void;
  setManualAvgViews: (v: string) => void;
  setManualEngagement: (v: string) => void;
  setManualNiche: (v: string) => void;
  setBrandName: (v: string) => void;
  setDealType: (v: DealType) => void;
  setUsageRights: (v: UsageRights) => void;
  setExclusivity: (v: Exclusivity) => void;
  setIsFirstBrandDeal: (v: boolean) => void;
  setManualCoinRate: (v: string) => void;
  setManualFavoriteRate: (v: string) => void;
  setManualCompletionRate: (v: string) => void;
  setManualShareRate: (v: string) => void;
  setManualRevisitRate: (v: string) => void;
  setManualCityTier: (v: CityTier) => void;
  setManualMcnStatus: (v: string) => void;
  setHasLivestream: (v: boolean) => void;
  setNumPlatforms: (v: number) => void;
  resetPlatform: (p: Platform) => void;
}

export const useCreatorStore = create<CreatorState>()((set) => ({
  platform: null,
  channelUrl: "",
  profile: null,
  fetchError: null,
  useManual: false,
  manualHandle: "",
  manualName: "",
  manualFollowers: "",
  manualAvgViews: "",
  manualEngagement: "",
  manualNiche: "",
  brandName: "",
  dealType: "dedicated_video",
  usageRights: "organic_only",
  exclusivity: "none",
  isFirstBrandDeal: false,
  manualCoinRate: "",
  manualFavoriteRate: "",
  manualCompletionRate: "",
  manualShareRate: "",
  manualRevisitRate: "",
  manualCityTier: "other",
  manualMcnStatus: "none",
  hasLivestream: false,
  numPlatforms: 1,

  setPlatform: (platform) => set({ platform }),
  setChannelUrl: (channelUrl) => set({ channelUrl }),
  setProfile: (profile) => set({ profile }),
  setFetchError: (fetchError) => set({ fetchError }),
  setUseManual: (useManual) => set({ useManual }),
  setManualHandle: (manualHandle) => set({ manualHandle }),
  setManualName: (manualName) => set({ manualName }),
  setManualFollowers: (manualFollowers) => set({ manualFollowers }),
  setManualAvgViews: (manualAvgViews) => set({ manualAvgViews }),
  setManualEngagement: (manualEngagement) => set({ manualEngagement }),
  setManualNiche: (manualNiche) => set({ manualNiche }),
  setBrandName: (brandName) => set({ brandName }),
  setDealType: (dealType) => set({ dealType }),
  setUsageRights: (usageRights) => set({ usageRights }),
  setExclusivity: (exclusivity) => set({ exclusivity }),
  setIsFirstBrandDeal: (isFirstBrandDeal) => set({ isFirstBrandDeal }),
  setManualCoinRate: (manualCoinRate) => set({ manualCoinRate }),
  setManualFavoriteRate: (manualFavoriteRate) => set({ manualFavoriteRate }),
  setManualCompletionRate: (manualCompletionRate) => set({ manualCompletionRate }),
  setManualShareRate: (manualShareRate) => set({ manualShareRate }),
  setManualRevisitRate: (manualRevisitRate) => set({ manualRevisitRate }),
  setManualCityTier: (manualCityTier) => set({ manualCityTier }),
  setManualMcnStatus: (manualMcnStatus) => set({ manualMcnStatus }),
  setHasLivestream: (hasLivestream) => set({ hasLivestream }),
  setNumPlatforms: (numPlatforms) => set({ numPlatforms }),
  resetPlatform: (p) =>
    set({
      platform: p,
      profile: null,
      fetchError: null,
      useManual: CN_MANUAL_PLATFORMS.includes(p),
      dealType: DEFAULT_DEAL_TYPE[p] ?? "dedicated_video",
      manualCoinRate: "",
      manualFavoriteRate: "",
      manualCompletionRate: "",
      manualShareRate: "",
      manualRevisitRate: "",
      manualCityTier: "other",
      manualMcnStatus: "none",
    }),
}));
