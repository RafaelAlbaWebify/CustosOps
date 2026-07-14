import { expect, test } from "@playwright/test";

const WORKSPACES = [
  { id: "overview", label: "Overview" },
  { id: "endpoint", label: "Endpoint" },
  { id: "dns", label: "DNS Hygiene" },
  { id: "app-log", label: "App Logs" },
  { id: "windows-events", label: "Windows Events" },
  { id: "iis", label: "IIS/Application" },
  { id: "reports", label: "Reports" },
  { id: "redaction", label: "Redaction" },
  { id: "run-history", label: "Run History" },
  { id: "archive", label: "Archive" }
] as const;

test("CustosOps loads with a healthy backend and no browser errors", async ({ page, request }) => {
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

  const healthResponse = await request.get("http://127.0.0.1:8000/api/health");
  expect(healthResponse.ok()).toBeTruthy();

  await page.goto("/#overview", { waitUntil: "networkidle" });

  await expect(page.getByText("Overview", { exact: true }).first()).toBeVisible();
  await expect(page.locator("body")).toContainText("CustosOps");

  await page.screenshot({ path: "test-results/workspaces/overview.png", fullPage: true });

  expect(failedRequests, `Failed browser requests:\n${failedRequests.join("\n")}`).toEqual([]);
  expect(consoleErrors, `Browser console errors:\n${consoleErrors.join("\n")}`).toEqual([]);
});

test("all CustosOps workspaces render without browser or network failures", async ({ page }) => {
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

  for (const workspace of WORKSPACES) {
    await page.goto(`/#${workspace.id}`, { waitUntil: "networkidle" });
    await expect(page).toHaveURL(new RegExp(`#${workspace.id}$`));
    await expect(page.locator("body")).toContainText("CustosOps");
    await expect(page.getByText(workspace.label, { exact: true }).first()).toBeVisible();
    await page.screenshot({
      path: `test-results/workspaces/${workspace.id}.png`,
      fullPage: true
    });
  }

  expect(failedRequests, `Failed browser requests:\n${failedRequests.join("\n")}`).toEqual([]);
  expect(consoleErrors, `Browser console errors:\n${consoleErrors.join("\n")}`).toEqual([]);
});
