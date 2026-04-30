import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

const toneClassNames = {
  neutral:
    "border-[color:var(--line)] bg-[color:var(--surface-strong)] text-[color:var(--accent-strong)]",
  accent:
    "border-[color:rgba(29,95,90,0.35)] bg-[color:rgba(29,95,90,0.12)] text-[color:var(--accent-strong)]",
  warm: "border-[color:rgba(139,106,63,0.28)] bg-[color:rgba(139,106,63,0.14)] text-[color:var(--warm)]",
} as const;

type FoundationChipProps = {
  children: ReactNode;
  tone?: keyof typeof toneClassNames;
};

export function FoundationChip({
  children,
  tone = "neutral",
}: FoundationChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.18em]",
        toneClassNames[tone],
      )}
    >
      {children}
    </span>
  );
}
