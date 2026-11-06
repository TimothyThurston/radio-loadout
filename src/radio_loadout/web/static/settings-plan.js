/* Pure, typed session-plan operations. No storage, channels, network or device access. */
(() => {
    "use strict";
    function createPlanner(catalog) {
        if (catalog?.schema_version !== 1 || catalog.catalog_revision !== 1
            || catalog.delivery !== "manual-guidance-only" || catalog.hardware_verified !== false
            || !catalog.radio_profile?.profile_id || catalog.radio_profile.hardware_verified !== false
            || !Array.isArray(catalog.settings) || !catalog.settings.length) {
            throw new Error("Unsupported settings guide. No plan was changed.");
        }
        const definitions = new Map();
        const previews = new WeakSet();
        const primitive = (value) => typeof value === "boolean" || typeof value === "string"
            || (typeof value === "number" && Number.isSafeInteger(value));
        for (const input of catalog.settings) {
            const setting = structuredClone(input);
            if (!/^[a-z][a-z0-9_]{0,63}$/.test(setting.setting_id) || definitions.has(setting.setting_id)
                || typeof setting.label !== "string" || !Array.isArray(setting.options) || !setting.options.length
                || setting.options.some((option, index) => !primitive(option.value) || typeof option.label !== "string"
                    || setting.options.slice(0, index).some((other) => other.value === option.value))
                || !Number.isInteger(setting.recommendation?.revision) || setting.recommendation.revision < 1
                || !setting.options.some((option) => option.value === setting.recommendation.value)) {
                throw new Error("Invalid settings definition. No plan was changed.");
            }
            definitions.set(setting.setting_id, setting);
        }
        const definition = (id) => {
            if (!definitions.has(id)) throw new Error("Unknown setting; no substitution was made.");
            return definitions.get(id);
        };
        const checkedValue = (id, value) => {
            if (!definition(id).options.some((option) => option.value === value)) {
                throw new Error("Unsupported setting value; no substitution was made.");
            }
            return value;
        };
        const freeze = (revision, entries) => Object.freeze({ revision, entries: Object.freeze(entries) });
        const checkPlan = (plan) => {
            if (!Number.isSafeInteger(plan?.revision) || plan.revision < 0
                || !plan.entries || Array.isArray(plan.entries)) throw new Error("Invalid settings plan.");
            for (const [id, entry] of Object.entries(plan.entries)) {
                checkedValue(id, entry.value);
                if (!["user-customized", "radio-loadout-recommendation"].includes(entry.origin)) {
                    throw new Error("Invalid plan origin.");
                }
            }
        };
        return Object.freeze({
            empty: () => freeze(0, {}),
            label(id, value) {
                if (value === undefined) return "Unset (radio state unknown)";
                checkedValue(id, value);
                return definition(id).options.find((option) => option.value === value).label;
            },
            setCustom(plan, id, value) {
                checkPlan(plan);
                definition(id);
                const entries = { ...plan.entries };
                if (value === undefined) delete entries[id];
                else entries[id] = Object.freeze({ value: checkedValue(id, value), origin: "user-customized" });
                return freeze(plan.revision + 1, entries);
            },
            preview(plan, proposals) {
                checkPlan(plan);
                if (!Array.isArray(proposals)) throw new Error("Invalid proposed settings.");
                const seen = new Set();
                const changes = [];
                for (const { id, value } of proposals) {
                    if (seen.has(id)) throw new Error("Duplicate proposed setting.");
                    seen.add(id);
                    checkedValue(id, value);
                    const setting = definition(id);
                    const origin = value === setting.recommendation.value ? "radio-loadout-recommendation" : "user-customized";
                    const entry = Object.freeze({ value, origin,
                        ...(origin === "radio-loadout-recommendation" ? { recommendation_revision: setting.recommendation.revision } : {}) });
                    if (plan.entries[id]?.value !== value || plan.entries[id]?.origin !== origin) {
                        changes.push(Object.freeze({ id, before: plan.entries[id], after: entry }));
                    }
                }
                const preview = Object.freeze({ base: plan, changes: Object.freeze(changes) });
                previews.add(preview);
                return preview;
            },
            apply(plan, preview) {
                checkPlan(plan);
                if (!previews.has(preview) || preview.base !== plan) {
                    throw new Error("Settings changed. Preview again before adding changes.");
                }
                const entries = { ...plan.entries };
                for (const change of preview.changes) entries[change.id] = change.after;
                previews.delete(preview);
                return freeze(plan.revision + 1, entries);
            },
        });
    }
    globalThis.RadioSettingsPlan = Object.freeze({ createPlanner });
})();
