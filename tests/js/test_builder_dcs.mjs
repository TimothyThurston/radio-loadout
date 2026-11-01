// Run with: node --test tests/js/*.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createContext, runInContext } from "node:vm";

const source = readFileSync(new URL("../../src/radio_loadout/web/static/builder.js", import.meta.url), "utf8");
const html = readFileSync(new URL("../../src/radio_loadout/web/templates/builder.html", import.meta.url), "utf8");
const template = html.split('<template id="channel-template">')[1].split("</template>")[0];
const attributes = (text) => Object.fromEntries(
    [...text.matchAll(/([\w-]+)(?:="([^"]*)")?/g)].map((match) => [match[1], match[2] ?? ""])
);

class Element {
    constructor() {
        this.children = [];
        this.dataset = {};
        this.style = {};
        this.listeners = new Map();
        this.classList = { add() {}, remove() {} };
        this.value = "";
        this.textContent = "";
    }
    addEventListener(event, listener) { this.listeners.set(event, listener); }
    appendChild(child) { this.children.push(...(child.fragment ? child.children : [child])); }
    replaceChildren(...children) {
        this.children = [];
        children.forEach((child) => this.appendChild(child));
    }
    querySelectorAll(selector) { return selector === "[data-channel-card]" ? this.children : []; }
    querySelector(selector) { return selector === "[data-channel-card]" ? this.children[0] : null; }
    scrollIntoView() {}
    remove() {}
}

class Field {
    constructor(tag, attrs, options) {
        this.tagName = tag.toUpperCase();
        this.type = tag === "select" ? "select-one" : attrs.type || "text";
        this.dataset = { field: attrs["data-field"] };
        this.attrs = attrs;
        this.options = [];
        this.checked = false;
        this.disabled = false;
        this.maxLength = Number(attrs.maxlength ?? -1);
        this.validity = { rangeUnderflow: false, rangeOverflow: false, stepMismatch: false };
        this._value = attrs.value || "";
        options.forEach((option) => this.appendChild(option));
    }
    matches(selector) {
        return selector.split(",").some((part) => Object.hasOwn(this.attrs, part.trim().slice(1, -1)));
    }
    get value() { return this._value; }
    set value(value) {
        const text = String(value);
        // Model actual select behavior: an unknown value becomes empty. Without
        // adding a real option, 777 cannot survive assignment or serialization.
        this._value = this.tagName !== "SELECT" || this.options.some((option) => option.value === text) ? text : "";
    }
    appendChild(option) {
        this.options.push(option);
        if (this.options.length === 1 || option.selected) this._value = option.value;
    }
}

function makeCard() {
    const fields = [];
    for (const match of template.matchAll(/<(input|select)\b([^>]*)>/g)) {
        const attrs = attributes(match[2]);
        if (!attrs["data-field"]) continue;
        const inner = match[1] === "select"
            ? template.slice(match.index + match[0].length, template.indexOf("</select>", match.index)) : "";
        const options = [...inner.matchAll(/<option\b([^>]*)>/g)].map((option) => {
            const attrs = attributes(option[1]);
            return { value: attrs.value, selected: Object.hasOwn(attrs, "selected") };
        });
        fields.push(new Field(match[1], attrs, options));
    }
    return {
        fields,
        querySelectorAll(selector) {
            if (selector === "[data-field]") return fields;
            if (["[data-ctcss-select]", "[data-dcs-select]"].includes(selector)) {
                return fields.filter((field) => field.matches(selector));
            }
            return [];
        },
        querySelector(selector) {
            const name = selector.match(/^\[data-field="([^"]+)"\]$/)?.[1];
            return name ? fields.find((field) => field.dataset.field === name) : new Element();
        },
    };
}

function setup(importedChannels = []) {
    const elements = Object.fromEntries([
        "channel-form", "channel-list", "generate-csv", "form-message", "draft-status",
        "channels-json", "chirp-csv-file", "import-chirp-csv", "backup-file", "import-backup", "export-backup",
    ].map((id) => [`#${id}`, new Element()]));
    elements["#channel-form"].action = "/downloads/chirp.csv";
    const fragment = () => Object.assign(new Element(), { fragment: true });
    elements["#channel-template"] = { content: {
        cloneNode() { const result = fragment(); result.appendChild(makeCard()); return result; },
    } };
    const saved = new Map();
    const downloads = [];
    const blobs = new Map();
    const requests = [];
    const context = createContext({
        Blob, FormData: class extends FormData {
            constructor(form) {
                super();
                if (form) this.append("channels_json", elements["#channels-json"].value);
            }
        },
        console: { warn() {}, error() {} },
        window: {
            clearTimeout() {}, setTimeout() { return 1; },
            localStorage: { getItem: (key) => saved.get(key) ?? null, setItem: (key, value) => saved.set(key, value) },
            fetch: async (url, options) => {
                requests.push({ url, options });
                if (url === "/imports/chirp.csv") return { ok: true, json: async () => ({ channels: importedChannels }) };
                if (url === "/validation/chirp.csv") return { ok: true, json: async () => ({
                    compatible: true, channel_count: elements["#channel-list"].children.length, issues: [],
                }) };
                return { ok: true, headers: { get: () => null }, blob: async () => new Blob(["csv"]) };
            },
        },
        URL: {
            createObjectURL(blob) { const url = `blob:${blobs.size}`; blobs.set(url, blob); return url; },
            revokeObjectURL(url) { blobs.delete(url); },
        },
        document: {
            querySelector: (selector) => elements[selector] || null,
            createDocumentFragment: fragment,
            body: new Element(),
            createElement(tag) {
                const element = new Element();
                if (tag === "a") element.click = () => downloads.push({ filename: element.download, blob: blobs.get(element.href) });
                return element;
            },
        },
    });
    runInContext(source, context);
    return {
        elements, downloads, requests, saved,
        evaluate: (code) => runInContext(code, context),
        draft: () => JSON.parse(runInContext("JSON.stringify(getChannelCards().map(getCardDraft))", context)),
        field: (index, name) => elements["#channel-list"].children[index].fields.find((field) => field.dataset.field === name),
    };
}

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
