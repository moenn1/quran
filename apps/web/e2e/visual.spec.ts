import { expect, test } from "@playwright/test";

import { gotoAndSettle } from "./helpers";

test("exact search remains readable on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await gotoAndSettle(page, "/search");

  await expect(page.locator(".reader-layout")).toHaveScreenshot("exact-search-mobile.png", {
    animations: "disabled",
    caret: "initial",
    maxDiffPixelRatio: 0.015,
    scale: "css",
  });
});

test("surah reader keeps Quran text central on desktop", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1100 });
  await gotoAndSettle(page, "/surah/112");

  await expect(page.locator("main")).toHaveScreenshot("surah-reader-desktop.png", {
    animations: "disabled",
    caret: "initial",
    scale: "css",
  });
});
