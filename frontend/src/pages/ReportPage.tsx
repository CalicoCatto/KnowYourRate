import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getAnalysisResult, saveReport } from "@/api/client";
import PriceRangeChart from "@/components/PriceRangeChart";
import NegotiationPoints from "@/components/NegotiationPoints";
import ContractRedFlags from "@/components/ContractRedFlags";
import type {
  AnalysisResult,
  FinalReport,
  NegotiationPoint,
  ContractRedFlag,
  ContentTypePricing,
} from "@/types";

export default function ReportPage() {
  const { runId } = useParams<{ runId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!runId) return;
    getAnalysisResult(runId)
      .then(setResult)
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

  const negotiationPoints: NegotiationPoint[] =
    report.negotiation_points ?? [];
  const redFlags: ContractRedFlag[] = report.contract_red_flags ?? [];
  const contentTypePricing: ContentTypePricing[] =
    report.content_type_pricing ?? [];

  const handleSave = async () => {
    if (!runId) return;
    setSaving(true);
    try {
      await saveReport(runId);
      setSaved(true);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

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
          {result?.started_at && result?.completed_at && (
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {new Date(result.completed_at).toLocaleDateString()}
            </p>
          )}
        </div>
        <div className="flex gap-3">
          <button onClick={handlePrint} className="btn-secondary">
            {t("report.export")}
          </button>
          <button
            onClick={handleSave}
            disabled={saving || saved}
            className="btn-primary"
          >
            {saved
              ? t("report.saved")
              : saving
                ? t("report.saving")
                : t("report.saveReport")}
          </button>
        </div>
      </div>

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

      {/* Content type table (fallback if no chart data) */}
      {contentTypePricing.length > 0 && (
        <div className="card overflow-x-auto">
          <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
            {t("report.contentBreakdown")}
          </h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="pb-3 text-left font-medium text-gray-500 dark:text-gray-400">
                  {t("report.contentType")}
                </th>
                <th className="pb-3 text-right font-medium text-gray-500 dark:text-gray-400">
                  {t("report.low")}
                </th>
                <th className="pb-3 text-right font-medium text-gray-500 dark:text-gray-400">
                  {t("report.mid")}
                </th>
                <th className="pb-3 text-right font-medium text-gray-500 dark:text-gray-400">
                  {t("report.high")}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {contentTypePricing.map((ct, idx) => (
                <tr key={idx}>
                  <td className="py-3 font-medium text-gray-900 dark:text-white">
                    {ct.label}
                  </td>
                  <td className="py-3 text-right text-gray-600 dark:text-gray-400">
                    {fmtCurrency(ct.price_range.low, ct.price_range.currency)}
                  </td>
                  <td className="py-3 text-right font-semibold text-primary-600 dark:text-primary-400">
                    {fmtCurrency(ct.price_range.mid, ct.price_range.currency)}
                  </td>
                  <td className="py-3 text-right text-gray-600 dark:text-gray-400">
                    {fmtCurrency(ct.price_range.high, ct.price_range.currency)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Negotiation Points */}
      <NegotiationPoints points={negotiationPoints} />

      {/* Contract Red Flags */}
      <ContractRedFlags flags={redFlags} />

      {/* Market Context */}
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

      {/* Bottom actions */}
      <div className="flex gap-3 border-t border-gray-200 pt-8 dark:border-gray-800">
        <button onClick={() => navigate("/creator")} className="btn-secondary flex-1">
          {t("report.newAnalysis")}
        </button>
        <button onClick={handlePrint} className="btn-primary flex-1">
          {t("report.export")}
        </button>
      </div>
    </div>
  );
}

function fmtCurrency(value: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}
