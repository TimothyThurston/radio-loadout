import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { setupBuilderHarness } from "./helpers/builder-harness.mjs";
import { catalog, fixture, validator } from "./helpers/loadout-fixtures.mjs";

const setup = (hooks = {}) => setupBuilderHarness([], { catalog: catalog(), ...hooks });
async function restore(state, value) {
    const text = typeof value === "string" ? value : JSON.stringify(value);
    state.elements["#backup-file"].files = [{ size: new Blob([text]).size, text: async () => text }];
    await state.evaluate("importBackup()");
}
const profile = (state) => state.elements["#radio-profile"].value;
const settings = (state) => JSON.parse(state.evaluate("JSON.stringify(RadioSettingsEditor.snapshot())"));
function snapshot(state) { return JSON.stringify({ channels: state.draft(), profile: profile(state), settings: settings(state), saved: [...state.saved.entries()] }); }

test("v2 full export/restore retains exact profile and settings while v1 export remains channel-only", async () => {
    const state = setup();
    await restore(state, fixture("complete-v2.json"));
    const normalized = JSON.parse(JSON.stringify(validator().validate(fixture("complete-v2.json"))));
    assert.deepEqual(state.draft(), normalized.channels);
    assert.equal(profile(state), normalized.radio_profile.profile_id);
    assert.deepEqual(settings(state), normalized.settings_plan.entries);
    assert.equal(state.elements["#builder-settings"].hidden, false);
    state.evaluate("exportFullLoadout()");
    assert.equal(state.downloads.at(-1).filename, "radio_loadout_full_v2.json");
    const text = await state.downloads.at(-1).blob.text();
    assert.deepEqual(JSON.parse(text), normalized);
    state.evaluate("exportBackup()");
    const old = JSON.parse(await state.downloads.at(-1).blob.text());
    assert.deepEqual(Object.keys(old), ["format", "version", "channels"]);
    assert.equal(old.version, 1);
    await restore(state, "\ufeff" + text);
    assert.deepEqual(settings(state), normalized.settings_plan.entries);
    assert.deepEqual(JSON.parse([...state.saved.values()][0]), normalized.channels); // Autosave remains channels only.
});

test("cancelled v2 restore preserves cards, profile, settings and autosave", async () => {
    let accept = true;
    const state = setup({ confirm: () => accept });
    await restore(state, fixture("complete-v2.json"));
    const before = snapshot(state);
    const cards = state.elements["#channel-list"].children;
    accept = false;
    await restore(state, fixture("generic-v2.json"));
    assert.equal(snapshot(state), before);
    assert.equal(state.elements["#channel-list"].children, cards);
    assert.match(state.elements["#form-message"].textContent, /cancelled/);
});

test("invalid v2 and malformed files cannot partially restore any state", async () => {
    const state = setup(); await restore(state, fixture("complete-v2.json"));
    const before = snapshot(state);
    for (const input of [fixture("unknown-profile-v2.json"), "{broken", { ...fixture("generic-v2.json"), future: "bad" },
        { ...fixture("complete-v2.json"), settings_plan: { catalog_revision: 999, recommendation_id: "bad", entries: {} } }]) {
        await restore(state, input);
        assert.equal(snapshot(state), before);
        assert.equal(state.elements["#form-message"].classList.contains("form-message-error"), true);
    }
});

test("storage failure rolls back cards/profile/settings and preserves the prior saved draft", async () => {
    const state = setup(); await restore(state, fixture("complete-v2.json"));
    const before = snapshot(state);
    const cards = state.elements["#channel-list"].children;
    state.evaluate("window.localStorage.setItem = () => { throw new Error('Quota exceeded'); }");
    await restore(state, fixture("generic-v2.json"));
    assert.equal(snapshot(state), before);
    assert.deepEqual(state.elements["#channel-list"].children, cards);
    assert.match(state.elements["#form-message"].textContent, /Quota exceeded/);
});

test("settings-editor failure rolls back channels/profile and does not persist partial restoration", async () => {
    const state = setup();
    await restore(state, fixture("complete-v2.json"));
    const before = snapshot(state);
    state.evaluate("const originalRestore = RadioSettingsEditor.restore; RadioSettingsEditor.restore = (entries) => { if (!Object.keys(entries).length) throw new Error('Editor failed'); originalRestore(entries); }");
    await restore(state, fixture("generic-v2.json"));
    assert.equal(snapshot(state), before);
    assert.match(state.elements["#form-message"].textContent, /Editor failed/);
});

test("v1 restore requires confirmation before discarding a nonempty settings plan", async () => {
    let accept = true;
    const state = setup({ confirm: () => accept });
    await restore(state, fixture("complete-v2.json")); const before = snapshot(state);
    const old = readFileSync(new URL("../fixtures/backups/existing-v1.json", import.meta.url), "utf8");
    accept = false; await restore(state, old); assert.equal(snapshot(state), before);
    accept = true; await restore(state, old);
    assert.equal(profile(state), ""); assert.deepEqual(settings(state), {});
    assert.equal(state.elements["#builder-settings"].hidden, true);
});

test("changing profile cancels or explicitly clears a settings plan; CSV reset also needs confirmation", async () => {
    let accept = true;
    const state = setup({ confirm: () => accept }); await restore(state, fixture("complete-v2.json"));
    const before = settings(state);
    accept = false;
    state.elements["#radio-profile"].value = ""; state.evaluate("changeRadioProfile()");
    assert.equal(profile(state), catalog().radio_profile.profile_id); assert.deepEqual(settings(state), before);
    assert.equal(state.evaluate("confirmSettingsResetForCsv()"), false);
    accept = true; state.elements["#radio-profile"].value = ""; state.evaluate("changeRadioProfile()");
    assert.deepEqual(settings(state), {}); assert.equal(profile(state), "");
});

test("editing settings or channels while a file is read prevents stale replacement", async () => {
    for (const edit of ["RadioSettingsEditor.restore({vox:{value:true,origin:'user-customized'}})",
        "getField(getChannelCards()[0], 'name').value = 'EDITED'; saveDraft()"] ) {
        const state = setup(); await restore(state, fixture("complete-v2.json"));
        let release;
        state.elements["#backup-file"].files = [{ size: 100, text: () => new Promise((resolve) => { release = resolve; }) }];
        const pending = state.evaluate("importBackup()");
        state.evaluate(edit); const before = snapshot(state);
        release(JSON.stringify(fixture("generic-v2.json"))); await pending;
        assert.equal(snapshot(state), before);
        assert.match(state.elements["#form-message"].textContent, /changed while reading/);
    }
});

test("byte limit rejection happens before reading; full export never silently drops an unsupported profile", async () => {
    const state = setup(); await restore(state, fixture("complete-v2.json"));
    const before = snapshot(state);
    state.elements["#backup-file"].files = [{ size: 4194305, text: () => { throw new Error("Must not read"); } }];
    await state.evaluate("importBackup()"); assert.equal(snapshot(state), before);
    assert.match(state.elements["#form-message"].textContent, /byte limit/);
    state.elements["#radio-profile"].value = "unknown";
    state.evaluate("exportFullLoadout()"); assert.equal(state.downloads.length, 0);
    assert.match(state.elements["#form-message"].textContent, /Unknown radio profile/);
});

test("oversized full-loadout generation cannot request a download", () => {
    const state = setup();
    state.evaluate("getField(getChannelCards()[0], 'comment').value = 'x'.repeat(4194305); exportFullLoadout()");
    assert.equal(state.downloads.length, 0);
    assert.match(state.elements["#form-message"].textContent, /byte limit/);
});

test("an inconsistent generic editor state cannot silently omit settings on export", () => {
    const state = setup();
    state.evaluate("RadioSettingsEditor.restore({vox:{value:true,origin:'user-customized'}}); exportFullLoadout()");
    assert.equal(state.downloads.length, 0);
    assert.match(state.elements["#form-message"].textContent, /settings were not discarded/);
    assert.equal(settings(state).vox.value, true);
});

test("autosave and download feedback distinguish channel-only storage from a full-loadout request", async () => {
    const state = setup(); await restore(state, fixture("complete-v2.json"));
    const before = snapshot(state);
    assert.match(state.elements["#draft-status"].textContent, /channels only/);
    assert.match(state.elements["#draft-status"].textContent, /profile and settings plan are not autosaved/);
    state.evaluate("exportBackup()");
    assert.match(state.elements["#form-message"].textContent, /Backup download requested/);
    assert.match(state.elements["#form-message"].textContent, /Channel-only v1/);
    assert.match(state.elements["#form-message"].textContent, /profile and settings plan are excluded/);
    state.evaluate("exportFullLoadout()");
    assert.match(state.elements["#form-message"].textContent, /download requested/);
    assert.match(state.elements["#form-message"].textContent, /Check your browser's downloads/);
    assert.equal(snapshot(state), before); // A download request changes neither the plan nor autosave.
    state.evaluate("window.localStorage.setItem = () => { throw new Error('Quota exceeded'); }; saveDraft()");
    assert.match(state.elements["#draft-status"].textContent, /could not be saved/);
    assert.match(state.elements["#draft-status"].textContent, /channels only/);
});

test("clear draft cancels without touching a nonempty plan and clears it only after confirmation", async () => {
    let accept = true;
    const state = setup({ confirm: () => accept }); await restore(state, fixture("complete-v2.json"));
    const before = snapshot(state);
    accept = false; state.evaluate("clearDraft()");
    assert.equal(snapshot(state), before);
    accept = true; state.evaluate("clearDraft()");
    assert.deepEqual(settings(state), {});
    assert.equal(profile(state), "");
    assert.equal(state.saved.size, 0);
    assert.equal(state.draft().length, 1);
    assert.equal(state.draft()[0].name, "");
});
