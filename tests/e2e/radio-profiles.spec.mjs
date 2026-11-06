import { test, expect, configureTwoChannels, downloadedText, snapshot, savedDraft, restoreBackup } from "./builder.fixture.mjs";

const pilotId = "baofeng-bf-f8hp-pro-v053-us";

test("documented pilot reviews and exports without modifying channels or version-1 backup", async ({ page }, testInfo) => {
    const before = await configureTwoChannels(page);
    const draft = await savedDraft(page);
    const target = page.getByRole("combobox", { name: "Review target", exact: true });
    await expect(target).toHaveValue("");
    await target.selectOption(pilotId);
    await page.getByRole("button", { name: "Review Compatibility", exact: true }).click();
    await expect(page.locator("#compatibility-summary")).toContainText("not hardware verified");
    expect(await snapshot(page)).toEqual(before);
    expect(await savedDraft(page)).toBe(draft);
    const csv = await downloadedText(page, page.getByRole("button", { name: "Generate CHIRP CSV", exact: true }), testInfo, "radio_loadout_custom.csv");
    expect(csv.text).toContain("SYNTH RPT");
    const backup = await downloadedText(page, page.getByRole("button", { name: "Export Backup", exact: true }), testInfo, "radio_loadout_backup.json");
    expect(Object.keys(JSON.parse(backup.text)).sort()).toEqual(["channels", "format", "version"]);
    await page.reload();
    await expect(target).toHaveValue("");
    expect(await snapshot(page)).toEqual(before);
});

test("radio-only errors block export, selection invalidates review, and restore resets target", async ({ page }, testInfo) => {
    const before = await configureTwoChannels(page);
    const target = page.getByRole("combobox", { name: "Review target", exact: true });
    await target.selectOption(pilotId);
    await page.getByRole("article").first().getByRole("spinbutton", { name: "Power (watts)", exact: true }).fill("25.0");
    await page.getByRole("button", { name: "Review Compatibility", exact: true }).click();
    await expect(page.locator("#compatibility-results")).toHaveAttribute("data-state", "error");
    await expect(page.getByRole("button", { name: "Generate CHIRP CSV", exact: true })).toBeDisabled();
    await target.selectOption("");
    await expect(page.locator("#compatibility-results")).toHaveAttribute("data-state", "outdated");
    await downloadedText(page, page.getByRole("button", { name: "Generate CHIRP CSV", exact: true }), testInfo, "radio_loadout_custom.csv");
    await target.selectOption(pilotId);
    await page.getByLabel("Radio Loadout JSON backup", { exact: true }).setInputFiles({ name: "bad.json", mimeType: "application/json", buffer: Buffer.from("{broken") });
    await page.getByRole("button", { name: "Import Backup", exact: true }).click();
    await expect(page.getByRole("alert")).toContainText("not valid JSON");
    await expect(target).toHaveValue(pilotId);
    await restoreBackup(page);
    await expect(target).toHaveValue("");
    expect(before.length).toBe(2);
});
