import { expect, test } from "@playwright/test";

const workspaces = [
  "overview",
  "endpoint",
  "dns",
  "app-log",
  "windows-events",
  "iis",
  "reports",
  "archive",
  "run-history",
  "redaction"
];

test("primary workspaces remain keyboard reachable", async ({ page }) => {
  await page.goto("/#overview");
  await expect(page.locator("body")).toBeVisible();

  const focused: string[] = [];
  for (let index = 0; index < 18; index += 1) {
    await page.keyboard.press("Tab");
    focused.push(
      await page.evaluate(() => {
        const element = document.activeElement as HTMLElement | null;
        return element ? `${element.tagName}:${element.getAttribute("aria-label") ?? element.textContent ?? ""}`.trim() : "";
      })
    );
  }

  const interactiveFocus = focused.filter((entry) => /^(A|BUTTON|INPUT|SELECT|TEXTAREA):/.test(entry));
  expect(new Set(interactiveFocus).size).toBeGreaterThan(2);
});

test("interactive controls expose accessible names", async ({ page }) => {
  await page.goto("/#overview");

  const unnamedControls = await page.locator("button, a[href], input:not([type='hidden']), select, textarea").evaluateAll((elements) =>
    elements
      .filter((element) => {
        const htmlElement = element as HTMLElement;
        if (htmlElement.hidden || htmlElement.getAttribute("aria-hidden") === "true") return false;
        const ariaLabel = htmlElement.getAttribute("aria-label")?.trim();
        const ariaLabelledBy = htmlElement.getAttribute("aria-labelledby")?.trim();
        const title = htmlElement.getAttribute("title")?.trim();
        const text = htmlElement.textContent?.trim();
        const input = htmlElement as HTMLInputElement;
        const associatedLabel = input.id ? document.querySelector(`label[for='${CSS.escape(input.id)}']`)?.textContent?.trim() : "";
        return !(ariaLabel || ariaLabelledBy || title || text || associatedLabel || input.placeholder?.trim());
      })
      .map((element) => element.outerHTML.slice(0, 240))
  );

  expect(unnamedControls, unnamedControls.join("\n")).toEqual([]);
});

test("all workspaces avoid horizontal page overflow at mobile width", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });

  for (const workspace of workspaces) {
    await page.goto(`/#${workspace}`);
    await page.waitForTimeout(250);
    const dimensions = await page.evaluate(() => ({
      viewport: window.innerWidth,
      document: document.documentElement.scrollWidth
    }));
    expect(dimensions.document, `${workspace} overflowed the viewport`).toBeLessThanOrEqual(dimensions.viewport + 1);
  }
});

test("TRACE-light visual contract remains active", async ({ page }) => {
  await page.goto("/#overview");

  const contract = await page.evaluate(() => {
    const body = getComputedStyle(document.body);
    const surfaces = [...document.querySelectorAll<HTMLElement>(".panel, .card, .metric-card")].slice(0, 12);
    const darkSurfaces = surfaces.filter((element) => {
      const match = getComputedStyle(element).backgroundColor.match(/\d+/g)?.map(Number);
      return match ? match[0] < 70 && match[1] < 80 && match[2] < 95 : false;
    }).length;
    return {
      bodyBackground: body.backgroundColor,
      darkSurfaces
    };
  });

  expect(contract.bodyBackground).not.toMatch(/rgb\((0|1?\d|2\d|3\d),\s*(0|1?\d|2\d|3\d),\s*(0|1?\d|2\d|3\d)\)/);
  expect(contract.darkSurfaces).toBe(0);
});

test("committed v1.1 visual baseline", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto("/#overview");
  await expect(page).toHaveScreenshot("custosops-overview-v1.1.png", {
    animations: "disabled",
    fullPage: true,
    maxDiffPixelRatio: 0.01
  });
});
