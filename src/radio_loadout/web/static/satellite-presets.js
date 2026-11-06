/* Non-mutating receive-only addition planning; no fetch, storage or device access. */
globalThis.RadioSatellitePresets = (() => {
    "use strict";
    function plan(catalog, presetId, selectedIds, existing, channelLimit) {
        if (catalog?.schema_version !== 1 || !Array.isArray(catalog.packs)
            || !Array.isArray(existing) || !Number.isInteger(channelLimit) || channelLimit < 1
            || existing.length > channelLimit) throw new Error("Satellite preset data or channel limits are unavailable.");
        const packs = catalog.packs.filter((pack) => pack?.preset_id === presetId);
        if (packs.length !== 1) throw new Error("Unknown or ambiguous satellite preset; no fallback was used.");
        const pack = packs[0];
        if (!Number.isInteger(pack.revision) || pack.revision < 1
            || pack.hardware_verified !== false || pack.operational_status !== "unknown-not-live-checked"
            || !/^\d{4}-\d{2}-\d{2}$/.test(pack.frequency_sources_checked_on)
            || !Array.isArray(pack.channels) || !pack.channels.length) throw new Error("Unsupported satellite preset metadata.");
        const definitions = new Map();
        for (const item of pack.channels) {
            if (typeof item?.channel_id !== "string" || definitions.has(item.channel_id)
                || item.receive_only !== true || item.transmit_frequency_hz !== null
                || item.role !== "earth-station-receive-downlink" || item.mode !== "FM"
                || !Number.isSafeInteger(item.receive_frequency_hz) || item.receive_frequency_hz <= 0) {
                throw new Error("Satellite monitoring presets must contain explicit receive-only FM downlinks.");
            }
            const draft = RadioLoadoutBackup.validate({ format: "radio-loadout", version: 1, channels: [item.draft] })[0];
            if (draft.receive_only !== true || draft.transmit_frequency_mhz !== "" || draft.mode !== "FM"
                || draft.tone_mode !== "none" || Math.round(Number(draft.receive_frequency_mhz) * 1e6) !== item.receive_frequency_hz) {
                throw new Error("Satellite preset channel does not match its receive-only nominal frequency.");
            }
            definitions.set(item.channel_id, { item, draft });
        }
        if (!Array.isArray(selectedIds) || !selectedIds.length || new Set(selectedIds).size !== selectedIds.length
            || selectedIds.some((id) => !definitions.has(id))) throw new Error("Select at least one known satellite channel, without duplicates.");
        const current = existing.length ? RadioLoadoutBackup.validate({ format: "radio-loadout", version: 1, channels: existing }) : [];
        const blank = RadioLoadoutBackup.validate({ format: "radio-loadout", version: 1, channels: [{ name: "", receive_frequency_mhz: "" }] })[0];
        const pristine = current.length === 1 && JSON.stringify(current[0]) === JSON.stringify(blank);
        const additions = [];
        const skipped = [];
        for (const id of selectedIds) {
            const { item, draft } = definitions.get(id);
            // Never overwrite, convert or treat a transmit-enabled/tone-filtered
            // channel at the same frequency as the safe RX-only monitoring entry.
            const duplicate = current.some((channel) => channel.receive_only === true && channel.mode === "FM"
                && channel.tone_mode === "none" && channel.receive_frequency_mhz !== ""
                && Math.round(Number(channel.receive_frequency_mhz) * 1e6) === item.receive_frequency_hz);
            if (duplicate) skipped.push(id);
            else additions.push(Object.freeze({ ...draft }));
        }
        const replacePristine = pristine && additions.length > 0;
        const resultingCount = current.length - Number(replacePristine) + additions.length;
        if (resultingCount > channelLimit) throw new Error(`Adding these channels exceeds the ${channelLimit}-channel limit. No channels were changed.`);
        const reviewChannels = additions.map((draft) => Object.freeze({ name: draft.name,
            receive_frequency_mhz: Number(draft.receive_frequency_mhz), transmit_frequency_mhz: null,
            receive_only: true, mode: "FM", tone_mode: "none", power_watts: Number(draft.power_watts),
            tuning_step_khz: Number(draft.tuning_step_khz), scan_behavior: draft.scan_behavior, comment: draft.comment }));
        return Object.freeze({ preset_id: pack.preset_id, revision: pack.revision,
            additions: Object.freeze(additions), reviewChannels: Object.freeze(reviewChannels),
            skipped: Object.freeze(skipped), replacePristine, resultingCount });
    }
    return Object.freeze({ plan });
})();
