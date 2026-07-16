import { readFile } from "node:fs/promises";
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

const ANALYST_NOTE = "Validate the affected endpoint, authentication context, and dependency timeline before escalation.";

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

function navigationButton(page: import("@playwright/test").Page, label: string) {
  return page.getByRole("button", { name: new RegExp(`\\b${label.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")}$`) });
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

test("Overview is readable at 1280x720 without horizontal clipping", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto("/#overview", { waitUntil: "networkidle" });

  await expect(page.getByRole("heading", { name: "Findings by Severity" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Evidence coverage" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Good vs risk posture" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Review queue" })).toBeVisible();

  for (const severity of ["Critical", "High", "Medium", "Low", "Info"]) {
    await expect(page.locator(".dashboard-donut-legend > div > span:not(.severity-dot)", { hasText: severity })).toBeVisible();
  }

  const layout = await page.evaluate(() => {
    const viewportWidth = document.documentElement.clientWidth;
    const cards = Array.from(document.querySelectorAll<HTMLElement>(".professional-dashboard-shell .professional-card")).map((card) => {
      const rect = card.getBoundingClientRect();
      return { left: rect.left, right: rect.right, width: rect.width };
    });

    return {
      viewportWidth,
      documentScrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body.scrollWidth,
      cards
    };
  });

  expect(layout.documentScrollWidth).toBeLessThanOrEqual(layout.viewportWidth);
  expect(layout.bodyScrollWidth).toBeLessThanOrEqual(layout.viewportWidth);
  expect(layout.cards.length).toBeGreaterThan(0);

  for (const card of layout.cards) {
    expect(card.width).toBeGreaterThan(0);
    expect(card.left).toBeGreaterThanOrEqual(0);
    expect(card.right).toBeLessThanOrEqual(layout.viewportWidth + 1);
  }

  await page.screenshot({ path: "test-results/overview-1280x720.png", fullPage: true });
});

test("all CustosOps workspaces render and produce visual audit evidence", async ({ page }) => {
  const { consoleErrors, failedRequests } = captureBrowserFailures(page);

  await page.goto("/", { waitUntil: "networkidle" });

  for (const workspace of WORKSPACES) {
    const button = navigationButton(page, workspace.label);
    await expect(button).toBeVisible();
    await button.click();
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
  const reportPath = "test-results/application-log-evidence-report.md";

  await page.goto("/#app-log", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: "Application Log Evidence" })).toBeVisible();

  const logInput = page.locator('input[type="file"][accept*=".log"]');
  await logInput.setInputFiles(sampleLog);

  await expect(page.getByRole("button", { name: /Application log contains HTTP server errors/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Application log contains authentication or authorization failures/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Application log contains TLS or certificate errors/ })).toBeVisible();
  await expect(page.getByText(/\d+ findings/).first()).toBeVisible();

  await page.getByLabel("Status").selectOption("needs_follow_up");
  await page.getByLabel("Notes").fill(ANALYST_NOTE);
  await expect(page.getByLabel("Status")).toHaveValue("needs_follow_up");

  const downloadPromise = page.waitForEvent("download");
  await page.locator(".workspace-actions").getByRole("button", { name: "Markdown", exact: true }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/app.*log.*\.md$/i);
  await download.saveAs(reportPath);

  const reportContent = await readFile(reportPath, "utf-8");
  expect(reportContent).toContain("needs_follow_up");
  expect(reportContent).toContain(ANALYST_NOTE);
  expect(reportContent).toMatch(/Application log contains HTTP server errors/i);

  await expect(page.getByText("app-log markdown report created and archived.", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/soc-app-log-triage.png", fullPage: true });

  await navigationButton(page, "Archive").click();
  await expect(page).toHaveURL(/#archive$/);
  await expect(page.locator("main")).toContainText(/app.*log/i);
  await page.screenshot({ path: "test-results/soc-app-log-archive.png", fullPage: true });

  await navigationButton(page, "Run History").click();
  await expect(page).toHaveURL(/#run-history$/);
  await expect(page.locator("main")).toContainText("Application Logs");
  await page.screenshot({ path: "test-results/soc-app-log-run-history.png", fullPage: true });

  expect(failedRequests, `Failed browser requests:\n${failedRequests.join("\n")}`).toEqual([]);
  expect(consoleErrors, `Browser console errors:\n${consoleErrors.join("\n")}`).toEqual([]);
});
