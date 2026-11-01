/* Portable version-1 draft schema. Deliberately independent of HTML and export validation. */
globalThis.RadioLoadoutBackup = (() => {
    const numberPattern = /^-?(?:\d+|\d*\.\d+)(?:[eE][+-]?\d+)?$/;
    const steps = [1, 2.5, 5, 6.25, 9, 10, 12.5, 15, 20, 25, 30, 50, 100, 125, 200];
    const string = (kind, defaultValue, values) => Object.freeze({
        type: "string", kind, default: defaultValue, values: values && Object.freeze(values),
    });
    const fields = Object.freeze({
        name: Object.freeze({ type: "string", kind: "text", required: true }),
        receive_frequency_mhz: Object.freeze({ type: "string", kind: "number", required: true }),
        transmit_frequency_mhz: string("number", ""),
        receive_only: Object.freeze({ type: "boolean", default: false }),
        mode: string("enum", "FM", ["FM", "NFM", "AM"]),
        power_watts: string("number", "5.0"),
        tone_mode: string("enum", "none", ["none", "tone", "tsql", "dtcs", "cross"]),
        tone_frequency_hz: string("number", "100.0"),
        dcs_code: string("dcs", "23"),
        dcs_polarity: string("enum", "NN", ["NN", "NR", "RN", "RR"]),
        transmit_tone_mode: string("enum", "none", ["none", "ctcss", "dcs"]),
        transmit_ctcss_frequency_hz: string("number", "100.0"),
        transmit_dcs_code: string("dcs", "23"),
        transmit_dcs_polarity: string("enum", "N", ["N", "R"]),
        receive_tone_mode: string("enum", "none", ["none", "ctcss", "dcs"]),
        receive_ctcss_frequency_hz: string("number", "100.0"),
        receive_dcs_code: string("dcs", "23"),
        receive_dcs_polarity: string("enum", "N", ["N", "R"]),
        tuning_step_khz: string("step", "5"),
        scan_behavior: string("enum", "", ["", "S", "P"]),
        comment: string("text", ""),
    });

    function normalizeDcsCode(value) {
        if (typeof value === "number" && Number.isInteger(value)) value = String(value);
        if (typeof value === "string") value = value.trim();
        if (typeof value !== "string" || !/^[0-7]{1,3}$/.test(value)) {
            throw new Error("A DCS code must be an integer represented by three octal digits (000–777).");
        }
        return String(Number(value));
    }

    function record(value) {
        return value !== null && typeof value === "object" && !Array.isArray(value);
    }

    function rejectUnknown(value, allowed, label) {
        const unknown = Object.keys(value).find((key) => !Object.hasOwn(allowed, key));
        if (unknown !== undefined) {
            throw new Error(`${label}: unknown field ${JSON.stringify(unknown)} is not supported by backup version 1. Nothing was restored.`);
        }
    }

    function validateField(name, value, rule, label) {
        const fail = (message) => { throw new Error(`${label}, ${name}: ${message}`); };
        if (typeof value !== rule.type) fail(`must be a ${rule.type}.`);
        if (rule.type === "boolean" || value === "") return value;
        if (rule.kind === "enum" && !rule.values.includes(value)) fail("has an unsupported value.");
        if (rule.kind === "text" && /[\r\n]/.test(value)) fail("must be single-line text.");
        if (rule.kind === "number" || rule.kind === "step") {
            if (!numberPattern.test(value) || !Number.isFinite(Number(value))) {
                fail("must be an empty string or a finite decimal number stored as a string.");
            }
            if (rule.kind === "step") {
                if (!steps.includes(Number(value))) fail("has an unsupported tuning step.");
                return String(Number(value));
            }
        }
        if (rule.kind === "dcs") {
            try { return normalizeDcsCode(value); }
            catch { fail("must contain one to three octal digits (000–777), or be empty for an unfinished draft."); }
        }
        return value;
    }

    function validate(backup) {
        if (!record(backup) || backup.format !== "radio-loadout") {
            throw new Error('Choose a Radio Loadout JSON backup with format "radio-loadout".');
        }
        rejectUnknown(backup, { format: true, version: true, channels: true }, "Backup");
        if (!Number.isInteger(backup.version)) throw new Error("Backup version must be the integer 1.");
        if (backup.version !== 1) throw new Error(`Unsupported backup version ${backup.version}. This builder supports version 1.`);
        if (!Array.isArray(backup.channels) || backup.channels.length === 0) {
            throw new Error("The backup must contain a non-empty channels array.");
        }
        // Normalize every channel before any caller can replace visible cards.
        return backup.channels.map((channel, index) => {
            const label = `Backup channel ${index + 1}`;
            if (!record(channel)) throw new Error(`${label}: must be a channel object.`);
            rejectUnknown(channel, fields, label);
            return Object.fromEntries(Object.entries(fields).map(([name, rule]) => {
                if (!Object.hasOwn(channel, name)) {
                    if (rule.required) throw new Error(`${label}: missing required field ${name} (an empty string is allowed).`);
                    return [name, rule.default];
                }
                return [name, validateField(name, channel[name], rule, label)];
            }));
        });
    }

    return Object.freeze({ format: "radio-loadout", version: 1, fields, validate, normalizeDcsCode });
})();
