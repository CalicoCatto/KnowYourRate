import { useTranslation } from "react-i18next";
import type { ContractRedFlag } from "@/types";

interface Props {
  flags: ContractRedFlag[];
}

const SEVERITY_STYLES: Record<string, { bg: string; border: string; icon: string; badge: string }> = {
  high: {
    bg: "bg-red-50 dark:bg-red-950/30",
    border: "border-red-200 dark:border-red-800",
    icon: "text-red-500",
    badge: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  },
  medium: {
    bg: "bg-amber-50 dark:bg-amber-950/30",
    border: "border-amber-200 dark:border-amber-800",
    icon: "text-amber-500",
    badge: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  },
  low: {
    bg: "bg-blue-50 dark:bg-blue-950/30",
    border: "border-blue-200 dark:border-blue-800",
    icon: "text-blue-500",
    badge: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  },
};

export default function ContractRedFlags({ flags }: Props) {
  const { t } = useTranslation();

  if (!flags.length) return null;

  return (
    <div className="card">
      <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        {t("report.redFlags")}
      </h3>
      <div className="space-y-3">
        {flags.map((flag, idx) => {
          const styles = SEVERITY_STYLES[flag.severity] ?? SEVERITY_STYLES.low!;
          return (
            <div
              key={idx}
              className={`flex items-start gap-3 rounded-xl border p-4 ${styles.bg} ${styles.border}`}
            >
              {/* Warning icon */}
              <svg
                className={`mt-0.5 h-5 w-5 flex-shrink-0 ${styles.icon}`}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
                  clipRule="evenodd"
                />
              </svg>

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-gray-900 dark:text-white">
                    {flag.title}
                  </p>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles.badge}`}
                  >
                    {t(`report.severity.${flag.severity}`)}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  {flag.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
