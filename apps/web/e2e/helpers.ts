import AxeBuilder from "@axe-core/playwright";
import { expect, type Page } from "@playwright/test";

const STUDY_STORAGE_KEY = "qurankit.study-state.v1";

export async function gotoAndSettle(page: Page, path: string) {
  await page.goto(path, { waitUntil: "domcontentloaded" });
  await expect(page.locator("main")).toBeVisible();
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
}

export async function expectNoAccessibilityViolations(page: Page) {
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
}

export async function seedStudyState(page: Page, snapshot: object) {
  await page.addInitScript(
    ([storageKey, value]) => {
      window.localStorage.setItem(storageKey, JSON.stringify(value));
    },
    [STUDY_STORAGE_KEY, snapshot] as const,
  );
}
