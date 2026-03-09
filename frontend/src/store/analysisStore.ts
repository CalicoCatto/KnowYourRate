import { create } from "zustand";
import { subscribeToStatus, getAnalysisResult, saveReport } from "@/api/client";
import type { AgentStep, AgentStatus, AnalysisResult, SSEEvent } from "@/types";

const DEFAULT_STEPS: AgentStep[] = [
  { agent: "creator_profile", label: "Creator Analysis", description: "Computing base pricing from CPM data and evaluating creator quality", status: "pending" },
  { agent: "market_intel", label: "Market Intelligence", description: "Analyzing deal conditions, brand intel, and comparable deals", status: "pending" },
  { agent: "debate", label: "Price Debate", description: "Bull vs Bear adversarial debate to find optimal price", status: "pending" },
  { agent: "report", label: "Report Generation", description: "Compiling final pricing strategy report", status: "pending" },
];

interface AnalysisRun {
  steps: AgentStep[];
  done: boolean;
  error: string | null;
  result: AnalysisResult | null;
}

interface AnalysisState {
  runs: Record<string, AnalysisRun>;
  trackRun: (runId: string) => void;
}

const _activeSubscriptions = new Set<string>();

function newRun(): AnalysisRun {
  return {
    steps: DEFAULT_STEPS.map((s) => ({ ...s })),
    done: false,
    error: null,
    result: null,
  };
}

/** Helper: update a single run inside state, safely handling missing entries */
function updateRun(
  state: AnalysisState,
  runId: string,
  patch: Partial<AnalysisRun>,
): AnalysisState {
  const prev = state.runs[runId] ?? newRun();
  return { ...state, runs: { ...state.runs, [runId]: { ...prev, ...patch } } };
}

export const useAnalysisStore = create<AnalysisState>()((set, get) => ({
  runs: {},

  trackRun: (runId: string) => {
    if (_activeSubscriptions.has(runId)) return;

    const existing = get().runs[runId];
    if (existing?.done) return;

    _activeSubscriptions.add(runId);

    if (!existing) {
      set((s) => updateRun(s, runId, newRun()));
    }

    const handleEvent = (evt: SSEEvent) => {
      if (evt.error) {
        set((s) => updateRun(s, runId, { error: evt.error!, done: true }));
        _activeSubscriptions.delete(runId);
        return;
      }

      if (evt.done) {
        set((s) => updateRun(s, runId, { done: true }));
        _activeSubscriptions.delete(runId);

        getAnalysisResult(runId)
          .then((result) => {
            set((s) => updateRun(s, runId, { result }));
            // Auto-save report
            saveReport(runId).catch(() => {});
          })
          .catch((err) => {
            set((s) =>
              updateRun(s, runId, {
                error: err instanceof Error ? err.message : "Failed to fetch result",
              }),
            );
          });
        return;
      }

      if (evt.agent && evt.status) {
        set((s) => {
          const run = s.runs[runId] ?? newRun();
          const steps = run.steps.map((step) =>
            step.agent === evt.agent
              ? { ...step, status: evt.status as AgentStatus }
              : step,
          );

          let done = run.done;
          let error = run.error;
          if (evt.agent === "pipeline") {
            done = true;
            _activeSubscriptions.delete(runId);
            if (evt.status === "failed") {
              error = "Analysis pipeline failed";
            }
          }

          return updateRun(s, runId, { steps, done, error });
        });
      }
    };

    subscribeToStatus(runId, handleEvent);
  },
}));
