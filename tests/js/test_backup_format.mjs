import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createContext, runInContext } from "node:vm";

const source = readFileSync(new URL("../../src/radio_loadout/web/static/backup-format.js", import.meta.url), "utf8");
const context = createContext({
    document: new Proxy({}, { get() { throw new Error("Schema validation must not use the DOM"); } }),
});
runInContext(source, context);
const api = context.RadioLoadoutBackup;
const fixture = (name) => JSON.parse(readFileSync(new URL(`../fixtures/backups/${name}`, import.meta.url), "utf8"));
const normalized = (backup) => JSON.parse(JSON.stringify(api.validate(backup)));

test("existing v1 backup validates without accessing HTML or mutating input", () => {
    const backup = fixture("existing-v1.json");
    const before = JSON.stringify(backup);
    assert.deepEqual(normalized(backup), backup.channels);
    assert.equal(JSON.stringify(backup), before);
    assert.equal(Object.isFrozen(api.fields), true);
});

test("missing legacy optionals receive explicit historical defaults", () => {
    const backup = fixture("legacy-missing-optionals-v1.json");
    const historical = fixture("existing-v1.json").channels[0];
    assert.deepEqual(normalized(backup), backup.channels.map((channel) => ({ ...historical, ...channel })));
    assert.equal(Object.keys(backup.channels[0]).length, 2);
});

test("unfinished drafts remain valid independently of export readiness", () => {
    const backup = fixture("unfinished-v1.json");
    assert.deepEqual(normalized(backup), backup.channels);
    assert.equal(normalized(backup)[0].tone_frequency_hz, "50.04");
    assert.equal(normalized(backup)[1].receive_frequency_mhz, "-1");
});

test("draft text and numeric values are not restricted by completed-channel limits", () => {
    const backup = fixture("existing-v1.json");
    Object.assign(backup.channels[0], {
        name: "N".repeat(200), comment: "C".repeat(300), power_watts: "-1.23456",
        receive_frequency_mhz: "0", transmit_ctcss_frequency_hz: "400.125",
    });
    assert.deepEqual(normalized(backup), backup.channels);
});

test("the complete fixture preserves channel order and all hidden tone data", () => {
    const backup = fixture("complete-v1.json");
    assert.deepEqual(normalized(backup), backup.channels);
    assert.equal(normalized(backup)[0].dcs_code, "777");
    assert.equal(normalized(backup)[1].transmit_dcs_polarity, "R");
    assert.equal(normalized(backup)[1].receive_dcs_polarity, "N");
});

test("v1 types are strict for every field, including booleans and null", () => {
    for (const [name, rule] of Object.entries(api.fields)) {
        const wrongValues = rule.type === "boolean" ? ["false", "true", 0, 1, null, [], {}] : [false, true, 23, 23.5, null, [], {}];
        for (const value of wrongValues) {
            const backup = fixture("complete-v1.json");
            backup.channels[0][name] = value;
            assert.throws(() => api.validate(backup), new RegExp(`${name}: must be a ${rule.type}`));
        }
    }
});

test("required legacy fields can be empty, but cannot be omitted", () => {
    for (const name of ["name", "receive_frequency_mhz"]) {
        const backup = fixture("existing-v1.json");
        delete backup.channels[0][name];
        assert.throws(() => api.validate(backup), new RegExp(`missing required field ${name}`));
    }
});

test("unknown envelope and channel fields are rejected rather than lost", () => {
    assert.throws(() => api.validate(fixture("unknown-envelope-v1.json")), /unknown field "future_metadata"/);
    assert.throws(() => api.validate(fixture("unknown-fields-v1.json")), /channel 2: unknown field "future_radio_feature"/);
    const unsafe = JSON.parse('{"format":"radio-loadout","version":1,"channels":[{"name":"TEST","receive_frequency_mhz":"146.52","__proto__":{"polluted":true}}]}');
    assert.throws(() => api.validate(unsafe), /unknown field "__proto__"/);
    assert.equal({}.polluted, undefined);
});

test("unsupported versions and malformed structures fail with explanations", () => {
    assert.throws(() => api.validate(fixture("unsupported-version-999.json")), /Unsupported backup version 999/);
    for (const value of [null, [], {}, { format: "chirp" }]) {
        assert.throws(() => api.validate(value), /format/);
    }
    for (const version of ["1", null, true, 1.5]) {
        assert.throws(() => api.validate({ ...fixture("existing-v1.json"), version }), /version must be the integer 1/);
    }
    for (const channels of [[], {}, null, "channels"]) {
        assert.throws(() => api.validate({ format: "radio-loadout", version: 1, channels }), /non-empty channels array/);
    }
    for (const channel of [null, [], 42, "channel"]) {
        assert.throws(() => api.validate({ format: "radio-loadout", version: 1, channels: [channel] }), /channel 1: must be a channel object/);
    }
});

test("enumerations and numeric spellings are explicit, without completed-export rules", () => {
    for (const [field, value] of [["mode", "DMR"], ["tone_mode", "unknown"], ["dcs_polarity", "RX"],
        ["transmit_dcs_polarity", "X"], ["receive_tone_mode", "unknown"], ["scan_behavior", "X"],
        ["tuning_step_khz", "8.33"], ["receive_frequency_mhz", "NaN"], ["power_watts", "Infinity"],
        ["tone_frequency_hz", "nope"], ["comment", "line\nbreak"], ["name", "line\rbreak"]]) {
        const backup = fixture("complete-v1.json");
        backup.channels[0][field] = value;
        assert.throws(() => api.validate(backup), new RegExp(field));
    }
    const draft = fixture("existing-v1.json");
    for (const [field, rule] of Object.entries(api.fields)) {
        if (rule.type === "string") draft.channels[0][field] = "";
    }
    assert.deepEqual(normalized(draft), draft.channels);
});

test("generic DCS and numeric selection spellings normalize safely", () => {
    const backup = fixture("complete-v1.json");
    Object.assign(backup.channels[0], { dcs_code: "001", transmit_dcs_code: "000", receive_dcs_code: "777", tuning_step_khz: "5.00" });
    const channel = normalized(backup)[0];
    assert.equal(channel.dcs_code, "1");
    assert.equal(channel.transmit_dcs_code, "0");
    assert.equal(channel.receive_dcs_code, "777");
    assert.equal(channel.tuning_step_khz, "5");
});
