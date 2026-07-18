import { expect, test, type Page, type TestInfo } from "@playwright/test";

const desktopViewports = [
  { name: "1280x720", width: 1280, height: 720 },
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1920x1080", width: 1920, height: 1080 }
];

const expectedNavigationLabels = [
  "Overview",
  "Endpoint",
  "DNS Hygiene",
  "App Logs",
  "Windows Events",
  "IIS/Application",
  "Reports",
  "Redaction",
  "Run History",
  "Archive"
];

type LayoutProblem = {
  selector: string;
  kind: string;
  detail: string;
};

async function attachFullPageScreenshot(page: Page, testInfo: TestInfo, name: string) {
  const screenshot = await page.screenshot({
    animations: "disabled",
    fullPage: true
  });
  await testInfo.attach(name, { body: screenshot, contentType: "image/png" });
}

async function collectLayoutProblems(page: Page): Promise<LayoutProblem[]> {
  return page.evaluate(() => {
    const problems: LayoutProblem[] = [];
    const visible = (element: Element) => {
      const node = element as HTMLElement;
      const style = getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
    };

    const describe = (element: Element) => {
      const node = element as HTMLElement;
      const classes = [...node.classList].join(".");
      return `${node.tagName.toLowerCase()}${classes ? `.${classes}` : ""}`;
    };

    const overlapArea = (left: DOMRect, right: DOMRect) => {
      const width = Math.max(0, Math.min(left.right, right.right) - Math.max(left.left, right.left));
      const height = Math.max(0, Math.min(left.bottom, right.bottom) - Math.max(left.top, right.top));
      return width * height;
    };

    for (const label of document.querySelectorAll<HTMLElement>(".workspace-nav .nav-label")) {
      if (!visible(label)) continue;
      const style = getComputedStyle(label);
      if (label.scrollWidth > label.clientWidth + 1) {
        problems.push({
          selector: describe(label),
          kind: "truncated-navigation-label",
          detail: `${label.textContent?.trim() ?? ""}: scrollWidth=${label.scrollWidth}, clientWidth=${label.clientWidth}`
        });
      }
      if (style.textOverflow === "ellipsis" || style.whiteSpace === "nowrap") {
        problems.push({
          selector: describe(label),
          kind: "unsafe-navigation-text-style",
          detail: `${label.textContent?.trim() ?? ""}: textOverflow=${style.textOverflow}, whiteSpace=${style.whiteSpace}`
        });
      }
    }

    const collisionRows = [
      ".dashboard-donut-legend > div",
      ".module-health-list > div",
      ".module-score-row",
      ".dashboard-priority-row"
    ];

    for (const rowSelector of collisionRows) {
      for (const row of document.querySelectorAll<HTMLElement>(rowSelector)) {
        if (!visible(row)) continue;
        const children = [...row.children].filter(visible);
        for (let leftIndex = 0; leftIndex < children.length; leftIndex += 1) {
          for (let rightIndex = leftIndex + 1; rightIndex < children.length; rightIndex += 1) {
            const left = children[leftIndex].getBoundingClientRect();
            const right = children[rightIndex].getBoundingClientRect();
            const area = overlapArea(left, right);
            if (area > 2) {
              problems.push({
                selector: rowSelector,
                kind: "child-overlap",
                detail: `${describe(children[leftIndex])} overlaps ${describe(children[rightIndex])} by ${Math.round(area)}px2`
              });
            }
          }
        }
      }
    }

    const clippingSelectors = [
      ".professional-dashboard-shell",
      ".professional-card",
      ".dashboard-priority-list",
      ".dashboard-priority-row",
      ".dashboard-donut-legend",
      ".module-health-list"
    ];

    for (const selector of clippingSelectors) {
      for (const element of document.querySelectorAll<HTMLElement>(selector)) {
        if (!visible(element)) continue;
        const style = getComputedStyle(element);
        const clipsVertically = ["hidden", "clip"].includes(style.overflowY);
        if (clipsVertically && element.scrollHeight > element.clientHeight + 1) {
          problems.push({
            selector,
            kind: "vertical-content-clipping",
            detail: `scrollHeight=${element.scrollHeight}, clientHeight=${element.clientHeight}`
          });
        }
      }
    }

    for (const list of document.querySelectorAll<HTMLElement>(".dashboard-priority-list")) {
      if (!visible(list)) continue;
      const listRect = list.getBoundingClientRect();
      for (const row of list.querySelectorAll<HTMLElement>(".dashboard-priority-row")) {
        if (!visible(row)) continue;
        const rowRect = row.getBoundingClientRect();
        if (rowRect.bottom > listRect.bottom + 1 || rowRect.right > listRect.right + 1) {
          problems.push({
            selector: ".dashboard-priority-row",
            kind: "row-outside-priority-panel",
            detail: `row=${JSON.stringify({ right: rowRect.right, bottom: rowRect.bottom })}, panel=${JSON.stringify({ right: listRect.right, bottom: listRect.bottom })}`
          });
        }
      }
    }

    const documentWidth = document.documentElement.scrollWidth;
    if (documentWidth > window.innerWidth + 1) {
      problems.push({
        selector: "document.documentElement",
        kind: "horizontal-page-overflow",
        detail: `scrollWidth=${documentWidth}, viewport=${window.innerWidth}`
      });
    }

    return problems;
  });
}

test.describe("multi-viewport visual layout audit", () => {
  for (const viewport of desktopViewports) {
    test(`Overview has no truncation, overlap, or clipping at ${viewport.name}`, async ({ page }, testInfo) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto("/#overview");
      await expect(page.locator(".professional-dashboard-shell")).toBeVisible();
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(400);

      const labels = await page.locator(".workspace-nav .nav-label").allTextContents();
      expect(labels.map((label) => label.trim())).toEqual(expectedNavigationLabels);

      const problems = await collectLayoutProblems(page);
      await attachFullPageScreenshot(page, testInfo, `overview-${viewport.name}`);
      expect(problems, JSON.stringify(problems, null, 2)).toEqual([]);
    });
  }

  test("all desktop workspaces keep readable navigation and remain inside the viewport", async ({ page }, testInfo) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto("/#overview");
    await expect(page.locator(".workspace-nav")).toBeVisible();

    const buttons = page.locator(".workspace-nav button");
    await expect(buttons).toHaveCount(expectedNavigationLabels.length);

    for (let index = 0; index < expectedNavigationLabels.length; index += 1) {
      await buttons.nth(index).click();
      await page.waitForTimeout(150);
      const label = buttons.nth(index).locator(".nav-label");
      await expect(label).toHaveText(expectedNavigationLabels[index]);
      const dimensions = await page.evaluate(() => ({
        viewport: window.innerWidth,
        document: document.documentElement.scrollWidth
      }));
      expect(dimensions.document, `${expectedNavigationLabels[index]} overflowed horizontally`).toBeLessThanOrEqual(dimensions.viewport + 1);
    }

    await attachFullPageScreenshot(page, testInfo, "all-workspaces-final-state-1920x1080");
  });
});
