import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import {
    test, expect, backupFixture, lossFixture, snapshot, savedDraft, expectSaved,
    restoreBackup, downloadedText, configureTwoChannels,
} from "./builder.fixture.mjs";

test("create, duplicate, reorder and remove channels without changing their settings", async ({ page }) => {
    const original = await configureTwoChannels(page);
    expect(original.map((channel) => channel.name)).toEqual(["SYNTH RPT", "SYNTH AIR"]);
    expect(original[0]).toMatchObject({ mode: "NFM", transmit_ctcss_frequency_hz: "151.4", receive_dcs_polarity: "R" });
    expect(original[1]).toMatchObject({ mode: "AM", receive_only: true, transmit_frequency_mhz: "" });
    await page.getByRole("article").nth(0).getByRole("button", { name: "Duplicate channel", exact: true }).click();
    const copy = { ...original[0], name: "SYNTH RPT COPY" };
    expect(await snapshot(page)).toEqual([original[0], copy, original[1]]);
    await page.getByRole("article").nth(2).getByRole("button", { name: "Move channel up", exact: true }).click();
    expect(await snapshot(page)).toEqual([original[0], original[1], copy]);
    await page.getByRole("article").nth(0).getByRole("button", { name: "Move channel down", exact: true }).click();
    expect(await snapshot(page)).toEqual([original[1], original[0], copy]);
    await page.getByRole("article").nth(2).getByRole("button", { name: "Remove", exact: true }).click();
    expect(await snapshot(page)).toEqual([original[1], original[0]]);
    await expect(page.getByRole("article").nth(0).getByRole("button", { name: "Move channel up", exact: true })).toBeDisabled();
    await expect(page.getByRole("article").nth(1).getByRole("button", { name: "Move channel down", exact: true })).toBeDisabled();
    await expectSaved(page, [original[1], original[0]]);
});

test("real JSON download restores every saved field, order, and autosave after refresh", async ({ page }, testInfo) => {
    const fixture = JSON.parse(await readFile(backupFixture, "utf8"));
    await restoreBackup(page);
    expect(await snapshot(page)).toEqual(fixture.channels);
    const expected = await snapshot(page);
    const download = await downloadedText(page, page.getByRole("button", { name: "Export Backup", exact: true }), testInfo, "radio_loadout_backup.json");
    expect(JSON.parse(download.text)).toEqual({ format: "radio-loadout", version: 1, channels: expected });
    await page.getByRole("article").nth(0).getByRole("textbox", { name: "Channel name", exact: true }).fill("CHANGED AFTER EXPORT");
    await page.getByRole("article").nth(1).getByRole("button", { name: "Remove", exact: true }).click();
    await restoreBackup(page, download.filename);
    expect(await snapshot(page)).toEqual(expected);
    await expectSaved(page, expected);
    const saved = await savedDraft(page);
    await page.reload();
    await expect(page.getByRole("article")).toHaveCount(expected.length);
    expect(await snapshot(page)).toEqual(expected);
    expect(await savedDraft(page)).toBe(saved);
});

test("invalid backup keeps existing controls and the saved draft unchanged", async ({ page }) => {
    const expected = await configureTwoChannels(page);
    const saved = await savedDraft(page);
    const invalid = fileURLToPath(new URL("../fixtures/backups/unsupported-version-999.json", import.meta.url));
    await page.getByLabel("Radio Loadout JSON backup", { exact: true }).setInputFiles(invalid);
    await page.getByRole("button", { name: "Import Backup", exact: true }).click();
    await expect(page.getByRole("alert")).toContainText(/unsupported.*999/i);
    expect(await snapshot(page)).toEqual(expected);
    expect(await savedDraft(page)).toBe(saved);
    await page.reload();
    await expect(page.getByRole("article")).toHaveCount(2);
    expect(await snapshot(page)).toEqual(expected);
});

test("CHIRP loss review supports cancellation and confirms only the captured data safely", async ({ page }) => {
    const expected = await configureTwoChannels(page);
    const saved = await savedDraft(page);
    const input = page.getByLabel("CHIRP CSV file", { exact: true });
    const importButton = page.getByRole("button", { name: "Import CHIRP CSV", exact: true });
    await input.setInputFiles(lossFixture);
    await importButton.click();
    const panel = page.getByRole("region", { name: "CHIRP import review", exact: true });
    await expect(panel).toContainText("Bank");
    await expect(panel).toContainText("Location");
    await expect(panel).toContainText("CSV row 2, channel 1");
    await expect(panel).toContainText("<img src=x onerror=alert(1)>");
    expect(await snapshot(page)).toEqual(expected);
    expect(await savedDraft(page)).toBe(saved);
    await page.getByRole("button", { name: "Cancel import", exact: true }).click();
    await expect(panel).toBeHidden();
    expect(await snapshot(page)).toEqual(expected);
    expect(await savedDraft(page)).toBe(saved);
    await input.setInputFiles(lossFixture);
    await importButton.click();
    const confirm = page.getByRole("button", { name: "Replace channels with reviewed import", exact: true });
    await expect(confirm).toBeVisible();
    await input.setInputFiles({ name: "subsequently-selected.csv", mimeType: "text/csv", buffer: Buffer.from("Name,Frequency\nDIFFERENT FILE,446\n") });
    await confirm.click();
    await expect(page.getByRole("alert")).toContainText("Imported 1 reviewed channels");
    const imported = await snapshot(page);
    expect(imported).toHaveLength(1);
    expect(imported[0]).toMatchObject({
        name: "<img src=x onerror=alert(1)>", receive_frequency_mhz: "146.94", transmit_frequency_mhz: "146.34",
        mode: "NFM", tone_mode: "cross", transmit_ctcss_frequency_hz: "100.0", receive_dcs_code: "777",
        receive_dcs_polarity: "R", tuning_step_khz: "6.25", scan_behavior: "S", power_watts: "2.5",
        comment: "<script>window.__importInjected=true</script>",
    });
    await expectSaved(page, imported);
    expect(await page.locator("main img, main script").count()).toBe(0);
    expect(await page.evaluate(() => window.__importInjected)).toBeUndefined();
});

test("compatibility becomes outdated on edits and blocks invalid CSV before valid download", async ({ page }, testInfo) => {
    const requests = [];
    const downloads = [];
    page.on("request", (request) => { if (new URL(request.url()).pathname === "/downloads/chirp.csv") requests.push(request.url()); });
    page.on("download", (download) => downloads.push(download));
    const first = page.getByRole("article").nth(0);
    await first.getByRole("textbox", { name: "Channel name", exact: true }).fill("SYNTH VALID");
    await first.getByRole("spinbutton", { name: "Receive frequency (MHz)", exact: true }).fill("146.520000");
    await page.getByRole("button", { name: "Review Compatibility", exact: true }).click();
    const results = page.getByRole("region", { name: "CHIRP Generic CSV compatibility", exact: true });
    await expect(results).toContainText("All 1 channels are compatible");
    await first.getByRole("textbox", { name: "Comment", exact: true }).fill("Edited since review");
    await expect(results).toContainText("This report is outdated");
    const invalidDraft = { format: "radio-loadout", version: 1, channels: [{
        name: "BOUNDARY", receive_frequency_mhz: "146.52", tone_mode: "tone", tone_frequency_hz: "50.0",
    }] };
    await restoreBackup(page, { name: "synthetic-boundary.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(invalidDraft)) });
    const generate = page.getByRole("button", { name: "Generate CHIRP CSV", exact: true });
    await generate.click();
    await expect(results).toContainText(/Channel 1 \(BOUNDARY\).*CTCSS/i);
    await expect(results).toHaveAttribute("data-state", "error");
    await expect(generate).toBeDisabled();
    expect(requests).toEqual([]);
    expect(downloads).toEqual([]);
    await first.getByRole("combobox", { name: "CTCSS frequency (Hz)", exact: true }).selectOption("100.0");
    await expect(results).toContainText("This report is outdated");
    await expect(generate).toBeEnabled();
    const download = await downloadedText(page, generate, testInfo, "radio_loadout_custom.csv");
    await expect(results).toHaveAttribute("data-state", "compatible");
    expect(requests).toHaveLength(1);
    const [header, row] = download.text.trim().split(/\r?\n/).map((line) => line.split(","));
    expect(row[header.indexOf("Name")]).toBe("BOUNDARY");
    expect(row[header.indexOf("Frequency")]).toBe("146.520000");
    expect(row[header.indexOf("Tone")]).toBe("Tone");
    expect(row[header.indexOf("rToneFreq")]).toBe("100.0");
});

test("duplicating restored custom tones preserves nonstandard options and independent polarities", async ({ page }) => {
    await restoreBackup(page);
    const original = await snapshot(page);
    await page.getByRole("article").nth(0).getByRole("button", { name: "Duplicate channel", exact: true }).click();
    expect(await snapshot(page)).toEqual([original[0], { ...original[0], name: "MATCHED 777 COPY" }, ...original.slice(1)]);
    await expectSaved(page, await snapshot(page));
});
