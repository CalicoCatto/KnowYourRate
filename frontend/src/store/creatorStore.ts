import { create } from "zustand";
import type { Platform, CreatorProfile, DealType } from "@/types";

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
  resetPlatform: (p) =>
    set({
      platform: p,
      profile: null,
      fetchError: null,
      useManual: p === "tiktok",
    }),
}));
