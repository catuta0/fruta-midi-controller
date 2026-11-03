"""Button sampling and short / long press classification (fm_button.h)."""
import random

import pytest


def test_constants(probe):
    sample, long_ms = (int(x) for x in probe.one("consts").split()[:2])
    assert (sample, long_ms) == (10, 800)


def test_sample_gate_boundary(probe):
    # lastSample starts at 0: due at 10, not at 9; next due 10 ms after the last due one.
    assert probe.one("bdue 0 9 10 19 20 29 35 44 45") == "0 0 1 0 1 0 1 0 1"


def test_long_press_threshold_boundary(probe):
    # held exactly 800 ms -> not long yet; 801 ms -> long (strictly greater).
    assert probe.one("bupdate 1000:1 1800:1 1801:1 1900:1 2000:0") == "- - L - -"


def test_release_at_800_is_short(probe):
    assert probe.one("bupdate 1000:1 1800:1 1800:0") == "- - S"


def test_release_after_long_is_silent_and_rearms(probe):
    assert probe.one("bupdate 0:1 801:1 900:0 1000:1 1100:0") == "- L - - S"


def test_idle_and_held_produce_nothing(probe):
    assert probe.one("bupdate 0:0 10:0 20:0") == "- - -"


def trace(probe, bits):
    out = probe.one(f"btrace {bits}")
    return [tuple(x.split(":")) for x in out.split()] if out else []


def test_sampled_long_press_timing(probe):
    # Pin down from t=1000. Samples every 10 ms -> first sample > 800 ms after 1000 is 1810.
    bits = "0" * 1000 + "1" * 1000 + "0" * 100
    assert trace(probe, bits) == [("1810", "L")]


def test_sampled_short_press_just_below_long(probe):
    # Pin down 1000..1809 (last down sample at 1800 = exactly 800 ms) -> short at release 1810.
    bits = "0" * 1000 + "1" * 810 + "0" * 100
    assert trace(probe, bits) == [("1810", "S")]


def test_contact_bounce_under_sample_period_gives_one_event(probe):
    rng = random.Random(1234)  # deterministic
    for _ in range(50):
        press = rng.randrange(100, 200)
        hold = rng.randrange(50, 700)          # always a short press
        bits = ["0"] * (press + hold + 200)
        for t in range(press, press + hold):
            bits[t] = "1"
        # bounce windows of < 10 ms at press and release
        for t in range(press, press + rng.randrange(1, 10)):
            bits[t] = rng.choice("01")
        rel = press + hold
        for t in range(rel, rel + rng.randrange(1, 10)):
            bits[t] = rng.choice("01")
        events = trace(probe, "".join(bits))
        assert len(events) == 1 and events[0][1] == "S", (press, hold, events)
