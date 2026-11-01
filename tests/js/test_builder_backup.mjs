import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { setupBuilderHarness as setup } from "./helpers/builder-harness.mjs";

const text = (name) => readFileSync(new URL(`../fixtures/backups/${name}`, import.meta.url), "utf8");
async function restore(state, contents) {
    state.elements["#backup-file"].files = [{ text: async () => contents }];
    await state.evaluate("importBackup()");
}

test("restores an existing exported version-1 backup including its blank channel", async () => {
    const state = setup();
    await restore(state, text("existing-v1.json"));
    assert.deepEqual(state.draft(), JSON.parse(text("existing-v1.json")).channels);
    assert.match(state.elements["#form-message"].textContent, /Restored 1 channels/);
    assert.deepEqual(JSON.parse([...state.saved.values()][0]), state.draft());
});

test("complete backup export/import round trip preserves order, presets, hidden settings and polarities", async () => {
    const state = setup();
    const fixture = JSON.parse(text("complete-v1.json"));
    await restore(state, JSON.stringify(fixture));
    assert.deepEqual(state.draft(), fixture.channels);
    state.evaluate("exportBackup()");
    const download = state.downloads.at(-1);
    assert.equal(download.filename, "radio_loadout_backup.json");
    const exported = await download.blob.text();
    assert.deepEqual(JSON.parse(exported), fixture);
    state.evaluate("replaceChannelCards([{name: 'DIFFERENT'}])");
    await restore(state, "\ufeff" + exported);
    assert.deepEqual(state.draft(), fixture.channels);
    assert.equal(state.field(0, "dcs_code").value, "777");
    assert.equal(state.field(0, "dcs_polarity").value, "NR");
    assert.equal(state.field(1, "transmit_dcs_code").value, "777");
    assert.equal(state.field(1, "receive_dcs_code").value, "1");
    assert.equal(state.field(1, "transmit_dcs_polarity").value, "R");
    assert.equal(state.field(1, "receive_dcs_polarity").value, "N");
});

test("unfinished draft round trip does not enforce export validity or erase stored values", async () => {
    const state = setup();
    const fixture = JSON.parse(text("unfinished-v1.json"));
    await restore(state, JSON.stringify(fixture));
    assert.deepEqual(state.draft(), fixture.channels);
    assert.equal(state.field(0, "tone_frequency_hz").value, "50.04");
    assert.equal(state.field(1, "transmit_frequency_mhz").disabled, true);
    assert.equal(state.field(1, "transmit_frequency_mhz").value, "145.5");
    state.evaluate("exportBackup()");
    const exported = await state.downloads.at(-1).blob.text();
    state.evaluate("replaceChannelCards([{name: 'TEMP'}])");
    await restore(state, exported);
    assert.deepEqual(state.draft(), fixture.channels);
});

test("missing optional legacy fields restore using documented historical defaults", async () => {
    const state = setup();
    const legacy = JSON.parse(text("legacy-missing-optionals-v1.json"));
    const defaults = JSON.parse(text("existing-v1.json")).channels[0];
    await restore(state, JSON.stringify(legacy));
    assert.deepEqual(state.draft(), legacy.channels.map((channel) => ({ ...defaults, ...channel })));
});

test("explicit receive-only editing still clears transmit frequency", async () => {
    const state = setup();
    await restore(state, text("unfinished-v1.json"));
    assert.equal(state.field(1, "transmit_frequency_mhz").value, "145.5");
    state.evaluate("updateTransmitField(getChannelCards()[1])");
    assert.equal(state.field(1, "transmit_frequency_mhz").value, "");
});

for (const [name, message] of [
    ["unknown-fields-v1.json", /channel 2: unknown field "future_radio_feature"/],
    ["unknown-envelope-v1.json", /unknown field "future_metadata"/],
    ["unsupported-version-999.json", /Unsupported backup version 999/],
    ["malformed-structure-v1.json", /non-empty channels array/],
    ["invalid-types-v1.json", /receive_frequency_mhz: must be a string/],
    ["malformed.json", /not valid JSON/],
]) {
    test(`failed ${name} restore leaves existing cards and autosave unchanged`, async () => {
        const state = setup();
        await restore(state, text("complete-v1.json"));
        const before = state.draft();
        const cards = state.elements["#channel-list"].children;
        const saved = [...state.saved.entries()];
        await restore(state, text(name));
        assert.match(state.elements["#form-message"].textContent, message);
        assert.deepEqual(state.draft(), before);
        assert.equal(state.elements["#channel-list"].children, cards);
        assert.deepEqual([...state.saved.entries()], saved);
        assert.equal(state.elements["#import-backup"].disabled, false);
        assert.equal(state.elements["#backup-file"].disabled, false);
    });
}

test("invalid types in a later channel do not partially replace any cards", async () => {
    const state = setup();
    const fixture = JSON.parse(text("complete-v1.json"));
    await restore(state, JSON.stringify(fixture));
    fixture.channels[0].name = "WOULD CHANGE FIRST";
    fixture.channels[2].receive_only = "true";
    const before = state.draft();
    await restore(state, JSON.stringify(fixture));
    assert.match(state.elements["#form-message"].textContent, /channel 3, receive_only: must be a boolean/);
    assert.deepEqual(state.draft(), before);
});
