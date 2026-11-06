import AxeBuilder from "@axe-core/playwright";
import { test, expect, configureTwoChannels, savedDraft, snapshot } from "./builder.fixture.mjs";

const guide = "/radio-settings?profile_id=baofeng-bf-f8hp-pro-v053-us";
const current = (page, label) => page.getByRole("combobox", { name: `Your plan: ${label}`, exact: true });
const proposed = (page, label) => page.getByRole("combobox", { name: `Proposed: ${label}`, exact: true });
const preview = (page) => page.getByRole("button", { name: "Preview selected suggestions", exact: true });
const apply = (page) => page.getByRole("button", { name: "Add reviewed changes to plan", exact: true });

test("settings suggestions require selective preview and do not modify channels or their saved draft", async ({ page }) => {
    const channels = await configureTwoChannels(page);
    const draft = await savedDraft(page);
    await page.goto(guide);
    await expect(current(page, "Squelch")).toHaveValue("");
    await expect(page.getByRole("status")).toContainText("Plan empty");
    await current(page, "Squelch").selectOption("3");
    await page.getByRole("checkbox", { name: "Include Squelch in preview", exact: true }).uncheck();
    await proposed(page, "Backlight timeout").selectOption("60");
    await preview(page).click();
    await expect(page.locator("#settings-diff li")).toHaveCount(6);
    await expect(current(page, "VOX")).toHaveValue("");
    await expect(page.locator("#settings-diff")).toContainText("user-customized");
    await apply(page).click();
    await expect(current(page, "Squelch")).toHaveValue("3");
    await expect(current(page, "VOX")).toHaveValue("false");
    await expect(current(page, "Backlight timeout")).toHaveValue("60");
    await expect(page.locator('[data-setting="backlight_seconds"] [data-origin]')).toContainText("user-customized");
    await expect(page.locator('[data-setting="vox"] [data-origin]')).toContainText("radio-loadout-recommendation");
    expect(await savedDraft(page)).toBe(draft);
    await page.getByRole("link", { name: "Channel Builder", exact: true }).click();
    expect(await snapshot(page)).toEqual(channels);
    expect(await savedDraft(page)).toBe(draft);
});

test("cancel, edited proposals and edited plan invalidate review; clear and reload do not reset a radio", async ({ page }) => {
    await page.goto(guide);
    await preview(page).click();
    await page.getByRole("button", { name: "Cancel preview", exact: true }).click();
    await expect(current(page, "Squelch")).toHaveValue("");
    await preview(page).click();
    await current(page, "Squelch").selectOption("1");
    await expect(page.locator("#settings-preview")).toBeHidden();
    // Role locators correctly omit a button inside the now-hidden preview.
    // Check the DOM disabled state independently, without weakening either check.
    await expect(page.locator("#apply-settings")).toBeDisabled();
    await expect(apply(page)).toHaveCount(0);
    await preview(page).click();
    await proposed(page, "Squelch").selectOption("3");
    await expect(page.locator("#settings-preview")).toBeHidden();
    await expect(page.locator("#apply-settings")).toBeDisabled();
    await preview(page).click();
    await expect(page.locator("#settings-diff")).toContainText("Squelch: Level 1 [user-customized] → Level 3");
    await apply(page).click();
    await expect(current(page, "Squelch")).toHaveValue("3");
    await page.getByRole("button", { name: "Clear settings plan", exact: true }).click();
    await expect(current(page, "Squelch")).toHaveValue("");
    await expect(page.getByRole("status")).toContainText("No factory reset");
    await current(page, "VOX").selectOption("true");
    await page.reload();
    await expect(current(page, "VOX")).toHaveValue("");
});

test("settings guide has local-only loading, accessible controls and a narrow layout", async ({ page }) => {
    const external = [];
    page.on("request", (request) => { if (!request.url().startsWith(new URL(page.url()).origin)) external.push(request.url()); });
    await page.goto(guide);
    await expect(preview(page)).toBeEnabled();
    await expect(page.locator("#settings-js-required")).toBeHidden();
    await preview(page).click();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await preview(page).focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("status")).toContainText("Previewing 7");
    const widths = page.viewportSize().width === 375 ? [375, 320] : [1440];
    for (const width of widths) {
        await page.setViewportSize({ width, height: 900 });
        await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
    await page.keyboard.press("Tab");
    await expect(page.getByRole("button", { name: "Clear settings plan", exact: true })).toBeFocused();
    expect(external).toEqual([]);
});

test("generic/unknown profiles and disabled JavaScript cannot silently apply a preset", async ({ page, browser }) => {
    await page.goto("/radio-settings");
    await expect(page.getByText("No radio is selected.", { exact: false })).toBeVisible();
    expect((await page.goto("/radio-settings?profile_id=uv-5r")).status()).toBe(404);
    const context = await browser.newContext({ javaScriptEnabled: false, baseURL: new URL(page.url()).origin });
    try {
        const noJs = await context.newPage();
        await noJs.goto(guide);
        await expect(noJs.locator("#settings-js-required")).toBeVisible();
        await expect(noJs.locator("#settings-js-required")).toContainText("JavaScript is required for plan editing");
        await expect(current(noJs, "Squelch")).toBeDisabled();
        await expect(preview(noJs)).toBeDisabled();
        await expect(noJs.getByText("Manufacturer default:", { exact: false })).toHaveCount(7);
    } finally {
        await context.close();
    }
});

test("missing settings controller keeps guidance visible and editing disabled", async ({ page, browser }) => {
    // Isolate the intentional resource failure; don't relax the shared fixture's
    // error checks for normal application pages.
    const context = await browser.newContext({ baseURL: new URL(page.url()).origin });
    try {
        const missing = await context.newPage();
        const errors = [];
        const failures = [];
        missing.on("pageerror", (error) => errors.push(error.message));
        missing.on("requestfailed", (request) => failures.push(new URL(request.url()).pathname));
        await missing.route("**/static/radio-settings.js*", (route) => route.abort());
        await missing.goto(guide);
        await expect(missing.locator("#settings-js-required")).toBeVisible();
        await expect(current(missing, "Squelch")).toBeDisabled();
        await expect(preview(missing)).toBeDisabled();
        await expect(missing.getByRole("status")).toContainText("Plan empty");
        expect(failures).toEqual(["/static/radio-settings.js"]);
        expect(errors).toEqual([]);
    } finally {
        await context.close();
    }
});
