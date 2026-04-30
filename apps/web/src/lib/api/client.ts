import { QUERY_DEFAULTS } from "@/lib/api/query-client";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export type ApiClientOptions = {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
};

export type RuntimeSetup = {
  baseUrl: string;
  healthUrl: string;
  queryFreshnessMs: number;
  queryGcTimeMs: number;
  queryRetryCount: number;
  readerMode: string;
  studyStorage: string;
};

export function resolveApiBaseUrl(baseUrl?: string) {
  const candidate = baseUrl?.trim() || DEFAULT_API_BASE_URL;
  return candidate.replace(/\/+$/, "");
}

export class ApiClient {
  readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;

  constructor({ baseUrl, fetchImpl = fetch }: ApiClientOptions = {}) {
    this.baseUrl = resolveApiBaseUrl(baseUrl);
    this.fetchImpl = fetchImpl;
  }

  buildUrl(path: string) {
    const normalizedPath = path.replace(/^\/+/, "");
    return new URL(normalizedPath, `${this.baseUrl}/`).toString();
  }

  async getJson<T>(path: string, init: RequestInit = {}) {
    const response = await this.fetchImpl(this.buildUrl(path), {
      ...init,
      headers: {
        Accept: "application/json",
        ...init.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`QuranKit API request failed with ${response.status}`);
    }

    return (await response.json()) as T;
  }

  describeRuntime(): RuntimeSetup {
    return {
      baseUrl: this.baseUrl,
      healthUrl: this.buildUrl("/health"),
      queryFreshnessMs: QUERY_DEFAULTS.staleTimeMs,
      queryGcTimeMs: QUERY_DEFAULTS.gcTimeMs,
      queryRetryCount: QUERY_DEFAULTS.retry,
      readerMode:
        "Server components for read-heavy routes and client islands for interaction.",
      studyStorage:
        "Local-first for progress, bookmarks, notes, and reading plans.",
    };
  }
}

export function createApiClient(options: ApiClientOptions = {}) {
  return new ApiClient(options);
}

export function getRuntimeSetup(baseUrl?: string) {
  return createApiClient({ baseUrl }).describeRuntime();
}

export const apiClient = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL,
});
