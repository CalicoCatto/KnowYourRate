import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SettingsState {
  provider: string | null;
  model: string | null;
  hasApiKey: boolean;
  language: string;
  darkMode: boolean;
  setProvider: (provider: string | null, model?: string | null) => void;
  setHasApiKey: (has: boolean) => void;
  setLanguage: (lang: string) => void;
  toggleDarkMode: () => void;
  reset: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      provider: null,
      model: null,
      hasApiKey: false,
      language: "en",
      darkMode: false,
      setProvider: (provider, model) => set({ provider, model: model ?? null }),
      setHasApiKey: (has) => set({ hasApiKey: has }),
      setLanguage: (lang) => set({ language: lang }),
      toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
      reset: () =>
        set({ provider: null, model: null, hasApiKey: false }),
    }),
    { name: "kyr-settings" },
  ),
);
