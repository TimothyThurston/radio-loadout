import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";
import { test, expect, configureTwoChannels, downloadedText, snapshot, savedDraft } from "./builder.fixture.mjs";

const profileId = "baofeng-bf-f8hp-pro-v053-us";
const target = (page) => page.getByRole("combobox", { name: "Review target", exact: true });
const current = (page, name) => page.getByRole("combobox", { name: `Your plan: ${name}`, exact: true });
const legacyFile = new URL("../fixtures/backups/complete-v1.json", import.meta.url);
async function plan(page) {
    await target(page).selectOption(profileId);
    await page.locator("#builder-settings-details summary").click();
    await current(page, "Squelch").selectOption("3");
    await current(page, "VOX").selectOption("true");
    await current(page, "Backlight timeout").selectOption('"always_on"');
}
async function importFile(page, text, accept = true) {
    await page.getByLabel("Radio Loadout JSON backup", { exact: true }).setInputFiles({ name: "loadout.json", mimeType: "application/json", buffer: Buffer.from(text) });
    page.once("dialog", (dialog) => accept ? dialog.accept() : dialog.dismiss());
    await page.getByRole("button", { name: "Import Backup", exact: true }).click();
}

test("real full-loadout download restores channels/profile/settings while v1 stays channel-only", async ({ page }, testInfo) => {
    const channels = await configureTwoChannels(page);
    await plan(page);
    const full = await downloadedText(page, page.getByRole("button", { name: "Export Full Loadout (v2)", exact: true }), testInfo, "radio_loadout_full_v2.json");
    const saved = JSON.parse(full.text);
    expect(saved.version).toBe(2); expect(saved.radio_profile).toEqual({ profile_id: profileId, revision: 1 });
    expect(saved.settings_plan.entries.vox).toEqual({ value: true, origin: "user-customized" });
    expect(saved.channels).toEqual(channels);
    const old = await downloadedText(page, page.getByRole("button", { name: "Export Backup", exact: true }), testInfo, "radio_loadout_backup.json");
    expect(Object.keys(JSON.parse(old.text)).sort()).toEqual(["channels", "format", "version"]);
    await page.reload();
    await expect(target(page)).toHaveValue("");
    await expect(page.locator("#builder-settings")).toBeHidden();
    await importFile(page, full.text);
    await expect(page.getByRole("alert")).toContainText("Version-2 profile/settings plan restored");
    await expect(target(page)).toHaveValue(profileId);
    await page.locator("#builder-settings-details summary").click();
    await expect(current(page, "Squelch")).toHaveValue("3");
    await expect(current(page, "VOX")).toHaveValue("true");
    await expect(current(page, "Backlight timeout")).toHaveValue('"always_on"');
    expect(await snapshot(page)).toEqual(channels);
    const repeat = await downloadedText(page, page.getByRole("button", { name: "Export Full Loadout (v2)", exact: true }), testInfo, "radio_loadout_full_v2.json");
    expect(JSON.parse(repeat.text)).toEqual(saved);
});

test("cancelled restore and malformed/unknown v2 leave channels, plan, profile and autosave intact", async ({ page }, testInfo) => {
    const channels = await configureTwoChannels(page); await plan(page);
    const draft = await savedDraft(page);
    const full = await downloadedText(page, page.getByRole("button", { name: "Export Full Loadout (v2)", exact: true }), testInfo, "radio_loadout_full_v2.json");
    await importFile(page, full.text, false);
    await expect(page.getByRole("alert")).toContainText("cancelled");
    // Invalid files must not open any confirmation dialog.
    for (const changed of ["{broken", JSON.stringify({ ...JSON.parse(full.text), future: true }),
        JSON.stringify({ ...JSON.parse(full.text), radio_profile: { profile_id: "unknown", revision: 1 } })]) {
        await page.getByLabel("Radio Loadout JSON backup", { exact: true }).setInputFiles({ name: "bad.json", mimeType: "application/json", buffer: Buffer.from(changed) });
        await page.getByRole("button", { name: "Import Backup", exact: true }).click();
        await expect(page.getByRole("alert")).toHaveClass(/form-message-error/);
        await expect(target(page)).toHaveValue(profileId);
        await expect(current(page, "Squelch")).toHaveValue("3");
        expect(await snapshot(page)).toEqual(channels); expect(await savedDraft(page)).toBe(draft);
    }
});

test("legacy restore explicitly clears profile/settings only after confirmation", async ({ page }) => {
    const channels = await configureTwoChannels(page); await plan(page);
    const old = readFileSync(legacyFile, "utf8");
    await importFile(page, old, false);
    await expect(target(page)).toHaveValue(profileId); expect(await snapshot(page)).toEqual(channels);
    await importFile(page, old, true);
    await expect(page.getByRole("alert")).toContainText("Version 1 contains no profile/settings");
    await expect(target(page)).toHaveValue(""); await expect(page.locator("#builder-settings")).toBeHidden();
    await target(page).selectOption(profileId);
    await expect(current(page, "Squelch")).toHaveValue("");
});

test("embedded settings stay accessible and inside narrow viewports without adding CSV form fields", async ({ page }) => {
    await configureTwoChannels(page); await plan(page);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    for (const width of page.viewportSize().width === 375 ? [375, 320] : [1440]) {
        await page.setViewportSize({ width, height: 900 });
        await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
    expect(await page.locator("#channel-form").evaluate((form) => [...new FormData(form).keys()])).toEqual(["channels_json", "radio_profile_id"]);
});
