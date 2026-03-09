import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { lookupCreator, startAnalysis } from "@/api/client";
import { useSettingsStore } from "@/store/settingsStore";
import PlatformSelector from "@/components/PlatformSelector";
import type { Platform, CreatorProfile, DealType } from "@/types";
import { DEAL_TYPE_LABELS, NICHE_OPTIONS } from "@/types";

export default function CreatorPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const language = useSettingsStore((s) => s.language);

  /* Platform state */
  const [platform, setPlatform] = useState<Platform | null>(null);

  /* YouTube lookup */
  const [channelUrl, setChannelUrl] = useState("");
  const [fetching, setFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [profile, setProfile] = useState<CreatorProfile | null>(null);

  /* Manual input (shared by YouTube fallback and TikTok) */
  const [useManual, setUseManual] = useState(false);
  const [manualHandle, setManualHandle] = useState("");
  const [manualName, setManualName] = useState("");
  const [manualFollowers, setManualFollowers] = useState("");
  const [manualAvgViews, setManualAvgViews] = useState("");
  const [manualEngagement, setManualEngagement] = useState("");
  const [manualNiche, setManualNiche] = useState("");

  /* Brand info */
  const [brandName, setBrandName] = useState("");
  const [dealType, setDealType] = useState<DealType>("dedicated_video");

  /* Submit state */
  const [starting, setStarting] = useState(false);

  /* Reset when switching platform */
  const handlePlatformSelect = (p: Platform) => {
    setPlatform(p);
    setProfile(null);
    setFetchError(null);
    setUseManual(p === "tiktok");
  };

  /* Fetch YouTube profile */
  const handleFetch = async () => {
    if (!channelUrl.trim()) return;
    setFetching(true);
    setFetchError(null);
    setProfile(null);
    try {
      const result = await lookupCreator("youtube", channelUrl.trim());
      setProfile(result);
      setUseManual(false);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : t("creator.fetchFailed");
      setFetchError(msg);
    } finally {
      setFetching(false);
    }
  };

  /* Build manual data object */
  const buildManualData = () => ({
    platform: platform ?? "youtube",
    handle: manualHandle,
    display_name: manualName || manualHandle,
    subscriber_count: parseInt(manualFollowers) || 0,
    avg_views: parseInt(manualAvgViews) || 0,
    engagement_rate: parseFloat(manualEngagement) || 0,
    content_niche: manualNiche || "general",
  });

  /* Start analysis */
  const handleStart = async () => {
    if (!brandName.trim()) return;

    setStarting(true);
    try {
      let creatorId: string | undefined;
      let manualData: Record<string, unknown> | undefined;

      if (profile && !useManual) {
        creatorId = profile.id;
      } else {
        manualData = buildManualData();
      }

      const result = await startAnalysis({
        creator_id: creatorId ?? null,
        manual_data: manualData ?? null,
        brand_name: brandName.trim(),
        deal_type: dealType,
        language,
      });

      navigate(`/analysis/${result.run_id}`);
    } catch (err) {
      console.error(err);
      setStarting(false);
    }
  };

  const manualValid = manualHandle.trim() && manualFollowers.trim();
  const canStart =
    brandName.trim() &&
    ((platform === "youtube" && (profile || (useManual && manualValid))) ||
      (platform === "tiktok" && manualValid));

  return (
    <div className="mx-auto max-w-2xl animate-slide-up">
      {/* Header */}
      <div className="mb-10">
        <h1 className="section-title">{t("creator.title")}</h1>
        <p className="section-subtitle">{t("creator.subtitle")}</p>
      </div>

      <div className="space-y-8">
        {/* Platform selector */}
        <PlatformSelector selected={platform} onSelect={handlePlatformSelect} />

        {/* YouTube: URL lookup + manual fallback */}
        {platform === "youtube" && !useManual && (
          <div className="animate-fade-in space-y-5">
            <div>
              <label className="label">{t("creator.channelUrl")}</label>
              <div className="flex gap-3">
                <input
                  className="input flex-1"
                  placeholder={t("creator.channelUrlPlaceholder")}
                  value={channelUrl}
                  onChange={(e) => setChannelUrl(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleFetch()}
                />
                <button
                  onClick={handleFetch}
                  disabled={!channelUrl.trim() || fetching}
                  className="btn-primary flex-shrink-0"
                >
                  {fetching ? t("creator.fetching") : t("creator.fetchProfile")}
                </button>
              </div>
              {fetchError && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                  {fetchError}
                </p>
              )}
              {/* Manual entry switch */}
              <button
                onClick={() => setUseManual(true)}
                className="mt-3 text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
              >
                {t("creator.switchManual")}
              </button>
            </div>

            {/* Profile preview */}
            {profile && (
              <div className="animate-slide-up rounded-2xl border border-green-200 bg-green-50 p-6 dark:border-green-800 dark:bg-green-950/30">
                <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider text-green-700 dark:text-green-400">
                  {t("creator.profilePreview")}
                </h4>
                <div className="space-y-1">
                  <p className="text-xl font-bold text-gray-900 dark:text-white">
                    {profile.display_name}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    @{profile.handle}
                  </p>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <Stat
                    label={t("creator.subscribers")}
                    value={fmtNum(profile.subscriber_count)}
                  />
                  <Stat
                    label={t("creator.avgViews")}
                    value={fmtNum(profile.avg_views)}
                  />
                  <Stat
                    label={t("creator.engagementRate")}
                    value={
                      profile.engagement_rate != null
                        ? `${profile.engagement_rate.toFixed(1)}%`
                        : "N/A"
                    }
                  />
                  <Stat
                    label={t("creator.niche")}
                    value={profile.content_niche ?? "N/A"}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Manual entry form (TikTok always, YouTube when toggled or fetch failed) */}
        {platform && useManual && (
          <div className="animate-fade-in space-y-5 rounded-2xl border border-gray-200 bg-gray-50 p-6 dark:border-gray-800 dark:bg-gray-900">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white">
                  {t("creator.manualEntry")}
                </h4>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {platform === "tiktok"
                    ? t("creator.manualSubtitle")
                    : t("creator.manualYoutubeSubtitle")}
                </p>
              </div>
              {platform === "youtube" && (
                <button
                  onClick={() => setUseManual(false)}
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
                  value={manualHandle}
                  onChange={(e) => setManualHandle(e.target.value)}
                />
              </div>
              <div>
                <label className="label">{t("creator.displayName")}</label>
                <input
                  className="input"
                  placeholder={t("creator.displayNamePlaceholder")}
                  value={manualName}
                  onChange={(e) => setManualName(e.target.value)}
                />
              </div>
              <div>
                <label className="label">{t("creator.followerCount")}</label>
                <input
                  type="number"
                  className="input"
                  placeholder="500000"
                  value={manualFollowers}
                  onChange={(e) => setManualFollowers(e.target.value)}
                />
              </div>
              <div>
                <label className="label">{t("creator.avgViewsLabel")}</label>
                <input
                  type="number"
                  className="input"
                  placeholder="100000"
                  value={manualAvgViews}
                  onChange={(e) => setManualAvgViews(e.target.value)}
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
                  value={manualEngagement}
                  onChange={(e) => setManualEngagement(e.target.value)}
                />
              </div>
              <div>
                <label className="label">{t("creator.niche")}</label>
                <select
                  className="select"
                  value={manualNiche}
                  onChange={(e) => setManualNiche(e.target.value)}
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
        {platform && (
          <div className="animate-fade-in space-y-5 rounded-2xl border border-gray-200 bg-gray-50 p-6 dark:border-gray-800 dark:bg-gray-900">
            <h4 className="font-semibold text-gray-900 dark:text-white">
              {t("creator.brandInfo")}
            </h4>

            <div>
              <label className="label">{t("creator.brandName")}</label>
              <input
                className="input"
                placeholder={t("creator.brandNamePlaceholder")}
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
              />
            </div>

            <div>
              <label className="label">{t("creator.dealType")}</label>
              <select
                className="select"
                value={dealType}
                onChange={(e) => setDealType(e.target.value as DealType)}
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
        {platform && (
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
