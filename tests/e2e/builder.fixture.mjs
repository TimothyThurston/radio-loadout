import { test as base, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

export const draftKey = "radio-loadout-builder-draft-v1";
export const backupFixture = fileURLToPath(new URL("../fixtures/backups/complete-v1.json", import.meta.url));
export const lossFixture = fileURLToPath(new URL("./fixtures/loss-review.csv", import.meta.url));
export const test = base.extend({
    page: async ({ page }, use, testInfo) => {
        const errors = [];
        page.on("pageerror", (error) => errors.push(error.stack || error.message));
        page.on("console", (message) => {
            // Resource HTTP errors are separate from application console.error calls.
            if (message.type() === "error" && message.location().url.includes("/static/")) {
                errors.push(message.text());
            }
        });
        await page.goto("/builder");
        await expect(page.getByRole("article")).toHaveCount(1);
        await expect(page.getByRole("textbox", { name: "Channel name", exact: true })).toHaveValue("");
        // Every test gets a fresh non-persistent context, without storageState.
        expect(await savedDraft(page)).toBeNull();
        await use(page);
        if (errors.length) {
            await testInfo.attach("application-errors", { body: JSON.stringify(errors, null, 2), contentType: "application/json" });
        }
        expect(errors, "Unexpected application JavaScript errors").toEqual([]);
    },
});
export { expect };

export async function snapshot(page) {
    // Inspect actual DOM controls, including hidden/disabled saved fields; never call app helpers.
    return page.getByRole("article").evaluateAll((cards) => cards.map((card) => Object.fromEntries(
        [...card.querySelectorAll("[data-field]")].map((field) => [
            field.dataset.field, field.type === "checkbox" ? field.checked : field.value,
        ])
    )));
}

export async function savedDraft(page) {
    return page.evaluate((key) => window.localStorage.getItem(key), draftKey);
}

export async function expectSaved(page, expected) {
    await expect.poll(async () => JSON.parse(await savedDraft(page))).toEqual(expected);
}

export async function restoreBackup(page, file = backupFixture) {
    await page.getByLabel("Radio Loadout JSON backup", { exact: true }).setInputFiles(file);
    await page.getByRole("button", { name: "Import Backup", exact: true }).click();
    await expect(page.getByRole("alert")).toContainText(/Restored \d+ channels from backup/);
}

export async function downloadedText(page, button, testInfo, filename) {
    const pendingDownload = page.waitForEvent("download");
    await button.click();
    const download = await pendingDownload;
    expect(download.suggestedFilename()).toBe(filename);
    expect(await download.failure()).toBeNull();
    const destination = testInfo.outputPath(filename);
    await download.saveAs(destination);
    return { text: await readFile(destination, "utf8"), filename: destination };
}

export async function configureTwoChannels(page) {
    const first = page.getByRole("article").nth(0);
    await first.getByRole("textbox", { name: "Channel name", exact: true }).fill("SYNTH RPT");
    await first.getByRole("combobox", { name: "Mode", exact: true }).selectOption("NFM");
    await first.getByRole("spinbutton", { name: "Receive frequency (MHz)", exact: true }).fill("146.940000");
    await first.getByRole("spinbutton", { name: "Transmit frequency (MHz)", exact: true }).fill("146.340000");
    await first.getByRole("spinbutton", { name: "Power (watts)", exact: true }).fill("2.5");
    await first.getByRole("combobox", { name: "Tuning step (kHz)", exact: true }).selectOption("6.25");
    await first.getByRole("combobox", { name: "Scan behavior", exact: true }).selectOption("P");
    await first.getByRole("combobox", { name: "Tone configuration", exact: true }).selectOption("cross");
    await first.getByRole("combobox", { name: "Transmit tone type", exact: true }).selectOption("ctcss");
    await first.getByRole("combobox", { name: "Transmit CTCSS frequency", exact: true }).selectOption("151.4");
    await first.getByRole("combobox", { name: "Receive tone type", exact: true }).selectOption("dcs");
    await first.getByRole("combobox", { name: "Receive DCS code", exact: true }).selectOption("23");
    await first.getByRole("combobox", { name: "Receive DCS polarity", exact: true }).selectOption("R");
    await first.getByRole("textbox", { name: "Comment", exact: true }).fill("Synthetic repeater with cross tones");
    await page.getByRole("button", { name: "+ Add another channel", exact: true }).click();
    const second = page.getByRole("article").nth(1);
    await second.getByRole("textbox", { name: "Channel name", exact: true }).fill("SYNTH AIR");
    await second.getByRole("combobox", { name: "Mode", exact: true }).selectOption("AM");
    await second.getByRole("spinbutton", { name: "Receive frequency (MHz)", exact: true }).fill("121.500000");
    await second.getByRole("spinbutton", { name: "Power (watts)", exact: true }).fill("1.0");
    await second.getByRole("combobox", { name: "Tuning step (kHz)", exact: true }).selectOption("25");
    await second.getByRole("combobox", { name: "Scan behavior", exact: true }).selectOption("S");
    await second.getByLabel("Receive only", { exact: false }).check();
    await expect(second.getByRole("spinbutton", { name: "Transmit frequency (MHz)", exact: true })).toBeDisabled();
    await second.getByRole("textbox", { name: "Comment", exact: true }).fill("Synthetic receive-only AM channel");
    const expected = await snapshot(page);
    await expectSaved(page, expected);
    return expected;
}
