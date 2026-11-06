/* Portable full-loadout v2. Legacy v1 validation stays in backup-format.js, unchanged. */
globalThis.RadioLoadoutDocument = (() => {
    "use strict";
    const record = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
    function keys(value, allowed, label) {
        if (!record(value) || Object.keys(value).some((key) => !allowed.includes(key))
            || allowed.some((key) => !Object.hasOwn(value, key))) {
            throw new Error(`${label}: missing or unknown fields. Nothing was restored.`);
        }
    }
    function createValidator(catalogs, limits) {
        if (!Array.isArray(catalogs) || !Number.isInteger(limits?.channels) || limits.channels < 1) {
            throw new Error("Full-loadout validation is unavailable.");
        }
        const profiles = new Map();
        const channelLimit = limits.channels;
        for (const input of catalogs) {
            const catalog = structuredClone(input);
            const profile = catalog.radio_profile;
            if (!profile?.profile_id || !Number.isInteger(profile.revision) || profile.revision < 1
                || profiles.has(profile.profile_id)) throw new Error("Invalid profile catalog.");
            profiles.set(profile.profile_id, { catalog, planner: RadioSettingsPlan.createPlanner(catalog) });
        }
        function validate(backup) {
            if (!record(backup) || backup.format !== "radio-loadout") throw new Error('Choose a Radio Loadout JSON backup with format "radio-loadout".');
            if (!Array.isArray(backup.channels) || backup.channels.length > channelLimit) {
                throw new Error(`Loadout requires at most ${channelLimit} channels.`);
            }
            if (backup.version === 1) return { format: "radio-loadout", version: 1, channels: RadioLoadoutBackup.validate(backup) };
            if (backup.version !== 2) throw new Error(`Unsupported backup version ${JSON.stringify(backup.version)}. This builder supports versions 1 and 2.`);
            keys(backup, ["format", "version", "channels", "radio_profile", "settings_plan"], "Version-2 loadout");
            // Reuse the fixed channel draft contract, including unfinished/hidden values.
            const channels = RadioLoadoutBackup.validate({ format: "radio-loadout", version: 1, channels: backup.channels });
            let radio_profile = null;
            let settings_plan = null;
            let selected;
            if (backup.radio_profile !== null) {
                keys(backup.radio_profile, ["profile_id", "revision"], "Radio profile");
                selected = profiles.get(backup.radio_profile.profile_id);
                if (!selected || backup.radio_profile.revision !== selected.catalog.radio_profile.revision) {
                    throw new Error("Unknown radio profile or unsupported revision. Nothing was restored; no generic fallback.");
                }
                radio_profile = { profile_id: selected.catalog.radio_profile.profile_id, revision: selected.catalog.radio_profile.revision };
            }
            if (selected && backup.settings_plan === null) {
                throw new Error("A selected profile requires a settings-plan object; entries may be empty. Nothing was restored.");
            }
            if (backup.settings_plan !== null) {
                keys(backup.settings_plan, ["catalog_revision", "recommendation_id", "entries"], "Settings plan");
                const settings = backup.settings_plan;
                if (!selected || settings.catalog_revision !== selected.catalog.catalog_revision
                    || settings.recommendation_id !== selected.catalog.recommendation_id) {
                    throw new Error("Settings plan requires its exact known profile/catalog/recommendation. Nothing was restored.");
                }
                const restored = selected.planner.restore(settings.entries);
                settings_plan = { catalog_revision: settings.catalog_revision, recommendation_id: settings.recommendation_id,
                    entries: Object.fromEntries(Object.entries(restored.entries).map(([id, entry]) => [id, { ...entry }])) };
            }
            return { format: "radio-loadout", version: 2, channels, radio_profile, settings_plan };
        }
        return Object.freeze({ validate });
    }
    return Object.freeze({ format: "radio-loadout", version: 2, createValidator });
})();
