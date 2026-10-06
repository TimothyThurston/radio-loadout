const form = document.querySelector("#channel-form");
const channelList = document.querySelector("#channel-list");
const channelTemplate = document.querySelector("#channel-template");
const addChannelButton = document.querySelector("#add-channel");
const channelsJsonInput = document.querySelector("#channels-json");

function getChannelCards() {
    return [
        ...channelList.querySelectorAll(
            "[data-channel-card]"
        ),
    ];
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
    const receiveOnlyInput = card.querySelector(
        '[data-field="receive_only"]'
    );

    const transmitInput = card.querySelector(
        '[data-field="transmit_frequency_mhz"]'
    );

    transmitInput.disabled = receiveOnlyInput.checked;

    if (receiveOnlyInput.checked) {
        transmitInput.value = "";
    }
}

function updateToneFields(card) {
    const toneModeInput = card.querySelector(
        '[data-field="tone_mode"]'
    );

    const ctcssField = card.querySelector(
        "[data-ctcss-field]"
    );

    const ctcssInput = card.querySelector(
        '[data-field="tone_frequency_hz"]'
    );

    const dcsFields = card.querySelectorAll(
        "[data-dcs-field]"
    );

    const dcsCodeInput = card.querySelector(
        '[data-field="dcs_code"]'
    );

    const dcsPolarityInput = card.querySelector(
        '[data-field="dcs_polarity"]'
    );

    const ctcssEnabled = (
        toneModeInput.value === "tone"
        || toneModeInput.value === "tsql"
    );

    const dcsEnabled = (
        toneModeInput.value === "dtcs"
    );

    ctcssField.hidden = !ctcssEnabled;
    ctcssInput.disabled = !ctcssEnabled;
    ctcssInput.required = ctcssEnabled;

    dcsFields.forEach((field) => {
        field.hidden = !dcsEnabled;
    });

    dcsCodeInput.disabled = !dcsEnabled;
    dcsCodeInput.required = dcsEnabled;

    dcsPolarityInput.disabled = !dcsEnabled;
    dcsPolarityInput.required = dcsEnabled;

    if (!ctcssEnabled) {
        ctcssInput.value = "";
    }

    if (!dcsEnabled) {
        dcsCodeInput.value = "";
        dcsPolarityInput.value = "NN";
    }
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
});

form.addEventListener("submit", () => {
    const channels = getChannelCards().map(
        (card) => {
            const transmitValue = card.querySelector(
                '[data-field="transmit_frequency_mhz"]'
            ).value;

            const toneFrequencyValue =
                card.querySelector(
                    '[data-field="tone_frequency_hz"]'
                ).value;

            const dcsCodeValue = card.querySelector(
                '[data-field="dcs_code"]'
            ).value;

            const dcsPolarityValue =
                card.querySelector(
                    '[data-field="dcs_polarity"]'
                ).value;

            return {
                name: card.querySelector(
                    '[data-field="name"]'
                ).value,

                receive_frequency_mhz: Number(
                    card.querySelector(
                        '[data-field="receive_frequency_mhz"]'
                    ).value
                ),

                transmit_frequency_mhz:
                    transmitValue === ""
                        ? null
                        : Number(transmitValue),

                mode: card.querySelector(
                    '[data-field="mode"]'
                ).value,

                power_watts: Number(
                    card.querySelector(
                        '[data-field="power_watts"]'
                    ).value
                ),

                receive_only: card.querySelector(
                    '[data-field="receive_only"]'
                ).checked,

                tone_mode: card.querySelector(
                    '[data-field="tone_mode"]'
                ).value,

                tone_frequency_hz:
                    toneFrequencyValue === ""
                        ? null
                        : Number(toneFrequencyValue),

                dcs_code:
                    dcsCodeValue === ""
                        ? null
                        : Number(dcsCodeValue),

                dcs_polarity: dcsPolarityValue,

                comment: card.querySelector(
                    '[data-field="comment"]'
                ).value,
            };
        }
    );

    channelsJsonInput.value = JSON.stringify(
        channels
    );
});

addChannel();