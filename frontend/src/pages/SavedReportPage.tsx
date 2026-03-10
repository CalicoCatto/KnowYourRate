import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getReport } from "@/api/client";
import PriceRangeChart from "@/components/PriceRangeChart";
import NegotiationPoints from "@/components/NegotiationPoints";
import ContractRedFlags from "@/components/ContractRedFlags";
import DetailedAnalysis from "@/components/DetailedAnalysis";
import type {
  ReportResponse,
  FinalReport,
  NegotiationPoint,
  ContractRedFlag,
  ContentTypePricing,
} from "@/types";

export default function SavedReportPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDetailed, setShowDetailed] = useState(false);

  useEffect(() => {
    if (!reportId) return;
    getReport(reportId)
      .then(setReport)
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load report");
      })
      .finally(() => setLoading(false));
  }, [reportId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="mx-auto max-w-2xl py-24 text-center">
        <p className="text-red-600 dark:text-red-400">{error ?? "Report not found"}</p>
        <button onClick={() => navigate("/history")} className="btn-secondary mt-4">
          {t("common.back")}
        </button>
      </div>
    );
  }

  const fr: FinalReport = (report.full_report as FinalReport) ?? {};
  const priceLow = fr.price_low ?? Number(report.price_low ?? 0);
  const priceMid = fr.price_mid ?? Number(report.price_mid ?? 0);
  const priceHigh = fr.price_high ?? Number(report.price_high ?? 0);
  const currency = fr.currency ?? report.currency;
  const negotiationPoints: NegotiationPoint[] = fr.negotiation_points ?? [];
  const redFlags: ContractRedFlag[] = fr.contract_red_flags ?? [];
  const contentTypePricing: ContentTypePricing[] = fr.content_type_pricing ?? [];

  return (
    <div className="mx-auto max-w-4xl animate-slide-up space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <button
            onClick={() => navigate("/history")}
            className="mb-2 flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800 dark:text-gray-300 dark:hover:text-gray-100"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
            {t("history.title")}
          </button>
          <h1 className="section-title">{report.title}</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
            {new Date(report.created_at).toLocaleDateString(undefined, {
              year: "numeric",
              month: "long",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
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
          {(fr.executive_summary ?? fr.summary) && (
            <div className="card">
              <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                {t("report.executiveSummary")}
              </h2>
              <p className="leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-line">
                {fr.executive_summary ?? fr.summary}
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
                    <th className="pb-3 text-left font-medium text-gray-600 dark:text-gray-300">{t("report.contentType")}</th>
                    <th className="pb-3 text-right font-medium text-gray-600 dark:text-gray-300">{t("report.low")}</th>
                    <th className="pb-3 text-right font-medium text-gray-600 dark:text-gray-300">{t("report.mid")}</th>
                    <th className="pb-3 text-right font-medium text-gray-600 dark:text-gray-300">{t("report.high")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {contentTypePricing.map((ct, idx) => (
                    <tr key={idx}>
                      <td className="py-3 font-medium text-gray-900 dark:text-white">{ct.label}</td>
                      <td className="py-3 text-right text-gray-600 dark:text-gray-300">{fmtCurrency(ct.price_range.low, ct.price_range.currency)}</td>
                      <td className="py-3 text-right font-semibold text-primary-600 dark:text-primary-400">{fmtCurrency(ct.price_range.mid, ct.price_range.currency)}</td>
                      <td className="py-3 text-right text-gray-600 dark:text-gray-300">{fmtCurrency(ct.price_range.high, ct.price_range.currency)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <NegotiationPoints points={negotiationPoints} />
          <ContractRedFlags flags={redFlags} />

          {fr.market_context && (
            <div className="card">
              <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                {t("report.marketContext")}
              </h3>
              <p className="leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-line">
                {fr.market_context}
              </p>
            </div>
          )}
        </>
      ) : (
        <DetailedAnalysis
          agentOutputs={report.agent_outputs}
          finalReport={fr}
        />
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
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}
