import { expect, test } from "@playwright/test";

import { expectNoAccessibilityViolations, gotoAndSettle } from "./helpers";

test("exact search stays lexical and flows into ayah detail", async ({ page }) => {
  await gotoAndSettle(page, "/search");

  await expect(
    page.getByRole("heading", {
      name: "Search the text precisely without blurring what matched",
    }),
  ).toBeVisible();
  await expectNoAccessibilityViolations(page);

  await page.getByRole("searchbox", { name: "Exact query" }).fill("clear evidence");
  await page.getByLabel("Revelation place").selectOption("madinah");

  const matchingHeadings = page.getByRole("heading", { name: "Al-Bayyinah" });
  await expect(
    page.getByText("Showing 2 exact matches from the bundled sample."),
  ).toBeVisible();
  await expect(matchingHeadings).toHaveCount(2);
  await expect(
    page.locator(".search-result").first().locator(".search-context"),
  ).toContainText("Context after");

  await page
    .locator(".search-result")
    .first()
    .getByRole("link", { name: "Open ayah detail" })
    .click();

  await expect(page).toHaveURL(/\/ayah\/98\/[12]$/);
  await expect(
    page.getByRole("heading", { name: /Ayah 98:[12]/ }),
  ).toBeVisible();
});

test("semantic search keeps guardrails and private bookmark flow", async ({
  page,
}) => {
  await gotoAndSettle(page, "/semantic");

  await expect(
    page.getByText(
      "QuranKit's semantic search is intended to help readers discover related passages by similarity signals. It must never be presented as tafsir, fatwa, or a religious ruling.",
    ),
  ).toBeVisible();
  await expectNoAccessibilityViolations(page);

  await page
    .getByRole("checkbox", { name: /Show similarity scores for this preview/i })
    .check();
  await page.getByRole("searchbox", { name: "Similarity query" }).fill("evil");
  await page.getByLabel("Result limit").selectOption("3");
  await page.getByLabel("Surah filter").selectOption("113");

  await expect(
    page.getByText(
      "Showing 3 related passages from the bundled sample. Scores are approximate preview cues only.",
    ),
  ).toBeVisible();
  await expect(page.getByText(/Score \d+%/)).toHaveCount(3);

  const firstResult = page.locator(".search-result").first();
  const reference = (await firstResult.locator(".surah-chip").textContent())?.trim();

  expect(reference).toMatch(/^113:\d$/);

  await firstResult.getByRole("button", { name: "Bookmark" }).click();
  await expect(firstResult).toContainText(`${reference} saved to private bookmarks.`);

  await gotoAndSettle(page, "/bookmarks");

  const bookmarkCards = page.locator(".study-card-list .ayah-card");
  await expect(bookmarkCards).toHaveCount(1);
  await expect(bookmarkCards.first()).toContainText(reference ?? "");
  await expectNoAccessibilityViolations(page);
});

test("reader actions update progress across routes and reloads", async ({ page }) => {
  await gotoAndSettle(page, "/surah/112");

  await expect(
    page.getByRole("heading", { name: "Al-Ikhlas", exact: true }),
  ).toBeVisible();
  await expectNoAccessibilityViolations(page);

  await page.getByRole("button", { name: "Mark read" }).first().click();
  await expect(
    page.getByText("112:1 saved as the latest private checkpoint."),
  ).toBeVisible();

  await page.getByRole("button", { name: "Hide translation" }).click();
  await expect(page.getByText("Allah, the Eternal Refuge.")).not.toBeVisible();

  await gotoAndSettle(page, "/progress");

  await expect(page.locator(".study-stat-grid")).toContainText("1 of 47 ayahs");
  await expect(page.locator(".study-stat-grid")).toContainText("112:1");

  await page.reload({ waitUntil: "domcontentloaded" });
  await expect(page.locator(".study-stat-grid")).toContainText("1 of 47 ayahs");
  await expect(page.locator(".study-stat-grid")).toContainText("112:1");
  await expectNoAccessibilityViolations(page);
});
