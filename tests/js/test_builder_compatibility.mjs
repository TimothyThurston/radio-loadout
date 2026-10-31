// Run with: node --test tests/js/*.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createContext, runInContext } from "node:vm";

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
        "#form-message", "#draft-status", "#channels-json",
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
    const context = createContext({
        FormData: class extends FormData {
            constructor(form) {
                super();
                if (form) this.append("channels_json", elements["#channels-json"].value);
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
