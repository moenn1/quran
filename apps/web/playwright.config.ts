import { defineConfig, devices } from "@playwright/test";

const baseURL = "http://127.0.0.1:3101";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  outputDir: "./test-results",
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  reporter: process.env.CI
    ? [["list"], ["html", { open: "never" }]]
    : "list",
  use: {
    baseURL,
    colorScheme: "light",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    viewport: { width: 1440, height: 1024 },
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },
  ],
  webServer: {
    command:
      "npm run dev --workspace @qurankit/web -- --hostname 127.0.0.1 --port 3101",
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
