import { create } from "zustand";
import { subscribeToStatus, getAnalysisResult } from "@/api/client";
import type { AgentStep, AgentName, AgentStatus, AnalysisResult, SSEEvent } from "@/types";

const DEFAULT_STEPS: AgentStep[] = [
  { agent: "market_data", label: "Market Research", description: "Gathering current sponsorship market data and benchmarks", status: "pending" },
  { agent: "creator_profile", label: "Creator Analysis", description: "Analyzing creator metrics, audience, and content quality", status: "pending" },
  { agent: "brand_strategy", label: "Brand Strategy", description: "Evaluating brand fit, campaign goals, and deal structure", status: "pending" },
  { agent: "debate", label: "Price Debate", description: "Agents debate fair pricing from multiple perspectives", status: "pending" },
  { agent: "report", label: "Report Generation", description: "Compiling final pricing report with recommendations", status: "pending" },
];

interface AnalysisRun {
  steps: AgentStep[];
  done: boolean;
  error: string | null;
  result: AnalysisResult | null;
}

interface AnalysisState {
  /** All tracked runs keyed by runId */
  runs: Record<string, AnalysisRun>;

  /** Start tracking a run (subscribes to SSE). Idempotent — won't re-subscribe. */
  trackRun: (runId: string) => void;

  /** Get run state (returns undefined if not tracked) */
  getRun: (runId: string) => AnalysisRun | undefined;
}

/** Active SSE cleanup functions — kept outside Zustand to avoid serialization issues */
const _activeSubscriptions = new Set<string>();

export const useAnalysisStore = create<AnalysisState>()((set, get) => ({
  runs: {},

  trackRun: (runId: string) => {
    // Already tracking this run
    if (_activeSubscriptions.has(runId)) return;

    const existing = get().runs[runId];
    if (existing?.done) return; // Already finished

    _activeSubscriptions.add(runId);

    // Initialize run state if not present
    if (!existing) {
      set((s) => ({
        runs: {
          ...s.runs,
          [runId]: {
            steps: DEFAULT_STEPS.map((s) => ({ ...s })),
            done: false,
            error: null,
            result: null,
          },
        },
      }));
    }

    const handleEvent = (evt: SSEEvent) => {
      if (evt.error) {
        set((s) => ({
          runs: {
            ...s.runs,
            [runId]: { ...s.runs[runId], error: evt.error!, done: true },
          },
        }));
        _activeSubscriptions.delete(runId);
        return;
      }

      if (evt.done) {
        const run = get().runs[runId];
        set((s) => ({
          runs: { ...s.runs, [runId]: { ...run, done: true } },
        }));
        _activeSubscriptions.delete(runId);

        // Fetch the full result
        getAnalysisResult(runId)
          .then((result) => {
            set((s) => ({
              runs: { ...s.runs, [runId]: { ...s.runs[runId], result } },
            }));
          })
          .catch((err) => {
            set((s) => ({
              runs: {
                ...s.runs,
                [runId]: {
                  ...s.runs[runId],
                  error: err instanceof Error ? err.message : "Failed to fetch result",
                },
              },
            }));
          });
        return;
      }

      if (evt.agent && evt.status) {
        set((s) => {
          const run = s.runs[runId];
          if (!run) return s;

          const newSteps = run.steps.map((step) =>
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

          return {
            runs: {
              ...s.runs,
              [runId]: { ...run, steps: newSteps, done, error },
            },
          };
        });
      }
    };

    subscribeToStatus(runId, handleEvent);
  },

  getRun: (runId: string) => get().runs[runId],
}));
