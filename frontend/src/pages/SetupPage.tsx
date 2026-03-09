import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  getProviders,
  getProvider,
  saveProvider,
  testProvider,
  getYoutubeKey,
  saveYoutubeKey,
  deleteYoutubeKey,
} from "@/api/client";
import { useSettingsStore } from "@/store/settingsStore";
import ProviderSelector from "@/components/ProviderSelector";
import type { ProviderInfo, TestResult } from "@/types";

export default function SetupPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const settings = useSettingsStore();

  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [apiKey, setApiKey] = useState("");
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [existingProvider, setExistingProvider] = useState<{
    provider: string;
    model: string | null;
    masked: string;
  } | null>(null);

  /* YouTube API Key state */
  const [ytKey, setYtKey] = useState("");
  const [ytHasKey, setYtHasKey] = useState(false);
  const [ytMasked, setYtMasked] = useState("");
  const [ytSaving, setYtSaving] = useState(false);
  const [ytSaved, setYtSaved] = useState(false);

  /* Load providers and existing config */
  useEffect(() => {
    Promise.all([getProviders(), getProvider(), getYoutubeKey()])
      .then(([provList, existing, ytInfo]) => {
        setProviders(provList);
        if (existing) {
          setExistingProvider({
            provider: existing.provider,
            model: existing.model,
            masked: existing.api_key_masked,
          });
          setSelectedProvider(existing.provider);
          setSelectedModel(existing.model ?? "");
          settings.setProvider(existing.provider, existing.model);
          settings.setHasApiKey(true);
        }
        setYtHasKey(ytInfo.has_key);
        setYtMasked(ytInfo.api_key_masked);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const currentProviderInfo = providers.find(
    (p) => p.id === selectedProvider,
  );

  /* When provider changes, pick first model */
  const handleProviderSelect = (id: string) => {
    setSelectedProvider(id);
    setTestResult(null);
    setApiKey("");
    const info = providers.find((p) => p.id === id);
    setSelectedModel(info?.models[0] ?? "");
  };

  /* Test connection */
  const handleTest = async () => {
    if (!selectedProvider || !apiKey) return;
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testProvider(selectedProvider, apiKey, selectedModel || undefined);
      setTestResult(result);
    } catch {
      setTestResult({ success: false, message: "Network error" });
    } finally {
      setTesting(false);
    }
  };

  /* Save YouTube API Key */
  const handleSaveYtKey = async () => {
    if (!ytKey.trim()) return;
    setYtSaving(true);
    try {
      const result = await saveYoutubeKey(ytKey.trim());
      setYtHasKey(true);
      setYtMasked(result.api_key_masked);
      setYtKey("");
      setYtSaved(true);
      setTimeout(() => setYtSaved(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setYtSaving(false);
    }
  };

  const handleDeleteYtKey = async () => {
    await deleteYoutubeKey();
    setYtHasKey(false);
    setYtMasked("");
  };

  /* Save and continue */
  const handleContinue = async () => {
    if (!selectedProvider) return;

    // If we already have config and didn't enter a new key, just continue
    if (existingProvider && !apiKey) {
      navigate("/creator");
      return;
    }

    if (!apiKey) return;

    setSaving(true);
    try {
      await saveProvider(selectedProvider, apiKey, selectedModel || undefined);
      settings.setProvider(selectedProvider, selectedModel);
      settings.setHasApiKey(true);
      navigate("/creator");
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const canContinue =
    (testResult?.success && apiKey) ||
    (existingProvider && selectedProvider === existingProvider.provider && !apiKey);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl animate-slide-up">
      {/* Header */}
      <div className="mb-10 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-violet-600 text-2xl font-bold text-white shadow-lg">
          K
        </div>
        <h1 className="section-title">{t("setup.title")}</h1>
        <p className="section-subtitle">{t("setup.subtitle")}</p>
      </div>

      {/* Existing provider banner */}
      {existingProvider && (
        <div className="mb-8 flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-950/30">
          <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
              clipRule="evenodd"
            />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-medium text-green-800 dark:text-green-300">
              {t("setup.configured")}:{" "}
              {providers.find((p) => p.id === existingProvider.provider)?.display_name ??
                existingProvider.provider}{" "}
              ({existingProvider.masked})
            </p>
          </div>
        </div>
      )}

      {/* Provider selector */}
      <div className="space-y-8">
        <ProviderSelector
          providers={providers}
          selected={selectedProvider}
          onSelect={handleProviderSelect}
        />

        {/* Model & API Key */}
        {selectedProvider && currentProviderInfo && (
          <div className="animate-fade-in space-y-5 rounded-2xl border border-gray-200 bg-gray-50 p-6 dark:border-gray-800 dark:bg-gray-900">
            {/* Model selector */}
            <div>
              <label className="label">{t("setup.model")}</label>
              <select
                className="select"
                value={selectedModel}
                onChange={(e) => {
                  setSelectedModel(e.target.value);
                  setTestResult(null);
                }}
              >
                {currentProviderInfo.models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            {/* API Key */}
            <div>
              <div className="flex items-center justify-between">
                <label className="label">{t("setup.apiKey")}</label>
                <a
                  href={currentProviderInfo.docs_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400"
                >
                  {t("setup.getApiKey")} &rarr;
                </a>
              </div>
              <input
                type="password"
                className="input font-mono"
                placeholder={
                  existingProvider?.provider === selectedProvider
                    ? existingProvider.masked
                    : t("setup.apiKeyPlaceholder")
                }
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  setTestResult(null);
                }}
              />
            </div>

            {/* Test button */}
            <button
              onClick={handleTest}
              disabled={!apiKey || testing}
              className="btn-secondary w-full"
            >
              {testing ? (
                <>
                  <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {t("setup.testing")}
                </>
              ) : (
                t("setup.testConnection")
              )}
            </button>

            {/* Test result */}
            {testResult && (
              <div
                className={`rounded-xl p-4 text-sm ${
                  testResult.success
                    ? "bg-green-50 text-green-700 dark:bg-green-950/30 dark:text-green-300"
                    : "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-300"
                }`}
              >
                <p className="font-medium">
                  {testResult.success
                    ? t("setup.testSuccess")
                    : t("setup.testFailed")}
                </p>
                <p className="mt-1 text-xs opacity-80">{testResult.message}</p>
              </div>
            )}
          </div>
        )}

        {/* YouTube API Key (optional) */}
        <div className="rounded-2xl border border-gray-200 bg-gray-50 p-6 dark:border-gray-800 dark:bg-gray-900">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {t("setup.youtubeApiKey")}
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {t("setup.youtubeApiKeyDesc")}
              </p>
            </div>
            <span className="rounded-full bg-gray-200 px-2.5 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300">
              {t("setup.optional")}
            </span>
          </div>

          {ytHasKey && (
            <div className="mb-4 flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-3 dark:border-green-800 dark:bg-green-950/30">
              <svg className="h-4 w-4 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="flex-1 text-sm text-green-700 dark:text-green-300 font-mono">
                {ytMasked}
              </span>
              <button
                onClick={handleDeleteYtKey}
                className="text-xs text-red-600 hover:text-red-700 dark:text-red-400"
              >
                {t("common.delete")}
              </button>
            </div>
          )}

          <div className="flex gap-3">
            <input
              type="password"
              className="input flex-1 font-mono"
              placeholder={ytHasKey ? t("setup.youtubeApiKeyReplace") : t("setup.youtubeApiKeyPlaceholder")}
              value={ytKey}
              onChange={(e) => setYtKey(e.target.value)}
            />
            <button
              onClick={handleSaveYtKey}
              disabled={!ytKey.trim() || ytSaving}
              className="btn-secondary flex-shrink-0"
            >
              {ytSaved ? t("setup.saved") : ytSaving ? t("common.loading") : t("setup.save")}
            </button>
          </div>

          <p className="mt-3 text-xs text-gray-400 dark:text-gray-500">
            {t("setup.youtubeApiKeyHelp")}{" "}
            <a
              href="https://console.cloud.google.com/apis/credentials"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:text-primary-700 dark:text-primary-400"
            >
              Google Cloud Console &rarr;
            </a>
          </p>
        </div>

        {/* Continue */}
        <button
          onClick={handleContinue}
          disabled={!canContinue || saving}
          className="btn-primary w-full text-base"
        >
          {saving ? t("common.loading") : t("setup.continue")}
        </button>
      </div>
    </div>
  );
}
