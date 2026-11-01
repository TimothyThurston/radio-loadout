const CTCSS_FREQUENCIES = [
    67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5,
    94.8, 97.4, 100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0,
    127.3, 131.8, 136.5, 141.3, 146.2, 151.4, 156.7, 159.8, 162.2,
    165.5, 167.9, 171.3, 173.8, 177.3, 179.9, 183.5, 186.2, 189.9,
    192.8, 196.6, 199.5, 203.5, 206.5, 210.7, 218.1, 225.7, 229.1,
    233.6, 241.8, 250.3, 254.1,
];

const DCS_CODES = [
    23, 25, 26, 31, 32, 36, 43, 47, 51, 53, 54, 65, 71, 72, 73, 74,
    114, 115, 116, 122, 125, 131, 132, 134, 143, 145, 152, 155, 156,
    162, 165, 172, 174, 205, 212, 223, 225, 226, 243, 244, 245, 246,
    251, 252, 255, 261, 263, 265, 266, 271, 274, 306, 311, 315, 325,
    331, 332, 343, 346, 351, 356, 364, 365, 371, 411, 412, 413, 423,
    431, 432, 445, 446, 452, 454, 455, 462, 464, 465, 466, 503, 506,
    516, 523, 526, 532, 546, 565, 606, 612, 624, 627, 631, 632, 654,
    662, 664, 703, 712, 723, 731, 732, 734, 743, 754,
];

const NOAA_WEATHER_CHANNELS = [
    { name: "NOAA 1", receive_frequency_mhz: 162.4 },
    { name: "NOAA 2", receive_frequency_mhz: 162.425 },
    { name: "NOAA 3", receive_frequency_mhz: 162.45 },
    { name: "NOAA 4", receive_frequency_mhz: 162.475 },
    { name: "NOAA 5", receive_frequency_mhz: 162.5 },
    { name: "NOAA 6", receive_frequency_mhz: 162.525 },
    { name: "NOAA 7", receive_frequency_mhz: 162.55 },
];

const AMATEUR_CALLING_CHANNELS = [
    {
        name: "2M CALL",
        receive_frequency_mhz: 146.52,
        comment: "Two-meter national simplex calling frequency",
    },
    {
        name: "1.25 CALL",
        receive_frequency_mhz: 223.5,
        comment: "1.25-meter national simplex calling frequency",
    },
    {
        name: "70CM CALL",
        receive_frequency_mhz: 446.0,
        comment: "70-centimeter national simplex calling frequency",
    },
];

const DRAFT_STORAGE_KEY = "radio-loadout-builder-draft-v1";

const form = document.querySelector("#channel-form");
const channelList = document.querySelector("#channel-list");
const channelTemplate = document.querySelector("#channel-template");
const addChannelButton = document.querySelector("#add-channel");
const addNoaaWeatherButton = document.querySelector(
    "#add-noaa-weather"
);
const addAmateurCallingButton = document.querySelector(
    "#add-amateur-calling"
);
const clearDraftButton = document.querySelector("#clear-draft");
const channelsJsonInput = document.querySelector("#channels-json");
const draftStatus = document.querySelector("#draft-status");
const presetStatus = document.querySelector("#preset-status");
const formMessage = document.querySelector("#form-message");
const generateCsvButton = document.querySelector("#generate-csv");
const chirpCsvFileInput = document.querySelector("#chirp-csv-file");
const importChirpCsvButton = document.querySelector("#import-chirp-csv");
const exportBackupButton = document.querySelector("#export-backup");
const importBackupButton = document.querySelector("#import-backup");
const backupFileInput = document.querySelector("#backup-file");
const chirpImportPanel = document.querySelector("#chirp-import-review");
const chirpImportSummary = document.querySelector("#chirp-import-summary");
const chirpImportMessages = document.querySelector("#chirp-import-messages");
const confirmChirpImportButton = document.querySelector("#confirm-chirp-import");
const cancelChirpImportButton = document.querySelector("#cancel-chirp-import");
let pendingChirpImport = null;
let chirpImportRequestId = 0;
const reviewCompatibilityButton = document.querySelector("#review-compatibility");
const compatibilityPanel = document.querySelector("#compatibility-results");
const compatibilitySummary = document.querySelector("#compatibility-summary");
const compatibilityIssues = document.querySelector("#compatibility-issues");

let compatibilityReport = null;
let compatibilityRequestId = 0;
let csvGenerationInProgress = false;

let pendingSaveTimer = null;
let statusClearTimer = null;
let presetStatusClearTimer = null;

function getChannelCards() {
    return [
        ...channelList.querySelectorAll("[data-channel-card]"),
    ];
}

function getField(card, fieldName) {
    return card.querySelector(`[data-field="${fieldName}"]`);
}

function optionalNumber(card, fieldName) {
    const input = getField(card, fieldName);

    if (input.disabled || input.value === "") {
        return null;
    }

    return Number(input.value);
}

function showDraftStatus(message) {
    if (!draftStatus) {
        console.warn("Builder draft status element is missing:", message);
        return;
    }
    window.clearTimeout(statusClearTimer);
    draftStatus.textContent = message;

    statusClearTimer = window.setTimeout(() => {
        draftStatus.textContent = "";
    }, 2500);
}

function showPresetStatus(message) {
    if (!presetStatus) {
        console.warn("Builder preset status element is missing:", message);
        return;
    }
    window.clearTimeout(presetStatusClearTimer);
    presetStatus.textContent = message;

    presetStatusClearTimer = window.setTimeout(() => {
        presetStatus.textContent = "";
    }, 4000);
}

function clearFormMessage() {
    if (!formMessage) {
        return;
    }
    formMessage.textContent = "";
    formMessage.classList.remove(
        "form-message-error",
        "form-message-success"
    );
    formMessage.hidden = true;
}

function showFormMessage(message, type) {
    if (!formMessage) {
        console.error("Builder message element is missing:", message);
        return;
    }
    formMessage.textContent = message;
    formMessage.classList.remove(
        "form-message-error",
        "form-message-success"
    );
    formMessage.classList.add(`form-message-${type}`);
    formMessage.hidden = false;
    formMessage.scrollIntoView({
        behavior: "smooth",
        block: "center",
    });
}

function populateToneOptions(card) {
    card.querySelectorAll("[data-ctcss-select]").forEach(
        (select) => {
            CTCSS_FREQUENCIES.forEach((frequency) => {
                const option = document.createElement("option");

                option.value = frequency.toFixed(1);
                option.textContent = frequency.toFixed(1);

                if (frequency === 100.0) {
                    option.selected = true;
                }

                select.appendChild(option);
            });
        }
    );

    card.querySelectorAll("[data-dcs-select]").forEach(
        (select) => {
            DCS_CODES.forEach((code) => {
                const option = document.createElement("option");

                option.value = String(code);
                option.textContent = String(code).padStart(
                    3,
                    "0"
                );

                if (code === 23) {
                    option.selected = true;
                }

                select.appendChild(option);
            });
        }
    );
}

function updateChannelNumbers() {
    const cards = getChannelCards();

    cards.forEach((card, index) => {
        card.querySelector(
            "[data-channel-number]"
        ).textContent = `Channel ${index + 1}`;

        const moveUpButton = card.querySelector(
            "[data-move-channel-up]"
        );
        const moveDownButton = card.querySelector(
            "[data-move-channel-down]"
        );
        const removeButton = card.querySelector(
            "[data-remove-channel]"
        );

        moveUpButton.disabled = index === 0;
        moveDownButton.disabled = index === cards.length - 1;
        removeButton.disabled = cards.length === 1;
    });
}

function setSectionVisible(card, selector, visible) {
    card.querySelectorAll(selector).forEach((section) => {
        section.hidden = !visible;

        section.querySelectorAll("input, select").forEach(
            (control) => {
                control.disabled = !visible;

                if (
                    control.matches(
                        "[data-ctcss-select], [data-dcs-select]"
                    )
                ) {
                    control.required = visible;
                }
            }
        );
    });
}

function updateTransmitField(card, clearValue = true) {
    const receiveOnlyInput = getField(
        card,
        "receive_only"
    );
    const transmitInput = getField(
        card,
        "transmit_frequency_mhz"
    );

    transmitInput.disabled = receiveOnlyInput.checked;

    if (receiveOnlyInput.checked && clearValue) {
        transmitInput.value = "";
    }
}

function updateIndependentToneFields(card, direction) {
    const toneMode = getField(
        card,
        `${direction}_tone_mode`
    ).value;

    setSectionVisible(
        card,
        `[data-${direction}-ctcss-settings]`,
        toneMode === "ctcss"
    );

    setSectionVisible(
        card,
        `[data-${direction}-dcs-settings]`,
        toneMode === "dcs"
    );
}

function updateToneFields(card) {
    const toneMode = getField(card, "tone_mode").value;
    const usesQuickCtcss =
        toneMode === "tone" || toneMode === "tsql";
    const usesQuickDcs = toneMode === "dtcs";
    const usesCrossTone = toneMode === "cross";

    setSectionVisible(
        card,
        "[data-quick-ctcss-settings]",
        usesQuickCtcss
    );

    setSectionVisible(
        card,
        "[data-quick-dcs-settings]",
        usesQuickDcs
    );

    setSectionVisible(
        card,
        "[data-cross-tone-settings]",
        usesCrossTone
    );

    if (usesCrossTone) {
        updateIndependentToneFields(card, "transmit");
        updateIndependentToneFields(card, "receive");
    }
}

function createChannelCard(container = channelList) {
    const newChannel = channelTemplate.content.cloneNode(true);
    const newCard = newChannel.querySelector("[data-channel-card]");

    container.appendChild(newChannel);

    populateToneOptions(newCard);

    return newCard;
}

function initializeChannelCard(card) {
    updateTransmitField(card, false);
    updateToneFields(card);
}

function getCardDraft(card) {
    const cardDraft = {};

    card.querySelectorAll("[data-field]").forEach((field) => {
        if (field.type === "checkbox") {
            cardDraft[field.dataset.field] = field.checked;
        } else {
            cardDraft[field.dataset.field] = field.value;
        }
    });

    return cardDraft;
}

function saveDraft(throwOnError = false) {
    invalidateCompatibilityReport();
    window.clearTimeout(pendingSaveTimer);
    pendingSaveTimer = null;

    const draft = getChannelCards().map(getCardDraft);

    try {
        window.localStorage.setItem(
            DRAFT_STORAGE_KEY,
            JSON.stringify(draft)
        );

        showDraftStatus("Draft saved locally.");
    } catch (error) {
        if (throwOnError) throw error;
        showDraftStatus("Draft could not be saved.");
    }
}

function scheduleDraftSave() {
    invalidateCompatibilityReport();
    window.clearTimeout(pendingSaveTimer);

    pendingSaveTimer = window.setTimeout(() => {
        saveDraft();
    }, 250);
}

function loadDraft() {
    try {
        const savedDraft = window.localStorage.getItem(
            DRAFT_STORAGE_KEY
        );

        if (savedDraft === null) {
            return null;
        }

        const parsedDraft = JSON.parse(savedDraft);

        if (
            !Array.isArray(parsedDraft)
            || parsedDraft.length === 0
        ) {
            return null;
        }

        return parsedDraft;
    } catch {
        return null;
    }
}

function normalizeDcsCode(value) {
    return RadioLoadoutBackup.normalizeDcsCode(value);
}

function applyDraftToCard(card, cardDraft) {
    if (
        cardDraft === null
        || typeof cardDraft !== "object"
        || Array.isArray(cardDraft)
    ) {
        return;
    }

    Object.entries(cardDraft).forEach(
        ([fieldName, value]) => {
            const field = getField(card, fieldName);

            if (!field) {
                return;
            }

            if (field.type === "checkbox") {
                field.checked = Boolean(value);
            } else if (
                value === null
                || value === undefined
                || value === ""
            ) {
                field.value = "";
            } else if (field.matches("[data-ctcss-select]")) {
                // Match existing numeric choices, preserving draft precision when
                // a custom value has no equivalent option (e.g. 50.04 Hz).
                const existing = [...field.options].find((option) => (
                    Number(option.value) === Number(value)
                ));
                const toneValue = existing ? existing.value : String(value);

                if (![...field.options].some((option) => option.value === toneValue)) {
                    const option = document.createElement("option");
                    option.value = toneValue;
                    option.textContent = toneValue;
                    field.appendChild(option);
                }

                field.value = toneValue;
            } else if (field.matches("[data-dcs-select]")) {
                const code = normalizeDcsCode(value);
                if (![...field.options].some((option) => option.value === code)) {
                    const option = document.createElement("option");
                    option.value = code;
                    option.textContent = `${code.padStart(3, "0")} (generic)`;
                    field.appendChild(option);
                }
                field.value = code;
            } else {
                field.value = String(value);
            }
        }
    );
}

function replaceChannelCards(channels) {
    const replacement = document.createDocumentFragment();

    channels.forEach((cardDraft) => {
        const card = createChannelCard(replacement);

        applyDraftToCard(card, cardDraft);
        initializeChannelCard(card);
    });

    channelList.replaceChildren(replacement);
    invalidateCompatibilityReport();
    updateChannelNumbers();
}

function restoreDraft() {
    const savedDraft = loadDraft();

    if (savedDraft === null) {
        return false;
    }

    replaceChannelCards(savedDraft);
    showDraftStatus("Saved draft restored.");

    return true;
}

function addChannel(shouldSave = true) {
    invalidateCompatibilityReport();
    const newCard = createChannelCard();

    initializeChannelCard(newCard);
    updateChannelNumbers();

    if (shouldSave) {
        saveDraft();
    }
}

function copyChannelValues(sourceCard, targetCard) {
    // The shared population path also adds imported/custom select options.
    applyDraftToCard(targetCard, getCardDraft(sourceCard));
}

function duplicateChannel(card) {
    const newChannel = channelTemplate.content.cloneNode(true);

    card.after(newChannel);

    const duplicatedCard = card.nextElementSibling;

    populateToneOptions(duplicatedCard);
    copyChannelValues(card, duplicatedCard);

    const originalName = getField(
        card,
        "name"
    ).value.trim();

    if (originalName !== "") {
        getField(duplicatedCard, "name").value =
            `${originalName} COPY`.slice(0, 32);
    }

    initializeChannelCard(duplicatedCard);
    updateChannelNumbers();
    saveDraft();

    const nameField = getField(duplicatedCard, "name");

    nameField.focus();
    nameField.select();
}

function moveChannelUp(card) {
    const previousCard = card.previousElementSibling;

    if (
        previousCard
        && previousCard.matches("[data-channel-card]")
    ) {
        channelList.insertBefore(card, previousCard);
        updateChannelNumbers();
        saveDraft();
    }
}

function moveChannelDown(card) {
    const nextCard = card.nextElementSibling;

    if (
        nextCard
        && nextCard.matches("[data-channel-card]")
    ) {
        channelList.insertBefore(nextCard, card);
        updateChannelNumbers();
        saveDraft();
    }
}

function isBlankChannelCard(card) {
    return (
        getField(card, "name").value.trim() === ""
        && getField(
            card,
            "receive_frequency_mhz"
        ).value === ""
        && getField(
            card,
            "transmit_frequency_mhz"
        ).value === ""
        && getField(card, "comment").value.trim() === ""
    );
}

function frequencyKey(frequencyMhz) {
    return Number(frequencyMhz).toFixed(6);
}

function noaaChannelDraft(channel) {
    return {
        name: channel.name,
        receive_frequency_mhz:
            channel.receive_frequency_mhz,
        transmit_frequency_mhz: null,
        mode: "NFM",
        power_watts: 5.0,
        receive_only: true,
        tone_mode: "none",
        tuning_step_khz: 25,
        scan_behavior: "",
        comment: "NOAA Weather Radio — receive only",
    };
}

function addNoaaWeatherPreset() {
    const existingFrequencies = new Set();

    getChannelCards().forEach((card) => {
        const value = getField(
            card,
            "receive_frequency_mhz"
        ).value;

        if (value !== "") {
            existingFrequencies.add(frequencyKey(value));
        }
    });

    getChannelCards().forEach((card) => {
        if (isBlankChannelCard(card)) {
            card.remove();
        }
    });

    let addedCount = 0;
    let skippedCount = 0;

    NOAA_WEATHER_CHANNELS.forEach((channel) => {
        const key = frequencyKey(
            channel.receive_frequency_mhz
        );

        if (existingFrequencies.has(key)) {
            skippedCount += 1;
            return;
        }

        const card = createChannelCard();

        applyDraftToCard(
            card,
            noaaChannelDraft(channel)
        );
        initializeChannelCard(card);

        existingFrequencies.add(key);
        addedCount += 1;
    });

    if (getChannelCards().length === 0) {
        addChannel(false);
    }

    updateChannelNumbers();
    saveDraft();

    if (addedCount === 0) {
        showPresetStatus(
            "All seven NOAA Weather channels are already "
            + "in this loadout."
        );
    } else if (skippedCount > 0) {
        showPresetStatus(
            `Added ${addedCount} NOAA Weather channels; `
            + `skipped ${skippedCount} already present.`
        );
    } else {
        showPresetStatus(
            "Added all seven NOAA Weather channels."
        );
    }
}

function amateurCallingChannelDraft(channel) {
    return {
        name: channel.name,
        receive_frequency_mhz:
            channel.receive_frequency_mhz,
        transmit_frequency_mhz:
            channel.receive_frequency_mhz,
        mode: "FM",
        power_watts: 5.0,
        receive_only: false,
        tone_mode: "none",
        tuning_step_khz: 5,
        scan_behavior: "",
        comment: channel.comment,
    };
}

function addAmateurCallingPreset() {
    const existingFrequencies = new Set();

    getChannelCards().forEach((card) => {
        const value = getField(
            card,
            "receive_frequency_mhz"
        ).value;

        if (value !== "") {
            existingFrequencies.add(frequencyKey(value));
        }
    });

    getChannelCards().forEach((card) => {
        if (isBlankChannelCard(card)) {
            card.remove();
        }
    });

    let addedCount = 0;
    let skippedCount = 0;

    AMATEUR_CALLING_CHANNELS.forEach((channel) => {
        const key = frequencyKey(
            channel.receive_frequency_mhz
        );

        if (existingFrequencies.has(key)) {
            skippedCount += 1;
            return;
        }

        const card = createChannelCard();

        applyDraftToCard(
            card,
            amateurCallingChannelDraft(channel)
        );
        initializeChannelCard(card);

        existingFrequencies.add(key);
        addedCount += 1;
    });

    if (getChannelCards().length === 0) {
        addChannel(false);
    }

    updateChannelNumbers();
    saveDraft();

    if (addedCount === 0) {
        showPresetStatus(
            "All three Amateur Calling channels are already "
            + "in this loadout."
        );
    } else if (skippedCount > 0) {
        showPresetStatus(
            `Added ${addedCount} Amateur Calling channels; `
            + `skipped ${skippedCount} already present.`
        );
    } else {
        showPresetStatus(
            "Added all three Amateur Calling channels."
        );
    }
}

function clearDraft() {
    const shouldClear = window.confirm(
        "Clear every channel in the current draft?"
    );

    if (!shouldClear) {
        return;
    }

    try {
        window.localStorage.removeItem(
            DRAFT_STORAGE_KEY
        );
    } catch {
        showDraftStatus(
            "Saved draft could not be cleared."
        );

        return;
    }

    channelList.replaceChildren();
    addChannel(false);
    showDraftStatus("Draft cleared.");
}

function channelDataFromCard(card) {
    return {
        name: getField(card, "name").value,

        receive_frequency_mhz: Number(
            getField(
                card,
                "receive_frequency_mhz"
            ).value
        ),

        transmit_frequency_mhz: optionalNumber(
            card,
            "transmit_frequency_mhz"
        ),

        mode: getField(card, "mode").value,

        power_watts: Number(
            getField(card, "power_watts").value
        ),

        receive_only: getField(
            card,
            "receive_only"
        ).checked,

        tone_mode: getField(
            card,
            "tone_mode"
        ).value,

        tone_frequency_hz: optionalNumber(
            card,
            "tone_frequency_hz"
        ),

        dcs_code: optionalNumber(
            card,
            "dcs_code"
        ),

        dcs_polarity: getField(
            card,
            "dcs_polarity"
        ).value,

        transmit_tone_mode: getField(
            card,
            "transmit_tone_mode"
        ).value,

        transmit_ctcss_frequency_hz: optionalNumber(
            card,
            "transmit_ctcss_frequency_hz"
        ),

        transmit_dcs_code: optionalNumber(
            card,
            "transmit_dcs_code"
        ),

        transmit_dcs_polarity: getField(
            card,
            "transmit_dcs_polarity"
        ).value,

        receive_tone_mode: getField(
            card,
            "receive_tone_mode"
        ).value,

        receive_ctcss_frequency_hz: optionalNumber(
            card,
            "receive_ctcss_frequency_hz"
        ),

        receive_dcs_code: optionalNumber(
            card,
            "receive_dcs_code"
        ),

        receive_dcs_polarity: getField(
            card,
            "receive_dcs_polarity"
        ).value,

        tuning_step_khz: Number(
            getField(
                card,
                "tuning_step_khz"
            ).value
        ),

        scan_behavior: getField(
            card,
            "scan_behavior"
        ).value,

        comment: getField(card, "comment").value,
    };
}

async function getResponseErrorMessage(response, fallbackMessage =
        "Radio Loadout could not generate the CSV. "
        + "Please review the channel settings and try again.") {
    try {
        const responseData = await response.json();

        if (
            typeof responseData.detail === "string"
            && responseData.detail.trim() !== ""
        ) {
            return responseData.detail;
        }

        if (Array.isArray(responseData.detail)) {
            const messages = responseData.detail
                .map((error) => error.msg)
                .filter(Boolean);

            if (messages.length > 0) {
                return messages.join(" ");
            }
        }
    } catch {
        return fallbackMessage;
    }

    return fallbackMessage;
}

function getResponseFilename(response) {
    const disposition =
        response.headers.get("content-disposition") || "";

    const filenameMatch = disposition.match(
        /filename="?([^";]+)"?/i
    );

    if (filenameMatch) {
        return filenameMatch[1];
    }

    return "radio_loadout_custom.csv";
}

function downloadBlob(blob, filename) {
    const objectUrl = URL.createObjectURL(blob);
    let anchor;

    try {
        anchor = document.createElement("a");
        anchor.href = objectUrl;
        anchor.download = filename;
        anchor.style.display = "none";
        document.body.appendChild(anchor);
        anchor.click();
    } finally {
        // Give the browser time to start consuming the URL before releasing it.
        window.setTimeout(() => {
            anchor?.remove();
            URL.revokeObjectURL(objectUrl);
        }, 1000);
    }
}

function validateBackup(backup) {
    if (Array.isArray(backup?.channels)) checkChannelCount(backup.channels.length);
    return RadioLoadoutBackup.validate(backup);
}

function getInputLimits() {
    const config = document.querySelector("#input-limits");
    const limits = config ? JSON.parse(config.textContent) : null;
    if (!limits || ["csv_upload_bytes", "backup_bytes", "channels_json_bytes", "channels"].some(
        (key) => !Number.isInteger(limits[key]) || limits[key] <= 0
    )) throw new Error("Input limits are unavailable. Please reload the builder.");
    return limits;
}

function checkChannelCount(count) {
    if (count > getInputLimits().channels) throw new Error(`Channel count exceeds the ${getInputLimits().channels}-channel limit.`);
}

function checkFileBytes(size, maximum, label) {
    if (size > maximum) throw new Error(`${label} exceeds the ${maximum}-byte limit.`);
}

function applyImportedChannels(channels) {
    const previousCards = [...channelList.children];
    const previousSaved = window.localStorage.getItem(DRAFT_STORAGE_KEY);
    try {
        replaceChannelCards(channels);
        saveDraft(true);
    } catch (error) {
        const currentCards = [...channelList.children];
        if (currentCards.length !== previousCards.length || currentCards.some((card, index) => card !== previousCards[index])) {
            channelList.replaceChildren(...previousCards);
            updateChannelNumbers();
        }
        if (window.localStorage.getItem(DRAFT_STORAGE_KEY) !== previousSaved) {
            if (previousSaved === null) window.localStorage.removeItem(DRAFT_STORAGE_KEY);
            else window.localStorage.setItem(DRAFT_STORAGE_KEY, previousSaved);
        }
        throw error;
    }
}

function exportBackup() {
    try {
        clearFormMessage();
        if (!channelList || getChannelCards().length === 0) {
            throw new Error("No builder channels are available to back up.");
        }
        const backup = {
            format: "radio-loadout",
            version: 1,
            channels: getChannelCards().map(getCardDraft),
        };
        checkChannelCount(backup.channels.length);
        const blob = new Blob([JSON.stringify(backup, null, 2)], {
            type: "application/json;charset=utf-8",
        });
        checkFileBytes(blob.size, getInputLimits().backup_bytes, "JSON backup");
        downloadBlob(blob, "radio_loadout_backup.json");
        showFormMessage(
            "Backup download requested. Check your browser's downloads for radio_loadout_backup.json.",
            "success"
        );
    } catch (error) {
        console.error("Backup export failed:", error);
        showFormMessage("Could not export the backup. Please try again.", "error");
    }
}

async function importBackup() {
    clearFormMessage();
    const file = backupFileInput.files[0];

    if (!file) {
        showFormMessage("Choose a Radio Loadout JSON backup to restore.", "error");
        return;
    }

    importBackupButton.disabled = true;
    backupFileInput.disabled = true;
    importBackupButton.textContent = "Restoring...";

    try {
        checkFileBytes(file.size, getInputLimits().backup_bytes, "JSON backup");
        const text = await file.text();
        checkFileBytes(new Blob([text]).size, getInputLimits().backup_bytes, "JSON backup");
        const backup = JSON.parse(text.replace(/^\uFEFF/, ""));
        const channels = validateBackup(backup);
        applyImportedChannels(channels);
        backupFileInput.value = "";
        showFormMessage(`Restored ${channels.length} channels from backup.`, "success");
    } catch (error) {
        const message = error instanceof SyntaxError
            ? "The backup is not valid JSON."
            : error instanceof Error ? error.message : "Could not read the backup file.";
        showFormMessage(message, "error");
    } finally {
        importBackupButton.disabled = false;
        backupFileInput.disabled = false;
        importBackupButton.textContent = "Import Backup";
    }
}

async function importChirpCsv() {
    clearFormMessage();
    const requestId = ++chirpImportRequestId;
    pendingChirpImport = null;
    if (chirpImportPanel) chirpImportPanel.hidden = true;
    const file = chirpCsvFileInput.files[0];

    if (!file) {
        showFormMessage("Choose a CHIRP CSV file to import.", "error");
        return;
    }

    const fallbackMessage = "Could not import the CHIRP CSV. Please try again.";
    importChirpCsvButton.disabled = true;
    chirpCsvFileInput.disabled = true;
    importChirpCsvButton.textContent = "Importing...";

    try {
        checkFileBytes(file.size, getInputLimits().csv_upload_bytes, "CSV file");
        const upload = new FormData();
        upload.append("file", file);
        const response = await window.fetch("/imports/chirp.csv", {
            method: "POST",
            body: upload,
        });

        if (!response.ok) {
            throw new Error(await getResponseErrorMessage(response, fallbackMessage));
        }

        const result = await response.json();
        if (requestId !== chirpImportRequestId) return;

        if (
            !Array.isArray(result.channels)
            || result.channels.length === 0
            || result.channels.some((channel) => (
                channel === null
                || typeof channel !== "object"
                || Array.isArray(channel)
            ))
        ) {
            throw new Error("The import response did not contain valid channels.");
        }

        checkChannelCount(result.channels.length);
        const report = result.import_report;
        if (!report || typeof report.requires_confirmation !== "boolean" || !Array.isArray(report.messages)
            || !Number.isInteger(report.loss_count) || report.loss_count < 0
            || report.requires_confirmation !== (report.loss_count > 0)
            || (!report.requires_confirmation && report.messages.some((message) => message?.kind === "loss"))) {
            throw new Error("The server did not provide a valid import review. Please reload and try again.");
        }
        renderChirpImportReport(report, file.name || "CSV file");
        if (report.requires_confirmation) {
            pendingChirpImport = JSON.parse(JSON.stringify(result.channels));
            showFormMessage("Review the import information loss, then confirm replacement or cancel.", "error");
            return;
        }
        applyImportedChannels(result.channels);
        chirpCsvFileInput.value = "";
        showFormMessage(
            `Imported ${result.channels.length} channels from CHIRP CSV.`,
            "success"
        );
    } catch (error) {
        if (requestId === chirpImportRequestId) {
            showFormMessage(error instanceof Error ? error.message : fallbackMessage, "error");
        }
    } finally {
        importChirpCsvButton.disabled = false;
        chirpCsvFileInput.disabled = false;
        importChirpCsvButton.textContent = "Import CHIRP CSV";
    }
}

function renderChirpImportReport(report, filename) {
    if (!chirpImportPanel || !chirpImportSummary || !chirpImportMessages || !confirmChirpImportButton || !cancelChirpImportButton) {
        throw new Error("The import review panel is unavailable. Please reload the builder.");
    }
    chirpImportPanel.hidden = false;
    chirpImportSummary.textContent = `Review for ${filename}. ` + (report.requires_confirmation
        ? `${report.loss_count} information loss(es) detected on import or later CSV export. Confirm before replacing current channels.`
        : "No meaningful information loss was detected. Normalization and defaults are listed below.");
    chirpImportMessages.replaceChildren();
    report.messages.forEach((message) => {
        if (!message || !["normalization", "default", "loss"].includes(message.kind) || typeof message.message !== "string") {
            throw new Error("The import review contains an invalid message.");
        }
        const item = document.createElement("li");
        item.textContent = `${message.kind.toUpperCase()} — CSV row ${message.row_number}, channel ${message.channel_index + 1} (${message.channel_name}), ${message.field}: ${message.message}`;
        chirpImportMessages.appendChild(item);
    });
    if (report.omitted_messages) {
        const item = document.createElement("li");
        item.textContent = `${report.omitted_messages} additional messages omitted to keep this report bounded. Review the original CSV before confirming.`;
        chirpImportMessages.appendChild(item);
    }
    confirmChirpImportButton.hidden = !report.requires_confirmation;
    cancelChirpImportButton.hidden = !report.requires_confirmation;
}

function confirmChirpImport() {
    if (!pendingChirpImport) return;
    const channels = pendingChirpImport;
    try {
        applyImportedChannels(channels);
        pendingChirpImport = null;
        confirmChirpImportButton.hidden = true;
        cancelChirpImportButton.hidden = true;
        chirpCsvFileInput.value = "";
        showFormMessage(`Imported ${channels.length} reviewed channels from CHIRP CSV.`, "success");
    } catch (error) {
        showFormMessage(error instanceof Error ? error.message : "Could not apply the reviewed import.", "error");
    }
}

function cancelChirpImport() {
    chirpImportRequestId += 1;
    pendingChirpImport = null;
    if (chirpImportPanel) chirpImportPanel.hidden = true;
    showFormMessage("Import cancelled. Existing channels and saved draft are unchanged.", "success");
}

function invalidateCompatibilityReport() {
    compatibilityRequestId += 1;
    compatibilityReport = null;
    if (generateCsvButton) {
        generateCsvButton.disabled = csvGenerationInProgress;
    }
    if (compatibilityPanel && compatibilitySummary && compatibilityIssues && !compatibilityPanel.hidden) {
        compatibilityPanel.dataset.state = "outdated";
        compatibilitySummary.textContent = "This report is outdated. Review compatibility again after your changes.";
        compatibilityIssues.replaceChildren();
    }
}

function renderCompatibilityReport(report) {
    compatibilityReport = report;
    const errors = report.issues.filter((issue) => issue.severity === "error");
    const warnings = report.issues.filter((issue) => issue.severity === "warning");
    if (generateCsvButton) {
        generateCsvButton.disabled = csvGenerationInProgress || errors.length > 0;
    }
    if (!compatibilityPanel || !compatibilitySummary || !compatibilityIssues) {
        console.error("Compatibility results panel is missing.");
        return;
    }
    compatibilityPanel.hidden = false;
    compatibilityPanel.dataset.state = errors.length ? "error" : warnings.length ? "warning" : "compatible";
    compatibilitySummary.textContent = errors.length
        ? `Fix ${errors.length} compatibility error(s) before generating CHIRP CSV.`
        : `All ${report.channel_count} channels are compatible with CHIRP Generic CSV.`
            + (warnings.length ? ` Review ${warnings.length} warning(s); export is allowed.` : "");
    compatibilityIssues.replaceChildren();
    report.issues.forEach((issue) => {
        const item = document.createElement("li");
        const channel = Number.isInteger(issue.channel_index)
            ? `Channel ${issue.channel_index + 1} (${issue.channel_name || "unnamed"})`
            : "Loadout";
        item.textContent = `${issue.severity.toUpperCase()} — ${channel}, ${issue.field}: ${issue.message}`;
        compatibilityIssues.appendChild(item);
    });
}

async function requestCompatibilityReport(channels) {
    checkChannelCount(channels.length);
    const channelsJson = JSON.stringify(channels);
    checkFileBytes(new Blob([channelsJson]).size, getInputLimits().channels_json_bytes, "channels_json");
    const data = new FormData();
    data.append("channels_json", channelsJson);
    const response = await window.fetch("/validation/chirp.csv", {
        method: "POST",
        body: data,
    });
    if (!response.ok) {
        throw new Error(await getResponseErrorMessage(response, "Could not review compatibility. Please try again."));
    }
    const report = await response.json();
    if (
        typeof report?.compatible !== "boolean"
        || !Array.isArray(report.issues)
        || !Number.isInteger(report.channel_count)
        || report.issues.some((issue) => (
            !issue || !["info", "warning", "error"].includes(issue.severity)
            || typeof issue.message !== "string" || typeof issue.field !== "string"
        ))
        || report.compatible === report.issues.some((issue) => issue.severity === "error")
    ) {
        throw new Error("The compatibility service returned an invalid report. Please try again.");
    }
    return report;
}

async function reviewCompatibility(channels = getChannelCards().map(channelDataFromCard)) {
    const requestId = ++compatibilityRequestId;
    if (reviewCompatibilityButton) reviewCompatibilityButton.disabled = true;
    try {
        const report = await requestCompatibilityReport(channels);
        // Editing or another review supersedes this in-flight response.
        if (requestId !== compatibilityRequestId) return null;
        renderCompatibilityReport(report);
        return report;
    } catch (error) {
        if (requestId === compatibilityRequestId) {
            showFormMessage(error instanceof Error ? error.message : "Could not review compatibility.", "error");
        }
        return null;
    } finally {
        if (reviewCompatibilityButton) reviewCompatibilityButton.disabled = false;
    }
}

async function submitChannelForm(event) {
    event.preventDefault();
    clearFormMessage();
    saveDraft();

    const channels = getChannelCards().map(
        channelDataFromCard
    );

    channelsJsonInput.value = JSON.stringify(
        channels
    );

    generateCsvButton.disabled = true;
    csvGenerationInProgress = true;
    generateCsvButton.textContent = "Generating...";

    try {
        const report = await reviewCompatibility(channels);
        if (!report || !report.compatible) return;

        const response = await window.fetch(
            form.action,
            {
                method: "POST",
                body: new FormData(form),
            }
        );

        if (!response.ok) {
            const errorMessage =
                await getResponseErrorMessage(response);

            throw new Error(errorMessage);
        }

        const csvBlob = await response.blob();

        downloadBlob(
            csvBlob,
            getResponseFilename(response)
        );

        showFormMessage(
            "Your CHIRP CSV was generated and downloaded.",
            "success"
        );
    } catch (error) {
        const errorMessage =
            error instanceof Error
                ? error.message
                : "Radio Loadout could not generate the CSV.";

        showFormMessage(errorMessage, "error");
    } finally {
        csvGenerationInProgress = false;
        generateCsvButton.disabled = compatibilityReport !== null && !compatibilityReport.compatible;
        generateCsvButton.textContent =
            "Generate CHIRP CSV";
    }
}

function bindBuilderEvent(element, eventName, handler) {
    if (!element) {
        console.warn(`Builder control missing; skipped ${handler.name || eventName} listener.`);
        return;
    }
    element.addEventListener(eventName, handler);
}

// Register export independently so a missing optional control cannot disable it.
bindBuilderEvent(exportBackupButton, "click", exportBackup);
bindBuilderEvent(importBackupButton, "click", importBackup);
bindBuilderEvent(importChirpCsvButton, "click", importChirpCsv);
bindBuilderEvent(confirmChirpImportButton, "click", confirmChirpImport);
bindBuilderEvent(cancelChirpImportButton, "click", cancelChirpImport);
bindBuilderEvent(reviewCompatibilityButton, "click", () => {
    clearFormMessage();
    reviewCompatibility();
});

bindBuilderEvent(addChannelButton, "click", () => {
    addChannel();
});

bindBuilderEvent(
    addNoaaWeatherButton,
    "click",
    addNoaaWeatherPreset
);

bindBuilderEvent(
    addAmateurCallingButton,
    "click",
    addAmateurCallingPreset
);

bindBuilderEvent(
    clearDraftButton,
    "click",
    clearDraft
);

bindBuilderEvent(channelList, "click", (event) => {
    const card = event.target.closest(
        "[data-channel-card]"
    );

    if (!card) {
        return;
    }

    if (
        event.target.closest("[data-move-channel-up]")
    ) {
        moveChannelUp(card);
        return;
    }

    if (
        event.target.closest("[data-move-channel-down]")
    ) {
        moveChannelDown(card);
        return;
    }

    if (
        event.target.closest("[data-duplicate-channel]")
    ) {
        duplicateChannel(card);
        return;
    }

    const removeButton = event.target.closest(
        "[data-remove-channel]"
    );

    if (
        !removeButton
        || getChannelCards().length === 1
    ) {
        return;
    }

    card.remove();
    updateChannelNumbers();
    saveDraft();
});

bindBuilderEvent(channelList, "input", (event) => {
    if (
        event.target.closest("[data-channel-card]")
    ) {
        scheduleDraftSave();
    }
});

bindBuilderEvent(channelList, "change", (event) => {
    const card = event.target.closest(
        "[data-channel-card]"
    );

    if (!card) {
        return;
    }

    if (
        event.target.matches(
            '[data-field="receive_only"]'
        )
    ) {
        updateTransmitField(card);
    }

    if (
        event.target.matches(
            '[data-field="tone_mode"]'
        )
    ) {
        updateToneFields(card);
    }

    if (
        event.target.matches(
            '[data-field="transmit_tone_mode"]'
        )
    ) {
        updateIndependentToneFields(
            card,
            "transmit"
        );
    }

    if (
        event.target.matches(
            '[data-field="receive_tone_mode"]'
        )
    ) {
        updateIndependentToneFields(
            card,
            "receive"
        );
    }

    saveDraft();
});

bindBuilderEvent(
    form,
    "submit",
    submitChannelForm
);

try {
    if (!channelList || !channelTemplate || !form) {
        throw new Error("Required builder elements are missing.");
    }
    if (!restoreDraft()) {
        addChannel(false);
    }
} catch (error) {
    console.error("Builder initialization failed:", error);
    showFormMessage("The builder could not initialize. Please reload the page.", "error");
}
