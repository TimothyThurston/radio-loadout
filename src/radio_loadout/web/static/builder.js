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

const DRAFT_STORAGE_KEY = "radio-loadout-builder-draft-v1";

const form = document.querySelector("#channel-form");
const channelList = document.querySelector("#channel-list");
const channelTemplate = document.querySelector("#channel-template");
const addChannelButton = document.querySelector("#add-channel");
const addNoaaWeatherButton = document.querySelector(
    "#add-noaa-weather"
);
const clearDraftButton = document.querySelector("#clear-draft");
const channelsJsonInput = document.querySelector("#channels-json");
const draftStatus = document.querySelector("#draft-status");
const presetStatus = document.querySelector("#preset-status");

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
    window.clearTimeout(statusClearTimer);
    draftStatus.textContent = message;

    statusClearTimer = window.setTimeout(() => {
        draftStatus.textContent = "";
    }, 2500);
}

function showPresetStatus(message) {
    window.clearTimeout(presetStatusClearTimer);
    presetStatus.textContent = message;

    presetStatusClearTimer = window.setTimeout(() => {
        presetStatus.textContent = "";
    }, 4000);
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

function updateTransmitField(card) {
    const receiveOnlyInput = getField(
        card,
        "receive_only"
    );
    const transmitInput = getField(
        card,
        "transmit_frequency_mhz"
    );

    transmitInput.disabled = receiveOnlyInput.checked;

    if (receiveOnlyInput.checked) {
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

function createChannelCard() {
    const newChannel = channelTemplate.content.cloneNode(true);

    channelList.appendChild(newChannel);

    const newCard = getChannelCards().at(-1);

    populateToneOptions(newCard);

    return newCard;
}

function initializeChannelCard(card) {
    updateTransmitField(card);
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

function saveDraft() {
    window.clearTimeout(pendingSaveTimer);
    pendingSaveTimer = null;

    const draft = getChannelCards().map(getCardDraft);

    try {
        window.localStorage.setItem(
            DRAFT_STORAGE_KEY,
            JSON.stringify(draft)
        );

        showDraftStatus("Draft saved locally.");
    } catch {
        showDraftStatus("Draft could not be saved.");
    }
}

function scheduleDraftSave() {
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
            ) {
                field.value = "";
            } else {
                field.value = String(value);
            }
        }
    );
}

function restoreDraft() {
    const savedDraft = loadDraft();

    if (savedDraft === null) {
        return false;
    }

    channelList.replaceChildren();

    savedDraft.forEach((cardDraft) => {
        const card = createChannelCard();

        applyDraftToCard(card, cardDraft);
        initializeChannelCard(card);
    });

    updateChannelNumbers();
    showDraftStatus("Saved draft restored.");

    return true;
}

function addChannel(shouldSave = true) {
    const newCard = createChannelCard();

    initializeChannelCard(newCard);
    updateChannelNumbers();

    if (shouldSave) {
        saveDraft();
    }
}

function copyChannelValues(sourceCard, targetCard) {
    sourceCard.querySelectorAll("[data-field]").forEach(
        (sourceField) => {
            const fieldName = sourceField.dataset.field;
            const targetField = getField(
                targetCard,
                fieldName
            );

            if (!targetField) {
                return;
            }

            if (sourceField.type === "checkbox") {
                targetField.checked = sourceField.checked;
            } else {
                targetField.value = sourceField.value;
            }
        }
    );
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

addChannelButton.addEventListener("click", () => {
    addChannel();
});

addNoaaWeatherButton.addEventListener(
    "click",
    addNoaaWeatherPreset
);

clearDraftButton.addEventListener(
    "click",
    clearDraft
);

channelList.addEventListener("click", (event) => {
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

channelList.addEventListener("input", (event) => {
    if (
        event.target.closest("[data-channel-card]")
    ) {
        scheduleDraftSave();
    }
});

channelList.addEventListener("change", (event) => {
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

form.addEventListener("submit", () => {
    saveDraft();

    const channels = getChannelCards().map(
        channelDataFromCard
    );

    channelsJsonInput.value = JSON.stringify(
        channels
    );
});

if (!restoreDraft()) {
    addChannel(false);
}