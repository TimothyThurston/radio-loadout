import pytest

from radio_loadout.models import (
    AnalogSettings,
    Channel,
    ChannelMode,
    Tone,
    ToneMode,
)


def test_simplex_channel() -> None:
    channel = Channel(
        name="2M CALL",
        receive_frequency_hz=146_520_000,
        transmit_frequency_hz=146_520_000,
        mode=ChannelMode.FM,
    )

    assert channel.name == "2M CALL"
    assert channel.receive_frequency_hz == 146_520_000
    assert channel.receive_only is False


def test_receive_only_channel() -> None:
    channel = Channel(
        name="NOAA",
        receive_frequency_hz=162_550_000,
        transmit_frequency_hz=None,
        mode=ChannelMode.NFM,
    )

    assert channel.receive_only is True


def test_empty_channel_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="name"):
        Channel(
            name=" ",
            receive_frequency_hz=146_520_000,
            transmit_frequency_hz=146_520_000,
        )


def test_ctcss_repeater_settings() -> None:
    settings = AnalogSettings(
        transmit_tone=Tone(mode=ToneMode.CTCSS, value=100.0),
        receive_tone=Tone(mode=ToneMode.CTCSS, value=100.0),
        power_watts=5.0,
    )
    channel = Channel(
        name="LOCAL RPT",
        receive_frequency_hz=145_400_000,
        transmit_frequency_hz=144_800_000,
        mode=ChannelMode.FM,
        analog_settings=settings,
    )

    assert channel.analog_settings is not None
    assert channel.analog_settings.transmit_tone.value == 100.0
    assert channel.analog_settings.power_watts == 5.0


def test_cross_tone_configuration() -> None:
    settings = AnalogSettings(
        transmit_tone=Tone(mode=ToneMode.CTCSS, value=100.0),
        receive_tone=Tone(mode=ToneMode.DCS, value=23),
    )

    assert settings.transmit_tone.mode is ToneMode.CTCSS
    assert settings.receive_tone.mode is ToneMode.DCS


def test_invalid_dcs_code_is_rejected() -> None:
    with pytest.raises(ValueError, match="octal"):
        Tone(mode=ToneMode.DCS, value=889)


def test_dmr_channel_rejects_analog_settings() -> None:
    with pytest.raises(ValueError, match="analog"):
        Channel(
            name="DMR TEST",
            receive_frequency_hz=444_000_000,
            transmit_frequency_hz=449_000_000,
            mode=ChannelMode.DMR,
            analog_settings=AnalogSettings(),
        )