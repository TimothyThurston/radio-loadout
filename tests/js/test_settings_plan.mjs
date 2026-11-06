import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const source = readFileSync(new URL("../../src/radio_loadout/web/static/settings-plan.js", import.meta.url), "utf8");
export function fixture() {
    return { schema_version: 1, catalog_revision: 1, delivery: "manual-guidance-only", hardware_verified: false,
        radio_profile: { profile_id: "synthetic-pilot", hardware_verified: false }, settings: [
            { setting_id: "squelch", label: "Squelch", options: [0, 1, 2, 3].map((value) => ({ value, label: String(value) })), recommendation: { value: 2, revision: 1 } },
            { setting_id: "vox", label: "VOX", options: [{ value: false, label: "Off" }, { value: true, label: "On" }], recommendation: { value: false, revision: 1 } },
            { setting_id: "backlight", label: "Backlight", options: [{ value: "always_on", label: "Always on" }, { value: 20, label: "20 seconds" }], recommendation: { value: 20, revision: 1 } },
        ] };
}
export function setup(catalog = fixture()) {
    const context = { structuredClone };
    runInNewContext(source, context);
    return context.RadioSettingsPlan.createPlanner(catalog);
}

test("empty plan does not use recommendations or manufacturer defaults", () => {
    const planner = setup();
    assert.equal(Object.keys(planner.empty().entries).length, 0);
    assert.match(planner.label("squelch", undefined), /radio state unknown/);
});

test("preview is nonmutating, selective, and applying records recommendation origin", () => {
    const planner = setup();
    const plan = planner.empty();
    const preview = planner.preview(plan, [{ id: "squelch", value: 2 }]);
    assert.equal(Object.keys(plan.entries).length, 0);
    assert.equal(preview.changes.length, 1);
    const result = planner.apply(plan, preview);
    assert.equal(result.entries.squelch.value, 2);
    assert.equal(result.entries.squelch.origin, "radio-loadout-recommendation");
    assert.equal(result.entries.squelch.recommendation_revision, 1);
    assert.equal(result.entries.vox, undefined);
    assert.equal(Object.keys(plan.entries).length, 0);
});

test("custom choices and adjusted suggestions remain distinct from recommendations", () => {
    const planner = setup();
    const initial = planner.setCustom(planner.empty(), "squelch", 3);
    assert.equal(initial.entries.squelch.origin, "user-customized");
    const preview = planner.preview(initial, [{ id: "vox", value: true }]);
    const next = planner.apply(initial, preview);
    assert.equal(next.entries.squelch.value, 3);
    assert.equal(next.entries.vox.origin, "user-customized");
    assert.equal(next.entries.vox.value, true);
    assert.equal(next.entries.vox.recommendation_revision, undefined);
});

test("review captures before values and does not overwrite deselected settings", () => {
    const planner = setup();
    const initial = planner.setCustom(planner.empty(), "squelch", 3);
    const review = planner.preview(initial, [{ id: "squelch", value: 2 }]);
    assert.equal(review.changes[0].before.value, 3);
    assert.equal(review.changes[0].after.value, 2);
    assert.throws(() => { review.changes[0].after.value = 0; }, TypeError);
    assert.equal(planner.preview(initial, []).changes.length, 0);
    assert.equal(planner.apply(initial, planner.preview(initial, [])).entries.squelch.value, 3);
});

test("a stale, repeated, forged or other-planner preview cannot be applied", () => {
    const planner = setup();
    const initial = planner.empty();
    const review = planner.preview(initial, [{ id: "squelch", value: 2 }]);
    const edited = planner.setCustom(initial, "vox", true);
    assert.throws(() => planner.apply(edited, review), /Preview again/);
    assert.throws(() => planner.apply(initial, { base: initial, changes: [] }), /Preview again/);
    assert.throws(() => setup().apply(initial, review), /Preview again/);
    planner.apply(initial, review);
    assert.throws(() => planner.apply(initial, review), /Preview again/);
});

test("invalid types/unknown fields fail atomically without substitutions", () => {
    const planner = setup();
    const initial = planner.empty();
    for (const [id, value] of [["squelch", true], ["squelch", "2"], ["squelch", 4], ["squelch", NaN],
        ["vox", 0], ["vox", null], ["vox", "false"], ["backlight", false], ["backlight", 19], ["unknown", 2]]) {
        assert.throws(() => planner.setCustom(initial, id, value));
        assert.throws(() => planner.preview(initial, [{ id: "squelch", value: 2 }, { id, value }]));
        assert.equal(Object.keys(initial.entries).length, 0);
    }
    assert.throws(() => planner.preview(initial, [{ id: "vox", value: true }, { id: "vox", value: false }]), /Duplicate/);
});

test("false, zero, and string choices remain typed; unsetting is not a factory reset", () => {
    const planner = setup();
    let plan = planner.setCustom(planner.empty(), "squelch", 0);
    plan = planner.setCustom(plan, "vox", false);
    plan = planner.setCustom(plan, "backlight", "always_on");
    assert.equal(typeof plan.entries.squelch.value, "number");
    assert.equal(typeof plan.entries.vox.value, "boolean");
    assert.equal(typeof plan.entries.backlight.value, "string");
    assert.equal(planner.setCustom(plan, "squelch", undefined).entries.squelch, undefined);
    assert.equal(plan.entries.squelch.value, 0);
    assert.match(planner.label("vox", false), /Off/);
});

test("catalog validation fails closed and source mutation cannot alter the planner", () => {
    const catalog = fixture();
    const planner = setup(catalog);
    catalog.settings[0].options[2].value = 999;
    assert.equal(planner.setCustom(planner.empty(), "squelch", 2).entries.squelch.value, 2);
    for (const change of [{ schema_version: 999 }, { catalog_revision: 2 }, { delivery: "write-radio" },
        { hardware_verified: true }, { radio_profile: {} }, { settings: [] }]) {
        assert.throws(() => setup({ ...fixture(), ...change }));
    }
    for (const alter of [
        (data) => { data.settings.push(data.settings[0]); },
        (data) => { data.settings[0].recommendation.value = 9; },
        (data) => { data.settings[0].options[0].value = {}; },
        (data) => { data.settings[0].recommendation.revision = 0; },
    ]) {
        const invalid = fixture(); alter(invalid); assert.throws(() => setup(invalid));
    }
});

test("untrusted labels are data and guidance code has no device/storage/network behavior", () => {
    const catalog = fixture();
    catalog.settings[1].options[0].label = "<img src=x onerror=alert(1)>";
    assert.equal(setup(catalog).label("vox", false), "<img src=x onerror=alert(1)>");
    for (const filename of ["settings-plan.js", "radio-settings.js"]) {
        const code = readFileSync(new URL(`../../src/radio_loadout/web/static/${filename}`, import.meta.url), "utf8");
        assert.doesNotMatch(code, /\.innerHTML\s*=|\bfetch\s*\(|navigator\.(serial|usb|hid|bluetooth)|localStorage\./);
    }
});

// Deliberately small simulated DOM: this checks controller state, not browser layout/accessibility.
function setupUI(catalog = fixture()) {
    class Element {
        constructor() { this.value = ""; this.checked = true; this.disabled = true; this.hidden = true; this.textContent = ""; this.children = []; this.listeners = {}; }
        set innerHTML(_) { throw new Error("HTML rendering is forbidden"); }
        addEventListener(type, action) { this.listeners[type] = action; }
        appendChild(child) { this.children.push(child); }
        replaceChildren() { this.children = []; }
        fire(type) { this.listeners[type](); }
    }
    const elements = Object.fromEntries(["settings-error", "settings-status", "settings-preview", "settings-diff",
        "apply-settings", "preview-settings", "clear-settings", "cancel-settings", "settings-catalog", "settings-js-required"]
        .map((id) => [`#${id}`, new Element()]));
    elements["#settings-catalog"].textContent = JSON.stringify(catalog);
    elements["#settings-js-required"].hidden = false;
    const cards = catalog.settings.map((setting) => {
        const fields = Object.fromEntries(["current", "proposed", "include", "origin"].map((name) => [`[data-${name}]`, new Element()]));
        fields["[data-proposed]"].value = JSON.stringify(setting.recommendation.value);
        return { dataset: { setting: setting.setting_id }, fields,
            querySelector: (selector) => fields[selector],
            querySelectorAll: () => [fields["[data-proposed]"], fields["[data-include]"]],
        };
    });
    const context = { structuredClone, document: {
        querySelector: (selector) => elements[selector],
        querySelectorAll: (selector) => selector === "[data-setting]" ? cards : cards.flatMap((card) => Object.entries(card.fields).filter(([key]) => key !== "[data-origin]").map(([, value]) => value)),
        createElement: () => new Element(),
    } };
    runInNewContext(source, context);
    runInNewContext(readFileSync(new URL("../../src/radio_loadout/web/static/radio-settings.js", import.meta.url), "utf8"), context);
    return { elements, cards, editor: context.RadioSettingsEditor, click: (id) => elements[`#${id}`].fire("click"),
        field: (id, name) => cards.find((card) => card.dataset.setting === id).fields[`[data-${name}]`],
    };
}

test("controller previews without changing plan, cancels, and applies only selected adjustments", () => {
    const ui = setupUI();
    assert.equal(ui.elements["#preview-settings"].disabled, false);
    assert.equal(ui.elements["#settings-js-required"].hidden, true);
    ui.field("squelch", "current").value = "3";
    ui.field("squelch", "current").fire("change");
    ui.field("squelch", "include").checked = false;
    ui.field("vox", "proposed").value = "true";
    ui.click("preview-settings");
    assert.equal(ui.elements["#settings-diff"].children.length, 2);
    assert.equal(ui.field("vox", "current").value, "");
    ui.click("cancel-settings");
    assert.equal(ui.field("vox", "current").value, "");
    ui.click("preview-settings");
    ui.click("apply-settings");
    assert.equal(ui.field("squelch", "current").value, "3");
    assert.equal(ui.field("vox", "current").value, "true");
    assert.match(ui.field("vox", "origin").textContent, /user-customized/);
    assert.match(ui.field("backlight", "origin").textContent, /radio-loadout-recommendation/);
    assert.match(ui.elements["#settings-status"].textContent, /No radio, channels or backups/);
});

test("controller invalidates a preview after proposal, inclusion or current-plan edits", () => {
    for (const field of ["proposed", "include", "current"]) {
        const ui = setupUI();
        ui.click("preview-settings");
        assert.equal(ui.elements["#apply-settings"].disabled, false);
        const input = ui.field("squelch", field);
        if (field !== "include") input.value = "1";
        input.fire("change");
        assert.equal(ui.elements["#apply-settings"].disabled, true);
        assert.equal(ui.elements["#settings-preview"].hidden, true);
        ui.click("apply-settings"); // Even a programmatically dispatched stale click must fail.
        assert.equal(ui.elements["#settings-error"].hidden, false);
        assert.equal(ui.field("vox", "current").value, "");
    }
});

test("controller rejects invalid values without erasing the plan, clears locally, and restarts empty", () => {
    const ui = setupUI();
    const current = ui.field("squelch", "current");
    current.value = "3"; current.fire("change");
    current.value = "true"; current.fire("change");
    assert.equal(current.value, "3");
    assert.match(ui.elements["#settings-error"].textContent, /Unsupported setting/);
    ui.click("clear-settings");
    assert.equal(current.value, "");
    assert.match(ui.elements["#settings-status"].textContent, /No factory reset/);
    assert.equal(setupUI().field("squelch", "current").value, "");
});

test("controller renders malicious source labels literally and fails closed on bad catalog", () => {
    const catalog = fixture(); catalog.settings[0].label = "<img src=x onerror=alert(1)>";
    const ui = setupUI(catalog);
    ui.click("preview-settings");
    assert.match(ui.elements["#settings-diff"].children[0].textContent, /^<img src=x/);
    const bad = setupUI({ ...fixture(), schema_version: 999 });
    assert.equal(bad.elements["#preview-settings"].disabled, true);
    assert.equal(bad.field("squelch", "current").disabled, true);
    assert.equal(bad.elements["#settings-error"].hidden, false);
    assert.equal(bad.elements["#settings-js-required"].hidden, false);
});

test("editor snapshot/restore preserves typed entries and refuses a partly invalid replacement", () => {
    const ui = setupUI();
    ui.editor.restore({ squelch: { value: 0, origin: "user-customized" },
        vox: { value: false, origin: "radio-loadout-recommendation", recommendation_revision: 1 } });
    assert.equal(ui.field("squelch", "current").value, "0");
    assert.equal(ui.field("vox", "current").value, "false");
    assert.match(ui.field("vox", "origin").textContent, /radio-loadout-recommendation/);
    const before = JSON.stringify(ui.editor.snapshot());
    const copy = ui.editor.snapshot(); copy.squelch.value = 3;
    assert.equal(JSON.stringify(ui.editor.snapshot()), before);
    ui.click("preview-settings");
    assert.equal(ui.elements["#settings-preview"].hidden, false);
    assert.throws(() => ui.editor.restore({ squelch: { value: 3, origin: "user-customized" },
        vox: { value: "false", origin: "user-customized" } }));
    assert.equal(JSON.stringify(ui.editor.snapshot()), before);
    assert.equal(ui.elements["#settings-preview"].hidden, false);
});
