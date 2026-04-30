"use client";

import { useQuery } from "@tanstack/react-query";

import { FoundationChip } from "@/components/ui/foundation-chip";
import { apiClient } from "@/lib/api/client";

export function RuntimeFoundation() {
  const { data } = useQuery({
    queryKey: ["runtime-foundation", apiClient.baseUrl],
    queryFn: async () => apiClient.describeRuntime(),
    staleTime: Infinity,
  });

  if (!data) {
    return null;
  }

  return (
    <section className="surface-card surface-card--accent">
      <div className="surface-card__body flex flex-col gap-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-3">
            <p className="section-label">Application foundation</p>
            <h2 className="surface-card__title">
              Query caching and the API client are ready for live Quran data
            </h2>
            <p className="surface-card__description">
              The first usable screen stays application-focused: server
              components remain the default for read-heavy pages, and small
              client islands can rely on TanStack Query without changing the
              privacy-first study model.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 md:max-w-sm md:justify-end">
            <FoundationChip tone="accent">TanStack Query ready</FoundationChip>
            <FoundationChip tone="warm">API client ready</FoundationChip>
            <FoundationChip>Local-first study state</FoundationChip>
          </div>
        </div>

        <dl className="grid gap-4 md:grid-cols-3">
          <div className="rounded-[1rem] border border-[color:var(--line)] bg-[color:var(--surface-strong)] p-4">
            <dt className="section-label">API base URL</dt>
            <dd className="mt-3 text-base font-semibold text-[color:var(--ink)]">
              {data.baseUrl}
            </dd>
            <dd className="mt-2 text-sm text-[color:var(--muted)]">
              Health endpoint: {data.healthUrl}
            </dd>
          </div>
          <div className="rounded-[1rem] border border-[color:var(--line)] bg-[color:var(--surface-strong)] p-4">
            <dt className="section-label">Client cache policy</dt>
            <dd className="mt-3 text-base font-semibold text-[color:var(--ink)]">
              {Math.round(data.queryFreshnessMs / 1000)}s fresh,{" "}
              {data.queryRetryCount} retry
            </dd>
            <dd className="mt-2 text-sm text-[color:var(--muted)]">
              Cache retention: {Math.round(data.queryGcTimeMs / 1000)}s
            </dd>
          </div>
          <div className="rounded-[1rem] border border-[color:var(--line)] bg-[color:var(--surface-strong)] p-4">
            <dt className="section-label">Study data handling</dt>
            <dd className="mt-3 text-base font-semibold text-[color:var(--ink)]">
              {data.studyStorage}
            </dd>
            <dd className="mt-2 text-sm text-[color:var(--muted)]">
              {data.readerMode}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}
