import axios from "axios";
import type {
  ProviderInfo,
  ProviderSetup,
  ProviderResponse,
  TestResult,
  CreatorLookupRequest,
  CreatorProfile,
  AnalysisRequest,
  AnalysisStatus,
  AnalysisResult,
  ReportResponse,
  ReportList,
  SSEEvent,
} from "@/types";

const api = axios.create({ baseURL: "/api" });

/* ------------------------------------------------------------------ */
/*  Settings / Provider                                                */
/* ------------------------------------------------------------------ */

export async function getProviders(): Promise<ProviderInfo[]> {
  const { data } = await api.get<ProviderInfo[]>("/settings/providers");
  return data;
}

export async function saveProvider(
  provider: string,
  apiKey: string,
  model?: string | null,
): Promise<ProviderResponse> {
  const body: ProviderSetup = { provider, api_key: apiKey, model };
  const { data } = await api.post<ProviderResponse>("/settings/provider", body);
  return data;
}

export async function getProvider(): Promise<ProviderResponse | null> {
  const { data } = await api.get<ProviderResponse | null>("/settings/provider");
  return data;
}

export async function deleteProvider(): Promise<void> {
  await api.delete("/settings/provider");
}

export async function testProvider(
  provider: string,
  apiKey: string,
  model?: string | null,
): Promise<TestResult> {
  const body: ProviderSetup = { provider, api_key: apiKey, model };
  const { data } = await api.post<TestResult>("/settings/provider/test", body);
  return data;
}

/* ------------------------------------------------------------------ */
/*  Creators                                                           */
/* ------------------------------------------------------------------ */

export async function lookupCreator(
  platform: string,
  channelUrl: string,
): Promise<CreatorProfile> {
  const body: CreatorLookupRequest = { platform, channel_url: channelUrl };
  const { data } = await api.post<CreatorProfile>("/creators/lookup", body);
  return data;
}

/* ------------------------------------------------------------------ */
/*  Analysis                                                           */
/* ------------------------------------------------------------------ */

export async function startAnalysis(
  request: AnalysisRequest,
): Promise<AnalysisStatus> {
  const { data } = await api.post<AnalysisStatus>("/analysis/run", request);
  return data;
}

export async function getAnalysisResult(
  runId: string,
): Promise<AnalysisResult> {
  const { data } = await api.get<AnalysisResult>(
    `/analysis/${runId}/result`,
  );
  return data;
}

/**
 * Subscribe to analysis progress via Server-Sent Events.
 * Returns a cleanup function that closes the EventSource.
 */
export function subscribeToStatus(
  runId: string,
  onEvent: (event: SSEEvent) => void,
): () => void {
  const es = new EventSource(`/api/analysis/${runId}/status`);

  es.onmessage = (msg) => {
    try {
      const parsed = JSON.parse(msg.data as string) as SSEEvent;
      onEvent(parsed);
      if (parsed.done || parsed.error) {
        es.close();
      }
    } catch {
      // ignore parse errors
    }
  };

  es.onerror = () => {
    es.close();
  };

  return () => es.close();
}

/* ------------------------------------------------------------------ */
/*  Reports                                                            */
/* ------------------------------------------------------------------ */

export async function getReports(): Promise<ReportList[]> {
  const { data } = await api.get<ReportList[]>("/reports");
  return data;
}

export async function getReport(id: string): Promise<ReportResponse> {
  const { data } = await api.get<ReportResponse>(`/reports/${id}`);
  return data;
}

export async function deleteReport(id: string): Promise<void> {
  await api.delete(`/reports/${id}`);
}

export async function saveReport(
  analysisRunId: string,
): Promise<ReportResponse> {
  const { data } = await api.post<ReportResponse>("/reports", {
    analysis_run_id: analysisRunId,
  });
  return data;
}
