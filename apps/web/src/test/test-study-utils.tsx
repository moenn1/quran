import type { ReactElement } from "react";

import { render } from "@testing-library/react";

import { StudyStateProvider } from "@/components/study-state-provider";
import { STUDY_STORAGE_KEY, type StudySnapshot } from "@/lib/study-data";

export function renderWithStudyState(
  ui: ReactElement,
  snapshot?: StudySnapshot,
) {
  window.localStorage.clear();

  if (snapshot) {
    window.localStorage.setItem(STUDY_STORAGE_KEY, JSON.stringify(snapshot));
  }

  return render(<StudyStateProvider>{ui}</StudyStateProvider>);
}
