import {
  createApiClient,
  getRuntimeSetup,
  resolveApiBaseUrl,
} from "@/lib/api/client";

describe("api client", () => {
  it("normalizes configured base URLs", () => {
    expect(resolveApiBaseUrl("https://api.example.test/base/")).toBe(
      "https://api.example.test/base",
    );
    expect(resolveApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("builds endpoint URLs from the configured base", () => {
    const client = createApiClient({
      baseUrl: "https://api.example.test/base/",
      fetchImpl: fetch,
    });

    expect(client.buildUrl("/health")).toBe(
      "https://api.example.test/base/health",
    );
    expect(client.buildUrl("surahs/1")).toBe(
      "https://api.example.test/base/surahs/1",
    );
  });

  it("describes the web runtime setup for the app shell", () => {
    const runtime = getRuntimeSetup("https://api.example.test");

    expect(runtime.baseUrl).toBe("https://api.example.test");
    expect(runtime.healthUrl).toBe("https://api.example.test/health");
    expect(runtime.queryFreshnessMs).toBe(60_000);
    expect(runtime.queryRetryCount).toBe(1);
    expect(runtime.studyStorage).toMatch(/Local-first/);
  });
});
