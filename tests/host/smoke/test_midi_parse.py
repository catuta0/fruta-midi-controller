"""T-006-SW smoke test: minimal pure-Python MIDI channel-voice status parser.

Covers Note On, Note Off (including Note On with velocity 0 treated as Note Off)
and Polyphonic Key Pressure (aftertouch). Channels are reported 1-based (1..16).
"""

import pytest


def parse(msg):
    """Parse a 3-byte MIDI channel-voice message.

    Returns (kind, channel, data1, data2) where kind is 'note_on', 'note_off'
    or 'poly_at' and channel is 1..16.
    """
    data = bytes(msg)
    if len(data) != 3:
        raise ValueError("expected 3 bytes, got %d" % len(data))
    status, d1, d2 = data
    if status < 0x80 or d1 > 0x7F or d2 > 0x7F:
        raise ValueError("invalid status or data byte")
    kind_nibble = status & 0xF0
    channel = (status & 0x0F) + 1
    if kind_nibble == 0x90:
        return ("note_off" if d2 == 0 else "note_on", channel, d1, d2)
    if kind_nibble == 0x80:
        return ("note_off", channel, d1, d2)
    if kind_nibble == 0xA0:
        return ("poly_at", channel, d1, d2)
    raise ValueError("unsupported status 0x%02X" % status)


@pytest.mark.parametrize(
    "msg, expected",
    [
        ([0x90, 60, 100], ("note_on", 1, 60, 100)),
        ([0x90, 60, 0], ("note_off", 1, 60, 0)),
        ([0x81, 64, 0], ("note_off", 2, 64, 0)),
        ([0xA0, 60, 77], ("poly_at", 1, 60, 77)),
    ],
)
def test_known_answers(msg, expected):
    assert parse(msg) == expected


def test_rejects_unsupported_status():
    with pytest.raises(ValueError):
        parse([0xB0, 7, 100])


def test_rejects_data_byte_as_status():
    with pytest.raises(ValueError):
        parse([0x40, 60, 100])
