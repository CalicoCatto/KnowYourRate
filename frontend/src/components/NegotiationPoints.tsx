import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { NegotiationPoint } from "@/types";

interface Props {
  points: NegotiationPoint[];
}

export default function NegotiationPoints({ points }: Props) {
  const { t } = useTranslation();

  if (!points.length) return null;

  return (
    <div className="card">
      <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        {t("report.negotiation")}
      </h3>
      <ul className="space-y-3">
        {points.map((point, idx) => (
          <PointItem key={idx} point={point} />
        ))}
      </ul>
    </div>
  );
}

function PointItem({ point }: { point: NegotiationPoint }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(
      `${point.title}: ${point.description}`,
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <li className="group flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50 p-4 transition-colors hover:border-primary-200 hover:bg-primary-50 dark:border-gray-800 dark:bg-gray-800/50 dark:hover:border-primary-800 dark:hover:bg-primary-950/30">
      <div className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-primary-100 text-primary-600 dark:bg-primary-900 dark:text-primary-400">
        <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
        </svg>
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-medium text-gray-900 dark:text-white">
          {point.title}
        </p>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          {point.description}
        </p>
      </div>
      <button
        onClick={copy}
        className="flex-shrink-0 rounded-lg px-2 py-1 text-xs font-medium text-gray-400 opacity-0 transition-all hover:bg-gray-200 hover:text-gray-700 group-hover:opacity-100 dark:hover:bg-gray-700 dark:hover:text-gray-200"
      >
        {copied ? t("report.copied") : t("report.copyPoint")}
      </button>
    </li>
  );
}
