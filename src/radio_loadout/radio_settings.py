"""Documented, model-scoped settings guidance; never a radio programming payload."""

import re
from dataclasses import asdict, dataclass

from radio_loadout.radio_profiles import BF_F8HP_PRO_V053, get_radio_profile

SettingValue = bool | int | str


def same_value(left: SettingValue, right: SettingValue) -> bool:
    # bool is a subclass of int, but True must not be accepted as squelch level 1.
    return type(left) is type(right) and left == right


@dataclass(frozen=True, slots=True)
class SettingOption:
    value: SettingValue
    label: str

    def __post_init__(self):
        if type(self.value) not in (bool, int, str) or not self.label:
            raise ValueError("Settings require a labeled boolean, integer or string option.")


@dataclass(frozen=True, slots=True)
class SettingRecommendation:
    value: SettingValue
    rationale: str
    scenarios: str
    tradeoffs: str
    revision: int = 1


@dataclass(frozen=True, slots=True)
class RadioSetting:
    setting_id: str
    label: str
    explanation: str
    menu_locator: str
    source_locator: str
    options: tuple[SettingOption, ...]
    recommendation: SettingRecommendation
    options_exhaustive: bool = True
    manufacturer_default: SettingValue | None = None
    default_evidence: str = "Not established from the reviewed manual; not read from your radio."

    def __post_init__(self):
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", self.setting_id):
            raise ValueError("Invalid setting ID.")
        if not all((self.label, self.explanation, self.menu_locator, self.source_locator, self.options,
                    self.default_evidence, self.recommendation.rationale,
                    self.recommendation.scenarios, self.recommendation.tradeoffs)):
            raise ValueError("Setting definitions require explanations and evidence.")
        if type(self.recommendation.revision) is not int or self.recommendation.revision < 1:
            raise ValueError("Recommendation revisions must be positive integers.")
        for index, option in enumerate(self.options):
            if any(same_value(option.value, previous.value) for previous in self.options[:index]):
                raise ValueError("Duplicate setting option.")
        self.validate(self.recommendation.value)
        if self.manufacturer_default is not None:
            self.validate(self.manufacturer_default)

    def validate(self, value: SettingValue) -> SettingValue:
        if not any(same_value(value, option.value) for option in self.options):
            raise ValueError(f"Unsupported value for {self.setting_id}; no substitution was made.")
        return value


TOGGLE = (SettingOption(False, "Off"), SettingOption(True, "On"))
PILOT_SETTINGS = (
    RadioSetting("squelch", "Squelch", "Sets how readily the receiver opens for a signal.",
                 "Radio Setting > Squelch (2)", "printed p. 50",
                 tuple(SettingOption(i, "Off / open" if i == 0 else f"Level {i}") for i in range(9)),
                 SettingRecommendation(2, "Start low and raise only enough to quiet local noise.",
                                       "Initial local voice listening; adjust at your location.",
                                       "Too high can hide weak signals; too low can produce noise.")),
    RadioSetting("power_save", "Power save", "Cycles receiver activity to reduce battery use.",
                 "Radio Setting > Power Save (3)", "printed p. 50", TOGGLE,
                 SettingRecommendation(False, "Favor hearing the beginning of incoming calls.",
                                       "Listening-first setup with adequate battery power.",
                                       "Shorter battery runtime; enable when endurance matters more.")),
    RadioSetting("vox", "VOX", "Allows sound to trigger transmission without pressing PTT.",
                 "Radio Setting > VOX Switch (4)", "printed pp. 50-51", TOGGLE,
                 SettingRecommendation(False, "Keep transmit activation deliberate while learning.",
                                       "Handheld push-to-talk operation.",
                                       "Hands-free VOX users need separate sensitivity/accessory testing; off is not a transmit lock.")),
    RadioSetting("timeout_seconds", "Transmit time-out timer", "Limits a continuous PTT transmission.",
                 "Radio Setting > TOT (7)", "printed p. 51",
                 (SettingOption(0, "Off"), *(SettingOption(i, f"{i} seconds") for i in range(15, 181, 15))),
                 SettingRecommendation(60, "Use a finite starting limit rather than unlimited PTT time.",
                                       "Short conversational transmissions and initial practice.",
                                       "Can cut off a long transmission; coordinate with net/repeater procedures. Not a substitute for safe operation.")),
    RadioSetting("roger_tone", "Roger tone", "Adds an over-the-air indication when a transmission ends.",
                 "Radio Setting > Roger Tone (10)", "printed p. 52", TOGGLE,
                 SettingRecommendation(False, "Avoid adding an unnecessary transmitted tone.",
                                       "Ordinary amateur voice conversations.",
                                       "No end-of-transmission tone; follow local operating preferences.")),
    RadioSetting("key_beep", "Key beep", "Provides audible feedback when using the keys.",
                 "Radio Setting > Key Beep (11)", "printed p. 53", TOGGLE,
                 SettingRecommendation(True, "Provide confirmation while becoming familiar with the controls.",
                                       "Guided setup; operators who benefit from audible feedback.",
                                       "Can disturb quiet environments; turn off if unwanted. Not a full accessibility solution.")),
    RadioSetting("backlight_seconds", "Backlight timeout", "Controls how long the display stays lit after use.",
                 "Radio Setting > Backlight (12)", "printed p. 53",
                 (SettingOption("always_on", "Always on"),
                  *(SettingOption(i, f"{i} seconds") for i in (5, 20, 30, 60))),
                 SettingRecommendation(20, "Allow time to read the display without leaving it permanently lit.",
                                       "Everyday handheld setup with occasional screen checks.",
                                       "Longer lighting uses more battery. Choose longer for readability if needed."),
                 options_exhaustive=False),
)


def settings_catalog(profile_id: str) -> dict:
    profile = get_radio_profile(profile_id)
    if profile is not BF_F8HP_PRO_V053:
        raise ValueError("No settings guide is available for this exact documented profile.")
    return {
        "schema_version": 1, "catalog_revision": 1, "radio_profile": profile.to_dict(),
        "recommendation_id": "listening-first-handheld-v1",
        "recommendation_label": "Listening-first handheld starting plan",
        "recommendation_author": "Radio Loadout",
        "hardware_verified": False, "delivery": "manual-guidance-only",
        "settings": [asdict(setting) for setting in PILOT_SETTINGS],
        "limitations": [
            "Confirm the exact model and firmware manually; this page cannot detect either.",
            "Values describe a plan, not current radio state, factory defaults or successful programming.",
            "No device connection, radio writes, CPS format or radio-wide CHIRP CSV export is implemented.",
            "Session-only: leaving or reloading discards this plan. Channel drafts and backup v1 exclude it.",
            "Backlight options are a reviewed subset, not an exhaustive hardware claim.",
            "Scan, dual watch, VOX gain/delay, global power and other dependent settings are not modeled here.",
        ],
    }


def validate_setting_values(profile_id: str, values: dict) -> dict:
    """Strict validation for future adapters; no persistence or device operations."""
    settings_catalog(profile_id)
    if type(values) is not dict:
        raise ValueError("Settings must be an object.")
    definitions = {setting.setting_id: setting for setting in PILOT_SETTINGS}
    if set(values) - definitions.keys():
        raise ValueError("Unknown settings are not supported.")
    return {key: definitions[key].validate(value) for key, value in values.items()}
