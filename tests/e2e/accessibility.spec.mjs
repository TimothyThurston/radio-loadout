import AxeBuilder from "@axe-core/playwright";
import { test, expect, restoreBackup, lossFixture } from "./builder.fixture.mjs";

async function scan(page, testInfo, state) {
    const results = await new AxeBuilder({ page }).analyze();
    if (results.violations.length) {
        await testInfo.attach(`axe-${state}`, { body: JSON.stringify(results.violations, null, 2), contentType: "application/json" });
    }
    expect(results.violations, `Automated accessibility violations: ${state}`).toEqual([]);
}

test("axe checks the empty builder, advanced channels, errors and import review", async ({ page }, testInfo) => {
    await scan(page, testInfo, "empty");
    await restoreBackup(page);
    await scan(page, testInfo, "advanced");
    await page.getByRole("button", { name: "Review Compatibility", exact: true }).click();
    await expect(page.getByRole("region", { name: "CHIRP Generic CSV compatibility", exact: true })).toBeVisible();
    // Also scan a rendered error, not just hidden message markup.
    await page.getByLabel("Radio Loadout JSON backup", { exact: true }).setInputFiles({ name: "bad.json", mimeType: "application/json", buffer: Buffer.from("{broken") });
    await page.getByRole("button", { name: "Import Backup", exact: true }).click();
    await expect(page.getByRole("alert")).toContainText("not valid JSON");
    await scan(page, testInfo, "error");
    await page.getByLabel("CHIRP CSV file", { exact: true }).setInputFiles(lossFixture);
    await page.getByRole("button", { name: "Import CHIRP CSV", exact: true }).click();
    await expect(page.getByRole("button", { name: "Replace channels with reviewed import", exact: true })).toBeVisible();
    await scan(page, testInfo, "loss-review");
});

test("visible controls fit the viewport and remain reachable without clipping", async ({ page }) => {
    await restoreBackup(page);
    const widths = [page.viewportSize().width];
    if (widths[0] === 375) widths.push(320);
    for (const width of widths) {
        await page.setViewportSize({ width, height: page.viewportSize().height });
        await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
        const controls = page.locator("button, input:not([type=hidden]), select, a");
        for (const control of await controls.all()) {
            if (!(await control.isVisible())) continue;
            await control.scrollIntoViewIfNeeded();
            const geometry = await control.evaluate((element) => {
                const rect = element.getBoundingClientRect();
                const center = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
                return {
                    label: element.labels?.[0]?.textContent.trim() || element.getAttribute("aria-label") || element.textContent.trim(),
                    left: rect.left, right: rect.right, width: rect.width, height: rect.height,
                    viewport: window.innerWidth, reachable: center === element || element.contains(center),
                    clientWidth: element.clientWidth, scrollWidth: element.scrollWidth,
                };
            });
            expect(geometry.left, `${width}px: ${geometry.label} left edge`).toBeGreaterThanOrEqual(0);
            expect(geometry.right, `${width}px: ${geometry.label} right edge`).toBeLessThanOrEqual(geometry.viewport);
            expect(geometry.width, geometry.label).toBeGreaterThanOrEqual(16);
            expect(geometry.height, geometry.label).toBeGreaterThanOrEqual(16);
            expect(geometry.reachable, `${width}px: ${geometry.label} is covered or clipped`).toBe(true);
            // A native text input can scroll its value. Button/label text must fit.
            if (await control.evaluate((element) => element.tagName === "BUTTON")) {
                expect(geometry.scrollWidth, `${width}px: ${geometry.label} text is clipped`).toBeLessThanOrEqual(geometry.clientWidth);
            }
        }
    }
});

async function expectKeyboardFocus(locator) {
    await expect(locator).toBeFocused();
    await expect.poll(() => locator.evaluate((element) => {
        const style = getComputedStyle(element);
        return element.matches(":focus-visible") && (
            (style.outlineStyle !== "none" && parseFloat(style.outlineWidth) > 0)
            || style.boxShadow !== "none"
        );
    })).toBe(true);
}

test("keyboard tab order, visible focus, named controls and live feedback work", async ({ page }) => {
    const importBackup = page.getByRole("button", { name: "Import Backup", exact: true });
    const sequence = [
        page.getByRole("link", { name: "RL Radio Loadout", exact: true }),
        page.getByRole("button", { name: /Add NOAA Weather/ }),
        page.getByRole("button", { name: /Add Amateur Calling/ }),
        page.getByLabel("CHIRP CSV file", { exact: true }),
        page.getByRole("button", { name: "Import CHIRP CSV", exact: true }),
        page.getByRole("checkbox", { name: /^Include ISS RPT RX/ }),
        page.getByRole("checkbox", { name: /^Include ISS CREW RX/ }),
        page.getByRole("link", { name: "ARISS — Contact the ISS", exact: true }),
        page.getByRole("link", { name: "AMSAT — Amateur Radio on the ISS", exact: true }),
        page.getByRole("button", { name: "Preview ISS receive-only pack", exact: true }),
        page.getByRole("link", { name: "Check the ARISS status page", exact: true }),
        page.getByRole("button", { name: "Export Backup", exact: true }),
        page.getByRole("button", { name: "Export Full Loadout (v2)", exact: true }),
        page.getByLabel("Radio Loadout JSON backup", { exact: true }),
        importBackup,
    ];
    for (const control of sequence) {
        await page.keyboard.press("Tab");
        await expectKeyboardFocus(control);
    }
    await page.keyboard.press("Enter");
    const feedback = page.getByRole("alert");
    await expect(feedback).toContainText("Choose a Radio Loadout JSON backup to restore");
    await expect(feedback).toHaveAttribute("aria-live", "assertive");
    await expect(importBackup).toBeFocused();
    await page.keyboard.press("Tab");
    await expectKeyboardFocus(page.getByRole("combobox", { name: "Review target", exact: true }));
    await page.keyboard.press("Tab");
    await expectKeyboardFocus(page.getByRole("link", { name: "Open radio settings guide", exact: true }));
    await page.keyboard.press("Tab");
    await expectKeyboardFocus(page.getByRole("button", { name: "Duplicate channel", exact: true }));
    await page.keyboard.press("Tab");
    const name = page.getByRole("textbox", { name: "Channel name", exact: true });
    await expectKeyboardFocus(name);
    await page.keyboard.type("KEYBOARD SYNTH");
    await page.keyboard.press("Tab");
    await expectKeyboardFocus(page.getByRole("combobox", { name: "Mode", exact: true }));
    await page.keyboard.press("ArrowDown");
    await expect(page.getByRole("combobox", { name: "Mode", exact: true })).toHaveValue("NFM");
    await page.keyboard.press("Tab");
    await expectKeyboardFocus(page.getByRole("spinbutton", { name: "Receive frequency (MHz)", exact: true }));
    await page.keyboard.type("146.52");
    const review = page.getByRole("button", { name: "Review Compatibility", exact: true });
    for (let index = 0; index < 50 && !(await review.evaluate((element) => element === document.activeElement)); index += 1) {
        await page.keyboard.press("Tab");
    }
    await expectKeyboardFocus(review);
    await page.keyboard.press("Enter");
    const results = page.getByRole("region", { name: "CHIRP Generic CSV compatibility", exact: true });
    await expect(results).toHaveAttribute("aria-live", "polite");
    await expect(results).toContainText("All 1 channels are compatible");
});
