import { QueryClient } from "@tanstack/react-query";

export const QUERY_DEFAULTS = {
  staleTimeMs: 60_000,
  gcTimeMs: 300_000,
  retry: 1,
} as const;

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: QUERY_DEFAULTS.staleTimeMs,
        gcTime: QUERY_DEFAULTS.gcTimeMs,
        retry: QUERY_DEFAULTS.retry,
        refetchOnWindowFocus: false,
      },
    },
  });
}
