import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { AgentOutputs, FinalReport } from "@/types";

interface Props {
  agentOutputs: AgentOutputs | null;
  finalReport: FinalReport;
}

interface SectionProps {
  title: string;
  step: number;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
  skipped?: boolean;
}

function Section({ title, step, icon, children, defaultOpen = false, skipped = false }: SectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  if (skipped) {
    return (
      <div className="card overflow-hidden opacity-50">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500">
            {icon}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-400 dark:bg-gray-800 dark:text-gray-500">
                Step {step}
              </span>
              <h3 className="font-semibold text-gray-400 line-through dark:text-gray-500">{title}</h3>
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-400 dark:bg-gray-800">
                Skipped (Fast Track)
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-4 text-left"
      >
        {/* Step badge */}
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300">
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500 dark:bg-gray-800 dark:text-gray-400">
              Step {step}
            </span>
            <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
          </div>
        </div>
        <svg
          className={`h-5 w-5 flex-shrink-0 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>
      {open && <div className="mt-4 border-t border-gray-100 pt-4 dark:border-gray-800">{children}</div>}
    </div>
  );
}

function RenderData({ data }: { data: unknown }) {
  if (data == null) {
    return <p className="text-sm italic text-gray-400">No data available</p>;
  }

  if (typeof data === "string") {
    return (
      <p className="whitespace-pre-line leading-relaxed text-gray-700 dark:text-gray-300">
        {data}
      </p>
    );
  }

  if (typeof data === "number" || typeof data === "boolean") {
    return <p className="text-sm text-gray-700 dark:text-gray-300">{String(data)}</p>;
  }

  if (typeof data === "object" && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>;
    return (
      <div className="space-y-4">
        {Object.entries(obj).map(([key, value]) => (
          <div key={key}>
            <h4 className="mb-1 text-sm font-semibold text-gray-600 dark:text-gray-300">
              {formatKey(key)}
            </h4>
            {typeof value === "string" ? (
              <p className="whitespace-pre-line text-sm leading-relaxed text-gray-700 dark:text-gray-300">
                {value}
              </p>
            ) : typeof value === "number" || typeof value === "boolean" ? (
              <p className="text-sm text-gray-700 dark:text-gray-300">{String(value)}</p>
            ) : Array.isArray(value) ? (
              <ul className="list-inside list-disc space-y-1 text-sm text-gray-700 dark:text-gray-300">
                {value.map((item, i) => (
                  <li key={i}>
                    {typeof item === "object" ? (
                      <div className="ml-4 mt-1 rounded-lg bg-gray-50 p-3 dark:bg-gray-800/50">
                        <RenderData data={item} />
                      </div>
                    ) : (
                      String(item)
                    )}
                  </li>
                ))}
              </ul>
            ) : value != null ? (
              <div className="ml-2 rounded-lg bg-gray-50 p-3 dark:bg-gray-800/50">
                <RenderData data={value} />
              </div>
            ) : null}
          </div>
        ))}
      </div>
    );
  }

  return <pre className="overflow-x-auto text-xs text-gray-600 dark:text-gray-400">{JSON.stringify(data, null, 2)}</pre>;
}

function formatKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function DetailedAnalysis({ agentOutputs, finalReport }: Props) {
  const { t } = useTranslation();

  const hasMarketIntel = agentOutputs?.market_intel != null || agentOutputs?.market_data != null;
  const hasDebate = agentOutputs?.debate_result != null;

  return (
    <div className="space-y-4">
      {/* Analysis chain header */}
      <div className="card bg-gradient-to-r from-primary-50 to-violet-50 dark:from-primary-950/30 dark:to-violet-950/30">
        <div className="flex items-center gap-3">
          <svg className="h-6 w-6 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">
              {t("report.detailedTitle")}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t("report.detailedSubtitle")}
            </p>
          </div>
        </div>
      </div>

      {/* Step 1: Creator Analysis (always runs) */}
      <Section
        title={t("report.detailed.creatorAnalysis")}
        step={1}
        defaultOpen
        icon={
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
        }
      >
        <RenderData data={agentOutputs?.creator_analysis} />
      </Section>

      {/* Step 2: Market Intelligence */}
      <Section
        title={t("report.detailed.marketIntel")}
        step={2}
        skipped={!hasMarketIntel}
        icon={
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
          </svg>
        }
      >
        <RenderData data={agentOutputs?.market_intel ?? agentOutputs?.market_data} />
      </Section>

      {/* Step 3: Price Debate */}
      <Section
        title={t("report.detailed.debate")}
        step={3}
        skipped={!hasDebate}
        icon={
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
          </svg>
        }
      >
        <RenderData data={agentOutputs?.debate_result} />
      </Section>

      {/* Step 4: Final Report */}
      <Section
        title={t("report.detailed.finalReport")}
        step={4}
        icon={
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
        }
      >
        <RenderData data={finalReport} />
      </Section>
    </div>
  );
}
