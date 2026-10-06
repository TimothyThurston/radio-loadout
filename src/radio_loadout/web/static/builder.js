const CTCSS_FREQUENCIES = [
    67.0, 69.3, 71.9, 74.4, 77.0,
    79.7, 82.5, 85.4, 88.5, 91.5,
    94.8, 97.4, 100.0, 103.5, 107.2,
    110.9, 114.8, 118.8, 123.0, 127.3,
    131.8, 136.5, 141.3, 146.2, 151.4,
    156.7, 159.8, 162.2, 165.5, 167.9,
    171.3, 173.8, 177.3, 179.9, 183.5,
    186.2, 189.9, 192.8, 196.6, 199.5,
    203.5, 206.5, 210.7, 218.1, 225.7,
    229.1, 233.6, 241.8, 250.3, 254.1,
];

const DCS_CODES = [
    23, 25, 26, 31, 32, 36, 43, 47, 51, 53, 54,
    65, 71, 72, 73, 74, 114, 115, 116, 122, 125,
    131, 132, 134, 143, 145, 152, 155, 156, 162,
    165, 172, 174, 205, 212, 223, 225, 226, 243,
    244, 245, 246, 251, 252, 255, 261, 263, 265,
    266, 271, 274, 306, 311, 315, 325, 331, 332,
    343, 346, 351, 356, 364, 365, 371, 411, 412,
    413, 423, 431, 432, 445, 446, 452, 454, 455,
    462, 464, 465, 466, 503, 506, 516, 523, 526,
    532, 546, 565, 606, 612, 624, 627, 631, 632,
    654, 662, 664, 703, 712, 723, 731, 732, 734,
    743, 754,
];

const form = document.querySelector("#channel-form");
const channelList = document.querySelector("#channel-list");
const channelTemplate = document.querySelector(
    "#channel-template"
);
const addChannelButton = document.querySelector(
    "#add-channel"
);
const channelsJsonInput = document.querySelector(
    "#channels-json"
);

function populateToneOptions() {
    const templateContent = channelTemplate.content;

    templateContent
        .querySelectorAll("[data-ctcss-select]")
        .forEach((select) => {
            CTCSS_FREQUENCIES.forEach((frequency) => {
                const option = document.createElement(
                    "option"
                );

                option.value = frequency.toFixed(1);
                option.textContent = frequency.toFixed(1);

                select.appendChild(option);
            });
        });

    templateContent
        .querySelectorAll("[data-dcs-select]")
        .forEach((select) => {
            DCS_CODES.forEach((code) => {
                const option = document.createElement(
                    "option"
                );

                option.value = String(code);
                option.textContent = String(code).padStart(
                    3,
                    "0"
                );

                select.appendChild(option);
            });
        });
}

function getChannelCards() {
    return [
        ...channelList.querySelectorAll(
            "[data-channel-card]"
        ),
    ];
}

function getField(card, fieldName) {
    return card.querySelector(
        `[data-field="${fieldName}"]`
    );
}

function numberOrNull(value) {
    return value === "" ? null : Number(value);
}

function setFieldGroup(fields, enabled) {
    fields.forEach((field) => {
        field.hidden = !enabled;

        field
            .querySelectorAll("input, select")
            .forEach((control) => {
                control.disabled = !enabled;
            });
    });
}

function updateChannelNumbers() {
    const cards = getChannelCards();

    cards.forEach((card, index) => {
        card.querySelector(
            "[data-channel-number]"
        ).textContent = `Channel ${index + 1}`;

        const removeButton = card.querySelector(
            "[data-remove-channel]"
        );

        removeButton.disabled = cards.length === 1;
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

function updateAdvancedToneFields(card) {
    const toneModeInput = getField(
        card,
        "tone_mode"
    );

    const transmitToneModeInput = getField(
        card,
        "transmit_tone_mode"
    );

    const receiveToneModeInput = getField(
        card,
        "receive_tone_mode"
    );

    const advancedEnabled = (
        toneModeInput.value === "cross"
    );

    const advancedFields = card.querySelectorAll(
        "[data-advanced-tone-field]"
    );

    setFieldGroup(
        advancedFields,
        advancedEnabled
    );

    transmitToneModeInput.required = advancedEnabled;
    receiveToneModeInput.required = advancedEnabled;

    if (!advancedEnabled) {
        transmitToneModeInput.value = "none";
        receiveToneModeInput.value = "none";
    }

    const transmitCtcssEnabled = (
        advancedEnabled
        && transmitToneModeInput.value === "ctcss"
    );

    const transmitDcsEnabled = (
        advancedEnabled
        && transmitToneModeInput.value === "dcs"
    );

    const receiveCtcssEnabled = (
        advancedEnabled
        && receiveToneModeInput.value === "ctcss"
    );

    const receiveDcsEnabled = (
        advancedEnabled
        && receiveToneModeInput.value === "dcs"
    );

    const transmitCtcssFields = card.querySelectorAll(
        "[data-transmit-ctcss-field]"
    );

    const transmitDcsFields = card.querySelectorAll(
        "[data-transmit-dcs-field]"
    );

    const receiveCtcssFields = card.querySelectorAll(
        "[data-receive-ctcss-field]"
    );

    const receiveDcsFields = card.querySelectorAll(
        "[data-receive-dcs-field]"
    );

    setFieldGroup(
        transmitCtcssFields,
        transmitCtcssEnabled
    );

    setFieldGroup(
        transmitDcsFields,
        transmitDcsEnabled
    );

    setFieldGroup(
        receiveCtcssFields,
        receiveCtcssEnabled
    );

    setFieldGroup(
        receiveDcsFields,
        receiveDcsEnabled
    );

    const transmitCtcssInput = getField(
        card,
        "transmit_ctcss_frequency_hz"
    );

    const transmitDcsCodeInput = getField(
        card,
        "transmit_dcs_code"
    );

    const transmitDcsPolarityInput = getField(
        card,
        "transmit_dcs_polarity"
    );

    const receiveCtcssInput = getField(
        card,
        "receive_ctcss_frequency_hz"
    );

    const receiveDcsCodeInput = getField(
        card,
        "receive_dcs_code"
    );

    const receiveDcsPolarityInput = getField(
        card,
        "receive_dcs_polarity"
    );

    transmitCtcssInput.required = (
        transmitCtcssEnabled
    );

    transmitDcsCodeInput.required = (
        transmitDcsEnabled
    );

    transmitDcsPolarityInput.required = (
        transmitDcsEnabled
    );

    receiveCtcssInput.required = (
        receiveCtcssEnabled
    );

    receiveDcsCodeInput.required = (
        receiveDcsEnabled
    );

    receiveDcsPolarityInput.required = (
        receiveDcsEnabled
    );

    if (!transmitCtcssEnabled) {
        transmitCtcssInput.value = "";
    }

    if (!transmitDcsEnabled) {
        transmitDcsCodeInput.value = "";
        transmitDcsPolarityInput.value = "N";
    }

    if (!receiveCtcssEnabled) {
        receiveCtcssInput.value = "";
    }

    if (!receiveDcsEnabled) {
        receiveDcsCodeInput.value = "";
        receiveDcsPolarityInput.value = "N";
    }
}

function updateToneFields(card) {
    const toneModeInput = getField(
        card,
        "tone_mode"
    );

    const simpleCtcssField = card.querySelector(
        "[data-simple-ctcss-field]"
    );

    const simpleDcsFields = card.querySelectorAll(
        "[data-simple-dcs-field]"
    );

    const toneFrequencyInput = getField(
        card,
        "tone_frequency_hz"
    );

    const dcsCodeInput = getField(
        card,
        "dcs_code"
    );

    const dcsPolarityInput = getField(
        card,
        "dcs_polarity"
    );

    const simpleCtcssEnabled = (
        toneModeInput.value === "tone"
        || toneModeInput.value === "tsql"
    );

    const simpleDcsEnabled = (
        toneModeInput.value === "dtcs"
    );

    setFieldGroup(
        [simpleCtcssField],
        simpleCtcssEnabled
    );

    setFieldGroup(
        simpleDcsFields,
        simpleDcsEnabled
    );

    toneFrequencyInput.required = (
        simpleCtcssEnabled
    );

    dcsCodeInput.required = simpleDcsEnabled;
    dcsPolarityInput.required = simpleDcsEnabled;

    if (!simpleCtcssEnabled) {
        toneFrequencyInput.value = "";
    }

    if (!simpleDcsEnabled) {
        dcsCodeInput.value = "";
        dcsPolarityInput.value = "NN";
    }

    updateAdvancedToneFields(card);
}

function addChannel() {
    const newChannel = (
        channelTemplate.content.cloneNode(true)
    );

    channelList.appendChild(newChannel);

    const newCard = getChannelCards().at(-1);

    updateTransmitField(newCard);
    updateToneFields(newCard);
    updateChannelNumbers();
}

addChannelButton.addEventListener(
    "click",
    addChannel
);

channelList.addEventListener("click", (event) => {
    const removeButton = event.target.closest(
        "[data-remove-channel]"
    );

    if (
        !removeButton
        || getChannelCards().length === 1
    ) {
        return;
    }

    removeButton
        .closest("[data-channel-card]")
        .remove();

    updateChannelNumbers();
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
        || event.target.matches(
            '[data-field="receive_tone_mode"]'
        )
    ) {
        updateAdvancedToneFields(card);
    }
});

form.addEventListener("submit", () => {
    const channels = getChannelCards().map(
        (card) => {
            const transmitFrequencyValue = getField(
                card,
                "transmit_frequency_mhz"
            ).value;

            const toneFrequencyValue = getField(
                card,
                "tone_frequency_hz"
            ).value;

            const dcsCodeValue = getField(
                card,
                "dcs_code"
            ).value;

            const transmitCtcssValue = getField(
                card,
                "transmit_ctcss_frequency_hz"
            ).value;

            const transmitDcsCodeValue = getField(
                card,
                "transmit_dcs_code"
            ).value;

            const receiveCtcssValue = getField(
                card,
                "receive_ctcss_frequency_hz"
            ).value;

            const receiveDcsCodeValue = getField(
                card,
                "receive_dcs_code"
            ).value;

            return {
                name: getField(
                    card,
                    "name"
                ).value,

                receive_frequency_mhz: Number(
                    getField(
                        card,
                        "receive_frequency_mhz"
                    ).value
                ),

                transmit_frequency_mhz: numberOrNull(
                    transmitFrequencyValue
                ),

                mode: getField(
                    card,
                    "mode"
                ).value,

                power_watts: Number(
                    getField(
                        card,
                        "power_watts"
                    ).value
                ),

                receive_only: getField(
                    card,
                    "receive_only"
                ).checked,

                tone_mode: getField(
                    card,
                    "tone_mode"
                ).value,

                tone_frequency_hz: numberOrNull(
                    toneFrequencyValue
                ),

                dcs_code: numberOrNull(
                    dcsCodeValue
                ),

                dcs_polarity: getField(
                    card,
                    "dcs_polarity"
                ).value,

                transmit_tone_mode: getField(
                    card,
                    "transmit_tone_mode"
                ).value,

                transmit_ctcss_frequency_hz:
                    numberOrNull(
                        transmitCtcssValue
                    ),

                transmit_dcs_code: numberOrNull(
                    transmitDcsCodeValue
                ),

                transmit_dcs_polarity: getField(
                    card,
                    "transmit_dcs_polarity"
                ).value,

                receive_tone_mode: getField(
                    card,
                    "receive_tone_mode"
                ).value,

                receive_ctcss_frequency_hz:
                    numberOrNull(
                        receiveCtcssValue
                    ),

                receive_dcs_code: numberOrNull(
                    receiveDcsCodeValue
                ),

                receive_dcs_polarity: getField(
                    card,
                    "receive_dcs_polarity"
                ).value,

                comment: getField(
                    card,
                    "comment"
                ).value,
            };
        }
    );

    channelsJsonInput.value = JSON.stringify(
        channels
    );
});

populateToneOptions();
addChannel();