import { expect, test, type Page, type TestInfo } from "@playwright/test";

const actualWindows = [
  { name: "user-wide-1650x927", width: 1650, height: 927 },
  { name: "user-medium-1120x1033", width: 1120, height: 1033 }
];

async function attach(page: Page, testInfo: TestInfo, name: string) {
  const screenshot = await page.screenshot({ animations: "disabled", fullPage: true });
  await testInfo.attach(name, { body: screenshot, contentType: "image/png" });
}

async function collectCardOverlaps(page: Page) {
  return page.evaluate(() => {
    const problems: string[] = [];
    const visible = (element: Element) => {
      const node = element as HTMLElement;
      const style = getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
    };
    const overlapArea = (left: DOMRect, right: DOMRect) => {
      const width = Math.max(0, Math.min(left.right, right.right) - Math.max(left.left, right.left));
      const height = Math.max(0, Math.min(left.bottom, right.bottom) - Math.max(left.top, right.top));
      return width * height;
    };
    const groups = [
      ".professional-dashboard-shell",
      ".professional-dashboard-grid",
      ".professional-lower-grid",
      ".professional-kpi-grid"
    ];

    for (const selector of groups) {
      for (const group of document.querySelectorAll<HTMLElement>(selector)) {
        const children = [...group.children].filter(visible);
        for (let leftIndex = 0; leftIndex < children.length; leftIndex += 1) {
          for (let rightIndex = leftIndex + 1; rightIndex < children.length; rightIndex += 1) {
            const area = overlapArea(children[leftIndex].getBoundingClientRect(), children[rightIndex].getBoundingClientRect());
            if (area > 2) {
              problems.push(`${selector}: child ${leftIndex + 1} overlaps child ${rightIndex + 1} by ${Math.round(area)}px2`);
            }
          }
        }
      }
    }

    const shell = document.querySelector<HTMLElement>(".professional-dashboard-shell");
    if (shell) {
      const style = getComputedStyle(shell);
      if (style.gridTemplateRows.split(" ").some((track) => track.endsWith("px"))) {
        problems.push(`shell uses fixed grid rows: ${style.gridTemplateRows}`);
      }
    }

    return problems;
  });
}

for (const viewport of actualWindows) {
  test(`Overview remains contained at ${viewport.name}`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto("/#overview");
    await expect(page.locator(".professional-dashboard-shell")).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(500);

    const problems = await collectCardOverlaps(page);
    await attach(page, testInfo, viewport.name);
    expect(problems, problems.join("\n")).toEqual([]);
  });
}
