// Run with: node --test tests/js/*.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createContext, runInContext } from "node:vm";

const inputLimits = JSON.parse(readFileSync(new URL("../../src/radio_loadout/web/static/input-limits.json", import.meta.url), "utf8"));
const backupSource = readFileSync(new URL("../../src/radio_loadout/web/static/backup-format.js", import.meta.url), "utf8");
const source = readFileSync(new URL("../../src/radio_loadout/web/static/builder.js", import.meta.url), "utf8");

class Element {
    constructor() {
        this.listeners = new Map();
        this.children = [];
        this.dataset = {};
        this.style = {};
        this.hidden = false;
        this.disabled = false;
        this.textContent = "";
        this.classList = { add() {}, remove() {} };
    }
    addEventListener(type, listener) { this.listeners.set(type, listener); }
    appendChild(child) { this.children.push(child); }
    replaceChildren(...children) { this.children = children; }
    querySelectorAll() { return []; }
    scrollIntoView() {}
    remove() {}
}

function setup(responder) {
    const selectors = [
        "#channel-form", "#channel-list", "#review-compatibility", "#generate-csv",
        "#compatibility-results", "#compatibility-summary", "#compatibility-issues",
        "#form-message", "#draft-status", "#channels-json", "#radio-profile",
    ];
    const elements = Object.fromEntries(selectors.map((name) => [name, new Element()]));
    elements["#compatibility-results"].hidden = true;
    elements["#channel-form"].action = "/downloads/chirp.csv";
    const channels = [
        { name: "CALL", receive_frequency_mhz: 146.52 },
        { name: "WEATHER", receive_frequency_mhz: 162.55, receive_only: true },
    ];
    const requests = [];
    const downloads = [];
    elements["#input-limits"] = { textContent: JSON.stringify(inputLimits) };
    const context = createContext({
        FormData: class extends FormData {
            constructor(form) {
                super();
                if (form) {
                    this.append("channels_json", elements["#channels-json"].value);
                    this.append("radio_profile_id", elements["#radio-profile"].value || "");
                }
            }
        },
        Blob, channels,
        console: { warn() {}, error() {} },
        window: {
            clearTimeout() {}, setTimeout() { return 1; },
            localStorage: { setItem() {} },
            fetch: async (url, options) => {
                requests.push({ url, options });
                return responder(url, options);
            },
        },
        URL: { createObjectURL: () => "blob:csv", revokeObjectURL() {} },
        document: {
            querySelector: (name) => elements[name] || null,
            body: new Element(),
            createElement(tag) {
                const element = new Element();
                if (tag === "a") element.click = () => downloads.push(element.download);
                return element;
            },
        },
    });
    // Exercise real event registration and workflow functions. Only replace card
    // serialization here; DOM card rendering has its own existing asset checks.
    runInContext(backupSource, context);
    runInContext(source, context);
    runInContext(`
        getChannelCards = () => channels;
        channelDataFromCard = (channel) => channel;
        getCardDraft = (channel) => channel;
    `, context);
    return {
        elements, requests, downloads, channels,
        review: () => runInContext("reviewCompatibility()", context),
        submit: () => runInContext("submitChannelForm({preventDefault() {}})", context),
        selectProfile(value) {
            elements["#radio-profile"].value = value;
            elements["#radio-profile"].listeners.get("change")();
        },
        edit() {
            channels[0].name = "EDITED";
            elements["#channel-list"].listeners.get("input")({ target: { closest: () => ({}) } });
        },
    };
}

const successReport = { compatible: true, channel_count: 2, issues: [] };
const warningReport = {
    ...successReport,
    issues: [{ severity: "warning", channel_index: 0, channel_name: "CALL", field: "power_watts", message: "Power will be rounded." }],
};
const errorReport = {
    compatible: false, channel_count: 2,
    issues: [{ severity: "error", channel_index: 1, channel_name: "BAD <script>", field: "mode", message: "Choose FM, NFM, or AM." }],
};
const response = (report) => ({ ok: true, json: async () => report });

test("requests the review endpoint using the export channel JSON and renders success", async () => {
    const state = setup(() => response(successReport));
    assert.equal(typeof state.elements["#review-compatibility"].listeners.get("click"), "function");
    const report = await state.review();
    assert.equal(report.compatible, true);
    assert.equal(state.requests[0].url, "/validation/chirp.csv");
    assert.equal(state.requests[0].options.method, "POST");
    assert.deepEqual(JSON.parse(state.requests[0].options.body.get("channels_json")), state.channels);
    assert.equal(state.elements["#compatibility-results"].hidden, false);
    assert.equal(state.elements["#compatibility-results"].dataset.state, "compatible");
    assert.match(state.elements["#compatibility-summary"].textContent, /All 2 channels are compatible/);
    assert.equal(state.elements["#generate-csv"].disabled, false);
});

test("renders warnings and permits generation after reviewing", async () => {
    const state = setup((url) => url === "/validation/chirp.csv"
        ? response(warningReport) : { ok: true, headers: { get: () => null }, blob: async () => new Blob(["csv"]) });
    await state.submit();
    assert.equal(state.elements["#compatibility-results"].dataset.state, "warning");
    assert.match(state.elements["#compatibility-summary"].textContent, /export is allowed/);
    assert.match(state.elements["#compatibility-issues"].children[0].textContent, /WARNING.*Channel 1 \(CALL\).*Power/);
    assert.deepEqual(state.requests.map((item) => item.url), ["/validation/chirp.csv", "/downloads/chirp.csv"]);
    assert.deepEqual(JSON.parse(state.requests[1].options.body.get("channels_json")), state.channels);
    assert.deepEqual(state.downloads, ["radio_loadout_custom.csv"]);
    assert.equal(state.elements["#generate-csv"].disabled, false);
});

test("renders channel errors safely and blocks CSV generation", async () => {
    const state = setup(() => response(errorReport));
    await state.submit();
    assert.equal(state.elements["#compatibility-results"].dataset.state, "error");
    assert.match(state.elements["#compatibility-summary"].textContent, /Fix 1 compatibility error/);
    assert.match(state.elements["#compatibility-issues"].children[0].textContent, /ERROR.*Channel 2 \(BAD <script>\).*mode.*Choose FM/);
    assert.equal(state.elements["#generate-csv"].disabled, true);
    assert.deepEqual(state.requests.map((item) => item.url), ["/validation/chirp.csv"]);
    assert.deepEqual(state.downloads, []);
});

test("editing immediately marks a report outdated and permits a fresh review", async () => {
    const state = setup(() => response(errorReport));
    await state.review();
    state.edit();
    assert.equal(state.elements["#compatibility-results"].dataset.state, "outdated");
    assert.match(state.elements["#compatibility-summary"].textContent, /outdated/);
    assert.equal(state.elements["#compatibility-issues"].children.length, 0);
    assert.equal(state.elements["#generate-csv"].disabled, false);
});

test("editing during a review discards its stale response and blocks that export", async () => {
    let complete;
    const state = setup(() => new Promise((resolve) => { complete = resolve; }));
    const submission = state.submit();
    state.edit();
    complete(response(successReport));
    await submission;
    assert.equal(state.elements["#compatibility-results"].hidden, true);
    assert.equal(state.requests.length, 1);
    assert.deepEqual(state.downloads, []);
});

test("a review service failure blocks export and displays an error", async () => {
    const state = setup(() => ({ ok: false, json: async () => ({ detail: "Review unavailable" }) }));
    await state.submit();
    assert.match(state.elements["#form-message"].textContent, /Review unavailable/);
    assert.equal(state.requests.length, 1);
    assert.deepEqual(state.downloads, []);
});

test("an inconsistent report cannot authorize export", async () => {
    const state = setup(() => response({ ...errorReport, compatible: true }));
    await state.submit();
    assert.match(state.elements["#form-message"].textContent, /invalid report/);
    assert.equal(state.requests.length, 1);
    assert.deepEqual(state.downloads, []);
});

const pilotId = "baofeng-bf-f8hp-pro-v053-us";
const pilotReport = {
    ...warningReport,
    radio_profile: { schema_version: 1, revision: 1, profile_id: pilotId, model: "BF-F8HP PRO",
        firmware_scope: "V0.53", hardware_verified: false },
};
const csvResponse = () => ({ ok: true, headers: { get: () => null }, blob: async () => new Blob(["csv"]) });

test("selected pilot is bound to review and download without changing channel JSON", async () => {
    const state = setup((url) => url === "/validation/chirp.csv" ? response(pilotReport) : csvResponse());
    state.selectProfile(pilotId);
    await state.submit();
    assert.equal(state.requests.length, 2);
    for (const request of state.requests) {
        assert.equal(request.options.body.get("radio_profile_id"), pilotId);
        assert.deepEqual(JSON.parse(request.options.body.get("channels_json")), state.channels);
    }
    assert.match(state.elements["#compatibility-summary"].textContent, /not hardware verified/);
    assert.deepEqual(state.downloads, ["radio_loadout_custom.csv"]);
});

test("missing, wrong, or hardware-verified profile responses cannot authorize pilot export", async () => {
    for (const report of [successReport,
        { ...pilotReport, radio_profile: { ...pilotReport.radio_profile, profile_id: "other" } },
        { ...pilotReport, radio_profile: { ...pilotReport.radio_profile, hardware_verified: true } },
        { ...pilotReport, radio_profile: { ...pilotReport.radio_profile, schema_version: 2 } }]) {
        const state = setup(() => response(report));
        state.selectProfile(pilotId);
        await state.submit();
        assert.equal(state.requests.length, 1);
        assert.deepEqual(state.downloads, []);
        assert.match(state.elements["#form-message"].textContent, /invalid report/);
    }
});

test("changing profile immediately invalidates an existing report", async () => {
    const state = setup(() => response(pilotReport));
    state.selectProfile(pilotId);
    await state.review();
    state.selectProfile("");
    assert.equal(state.elements["#compatibility-results"].dataset.state, "outdated");
    assert.equal(state.elements["#generate-csv"].disabled, false);
});

test("profile change during review discards the old target response", async () => {
    let complete;
    const state = setup(() => new Promise((resolve) => { complete = resolve; }));
    state.selectProfile(pilotId);
    const submission = state.submit();
    state.selectProfile("");
    complete(response(pilotReport));
    await submission;
    assert.equal(state.requests.length, 1);
    assert.deepEqual(state.downloads, []);
});

test("profile change during CSV fetch suppresses the stale download", async () => {
    let complete;
    const state = setup((url) => url === "/validation/chirp.csv"
        ? response(pilotReport) : new Promise((resolve) => { complete = resolve; }));
    state.selectProfile(pilotId);
    const submission = state.submit();
    await new Promise(setImmediate);
    assert.equal(state.requests.length, 2);
    state.selectProfile("");
    complete(csvResponse());
    await submission;
    assert.deepEqual(state.downloads, []);
    assert.match(state.elements["#form-message"].textContent, /changed/);
});

test("untrusted profile labels remain literal text and a generic request rejects a pilot response", async () => {
    const state = setup(() => response({ ...pilotReport, radio_profile: {
        ...pilotReport.radio_profile, model: "<script>unsafe</script>" } }));
    state.selectProfile(pilotId);
    await state.review();
    assert.match(state.elements["#compatibility-summary"].textContent, /<script>unsafe<\/script>/);
    state.selectProfile("");
    assert.equal(await state.review(), null);
});
