import assert from "node:assert/strict";
import { test } from "node:test";
import { setupBuilderHarness as setup } from "./helpers/builder-harness.mjs";

const imported = (code) => [
    {
        name: "MATCHED", receive_frequency_mhz: 444.5, transmit_frequency_mhz: 449.5,
        mode: "FM", power_watts: 2.5, receive_only: false, tone_mode: "cross",
        dcs_code: null, transmit_tone_mode: "dcs", receive_tone_mode: "dcs",
        transmit_dcs_code: code, receive_dcs_code: code,
        transmit_dcs_polarity: "N", receive_dcs_polarity: "R",
        tuning_step_khz: 12.5, scan_behavior: "S", comment: "Generic matched code",
    },
    {
        name: "CROSS", receive_frequency_mhz: 446, transmit_frequency_mhz: 446,
        tone_mode: "cross", transmit_tone_mode: "dcs", receive_tone_mode: "dcs",
        transmit_dcs_code: code, receive_dcs_code: 1,
        transmit_dcs_polarity: "R", receive_dcs_polarity: "N",
    },
];

for (const code of [23, 777, 1, 0]) {
    test(`DCS ${String(code).padStart(3, "0")} survives import, options, backup restore, and CSV submission`, async () => {
        const state = setup(imported(code));
        state.elements["#chirp-csv-file"].files = [new Blob(["csv"], { type: "text/csv" })];
        await state.evaluate("importChirpCsv()");
        assert.equal(state.field(0, "transmit_dcs_code").value, String(code));
        const options = state.field(0, "transmit_dcs_code").options;
        assert.ok(options.some((option) => option.value === "23" && option.textContent === "023"));
        assert.ok(options.find((option) => option.value === String(code)).textContent.startsWith(String(code).padStart(3, "0")));
        state.evaluate("exportBackup()");
        assert.equal(state.downloads[0].filename, "radio_loadout_backup.json");
        const backupText = await state.downloads[0].blob.text();
        const backup = JSON.parse(backupText);
        assert.equal(backup.channels[0].transmit_dcs_code, String(code));
        assert.equal(backup.channels[0].receive_dcs_polarity, "R");
        state.evaluate("replaceChannelCards([{name: 'OTHER'}])");
        state.elements["#backup-file"].files = [{ text: async () => backupText }];
        await state.evaluate("importBackup()");
        assert.deepEqual(state.draft(), backup.channels);
        assert.deepEqual(JSON.parse([...state.saved.values()][0]), backup.channels);
        assert.equal(state.field(0, "dcs_code").value, "");
        await state.evaluate("submitChannelForm({preventDefault() {}})");
        const request = state.requests.find((request) => request.url === "/downloads/chirp.csv");
        assert.ok(request, state.elements["#form-message"].textContent);
        const submitted = JSON.parse(request.options.body.get("channels_json"));
        assert.equal(submitted[0].transmit_dcs_code, code);
        assert.equal(submitted[0].receive_dcs_code, code);
        assert.equal(submitted[0].transmit_dcs_polarity, "N");
        assert.equal(submitted[0].receive_dcs_polarity, "R");
        assert.equal(submitted[1].transmit_dcs_code, code);
        assert.equal(submitted[1].receive_dcs_code, 1);
        assert.equal(submitted[1].transmit_dcs_polarity, "R");
        assert.equal(submitted[1].receive_dcs_polarity, "N");
    });
}

test("quick matched DCS restores a nonstandard option and both polarities", async () => {
    const state = setup();
    state.evaluate('replaceChannelCards([{name: "QUICK", receive_frequency_mhz: 146.52, tone_mode: "dtcs", dcs_code: "777", dcs_polarity: "RN"}])');
    const code = state.field(0, "dcs_code");
    assert.equal(code.value, "777");
    assert.equal(code.options.filter((option) => option.value === "777").length, 1);
    assert.equal(code.options.find((option) => option.value === "777").textContent, "777 (generic)");
    const draft = state.draft();
    state.elements["#backup-file"].files = [{ text: async () => JSON.stringify({ format: "radio-loadout", version: 1, channels: draft }) }];
    await state.evaluate("importBackup()");
    assert.equal(state.field(0, "dcs_code").value, "777");
    assert.equal(state.field(0, "dcs_polarity").value, "RN");
});

test("leading-zero backup codes become selectable without substituting 023", () => {
    const state = setup();
    state.evaluate('replaceChannelCards([{tone_mode: "dtcs", dcs_code: "001", dcs_polarity: "NR"}])');
    assert.equal(state.field(0, "dcs_code").value, "1");
    assert.equal(state.field(0, "dcs_code").options.find((option) => option.value === "1").textContent, "001 (generic)");
    assert.equal(state.field(0, "dcs_polarity").value, "NR");
});

test("invalid code values and types cannot change the existing builder", async () => {
    const state = setup();
    const original = state.draft();
    for (const value of [true, false, 23.5, -1, 89, "23.5", "023.0", "089", "7777", "True"]) {
        state.evaluate(`globalThis.badCode = ${JSON.stringify(value)}`);
        assert.throws(() => state.evaluate("normalizeDcsCode(badCode)"), /octal/);
        const channels = structuredClone(original);
        channels[0].dcs_code = value;
        state.elements["#backup-file"].files = [{ text: async () => JSON.stringify({ format: "radio-loadout", version: 1, channels }) }];
        await state.evaluate("importBackup()");
        assert.deepEqual(state.draft(), original);
        assert.match(state.elements["#form-message"].textContent, /DCS|dcs/);
    }
});
