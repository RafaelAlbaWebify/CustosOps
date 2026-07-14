import { expect, test } from "@playwright/test";

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

  await page.goto("/", { waitUntil: "networkidle" });

  await expect(page.getByText("Overview", { exact: true }).first()).toBeVisible();
  await expect(page.locator("body")).toContainText("CustosOps");

  await page.screenshot({ path: "test-results/custosops-overview.png", fullPage: true });

  expect(failedRequests, `Failed browser requests:\n${failedRequests.join("\n")}`).toEqual([]);
  expect(consoleErrors, `Browser console errors:\n${consoleErrors.join("\n")}`).toEqual([]);
});
