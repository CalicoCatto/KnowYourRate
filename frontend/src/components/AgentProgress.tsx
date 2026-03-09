import { useTranslation } from "react-i18next";
import type { AgentStep } from "@/types";

interface Props {
  steps: AgentStep[];
}

export default function AgentProgress({ steps }: Props) {
  const { t } = useTranslation();

  return (
    <div className="space-y-0">
      {steps.map((step, idx) => (
        <div key={step.agent} className="animate-fade-in">
          <div className="flex gap-4">
            {/* Vertical line + indicator */}
            <div className="flex flex-col items-center">
              <StatusIndicator status={step.status} />
              {idx < steps.length - 1 && (
                <div
                  className={`w-0.5 flex-1 min-h-[2rem] transition-colors duration-500 ${
                    step.status === "completed"
                      ? "bg-green-400 dark:bg-green-500"
                      : "bg-gray-200 dark:bg-gray-700"
                  }`}
                />
              )}
            </div>

            {/* Content */}
            <div className="pb-8 pt-0.5">
              <div className="flex items-center gap-2">
                <h4
                  className={`font-semibold ${
                    step.status === "running"
                      ? "text-primary-600 dark:text-primary-400"
                      : step.status === "completed"
                        ? "text-green-700 dark:text-green-400"
                        : step.status === "failed"
                          ? "text-red-600 dark:text-red-400"
                          : step.status === "skipped"
                            ? "text-gray-400 line-through dark:text-gray-500"
                            : "text-gray-500 dark:text-gray-400"
                  }`}
                >
                  {t(`analysis.agents.${step.agent}`)}
                </h4>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    step.status === "running"
                      ? "bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300"
                      : step.status === "completed"
                        ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                        : step.status === "failed"
                          ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                          : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
                  }`}
                >
                  {t(`analysis.status.${step.status}`)}
                </span>
              </div>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {step.description}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function StatusIndicator({ status }: { status: string }) {
  if (status === "completed") {
    return (
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-500 text-white shadow-sm">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
        </svg>
      </div>
    );
  }

  if (status === "running") {
    return (
      <div className="relative flex h-8 w-8 items-center justify-center">
        <div className="absolute inset-0 animate-pulse-ring rounded-full bg-primary-400/40" />
        <div className="relative h-8 w-8 rounded-full bg-primary-500 shadow-sm">
          <div className="absolute inset-0 flex items-center justify-center">
            <svg className="h-4 w-4 animate-spin text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        </div>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-500 text-white shadow-sm">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    );
  }

  if (status === "skipped") {
    return (
      <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-dashed border-gray-300 bg-gray-50 dark:border-gray-600 dark:bg-gray-800">
        <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </div>
    );
  }

  // pending
  return (
    <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-gray-300 bg-white dark:border-gray-600 dark:bg-gray-800">
      <div className="h-2 w-2 rounded-full bg-gray-300 dark:bg-gray-600" />
    </div>
  );
}
