import { useTranslation } from "react-i18next";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { ContentTypePricing } from "@/types";

interface Props {
  low: number;
  mid: number;
  high: number;
  currency: string;
  contentTypePricing?: ContentTypePricing[];
}

function fmt(value: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

export default function PriceRangeChart({
  low,
  mid,
  high,
  currency,
  contentTypePricing,
}: Props) {
  const { t } = useTranslation();

  /* ---- Main price bar data ---- */
  const mainData = [
    { name: t("report.low"), value: low, fill: "#94a3b8" },
    { name: t("report.mid"), value: mid, fill: "#6366f1" },
    { name: t("report.high"), value: high, fill: "#8b5cf6" },
  ];

  /* ---- Content type data ---- */
  const ctData = contentTypePricing?.map((ct) => ({
    name: ct.label,
    low: ct.price_range.low,
    mid: ct.price_range.mid,
    high: ct.price_range.high,
  }));

  return (
    <div className="space-y-8">
      {/* Main price range */}
      <div className="card">
        <h3 className="mb-6 text-lg font-semibold text-gray-900 dark:text-white">
          {t("report.priceRange")}
        </h3>

        {/* Big number display */}
        <div className="mb-8 grid grid-cols-3 gap-4 text-center">
          <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800">
            <p className="text-xs font-medium uppercase tracking-wider text-gray-600 dark:text-gray-300">
              {t("report.low")}
            </p>
            <p className="mt-1 text-2xl font-bold text-gray-700 dark:text-gray-200">
              {fmt(low, currency)}
            </p>
          </div>
          <div className="rounded-xl bg-primary-50 p-4 ring-2 ring-primary-200 dark:bg-primary-950 dark:ring-primary-800">
            <p className="text-xs font-medium uppercase tracking-wider text-primary-600 dark:text-primary-400">
              {t("report.mid")}
            </p>
            <p className="mt-1 text-2xl font-bold text-primary-700 dark:text-primary-300">
              {fmt(mid, currency)}
            </p>
          </div>
          <div className="rounded-xl bg-violet-50 p-4 dark:bg-violet-950">
            <p className="text-xs font-medium uppercase tracking-wider text-violet-600 dark:text-violet-400">
              {t("report.high")}
            </p>
            <p className="mt-1 text-2xl font-bold text-violet-700 dark:text-violet-300">
              {fmt(high, currency)}
            </p>
          </div>
        </div>

        {/* Bar chart */}
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={mainData} layout="vertical" margin={{ left: 20, right: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                type="number"
                tickFormatter={(v: number) => fmt(v, currency)}
                tick={{ fontSize: 12 }}
              />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 13 }} width={100} />
              <Tooltip
                formatter={(v: number) => fmt(v, currency)}
                contentStyle={{
                  borderRadius: "0.75rem",
                  border: "1px solid #e5e7eb",
                  fontSize: "0.875rem",
                }}
              />
              <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={28}>
                {mainData.map((entry, index) => (
                  <Cell key={index} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Content type breakdown */}
      {ctData && ctData.length > 0 && (
        <div className="card">
          <h3 className="mb-6 text-lg font-semibold text-gray-900 dark:text-white">
            {t("report.contentBreakdown")}
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ctData} margin={{ left: 20, right: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={(v: number) => fmt(v, currency)} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(v: number) => fmt(v, currency)}
                  contentStyle={{
                    borderRadius: "0.75rem",
                    border: "1px solid #e5e7eb",
                    fontSize: "0.875rem",
                  }}
                />
                <Legend />
                <Bar dataKey="low" name={t("report.low")} fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="mid" name={t("report.mid")} fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="high" name={t("report.high")} fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
