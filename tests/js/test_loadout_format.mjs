import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { fixture, validator } from "./helpers/loadout-fixtures.mjs";

test("full v2 round trip preserves unfinished channels, tone precision/order and typed settings origins", () => {
    const validate = validator().validate;
    const input = fixture("complete-v2.json");
    const before = JSON.stringify(input);
    const canonical = validate(input);
    assert.equal(JSON.stringify(input), before);
    assert.equal(JSON.stringify(validate(JSON.parse(JSON.stringify(canonical)))), JSON.stringify(canonical));
    assert.equal(canonical.channels[0].transmit_frequency_mhz, "145.500000");
    assert.equal(canonical.channels[0].receive_only, true);
    assert.equal(canonical.channels[0].transmit_dcs_code, "777");
    assert.equal(canonical.channels[0].receive_dcs_code, "0");
    assert.equal(canonical.channels[0].transmit_dcs_polarity, "R");
    assert.equal(canonical.channels[1].tone_frequency_hz, "50.04");
    assert.equal(canonical.settings_plan.entries.vox.value, false);
    assert.equal(canonical.settings_plan.entries.timeout_seconds.value, 0);
    assert.equal(canonical.settings_plan.entries.backlight_seconds.value, "always_on");
    assert.equal(canonical.settings_plan.entries.vox.recommendation_revision, 1);
    assert.equal(canonical.settings_plan.entries.squelch.origin, "user-customized");
});

test("generic v2 and empty settings do not inject a radio or suggestions", () => {
    const validate = validator().validate;
    const generic = validate(fixture("generic-v2.json"));
    assert.equal(generic.radio_profile, null); assert.equal(generic.settings_plan, null);
    const complete = fixture("complete-v2.json");
    complete.settings_plan.entries = {};
    assert.equal(Object.keys(validate(complete).settings_plan.entries).length, 0);
    complete.settings_plan = null;
    assert.throws(() => validate(complete), /requires a settings-plan object/);
});

test("existing version-1 backups still normalize through the original schema only", () => {
    const old = JSON.parse(readFileSync(new URL("../fixtures/backups/unfinished-v1.json", import.meta.url), "utf8"));
    const result = validator().validate(old);
    assert.equal(result.version, 1);
    assert.deepEqual(Object.keys(result), ["format", "version", "channels"]);
    assert.equal(result.channels[0].tone_frequency_hz, "50.04");
    assert.throws(() => validator().validate({ ...old, radio_profile: null }), /unknown field/);
});

const mutations = [
    ["future version", (d) => { d.version = 999; }],
    ["string version", (d) => { d.version = "2"; }],
    ["missing profile", (d) => { delete d.radio_profile; }],
    ["unknown envelope field", (d) => { d.future = true; }],
    ["unknown radio", (d) => { d.radio_profile.profile_id = "uv-5r"; }],
    ["other firmware", (d) => { d.radio_profile.profile_id = "baofeng-bf-f8hp-pro-v044-us"; }],
    ["profile revision", (d) => { d.radio_profile.revision = 999; }],
    ["string revision", (d) => { d.radio_profile.revision = "1"; }],
    ["forged verification", (d) => { d.radio_profile.hardware_verified = true; }],
    ["orphan settings", (d) => { d.radio_profile = null; }],
    ["catalog revision", (d) => { d.settings_plan.catalog_revision = 2; }],
    ["other recommendation", (d) => { d.settings_plan.recommendation_id = "future"; }],
    ["unknown settings metadata", (d) => { d.settings_plan.readback = true; }],
    ["entries array", (d) => { d.settings_plan.entries = []; }],
    ["unknown setting", (d) => { d.settings_plan.entries.calibration = { value: 1, origin: "user-customized" }; }],
    ["prototype field", (d) => { d.settings_plan.entries = JSON.parse('{"__proto__":{"value":1,"origin":"user-customized"}}'); }],
    ["wrong boolean type", (d) => { d.settings_plan.entries.vox.value = "false"; }],
    ["boolean instead of number", (d) => { d.settings_plan.entries.squelch.value = true; }],
    ["out of range", (d) => { d.settings_plan.entries.squelch.value = 9; }],
    ["null value", (d) => { d.settings_plan.entries.squelch.value = null; }],
    ["unknown entry field", (d) => { d.settings_plan.entries.squelch.extra = 1; }],
    ["false origin", (d) => { d.settings_plan.entries.squelch.origin = "manufacturer-default"; }],
    ["old recommendation revision", (d) => { d.settings_plan.entries.vox.recommendation_revision = 2; }],
    ["missing recommendation revision", (d) => { delete d.settings_plan.entries.vox.recommendation_revision; }],
    ["different recommended value", (d) => { d.settings_plan.entries.vox.value = true; }],
    ["custom entry with recommendation revision", (d) => { d.settings_plan.entries.squelch.recommendation_revision = 1; }],
    ["bad later channel", (d) => { d.channels[1].receive_only = "true"; }],
    ["unknown channel field", (d) => { d.channels[1].global_settings = {}; }],
    ["empty channels", (d) => { d.channels = []; }],
];
for (const [label, alter] of mutations) {
    test(`rejects ${label} without mutating the input`, () => {
        const input = fixture("complete-v2.json"); alter(input);
        const before = JSON.stringify(input);
        assert.throws(() => validator().validate(input));
        assert.equal(JSON.stringify(input), before);
    });
}

test("channel bounds apply before normalization", () => {
    const input = fixture("generic-v2.json");
    input.channels = Array(2000).fill(input.channels[0]);
    assert.equal(validator().validate(input).channels.length, 2000);
    input.channels.push(input.channels[0]);
    assert.throws(() => validator().validate(input), /2000 channels/);
});
