import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getAnalysisResult, getReport, saveReport } from "@/api/client";
import PriceRangeChart from "@/components/PriceRangeChart";
import NegotiationPoints from "@/components/NegotiationPoints";
import ContractRedFlags from "@/components/ContractRedFlags";
import DetailedAnalysis from "@/components/DetailedAnalysis";
import type {
  AnalysisResult,
  FinalReport,
  NegotiationPoint,
  ContractRedFlag,
  ContentTypePricing,
  ReportResponse,
  AgentOutputs,
} from "@/types";

export default function ReportPage() {
  const { runId } = useParams<{ runId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [savedReport, setSavedReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDetailed, setShowDetailed] = useState(false);

  useEffect(() => {
    if (!runId) return;

    // Fetch analysis result and auto-save the report
    getAnalysisResult(runId)
      .then(async (res) => {
        setResult(res);
        // Auto-save and get full report with agent_outputs
        try {
          const saved = await saveReport(runId);
          // Fetch the full saved report to get agent_outputs
          const full = await getReport(saved.id);
          setSavedReport(full);
        } catch {
          // Already saved or save failed — try to find existing
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load report");
      })
      .finally(() => setLoading(false));
  }, [runId]);

  const report: FinalReport = (result?.final_report as FinalReport) ?? {};

  const priceLow = report.price_low ?? 0;
  const priceMid = report.price_mid ?? 0;
  const priceHigh = report.price_high ?? 0;
  const currency = report.currency ?? "USD";

  const negotiationPoints: NegotiationPoint[] = report.negotiation_points ?? [];
  const redFlags: ContractRedFlag[] = report.contract_red_flags ?? [];
  const contentTypePricing: ContentTypePricing[] = report.content_type_pricing ?? [];

  const agentOutputs: AgentOutputs | null = savedReport?.agent_outputs ?? (result ? {
    creator_analysis: result.creator_analysis,
    market_intel: result.market_intel ?? result.market_data,
    market_data: result.market_data,
    brand_analysis: result.brand_analysis,
    debate_result: result.debate_result,
  } : null);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl py-24 text-center">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button onClick={() => navigate("/creator")} className="btn-secondary mt-4">
          {t("common.back")}
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl animate-slide-up space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="section-title">
            {report.title ?? t("report.title")}
          </h1>
          {result?.completed_at && (
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {new Date(result.completed_at).toLocaleDateString()}
            </p>
          )}
        </div>
        <div className="flex gap-3">
          <button onClick={() => window.print()} className="btn-secondary">
            {t("report.export")}
          </button>
          <button
            onClick={() => setShowDetailed(!showDetailed)}
            className={showDetailed ? "btn-primary" : "btn-secondary"}
          >
            {showDetailed ? t("report.showSummary") : t("report.showDetailed")}
          </button>
        </div>
      </div>

      {!showDetailed ? (
        <>
          {/* Executive summary */}
          {(report.executive_summary ?? report.summary) && (
            <div className="card">
              <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                {t("report.executiveSummary")}
              </h2>
              <p className="leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-line">
                {report.executive_summary ?? report.summary}
              </p>
            </div>
          )}

          {/* Price Range Chart */}
          {(priceLow > 0 || priceMid > 0 || priceHigh > 0) && (
            <PriceRangeChart
              low={priceLow}
              mid={priceMid}
              high={priceHigh}
              currency={currency}
              contentTypePricing={contentTypePricing}
            />
          )}

          {/* Content type table */}
          {contentTypePricing.length > 0 && (
            <div className="card overflow-x-auto">
              <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
                {t("report.contentBreakdown")}
              </h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="pb-3 text-left font-medium text-gray-500 dark:text-gray-400">{t("report.contentType")}</th>
                    <th className="pb-3 text-right font-medium text-gray-500 dark:text-gray-400">{t("report.low")}</th>
                    <th className="pb-3 text-right font-medium text-gray-500 dark:text-gray-400">{t("report.mid")}</th>
                    <th className="pb-3 text-right font-medium text-gray-500 dark:text-gray-400">{t("report.high")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {contentTypePricing.map((ct, idx) => (
                    <tr key={idx}>
                      <td className="py-3 font-medium text-gray-900 dark:text-white">{ct.label}</td>
                      <td className="py-3 text-right text-gray-600 dark:text-gray-400">{fmtCurrency(ct.price_range.low, ct.price_range.currency)}</td>
                      <td className="py-3 text-right font-semibold text-primary-600 dark:text-primary-400">{fmtCurrency(ct.price_range.mid, ct.price_range.currency)}</td>
                      <td className="py-3 text-right text-gray-600 dark:text-gray-400">{fmtCurrency(ct.price_range.high, ct.price_range.currency)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Package Tiers */}
          {report.package_tiers && Object.keys(report.package_tiers).length > 0 && (
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
                {t("report.packageTiers")}
              </h3>
              <div className="grid gap-4 sm:grid-cols-3">
                {Object.values(report.package_tiers).map((tier, idx) => (
                  <div
                    key={idx}
                    className={`rounded-xl border p-5 ${
                      idx === 1
                        ? "border-primary-400 bg-primary-50 dark:border-primary-600 dark:bg-primary-950"
                        : "border-gray-200 dark:border-gray-700"
                    }`}
                  >
                    <h4 className="text-base font-semibold text-gray-900 dark:text-white">
                      {tier.name}
                    </h4>
                    <p className="mt-1 text-2xl font-bold text-primary-600 dark:text-primary-400">
                      {fmtCurrency(tier.price, currency)}
                    </p>
                    {tier.duration && (
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{tier.duration}</p>
                    )}
                    <ul className="mt-3 space-y-1">
                      {tier.includes.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                          <span className="mt-0.5 text-primary-500">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                    {tier.savings_vs_individual && (
                      <p className="mt-3 text-xs font-medium text-green-600 dark:text-green-400">
                        {t("report.savings")}: {tier.savings_vs_individual}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <NegotiationPoints points={negotiationPoints} />

          {/* Negotiation Scripts */}
          {report.negotiation_scripts && report.negotiation_scripts.length > 0 && (
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
                {t("report.negotiationScripts")}
              </h3>
              <div className="space-y-4">
                {report.negotiation_scripts.map((script, idx) => (
                  <div key={idx} className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                    <h4 className="mb-2 text-sm font-semibold text-gray-900 dark:text-white">
                      {script.scenario}
                    </h4>
                    <p className="whitespace-pre-line text-sm italic text-gray-700 dark:text-gray-300">
                      "{script.script}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <ContractRedFlags flags={redFlags} />

          {report.market_context && (
            <div className="card">
              <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                {t("report.marketContext")}
              </h3>
              <p className="leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-line">
                {report.market_context}
              </p>
            </div>
          )}

          {/* CN-specific: Tax Estimate */}
          {(report as Record<string, unknown>).tax_estimate && (
            <div className="card">
              <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                {t("report.taxEstimate")}
              </h3>
              <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                {Object.entries(
                  (report as Record<string, unknown>).tax_estimate as Record<string, unknown>,
                ).map(([key, val]) => (
                  <div key={key} className="flex justify-between border-b border-gray-100 dark:border-gray-800 pb-1">
                    <span className="text-gray-500 dark:text-gray-400">{key}</span>
                    <span className="font-medium">
                      {typeof val === "number" ? fmtCurrency(val, currency) : String(val)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CN-specific: Platform Official Pricing */}
          {(report as Record<string, unknown>).platform_pricing && (
            <div className="card">
              <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                {t("report.platformPricing")}
              </h3>
              <p className="leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-line">
                {JSON.stringify((report as Record<string, unknown>).platform_pricing, null, 2)}
              </p>
            </div>
          )}
        </>
      ) : (
        <DetailedAnalysis agentOutputs={agentOutputs} finalReport={report} />
      )}

      {/* Bottom actions */}
      <div className="flex gap-3 border-t border-gray-200 pt-8 dark:border-gray-800">
        <button onClick={() => navigate("/creator")} className="btn-secondary flex-1">
          {t("report.newAnalysis")}
        </button>
        <button onClick={() => window.print()} className="btn-primary flex-1">
          {t("report.export")}
        </button>
      </div>
    </div>
  );
}

function fmtCurrency(value: number, currency: string) {
  const locale = currency === "CNY" ? "zh-CN" : "en-US";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}
