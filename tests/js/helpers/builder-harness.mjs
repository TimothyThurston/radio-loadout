// Shared simulated builder DOM, derived from the real template.
import { readFileSync } from "node:fs";
import { createContext, runInContext } from "node:vm";

const inputLimits = JSON.parse(readFileSync(new URL("../../../src/radio_loadout/web/static/input-limits.json", import.meta.url), "utf8"));
const backupSource = readFileSync(new URL("../../../src/radio_loadout/web/static/backup-format.js", import.meta.url), "utf8");
const source = readFileSync(new URL("../../../src/radio_loadout/web/static/builder.js", import.meta.url), "utf8");
const html = readFileSync(new URL("../../../src/radio_loadout/web/templates/builder.html", import.meta.url), "utf8");
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
        const classes = new Set();
        this.classList = { add: (...names) => names.forEach((name) => classes.add(name)),
            remove: (...names) => names.forEach((name) => classes.delete(name)), contains: (name) => classes.has(name) };
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

export function setupBuilderHarness(importedChannels = [], hooks = {}) {
    const elements = Object.fromEntries([
        "channel-form", "channel-list", "generate-csv", "form-message", "draft-status",
        "input-limits", "chirp-import-review", "chirp-import-summary", "chirp-import-messages",
        "confirm-chirp-import", "cancel-chirp-import", "channels-json", "chirp-csv-file", "import-chirp-csv", "backup-file", "import-backup", "export-backup",
    ].map((id) => [`#${id}`, new Element()]));
    const satelliteChoices = [];
    if (hooks.satellites) {
        for (const id of ["preview-satellite", "add-satellite", "cancel-satellite", "satellite-preview", "satellite-summary", "satellite-issues", "satellite-catalog"]) elements[`#${id}`] = new Element();
        elements["#satellite-catalog"].textContent = JSON.stringify(hooks.satellites);
        elements["#add-satellite"].disabled = true;
        for (const channel of hooks.satellites.packs[0].channels) {
            const choice = new Element(); choice.checked = true; choice.dataset.satelliteChannel = channel.channel_id;
            satelliteChoices.push(choice);
        }
    }
    elements["#input-limits"].textContent = JSON.stringify(inputLimits);
    elements["#channel-form"].action = "/downloads/chirp.csv";
    const fragment = () => Object.assign(new Element(), { fragment: true });
    elements["#channel-template"] = { content: {
        cloneNode() { const result = fragment(); result.appendChild(makeCard()); return result; },
    } };
    const saved = new Map();
    const downloads = [];
    const blobs = new Map();
    const requests = [];
    const storage = { getItem: (key) => saved.get(key) ?? null, setItem: (key, value) => saved.set(key, value), removeItem: (key) => saved.delete(key) };
    const context = createContext({
        Blob, structuredClone, FormData: class extends FormData {
            constructor(form) {
                super();
                if (form) this.append("channels_json", elements["#channels-json"].value);
            }
        },
        console: { warn() {}, error() {} },
        window: {
            confirm: (message) => hooks.confirm ? hooks.confirm(message) : true,
            clearTimeout() {}, setTimeout() { return 1; },
            localStorage: storage,
            fetch: async (url, options) => {
                requests.push({ url, options });
                if (hooks.fetch) return hooks.fetch(url, options);
                if (url === "/imports/chirp.csv") return { ok: true, json: async () => ({ channels: importedChannels, import_report: { requires_confirmation: false, messages: [], omitted_messages: 0, loss_count: 0 } }) };
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
            querySelectorAll: (selector) => selector === "[data-satellite-channel]" ? satelliteChoices : [],
            createDocumentFragment: fragment,
            body: new Element(),
            createElement(tag) {
                const element = new Element();
                if (tag === "a") element.click = () => downloads.push({ filename: element.download, blob: blobs.get(element.href) });
                return element;
            },
        },
    });
    runInContext(backupSource, context);
    if (hooks.satellites) runInContext(readFileSync(new URL("../../../src/radio_loadout/web/static/satellite-presets.js", import.meta.url), "utf8"), context);
    if (hooks.catalog) {
        for (const name of ["settings-plan.js", "loadout-format.js"]) {
            runInContext(readFileSync(new URL(`../../../src/radio_loadout/web/static/${name}`, import.meta.url), "utf8"), context);
        }
        for (const id of ["radio-profile", "builder-settings", "export-loadout", "settings-catalog"]) elements[`#${id}`] = new Element();
        elements["#settings-catalog"].textContent = JSON.stringify(hooks.catalog);
        elements["#builder-settings"].dataset.profileId = hooks.catalog.radio_profile.profile_id;
        const planner = context.RadioSettingsPlan.createPlanner(hooks.catalog);
        let plan = planner.empty();
        context.RadioSettingsEditor = {
            snapshot: () => structuredClone(plan.entries),
            restore: (entries) => { if (hooks.restoreSettings) hooks.restoreSettings(entries); plan = planner.restore(entries); },
        };
    }
    runInContext(source, context);
    return {
        elements, downloads, requests, saved, storage, satelliteChoices,
        evaluate: (code) => runInContext(code, context),
        draft: () => JSON.parse(runInContext("JSON.stringify(getChannelCards().map(getCardDraft))", context)),
        field: (index, name) => elements["#channel-list"].children[index].fields.find((field) => field.dataset.field === name),
    };
}

