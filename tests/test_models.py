import pytest

from radio_loadout.models import Channel, ChannelMode


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