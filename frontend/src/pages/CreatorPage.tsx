import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { lookupCreator, startAnalysis } from "@/api/client";
import { useSettingsStore } from "@/store/settingsStore";
import { useCreatorStore } from "@/store/creatorStore";
import PlatformSelector from "@/components/PlatformSelector";
import type { Platform, DealType } from "@/types";
import { DEAL_TYPE_LABELS, NICHE_OPTIONS } from "@/types";

export default function CreatorPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const language = useSettingsStore((s) => s.language);

  const store = useCreatorStore();

  /* Local-only transient states */
  const [fetching, setFetching] = useState(false);
  const [starting, setStarting] = useState(false);

  /* Reset when switching platform */
  const handlePlatformSelect = (p: Platform) => {
    store.resetPlatform(p);
  };

  /* Fetch YouTube profile */
  const handleFetch = async () => {
    if (!store.channelUrl.trim()) return;
    setFetching(true);
    store.setFetchError(null);
    store.setProfile(null);
    try {
      const result = await lookupCreator("youtube", store.channelUrl.trim());
      store.setProfile(result);
      store.setUseManual(false);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : t("creator.fetchFailed");
      store.setFetchError(msg);
    } finally {
      setFetching(false);
    }
  };

  /* Build manual data object */
  const buildManualData = () => ({
    platform: store.platform ?? "youtube",
    handle: store.manualHandle,
    display_name: store.manualName || store.manualHandle,
    subscriber_count: parseInt(store.manualFollowers) || 0,
    avg_views: parseInt(store.manualAvgViews) || 0,
    engagement_rate: parseFloat(store.manualEngagement) || 0,
    content_niche: store.manualNiche || "general",
  });

  /* Start analysis */
  const handleStart = async () => {
    if (!store.brandName.trim()) return;

    setStarting(true);
    try {
      let creatorId: string | undefined;
      let manualData: Record<string, unknown> | undefined;

      if (store.profile && !store.useManual) {
        creatorId = store.profile.id;
      } else {
        manualData = buildManualData();
      }

      const result = await startAnalysis({
        creator_id: creatorId ?? null,
        manual_data: manualData ?? null,
        brand_name: store.brandName.trim(),
        deal_type: store.dealType,
        language,
      });

      navigate(`/analysis/${result.run_id}`);
    } catch (err) {
      console.error(err);
      setStarting(false);
    }
  };

  const manualValid = store.manualHandle.trim() && store.manualFollowers.trim();
  const canStart =
    store.brandName.trim() &&
    ((store.platform === "youtube" && (store.profile || (store.useManual && manualValid))) ||
      (store.platform === "tiktok" && manualValid));

  return (
    <div className="mx-auto max-w-2xl animate-slide-up">
      {/* Header */}
      <div className="mb-10">
        <h1 className="section-title">{t("creator.title")}</h1>
        <p className="section-subtitle">{t("creator.subtitle")}</p>
      </div>

      <div className="space-y-8">
        {/* Platform selector */}
        <PlatformSelector selected={store.platform} onSelect={handlePlatformSelect} />

        {/* YouTube: URL lookup + manual fallback */}
        {store.platform === "youtube" && !store.useManual && (
          <div className="animate-fade-in space-y-5">
            <div>
              <label className="label">{t("creator.channelUrl")}</label>
              <div className="flex gap-3">
                <input
                  className="input flex-1"
                  placeholder={t("creator.channelUrlPlaceholder")}
                  value={store.channelUrl}
                  onChange={(e) => store.setChannelUrl(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleFetch()}
                />
                <button
                  onClick={handleFetch}
                  disabled={!store.channelUrl.trim() || fetching}
                  className="btn-primary flex-shrink-0"
                >
                  {fetching ? t("creator.fetching") : t("creator.fetchProfile")}
                </button>
              </div>
              {store.fetchError && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                  {store.fetchError}
                </p>
              )}
              {/* Manual entry switch */}
              <button
                onClick={() => store.setUseManual(true)}
                className="mt-3 text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
              >
                {t("creator.switchManual")}
              </button>
            </div>

            {/* Profile preview */}
            {store.profile && (
              <div className="animate-slide-up rounded-2xl border border-green-200 bg-green-50 p-6 dark:border-green-800 dark:bg-green-950/30">
                <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider text-green-700 dark:text-green-400">
                  {t("creator.profilePreview")}
                </h4>
                <div className="space-y-1">
                  <p className="text-xl font-bold text-gray-900 dark:text-white">
                    {store.profile.display_name}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    @{store.profile.handle}
                  </p>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <Stat
                    label={t("creator.subscribers")}
                    value={fmtNum(store.profile.subscriber_count)}
                  />
                  <Stat
                    label={t("creator.avgViews")}
                    value={fmtNum(store.profile.avg_views)}
                  />
                  <Stat
                    label={t("creator.engagementRate")}
                    value={
                      store.profile.engagement_rate != null
                        ? `${store.profile.engagement_rate.toFixed(1)}%`
                        : "N/A"
                    }
                  />
                  <Stat
                    label={t("creator.niche")}
                    value={store.profile.content_niche ?? "N/A"}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Manual entry form (TikTok always, YouTube when toggled or fetch failed) */}
        {store.platform && store.useManual && (
          <div className="animate-fade-in space-y-5 rounded-2xl border border-gray-200 bg-gray-50 p-6 dark:border-gray-800 dark:bg-gray-900">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white">
                  {t("creator.manualEntry")}
                </h4>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {store.platform === "tiktok"
                    ? t("creator.manualSubtitle")
                    : t("creator.manualYoutubeSubtitle")}
                </p>
              </div>
              {store.platform === "youtube" && (
                <button
                  onClick={() => store.setUseManual(false)}
                  className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
                >
                  {t("creator.switchApi")}
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="label">{t("creator.handlePlaceholder")}</label>
                <input
                  className="input"
                  placeholder="@username"
                  value={store.manualHandle}
                  onChange={(e) => store.setManualHandle(e.target.value)}
                />
              </div>
              <div>
                <label className="label">{t("creator.displayName")}</label>
                <input
                  className="input"
                  placeholder={t("creator.displayNamePlaceholder")}
                  value={store.manualName}
                  onChange={(e) => store.setManualName(e.target.value)}
                />
              </div>
              <div>
                <label className="label">{t("creator.followerCount")}</label>
                <input
                  type="number"
                  className="input"
                  placeholder="500000"
                  value={store.manualFollowers}
                  onChange={(e) => store.setManualFollowers(e.target.value)}
                />
              </div>
              <div>
                <label className="label">{t("creator.avgViewsLabel")}</label>
                <input
                  type="number"
                  className="input"
                  placeholder="100000"
                  value={store.manualAvgViews}
                  onChange={(e) => store.setManualAvgViews(e.target.value)}
                />
              </div>
              <div>
                <label className="label">
                  {t("creator.engagementRateLabel")}
                </label>
                <input
                  type="number"
                  step="0.1"
                  className="input"
                  placeholder="4.5"
                  value={store.manualEngagement}
                  onChange={(e) => store.setManualEngagement(e.target.value)}
                />
              </div>
              <div>
                <label className="label">{t("creator.niche")}</label>
                <select
                  className="select"
                  value={store.manualNiche}
                  onChange={(e) => store.setManualNiche(e.target.value)}
                >
                  <option value="">{t("creator.selectNiche")}</option>
                  {NICHE_OPTIONS.map((n) => (
                    <option key={n} value={n}>
                      {n.charAt(0).toUpperCase() + n.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Brand info */}
        {store.platform && (
          <div className="animate-fade-in space-y-5 rounded-2xl border border-gray-200 bg-gray-50 p-6 dark:border-gray-800 dark:bg-gray-900">
            <h4 className="font-semibold text-gray-900 dark:text-white">
              {t("creator.brandInfo")}
            </h4>

            <div>
              <label className="label">{t("creator.brandName")}</label>
              <input
                className="input"
                placeholder={t("creator.brandNamePlaceholder")}
                value={store.brandName}
                onChange={(e) => store.setBrandName(e.target.value)}
              />
            </div>

            <div>
              <label className="label">{t("creator.dealType")}</label>
              <select
                className="select"
                value={store.dealType}
                onChange={(e) => store.setDealType(e.target.value as DealType)}
              >
                {(
                  Object.entries(DEAL_TYPE_LABELS) as [
                    DealType,
                    string,
                  ][]
                ).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Start Analysis */}
        {store.platform && (
          <button
            onClick={handleStart}
            disabled={!canStart || starting}
            className="btn-primary w-full text-base"
          >
            {starting ? t("creator.starting") : t("creator.startAnalysis")}
          </button>
        )}
      </div>
    </div>
  );
}

/* ---- Helpers ---- */

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold text-gray-900 dark:text-white">
        {value}
      </p>
    </div>
  );
}

function fmtNum(n: number | null | undefined): string {
  if (n == null) return "N/A";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}
