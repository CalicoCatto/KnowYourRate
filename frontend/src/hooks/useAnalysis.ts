import { useCallback, useEffect, useRef, useState } from "react";
import { subscribeToStatus, getAnalysisResult } from "@/api/client";
import type {
  AgentStep,
  AgentName,
  AgentStatus,
  AnalysisResult,
  SSEEvent,
} from "@/types";

const DEFAULT_STEPS: AgentStep[] = [
  {
    agent: "market_data",
    label: "Market Research",
    description: "Gathering current sponsorship market data and benchmarks",
    status: "pending",
  },
  {
    agent: "creator_profile",
    label: "Creator Analysis",
    description: "Analyzing creator metrics, audience, and content quality",
    status: "pending",
  },
  {
    agent: "brand_strategy",
    label: "Brand Strategy",
    description: "Evaluating brand fit, campaign goals, and deal structure",
    status: "pending",
  },
  {
    agent: "debate",
    label: "Price Debate",
    description: "Agents debate fair pricing from multiple perspectives",
    status: "pending",
  },
  {
    agent: "report",
    label: "Report Generation",
    description: "Compiling final pricing report with recommendations",
    status: "pending",
  },
];

export function useAnalysis(runId: string | undefined) {
  const [steps, setSteps] = useState<AgentStep[]>(
    DEFAULT_STEPS.map((s) => ({ ...s })),
  );
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  const handleEvent = useCallback((evt: SSEEvent) => {
    if (evt.error) {
      setError(evt.error);
      setDone(true);
      return;
    }

    if (evt.done) {
      setDone(true);
      return;
    }

    if (evt.agent && evt.status) {
      setSteps((prev) =>
        prev.map((step) => {
          if (step.agent === evt.agent) {
            return { ...step, status: evt.status as AgentStatus };
          }
          return step;
        }),
      );

      // When pipeline itself signals completed/failed
      if (evt.agent === "pipeline") {
        setDone(true);
        if (evt.status === "failed") {
          setError("Analysis pipeline failed");
        }
      }
    }
  }, []);

  useEffect(() => {
    if (!runId) return;

    // Reset state
    setSteps(DEFAULT_STEPS.map((s) => ({ ...s })));
    setDone(false);
    setError(null);
    setResult(null);

    cleanupRef.current = subscribeToStatus(runId, handleEvent);

    return () => {
      cleanupRef.current?.();
    };
  }, [runId, handleEvent]);

  // Fetch result once done
  useEffect(() => {
    if (!done || !runId || error) return;

    getAnalysisResult(runId)
      .then(setResult)
      .catch((err) => {
        setError(
          err instanceof Error ? err.message : "Failed to fetch result",
        );
      });
  }, [done, runId, error]);

  const currentAgent: AgentName | null =
    steps.find((s) => s.status === "running")?.agent ?? null;

  const progress =
    steps.filter((s) => s.status === "completed").length / steps.length;

  return { steps, currentAgent, progress, done, error, result };
}
