import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getReports, deleteReport } from "@/api/client";
import type { ReportList } from "@/types";

export default function HistoryPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [reports, setReports] = useState<ReportList[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getReports()
      .then(setReports)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    await deleteReport(id);
    setReports((prev) => prev.filter((r) => r.id !== id));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl animate-slide-up">
      <div className="mb-10">
        <h1 className="section-title">{t("history.title")}</h1>
        <p className="section-subtitle">{t("history.subtitle")}</p>
      </div>

      {reports.length === 0 ? (
        <div className="card py-16 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-600"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
            />
          </svg>
          <p className="mt-4 text-gray-500 dark:text-gray-400">{t("history.empty")}</p>
          <button
            onClick={() => navigate("/creator")}
            className="btn-primary mt-6"
          >
            {t("history.startFirst")}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="card group flex items-center gap-4 transition-shadow hover:shadow-md cursor-pointer"
              onClick={() => navigate(`/history/${report.id}`)}
            >
              {/* Price badge */}
              <div className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl bg-primary-50 dark:bg-primary-950">
                <span className="text-lg font-bold text-primary-600 dark:text-primary-400">
                  {report.currency === "USD" ? "$" : report.currency}
                </span>
              </div>

              {/* Info */}
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                  {report.title}
                </h3>
                <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400 line-clamp-1">
                  {report.summary}
                </p>
                <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
                  {new Date(report.created_at).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>

              {/* Price range */}
              {report.price_mid != null && (
                <div className="hidden text-right sm:block">
                  <p className="text-lg font-bold text-primary-600 dark:text-primary-400">
                    {fmtCurrency(Number(report.price_mid), report.currency)}
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">
                    {fmtCurrency(Number(report.price_low ?? 0), report.currency)} - {fmtCurrency(Number(report.price_high ?? 0), report.currency)}
                  </p>
                </div>
              )}

              {/* Delete button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(report.id);
                }}
                className="flex-shrink-0 rounded-lg p-2 text-gray-400 opacity-0 transition-all hover:bg-red-50 hover:text-red-600 group-hover:opacity-100 dark:hover:bg-red-950 dark:hover:text-red-400"
                title={t("common.delete")}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
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
