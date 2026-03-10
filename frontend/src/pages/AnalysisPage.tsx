import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAnalysisStore } from "@/store/analysisStore";
import AgentProgress from "@/components/AgentProgress";

export default function AnalysisPage() {
  const { runId } = useParams<{ runId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const trackRun = useAnalysisStore((s) => s.trackRun);
  const run = useAnalysisStore((s) => (runId ? s.runs[runId] : undefined));

  useEffect(() => {
    if (runId) trackRun(runId);
  }, [runId, trackRun]);

  const steps = run?.steps ?? [];
  const done = run?.done ?? false;
  const error = run?.error ?? null;
  const result = run?.result ?? null;

  const activeSteps = steps.filter((s) => s.status !== "skipped");
  const completedSteps = activeSteps.filter((s) => s.status === "completed");
  const progress = activeSteps.length > 0
    ? completedSteps.length / activeSteps.length
    : 0;

  // All active (non-skipped) agents must be completed before showing the report button
  const allCompleted = activeSteps.length > 0 && activeSteps.every((s) => s.status === "completed");

  return (
    <div className="mx-auto max-w-2xl animate-slide-up">
      {/* Header */}
      <div className="mb-10 text-center">
        {done && !error ? (
          <>
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
              <svg className="h-8 w-8 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <h1 className="section-title text-green-700 dark:text-green-400">
              {t("analysis.completed")}
            </h1>
          </>
        ) : error ? (
          <>
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900">
              <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="section-title text-red-700 dark:text-red-400">
              {t("analysis.failed")}
            </h1>
            <p className="section-subtitle text-red-500">{error}</p>
          </>
        ) : (
          <>
            <h1 className="section-title">{t("analysis.title")}</h1>
            <p className="section-subtitle">{t("analysis.subtitle")}</p>
          </>
        )}
      </div>

      {/* Progress bar */}
      {!done && (
        <div className="mb-8">
          <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-300">
            <span>{Math.round(progress * 100)}%</span>
            <span>{t("analysis.estimatedTime")}: ~{Math.max(1, Math.round((1 - progress) * 3))} min</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
            <div
              className="h-full rounded-full bg-gradient-to-r from-primary-500 to-violet-500 transition-all duration-700 ease-out"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Agent pipeline */}
      <div className="card">
        <AgentProgress steps={steps} />
      </div>

      {/* Actions */}
      {done && !error && allCompleted && result && (
        <div className="mt-8 animate-slide-up">
          <button
            onClick={() => navigate(`/report/${runId}`)}
            className="btn-primary w-full text-base"
          >
            {t("analysis.viewReport")}
          </button>
        </div>
      )}

      {error && (
        <div className="mt-8 flex gap-3">
          <button onClick={() => navigate("/creator")} className="btn-secondary flex-1">
            {t("common.back")}
          </button>
        </div>
      )}
    </div>
  );
}
