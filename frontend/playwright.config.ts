import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: {
    timeout: 10_000
  },
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI
    ? [["html", { outputFolder: "playwright-report", open: "never" }], ["list"]]
    : [["list"]],
  use: {
    baseURL: process.env.CUSTOSOPS_BASE_URL ?? "http://127.0.0.1:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure"
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ]
});
