"""MIDI byte helpers (fm_midi.h) and interval helpers (fm_time.h)."""
import pytest


def test_channel_from_sketch(cfg):
    assert 1 <= cfg["MIDI_CHANNEL"] <= 16


@pytest.mark.parametrize("status,ch,expected", [
    (0x90, 1, 0x90), (0x90, 16, 0x9F), (0x80, 1, 0x80), (0x80, 10, 0x89), (0xA0, 1, 0xA0), (0xA0, 16, 0xAF),
])
def test_channel_status(probe, status, ch, expected):
    assert probe.int(f"status {status} {ch}") == expected


def test_usb_midi_cin(probe):
    cin_on, cin_off, cin_pp = (int(x) for x in probe.one("consts").split()[4:7])
    assert (cin_on, cin_off, cin_pp) == (0x09, 0x08, 0x0A)


def test_sensor_retry_strictly_greater(probe):
    r = int(probe.one("healthconsts").split()[2])
    assert r == 2000
    assert probe.int(f"gt {r} 0 {r}") == 0
    assert probe.int(f"gt {r + 1} 0 {r}") == 1


@pytest.mark.parametrize("now,since,iv,ge,gt", [
    (0, 0, 0, 1, 0), (10, 0, 10, 1, 0), (9, 0, 10, 0, 0), (11, 0, 10, 1, 1),
    (4, 2**32 - 6, 10, 1, 0),   # wrap: elapsed = 10
    (3, 2**32 - 6, 10, 0, 0),   # wrap: elapsed = 9
])
def test_elapsed_helpers(probe, now, since, iv, ge, gt):
    assert probe.int(f"ge {now} {since} {iv}") == ge
    assert probe.int(f"gt {now} {since} {iv}") == gt


@pytest.mark.parametrize("now,since,iv,ge", [
    (2**32 - 5, 2**32 - 10, 15, 0),   # since + iv overflows but only 5 ms elapsed
    (2**32 - 1, 2**32 - 10, 15, 0),   # 9 ms elapsed, just before the wrap
    (5, 2**32 - 100, 10, 1),          # now wrapped, since + iv did not: 105 ms elapsed
    (2**31, 0, 15, 1),                # large elapsed time
])
def test_elapsed_is_wrap_safe(probe, now, since, iv, ge):
    """Catches the classic `now >= since + interval` bug (not wrap-safe)."""
    assert probe.int(f"ge {now} {since} {iv}") == ge
    assert probe.int(f"gt {now} {since} {iv}") == ge
