// Run with: node --test tests/js/test_builder_export.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createContext, runInContext } from "node:vm";

const source = readFileSync(
    new URL("../../src/radio_loadout/web/static/builder.js", import.meta.url),
    "utf8"
);

function setup({ missingMessage = false, failClick = false } = {}) {
    const events = [];
    const timers = [];
    const warnings = [];
    const errors = [];
    const channels = [
        {
            name: "Backup test", receive_frequency_mhz: "146.940000",
            transmit_frequency_mhz: "146.340000", receive_only: false,
            mode: "NFM", power_watts: "2.5", tone_mode: "cross",
            tone_frequency_hz: "100.0", dcs_code: "23", dcs_polarity: "NR",
            transmit_tone_mode: "ctcss", transmit_ctcss_frequency_hz: "123.0",
            transmit_dcs_code: "25", transmit_dcs_polarity: "R",
            receive_tone_mode: "dcs", receive_ctcss_frequency_hz: "88.5",
            receive_dcs_code: "26", receive_dcs_polarity: "R",
            tuning_step_khz: "12.5", scan_behavior: "S", comment: "Hidden settings too",
        },
        { name: "Second channel", receive_only: true, comment: "Preserve order" },
    ];
    const cards = channels.map((channel) => ({
        querySelectorAll: () => Object.entries(channel).map(([name, value]) => ({
            dataset: { field: name },
            type: typeof value === "boolean" ? "checkbox" : "text",
            value, checked: value,
        })),
    }));
    const button = { addEventListener: (name, handler) => { button[name] = handler; } };
    const message = {
        textContent: "", hidden: true,
        classList: { remove() {}, add(type) { events.push(type); } },
        scrollIntoView() {},
    };
    let attached = false;
    const anchor = {
        style: {},
        click() {
            assert.equal(attached, true);
            assert.equal(this.download, "radio_loadout_backup.json");
            assert.equal(this.href, "blob:test-backup");
            assert.equal(this.style.display, "none");
            events.push("click");
            if (failClick) throw new Error("Download unavailable");
        },
        remove() { attached = false; events.push("remove"); },
    };
    let capturedBlob;
    const context = createContext({
        Blob,
        URL: {
            createObjectURL(blob) { capturedBlob = blob; events.push("create-url"); return "blob:test-backup"; },
            revokeObjectURL(url) { assert.equal(url, "blob:test-backup"); events.push("revoke-url"); },
        },
        console: { warn: (...args) => warnings.push(args), error: (...args) => errors.push(args) },
        window: { setTimeout: (callback, delay) => { timers.push({ callback, delay }); }, clearTimeout() {} },
        document: {
            // Deliberately omit other controls and the template: they must not stop
            // export from registering or backing up already rendered channel cards.
            querySelector(selector) {
                if (selector === "#export-backup") return button;
                if (selector === "#channel-list") return { querySelectorAll: () => cards, addEventListener() {} };
                if (selector === "#form-message" && !missingMessage) return message;
                return null;
            },
            createElement(tag) { assert.equal(tag, "a"); return anchor; },
            body: {
                appendChild(element) {
                    assert.equal(element, anchor);
                    attached = true;
                    events.push("append");
                },
            },
        },
    });
    runInContext(source, context);
    assert.equal(typeof button.click, "function");
    assert.ok(warnings.length > 0, "missing optional controls produce diagnostics");
    assert.ok(errors.length > 0, "missing core elements produce diagnostics");
    events.length = 0;
    errors.length = 0;
    return { button, events, timers, channels, errors, blob: () => capturedBlob };
}

test("backup click downloads the current complete draft and cleans up after triggering", async () => {
    const state = setup();
    state.button.click();
    assert.equal(state.blob().type, "application/json;charset=utf-8");
    const expected = {
        format: "radio-loadout", version: 1, channels: state.channels,
    };
    assert.equal(await state.blob().text(), JSON.stringify(expected, null, 2));
    assert.deepEqual(state.events, ["create-url", "append", "click", "form-message-success"]);
    assert.ok(!state.events.includes("revoke-url"), "the URL remains available after click returns");
    assert.equal(state.timers.length, 1);
    assert.equal(state.timers[0].delay, 1000);
    state.timers[0].callback();
    assert.deepEqual(state.events.slice(-2), ["remove", "revoke-url"]);
});

test("missing feedback element does not prevent a backup download", () => {
    const state = setup({ missingMessage: true });
    state.button.click();
    assert.ok(state.events.includes("click"));
    assert.equal(state.blob().type, "application/json;charset=utf-8");
    assert.ok(state.errors.length > 0);
    state.timers[0].callback();
});

test("failed download shows an error, never success, and still releases the URL", () => {
    const state = setup({ failClick: true });
    state.button.click();
    assert.ok(state.events.includes("form-message-error"));
    assert.ok(!state.events.includes("form-message-success"));
    assert.ok(state.errors.length > 0);
    state.timers[0].callback();
    assert.deepEqual(state.events.slice(-2), ["remove", "revoke-url"]);
});
