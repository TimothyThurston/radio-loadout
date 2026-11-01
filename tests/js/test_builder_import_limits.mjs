import assert from "node:assert/strict";
import { test } from "node:test";
import { setupBuilderHarness as setup } from "./helpers/builder-harness.mjs";

const channels = () => [{ name: "REVIEWED", receive_frequency_mhz: 146.52, power_watts: 5 }];
const report = (loss = false) => ({
    requires_confirmation: loss, loss_count: loss ? 1 : 0, omitted_messages: 0,
    messages: [{ kind: loss ? "loss" : "default", row_number: 2, channel_index: 0,
        channel_name: "REVIEWED", field: loss ? "Bank" : "Power",
        message: loss ? "Non-empty Bank will be discarded." : "Unspecified power defaults to 5 W." }],
});
function makeState(result = { channels: channels(), import_report: report() }) {
    const state = setup([], { fetch: async () => ({ ok: true, json: async () => result }) });
    state.evaluate("replaceChannelCards([{name:'CURRENT', receive_frequency_mhz:145.5}]); saveDraft();");
    return state;
}
const file = (text, name = "original.csv") => Object.assign(new Blob([text], { type: "text/csv" }), { name });
async function startImport(state, selected = file("Name,Frequency\nREVIEWED,146.52\n")) {
    state.elements["#chirp-csv-file"].files = [selected];
    await state.evaluate("importChirpCsv()");
}
function limits(state, values) {
    const element = state.elements["#input-limits"];
    element.textContent = JSON.stringify({ ...JSON.parse(element.textContent), ...values });
}

test("expected normalization/default reports apply without a confirmation prompt", async () => {
    const state = makeState();
    await startImport(state);
    assert.equal(state.draft()[0].name, "REVIEWED");
    assert.equal(state.elements["#confirm-chirp-import"].hidden, true);
    assert.match(state.elements["#chirp-import-messages"].children[0].textContent, /DEFAULT.*CSV row 2.*Power.*5 W/);
    assert.deepEqual(JSON.parse([...state.saved.values()][0]), state.draft());
});

test("loss requires explicit confirmation and cancellation preserves cards and autosave", async () => {
    const state = makeState({ channels: channels(), import_report: report(true) });
    const before = state.draft();
    const cards = state.elements["#channel-list"].children;
    const saved = [...state.saved.entries()];
    await startImport(state);
    assert.deepEqual(state.draft(), before);
    assert.equal(state.elements["#channel-list"].children, cards);
    assert.deepEqual([...state.saved.entries()], saved);
    assert.equal(state.elements["#confirm-chirp-import"].hidden, false);
    assert.match(state.elements["#chirp-import-summary"].textContent, /1 information loss/);
    state.elements["#cancel-chirp-import"].listeners.get("click")();
    state.elements["#confirm-chirp-import"].listeners.get("click")();
    assert.deepEqual(state.draft(), before);
    assert.equal(state.elements["#channel-list"].children, cards);
    assert.deepEqual([...state.saved.entries()], saved);
    assert.equal(state.elements["#chirp-import-review"].hidden, true);
});

test("confirmation applies the captured review, not a changed file or response object", async () => {
    const result = { channels: channels(), import_report: report(true) };
    const state = makeState(result);
    await startImport(state);
    state.elements["#chirp-csv-file"].files = [file("DIFFERENT", "different.csv")];
    result.channels[0].name = "MUTATED AFTER REVIEW";
    state.elements["#confirm-chirp-import"].listeners.get("click")();
    assert.equal(state.draft()[0].name, "REVIEWED");
    assert.equal(state.requests.length, 1);
    assert.match(state.elements["#chirp-import-summary"].textContent, /original.csv/);
    assert.deepEqual(JSON.parse([...state.saved.values()][0]), state.draft());
});

test("untrusted import report and channel text is rendered as text, never HTML", async () => {
    const attack = '<img src=x onerror="alert(1)">';
    const result = { channels: [{ ...channels()[0], name: attack }], import_report: report(true) };
    Object.assign(result.import_report.messages[0], { channel_name: attack, field: attack, message: attack });
    const state = makeState(result);
    await startImport(state, file("CSV", attack));
    const item = state.elements["#chirp-import-messages"].children[0];
    assert.ok(item.textContent.includes(attack));
    assert.equal(item.innerHTML, undefined);
    assert.ok(state.elements["#chirp-import-summary"].textContent.includes(attack));
    state.evaluate("confirmChirpImport()");
    assert.equal(state.field(0, "name").value, attack);
});

test("a storage failure rolls back replacement and retains the previously saved draft", async () => {
    const state = makeState({ channels: channels(), import_report: report(true) });
    const before = state.draft();
    const card = state.elements["#channel-list"].children[0];
    const saved = [...state.saved.entries()];
    await startImport(state);
    state.evaluate("window.localStorage.setItem = () => { throw new Error('Storage quota exceeded'); };");
    state.evaluate("confirmChirpImport()");
    assert.match(state.elements["#form-message"].textContent, /Storage quota/);
    assert.deepEqual(state.draft(), before);
    assert.equal(state.elements["#channel-list"].children[0], card);
    assert.deepEqual([...state.saved.entries()], saved);
});

test("failed card conversion does not touch existing cards or autosave", async () => {
    const state = makeState({ channels: [{ ...channels()[0], transmit_dcs_code: 89 }], import_report: report() });
    const before = state.draft();
    const cards = state.elements["#channel-list"].children;
    const saved = [...state.saved.entries()];
    await startImport(state);
    assert.deepEqual(state.draft(), before);
    assert.equal(state.elements["#channel-list"].children, cards);
    assert.deepEqual([...state.saved.entries()], saved);
});

test("failed or inconsistent server reports cannot authorize replacement", async () => {
    for (const result of [
        { channels: channels() },
        { channels: [], import_report: report() },
        { channels: channels(), import_report: { ...report(true), requires_confirmation: false } },
    ]) {
        const state = makeState(result);
        const before = state.draft();
        const saved = [...state.saved.entries()];
        await startImport(state);
        assert.deepEqual(state.draft(), before);
        assert.deepEqual([...state.saved.entries()], saved);
    }
});

test("HTTP import failures leave cards and autosave unchanged", async () => {
    const state = setup([], { fetch: async () => ({ ok: false, json: async () => ({ detail: "Unsupported channel mode: USB" }) }) });
    state.evaluate("saveDraft()");
    const before = state.draft();
    const saved = [...state.saved.entries()];
    await startImport(state);
    assert.match(state.elements["#form-message"].textContent, /Unsupported channel mode/);
    assert.deepEqual(state.draft(), before);
    assert.deepEqual([...state.saved.entries()], saved);
});

test("cancelling an in-flight request ignores its later result", async () => {
    let complete;
    const state = setup([], { fetch: () => new Promise((resolve) => { complete = resolve; }) });
    state.evaluate("saveDraft()");
    const before = state.draft();
    const saved = [...state.saved.entries()];
    const pending = startImport(state);
    state.evaluate("cancelChirpImport()");
    complete({ ok: true, json: async () => ({ channels: channels(), import_report: report() }) });
    await pending;
    assert.match(state.elements["#form-message"].textContent, /cancelled/);
    assert.deepEqual(state.draft(), before);
    assert.deepEqual([...state.saved.entries()], saved);
});

test("CSV file byte boundary is checked before upload", async () => {
    const selected = file("CSV");
    const exact = makeState();
    limits(exact, { csv_upload_bytes: selected.size });
    await startImport(exact, selected);
    assert.equal(exact.requests.length, 1);
    assert.equal(exact.draft()[0].name, "REVIEWED");
    const over = makeState();
    limits(over, { csv_upload_bytes: selected.size - 1 });
    const before = over.draft();
    const saved = [...over.saved.entries()];
    await startImport(over, selected);
    assert.equal(over.requests.length, 0);
    assert.match(over.elements["#form-message"].textContent, /CSV file exceeds/);
    assert.deepEqual(over.draft(), before);
    assert.deepEqual([...over.saved.entries()], saved);
});

test("backup file byte boundary and channel limits apply before replacement", async () => {
    const backup = JSON.stringify({ format: "radio-loadout", version: 1, channels: [{ name: "LEGACY", receive_frequency_mhz: "146.52" }] });
    const size = new Blob([backup]).size;
    const state = makeState();
    limits(state, { backup_bytes: size });
    state.elements["#backup-file"].files = [{ size, text: async () => backup }];
    await state.evaluate("importBackup()");
    assert.equal(state.draft()[0].name, "LEGACY");
    const before = state.draft();
    const saved = [...state.saved.entries()];
    let read = false;
    state.elements["#backup-file"].files = [{ size: size + 1, text: async () => { read = true; return backup; } }];
    await state.evaluate("importBackup()");
    assert.equal(read, false);
    assert.deepEqual(state.draft(), before);
    assert.deepEqual([...state.saved.entries()], saved);
    limits(state, { backup_bytes: 10000, channels: 1 });
    const tooMany = JSON.stringify({ format: "radio-loadout", version: 1, channels: [before[0], before[0]] });
    state.elements["#backup-file"].files = [{ text: async () => tooMany }];
    await state.evaluate("importBackup()");
    assert.match(state.elements["#form-message"].textContent, /channel limit/);
    assert.deepEqual(state.draft(), before);
});

test("submitted JSON byte and channel checks run before compatibility requests", async () => {
    const state = setup();
    const data = [{ name: "Café", receive_frequency_mhz: 146.52 }];
    const size = new Blob([JSON.stringify(data)]).size;
    limits(state, { channels_json_bytes: size });
    await state.evaluate(`requestCompatibilityReport(${JSON.stringify(data)})`);
    assert.equal(state.requests.length, 1);
    data[0].name += "A";
    await assert.rejects(state.evaluate(`requestCompatibilityReport(${JSON.stringify(data)})`), /byte limit/);
    assert.equal(state.requests.length, 1);
    limits(state, { channels_json_bytes: 10000, channels: 1 });
    await assert.rejects(state.evaluate(`requestCompatibilityReport(${JSON.stringify([data[0], data[0]])})`), /channel limit/);
    assert.equal(state.requests.length, 1);
});
