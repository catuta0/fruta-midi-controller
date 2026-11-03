"""Pad debounce lockout (fm_debounce.h) at the production DEBOUNCE_MS."""
import pytest


def test_debounce_value_from_sketch(cfg):
    assert cfg["DEBOUNCE_MS"] == 15


@pytest.mark.parametrize("touched,active", [(1, 0), (0, 1)])
def test_boundary_exactly_debounce_ms(probe, cfg, touched, active):
    db = cfg["DEBOUNCE_MS"]
    last = 1000
    assert probe.int(f"debounce {touched} {active} {last + db - 1} {last} {db}") == 0
    assert probe.int(f"debounce {touched} {active} {last + db} {last} {db}") == 1
    assert probe.int(f"debounce {touched} {active} {last + db + 1} {last} {db}") == 1


@pytest.mark.parametrize("state", [0, 1])
def test_no_change_when_state_matches(probe, cfg, state):
    db = cfg["DEBOUNCE_MS"]
    assert probe.int(f"debounce {state} {state} 100000 0 {db}") == 0


def test_boundary_across_millis_wrap(probe, cfg):
    db = cfg["DEBOUNCE_MS"]
    last = 2**32 - 5
    assert probe.int(f"debounce 1 0 {(last + db - 1) % 2**32} {last} {db}") == 0
    assert probe.int(f"debounce 1 0 {(last + db) % 2**32} {last} {db}") == 1


def simulate(probe, db, raw):
    """Mirror of the sketch loop for one pad, 1 ms per tick. Returns note on/off events."""
    active, last, events = False, 0, []
    for t, bit in enumerate(raw):
        touched = bit == "1"
        if probe.int(f"debounce {int(touched)} {int(active)} {t} {last} {db}"):
            last = t
            active = touched
            events.append((t, "on" if touched else "off"))
    return events


def test_bounce_shorter_than_debounce_is_filtered(probe, cfg):
    db = cfg["DEBOUNCE_MS"]
    # Touch at t=100 with 8 ms of chatter, held to t=300, release with 8 ms chatter.
    raw = ["0"] * 400
    for t in range(100, 300):
        raw[t] = "1"
    for t in (101, 103, 106):          # dropouts while touching
        raw[t] = "0"
    for t in (302, 304, 307):          # blips after release
        raw[t] = "1"
    events = simulate(probe, db, "".join(raw))
    assert events == [(100, "on"), (300, "off")], events


def test_change_inside_lockout_is_applied_at_window_end(probe, cfg):
    db = cfg["DEBOUNCE_MS"]
    # Touch at 100, released (and stays released) at 105 -> off accepted at 100 + db.
    raw = "0" * 100 + "1" * 5 + "0" * 50
    assert simulate(probe, db, raw) == [(100, "on"), (100 + db, "off")]


@pytest.mark.parametrize("bits,e,expected", [
    (0x0000, 0, 0), (0x0001, 0, 1), (0x0800, 11, 1), (0x0800, 10, 0), (0x0FFF, 5, 1), (0xF000, 11, 0),
])
def test_pad_touched_bit(probe, bits, e, expected):
    assert probe.int(f"touched {bits} {e}") == expected
