import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createContext, runInContext } from "node:vm";
import { catalog as settingsCatalog } from "./helpers/loadout-fixtures.mjs";
import { setupBuilderHarness } from "./helpers/builder-harness.mjs";

const catalog = () => JSON.parse(readFileSync(new URL("../fixtures/satellites/iss-voice-rx-v1.json", import.meta.url), "utf8"));
const ids = ["iss-repeater-rx", "iss-crew-rx"];
const blank = { name: "", receive_frequency_mhz: "" };
function planner() {
    const context = createContext({});
    for (const filename of ["backup-format.js", "satellite-presets.js"]) {
        runInContext(readFileSync(new URL(`../../src/radio_loadout/web/static/${filename}`, import.meta.url), "utf8"), context);
    }
    return context.RadioSatellitePresets.plan;
}
function setup(hooks = {}) {
    return setupBuilderHarness([], { satellites: catalog(), catalog: settingsCatalog(),
        fetch: async (url, options) => ({ ok: true, json: async () => ({ compatible: true,
            channel_count: JSON.parse(options.body.get("channels_json")).length, issues: [],
            ...(options.body.get("radio_profile_id") ? { radio_profile: settingsCatalog().radio_profile } : {}),
        }) }), ...hooks });
}
const entries = (state) => JSON.parse(state.evaluate("JSON.stringify(RadioSettingsEditor.snapshot())"));
const snapshot = (state) => JSON.stringify({ draft: state.draft(), entries: entries(state), profile: state.elements["#radio-profile"].value, saved: [...state.saved.entries()] });

test("RX-only planning replaces only a pristine placeholder and preserves application defaults", () => {
    const input = catalog(); const before = JSON.stringify(input);
    const result = planner()(input, "iss-voice-rx", ids, [blank], 2000);
    assert.equal(result.replacePristine, true); assert.equal(result.resultingCount, 2);
    assert.deepEqual(Array.from(result.additions, (channel) => channel.receive_frequency_mhz), ["437.800000", "145.800000"]);
    assert.ok(result.additions.every((channel) => channel.receive_only && channel.transmit_frequency_mhz === "" && channel.mode === "FM" && channel.tone_mode === "none"));
    assert.ok(result.reviewChannels.every((channel) => channel.receive_only && channel.transmit_frequency_mhz === null && typeof channel.receive_frequency_mhz === "number"));
    assert.equal(JSON.stringify(input), before);
    assert.throws(() => { result.additions[0].receive_only = false; }, TypeError);
});

test("customized blank channels and existing TX/tone-filtered channels are never overwritten", () => {
    for (const old of [{ ...blank, power_watts: "2.5" }, { name: "TX", receive_frequency_mhz: "437.8", receive_only: false },
        { name: "SQL", receive_frequency_mhz: "437.8", receive_only: true, tone_mode: "tsql" }]) {
        const before = JSON.stringify(old);
        const result = planner()(catalog(), "iss-voice-rx", ids, [old], 2000);
        assert.equal(result.replacePristine, false); assert.equal(result.resultingCount, 3);
        assert.equal(JSON.stringify(old), before);
    }
});

test("duplicates require matching receive-only/no-tone FM and nominal whole-Hz frequency", () => {
    const existing = catalog().packs[0].channels.map((item) => item.draft);
    const result = planner()(catalog(), "iss-voice-rx", ids, existing, 2000);
    assert.equal(result.additions.length, 0); assert.equal(result.skipped.length, 2);
    const selected = planner()(catalog(), "iss-voice-rx", [ids[1]], [], 2000);
    assert.equal(selected.additions.length, 1); assert.equal(selected.additions[0].name, "ISS CREW RX");
});

test("unknown IDs, duplicate selections and channel overflow fail without substitutions", () => {
    for (const selected of [[], ["unknown"], [ids[0], ids[0]]]) assert.throws(() => planner()(catalog(), "iss-voice-rx", selected, [blank], 2000));
    assert.throws(() => planner()(catalog(), "unknown", ids, [blank], 2000), /Unknown/);
    assert.throws(() => planner()(catalog(), "iss-voice-rx", ids, [{ ...blank, name: "KEEP" }], 2), /2-channel limit/);
    assert.equal(planner()(catalog(), "iss-voice-rx", ids, [blank], 2).resultingCount, 2);
    const preserved = { ...blank, name: "KEEP" };
    assert.equal(planner()(catalog(), "iss-voice-rx", ids, Array(1998).fill(preserved), 2000).resultingCount, 2000);
    assert.throws(() => planner()(catalog(), "iss-voice-rx", ids, Array(2000).fill(preserved), 2000), /2000-channel limit/);
});

for (const [label, mutate] of [
    ["transmit-enabled metadata", (data) => { data.packs[0].channels[0].receive_only = false; }],
    ["transmit-enabled draft", (data) => { data.packs[0].channels[0].draft.receive_only = false; }],
    ["hidden TX frequency", (data) => { data.packs[0].channels[0].draft.transmit_frequency_mhz = "145.99"; }],
    ["wrong nominal frequency", (data) => { data.packs[0].channels[0].draft.receive_frequency_mhz = "437.9"; }],
    ["wrong role", (data) => { data.packs[0].channels[0].role = "uplink"; }],
    ["unsupported digital mode", (data) => { data.packs[0].channels[0].mode = "DMR"; }],
    ["live activity claim", (data) => { data.packs[0].operational_status = "active"; }],
    ["hardware claim", (data) => { data.packs[0].hardware_verified = true; }],
    ["duplicate channel ID", (data) => { data.packs[0].channels[1].channel_id = ids[0]; }],
]) {
    test(`rejects ${label} in a preset definition`, () => {
        const data = catalog(); mutate(data);
        assert.throws(() => planner()(data, "iss-voice-rx", ids, [blank], 2000));
    });
}

test("preview does not change cards/storage; confirm adds only reviewed RX channels", async () => {
    const state = setup();
    const before = snapshot(state);
    await state.evaluate("previewSatellitePreset()");
    assert.equal(snapshot(state), before); assert.equal(state.elements["#add-satellite"].disabled, false);
    assert.ok(JSON.parse(state.requests[0].options.body.get("channels_json")).every((channel) => channel.transmit_frequency_mhz === null));
    assert.match(state.elements["#satellite-summary"].textContent, /New channels only/);
    state.evaluate("addReviewedSatelliteChannels()");
    assert.equal(state.draft().length, 2);
    assert.ok(state.draft().every((channel) => channel.receive_only && channel.transmit_frequency_mhz === ""));
    assert.equal(state.elements["#add-satellite"].disabled, true);
    assert.deepEqual(JSON.parse([...state.saved.values()][0]), state.draft());
    await state.evaluate("previewSatellitePreset()");
    assert.equal(state.elements["#add-satellite"].disabled, true);
    assert.match(state.elements["#satellite-summary"].textContent, /already present/);
});

test("cancel and stale edits prevent additions without dropping profile/settings", async () => {
    const state = setup();
    state.elements["#radio-profile"].value = settingsCatalog().radio_profile.profile_id;
    state.evaluate("changeRadioProfile(); RadioSettingsEditor.restore({vox:{value:true,origin:'user-customized'}})");
    await state.evaluate("previewSatellitePreset()");
    const before = snapshot(state); state.evaluate("invalidateSatellitePreview(); addReviewedSatelliteChannels()");
    assert.equal(snapshot(state), before);
    await state.evaluate("previewSatellitePreset()");
    state.evaluate("RadioSettingsEditor.restore({vox:{value:false,origin:'user-customized'}})");
    const edited = snapshot(state); state.evaluate("addReviewedSatelliteChannels()");
    assert.equal(snapshot(state), edited); assert.match(state.elements["#form-message"].textContent, /changed/);
    await state.evaluate("previewSatellitePreset()"); state.evaluate("addReviewedSatelliteChannels()");
    assert.equal(state.elements["#radio-profile"].value, settingsCatalog().radio_profile.profile_id);
    assert.equal(entries(state).vox.value, false);
});

test("storage failure rolls back original card identities and saved draft", async () => {
    const state = setup(); state.evaluate("saveDraft()");
    await state.evaluate("previewSatellitePreset()"); const before = snapshot(state);
    const cards = [...state.elements["#channel-list"].children];
    state.evaluate("window.localStorage.setItem = () => { throw new Error('Quota exceeded'); }; addReviewedSatelliteChannels()");
    assert.equal(snapshot(state), before);
    assert.equal(state.elements["#channel-list"].children[0], cards[0]);
    assert.match(state.elements["#form-message"].textContent, /Quota exceeded/);
});

test("in-flight cancellation and changes to saved work cannot authorize stale additions", async () => {
    let resolve;
    const state = setup({ fetch: () => new Promise((done) => { resolve = done; }) });
    const pending = state.evaluate("previewSatellitePreset()");
    const before = snapshot(state); state.evaluate("invalidateSatellitePreview()");
    resolve({ ok: true, json: async () => ({ compatible: true, channel_count: 2, issues: [] }) }); await pending;
    assert.equal(state.elements["#add-satellite"].disabled, true); assert.equal(snapshot(state), before);
    const pending2 = state.evaluate("previewSatellitePreset()");
    state.saved.set("radio-loadout-builder-draft-v1", "other-tab-content");
    resolve({ ok: true, json: async () => ({ compatible: true, channel_count: 2, issues: [] }) }); await pending2;
    assert.equal(state.elements["#add-satellite"].disabled, true);
    assert.match(state.elements["#form-message"].textContent, /saved draft changed/);
});

test("compatibility failures and capacity block additions; preview text is rendered literally", async () => {
    const state = setup({ fetch: async () => ({ ok: true, json: async () => ({ compatible: false, channel_count: 2,
        issues: [{ severity: "error", field: "mode", message: "<img src=x onerror=alert(1)>" }] }) }) });
    await state.evaluate("previewSatellitePreset()");
    assert.equal(state.elements["#add-satellite"].disabled, true);
    assert.match(state.elements["#satellite-issues"].children.at(-1).textContent, /<img src=x/);
    const limited = settingsCatalog(); limited.radio_profile.memory_capacity = 1;
    const small = setup({ catalog: limited }); small.elements["#radio-profile"].value = limited.radio_profile.profile_id;
    await small.evaluate("previewSatellitePreset()");
    assert.equal(small.requests.length, 0); assert.match(small.elements["#form-message"].textContent, /capacity is 1/);
});

test("unknown selected profiles never fall back to generic preview", async () => {
    const state = setup(); state.elements["#radio-profile"].value = "unknown";
    const before = snapshot(state);
    await state.evaluate("previewSatellitePreset()");
    assert.equal(snapshot(state), before); assert.equal(state.requests.length, 0);
    assert.match(state.elements["#form-message"].textContent, /no generic fallback/);
});

test("a transmit-enabled existing entry keeps its identity and settings while a safe RX entry is appended", async () => {
    const state = setup();
    state.evaluate("getField(getChannelCards()[0], 'name').value = 'KEEP TX'; getField(getChannelCards()[0], 'receive_frequency_mhz').value = '437.8'; saveDraft()");
    const original = state.draft()[0]; const card = state.elements["#channel-list"].children[0];
    await state.evaluate("previewSatellitePreset()"); state.evaluate("addReviewedSatelliteChannels()");
    assert.equal(state.elements["#channel-list"].children[0], card);
    assert.deepEqual(state.draft()[0], original);
    assert.equal(state.draft()[0].receive_only, false);
    assert.equal(state.draft()[1].receive_only, true);
});
