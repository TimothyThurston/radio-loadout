import AxeBuilder from "@axe-core/playwright";
import { test, expect, downloadedText, configureTwoChannels, snapshot, savedDraft } from "./builder.fixture.mjs";

const preview = (page) => page.getByRole("button", { name: "Preview ISS receive-only pack", exact: true });
const add = (page) => page.getByRole("button", { name: "Add reviewed receive-only channels", exact: true });
const cancel = (page) => page.getByRole("button", { name: "Cancel satellite preview", exact: true });
async function reviewAndAdd(page) {
    await preview(page).click();
    await expect(add(page)).toBeEnabled();
    await add(page).click();
}

test("satellite preview requires confirmation and produces RX-only CSV and v2 round-trip channels", async ({ page }, testInfo) => {
    const initial = await snapshot(page);
    await preview(page).click(); await expect(add(page)).toBeEnabled();
    expect(await snapshot(page)).toEqual(initial); expect(await savedDraft(page)).toBeNull();
    await expect(page.locator("#satellite-summary")).toContainText("New channels only were reviewed");
    await add(page).click(); await expect(page.getByRole("article")).toHaveCount(2);
    const channels = await snapshot(page);
    expect(channels.map((channel) => channel.receive_frequency_mhz)).toEqual(["437.800000", "145.800000"]);
    expect(channels.every((channel) => channel.receive_only && channel.transmit_frequency_mhz === "")).toBe(true);
    const csv = await downloadedText(page, page.getByRole("button", { name: "Generate CHIRP CSV", exact: true }), testInfo, "radio_loadout_custom.csv");
    const rows = csv.text.trim().split(/\r?\n/).slice(1).map((row) => row.split(","));
    expect(rows.map((row) => row[3])).toEqual(["off", "off"]);
    expect(rows.map((row) => row[5])).toEqual(["", ""]);
    const full = await downloadedText(page, page.getByRole("button", { name: "Export Full Loadout (v2)", exact: true }), testInfo, "radio_loadout_full_v2.json");
    expect(JSON.parse(full.text).channels).toEqual(channels);
    await page.reload();
    await page.getByLabel("Radio Loadout JSON backup", { exact: true }).setInputFiles(full.filename);
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Import Backup", exact: true }).click();
    await expect(page.getByRole("alert")).toContainText("Version-2");
    expect(await snapshot(page)).toEqual(channels);
    await preview(page).click();
    await expect(page.locator("#satellite-summary")).toContainText("already present");
    await expect(add(page)).toBeDisabled(); await expect(page.getByRole("article")).toHaveCount(2);
});

test("selective additions preserve existing channels, selected profile and settings", async ({ page }) => {
    const original = await configureTwoChannels(page);
    await page.getByRole("combobox", { name: "Review target", exact: true }).selectOption("baofeng-bf-f8hp-pro-v053-us");
    await page.locator("#builder-settings-details summary").click();
    await page.getByRole("combobox", { name: "Your plan: Squelch", exact: true }).selectOption("3");
    await page.getByRole("checkbox", { name: /^Include ISS CREW RX/ }).uncheck();
    await reviewAndAdd(page);
    const added = await snapshot(page);
    expect(added.slice(0, 2)).toEqual(original); expect(added).toHaveLength(3);
    expect(added[2].name).toBe("ISS RPT RX"); expect(added[2].receive_only).toBe(true);
    await expect(page.getByRole("combobox", { name: "Review target", exact: true })).toHaveValue("baofeng-bf-f8hp-pro-v053-us");
    await expect(page.getByRole("combobox", { name: "Your plan: Squelch", exact: true })).toHaveValue("3");
    expect(JSON.parse(await savedDraft(page))).toEqual(added);
});

test("in-flight cancellation and service failures preserve cards and autosave", async ({ page }) => {
    const original = await configureTwoChannels(page); const saved = await savedDraft(page);
    let release;
    const gate = new Promise((resolve) => { release = resolve; });
    await page.route("**/validation/chirp.csv", async (route) => {
        await gate; const response = await route.fetch(); await route.fulfill({ response });
    });
    const requested = page.waitForRequest((request) => request.url().endsWith("/validation/chirp.csv"));
    await preview(page).click(); await requested;
    await expect(cancel(page)).toBeVisible(); await cancel(page).click();
    const completed = page.waitForResponse((response) => response.url().endsWith("/validation/chirp.csv"));
    release(); await completed;
    await expect(page.locator("#satellite-preview")).toBeHidden();
    expect(await snapshot(page)).toEqual(original); expect(await savedDraft(page)).toBe(saved);
    await page.unroute("**/validation/chirp.csv");
    await page.route("**/validation/chirp.csv", (route) => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Synthetic review unavailable" }) }));
    await preview(page).click();
    await expect(page.getByRole("alert")).toContainText("Synthetic review unavailable");
    expect(await snapshot(page)).toEqual(original); expect(await savedDraft(page)).toBe(saved);
});

test("satellite preview is accessible, fits narrow viewports and marks source dates as non-live", async ({ page }) => {
    await expect(page.locator("#satellite-panel")).toContainText("2026-11-06");
    await expect(page.locator("#satellite-panel")).toContainText("unknown — not checked live");
    await preview(page).focus(); await page.keyboard.press("Enter"); await expect(add(page)).toBeEnabled();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    for (const width of page.viewportSize().width === 375 ? [375, 320] : [1440]) {
        await page.setViewportSize({ width, height: 900 });
        await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
        for (const link of await page.locator("#satellite-panel a").all()) {
            await link.scrollIntoViewIfNeeded();
            const geometry = await link.evaluate((element) => {
                const rect = element.getBoundingClientRect();
                const center = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
                return {
                    label: element.textContent.trim(),
                    display: getComputedStyle(element).display,
                    fragments: element.getClientRects().length,
                    left: rect.left, right: rect.right, viewport: innerWidth,
                    reachable: center === element || element.contains(center),
                };
            });
            expect(geometry.display, `${width}px: ${geometry.label} has a continuous target`).toBe("inline-block");
            expect(geometry.fragments, geometry.label).toBe(1);
            expect(geometry.left, geometry.label).toBeGreaterThanOrEqual(0);
            expect(geometry.right, geometry.label).toBeLessThanOrEqual(geometry.viewport);
            expect(geometry.reachable, `${width}px: ${geometry.label} center reaches the link`).toBe(true);
        }
    }
    await add(page).focus(); await page.keyboard.press("Enter");
    await expect(page.getByRole("article")).toHaveCount(2);
    expect((await snapshot(page)).every((channel) => channel.receive_only)).toBe(true);
});
