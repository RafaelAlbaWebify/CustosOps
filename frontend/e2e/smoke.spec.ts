import path from "node:path";

import { expect, test } from "@playwright/test";

const WORKSPACES = [
  { label: "Overview", hash: "overview" },
  { label: "Endpoint", hash: "endpoint" },
  { label: "DNS Hygiene", hash: "dns" },
  { label: "App Logs", hash: "app-log" },
  { label: "Windows Events", hash: "windows-events" },
  { label: "IIS/Application", hash: "iis" },
  { label: "Reports", hash: "reports" },
  { label: "Redaction", hash: "redaction" },
  { label: "Run History", hash: "run-history" },
  { label: "Archive", hash: "archive" }
] as const;

function captureBrowserFailures(page: import("@playwright/test").Page) {
  const consoleErrors: string[] = [];
  const failedRequests: string[] = [];

  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });

  page.on("requestfailed", (request) => {
    failedRequests.push(`${request.method()} ${request.url()} :: ${request.failure()?.errorText ?? "unknown error"}`);
  });

  return { consoleErrors, failedRequests };
}

test("CustosOps loads with a healthy backend and no browser errors", async ({ page, request }) => {
  const { consoleErrors, failedRequests } = captureBrowserFailures(page);

  const healthResponse = await request.get("http://127.0.0.1:8000/api/health");
  expect(healthResponse.ok()).toBeTruthy();

  await page.goto("/", { waitUntil: "networkidle" });

  await expect(page.getByText("Overview", { exact: true }).first()).toBeVisible();
  await expect(page.locator("body")).toContainText("CustosOps");

  await page.screenshot({ path: "test-results/custosops-overview.png", fullPage: true });

  expect(failedRequests, `Failed browser requests:\n${failedRequests.join("\n")}`).toEqual([]);
  expect(consoleErrors, `Browser console errors:\n${consoleErrors.join("\n")}`).toEqual([]);
});

test("all CustosOps workspaces render and produce visual audit evidence", async ({ page }) => {
  const { consoleErrors, failedRequests } = captureBrowserFailures(page);

  await page.goto("/", { waitUntil: "networkidle" });

  for (const workspace of WORKSPACES) {
    const navigationButton = page.getByRole("button", { name: workspace.label, exact: true });
    await expect(navigationButton).toBeVisible();
    await navigationButton.click();
    await expect(page).toHaveURL(new RegExp(`#${workspace.hash}$`));
    await expect(page.locator("main h1")).toHaveText(workspace.label);
    await expect(page.locator("main")).not.toContainText("Backend Offline");
    await page.screenshot({
      path: `test-results/workspace-${workspace.hash}.png`,
      fullPage: true
    });
  }

  expect(failedRequests, `Failed browser requests:\n${failedRequests.join("\n")}`).toEqual([]);
  expect(consoleErrors, `Browser console errors:\n${consoleErrors.join("\n")}`).toEqual([]);
});

test("application-log evidence completes a defensive triage and reporting workflow", async ({ page }) => {
  const { consoleErrors, failedRequests } = captureBrowserFailures(page);
  const sampleLog = path.resolve("..", "samples", "app_logs", "fastapi-api-errors.log");

  await page.goto("/#app-log", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: "Application Log Evidence" })).toBeVisible();

  const logInput = page.locator('input[type="file"][accept*=".log"]');
  await logInput.setInputFiles(sampleLog);

  await expect(page.getByText("Application log contains HTTP server errors", { exact: true })).toBeVisible();
  await expect(page.getByText("Application log contains authentication or authorization failures", { exact: true })).toBeVisible();
  await expect(page.getByText("Application log contains TLS or certificate errors", { exact: true })).toBeVisible();
  await expect(page.getByText(/\d+ findings/).first()).toBeVisible();

  await page.getByLabel("Status").selectOption("needs_follow_up");
  await page.getByLabel("Notes").fill("Validate the affected endpoint, authentication context, and dependency timeline before escalation.");
  await expect(page.getByLabel("Status")).toHaveValue("needs_follow_up");

  const downloadPromise = page.waitForEvent("download");
  await page.locator(".workspace-actions").getByRole("button", { name: "Markdown", exact: true }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/app.*log.*\.md$/i);
  await download.saveAs("test-results/application-log-evidence-report.md");

  await expect(page.getByText("app-log markdown report created and archived.", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/soc-app-log-triage.png", fullPage: true });

  await page.getByRole("button", { name: "Archive", exact: true }).click();
  await expect(page).toHaveURL(/#archive$/);
  await expect(page.locator("main")).toContainText(/app.*log/i);
  await page.screenshot({ path: "test-results/soc-app-log-archive.png", fullPage: true });

  await page.getByRole("button", { name: "Run History", exact: true }).click();
  await expect(page).toHaveURL(/#run-history$/);
  await expect(page.locator("main")).toContainText("Application Logs");
  await page.screenshot({ path: "test-results/soc-app-log-run-history.png", fullPage: true });

  expect(failedRequests, `Failed browser requests:\n${failedRequests.join("\n")}`).toEqual([]);
  expect(consoleErrors, `Browser console errors:\n${consoleErrors.join("\n")}`).toEqual([]);
});
