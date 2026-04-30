"use client";

import type { ReactNode } from "react";
import { useState } from "react";

import { QueryClientProvider } from "@tanstack/react-query";

import { createQueryClient } from "@/lib/api/query-client";
import { StudyStateProvider } from "@/components/study-state-provider";

type AppProvidersProps = {
  children: ReactNode;
};

export function AppProviders({ children }: AppProvidersProps) {
  const [queryClient] = useState(() => createQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <StudyStateProvider>{children}</StudyStateProvider>
    </QueryClientProvider>
  );
}
