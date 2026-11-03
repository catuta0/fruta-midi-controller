"""Polyphonic aftertouch scaling, change filter and rate limit (fm_aftertouch.h, fm_time.h)."""
import pytest


def test_config_from_sketch(cfg):
    assert (cfg["TOUCH_THRESHOLD"], cfg["AT_MAX_DELTA"], cfg["AT_INTERVAL_MS"]) == (12, 120, 15)


# Hand-calculated with p = (clamp(delta, 12, 120) - 12) * 127 // 108.
@pytest.mark.parametrize("delta,expected", [
    (-50, 0), (0, 0), (11, 0), (12, 0), (13, 1),
    (66, 63),     # 54*127/108 = 63.5 -> 63 (truncation, as Arduino map())
    (119, 125),   # 107*127/108 = 125.8 -> 125
    (120, 127),   # AT_MAX_DELTA -> full scale
    (121, 127), (1000, 127), (32767, 127),
])
def test_pressure_from_delta(probe, cfg, delta, expected):
    assert probe.int(f"at {delta} {cfg['TOUCH_THRESHOLD']} {cfg['AT_MAX_DELTA']}") == expected


def test_pressure_monotonic_and_in_range(probe, cfg):
    t, m = cfg["TOUCH_THRESHOLD"], cfg["AT_MAX_DELTA"]
    got = [int(x) for x in probe.run([f"at {d} {t} {m}" for d in range(-20, 200)])]
    assert all(0 <= v <= 127 for v in got)
    assert all(b >= a for a, b in zip(got, got[1:]))


@pytest.mark.parametrize("p,last,expected", [
    (0, 0, 0), (1, 0, 0), (2, 0, 1), (0, 2, 1),
    (0, 1, 1),        # T-041: falling to the floor is always sent (was 0 before T-041)
    (0, 127, 1), (1, 2, 0), (2, 1, 0), (1, 3, 1),
    (127, 127, 0), (126, 127, 0), (125, 127, 1), (127, 0, 1),
])
def test_change_filter(probe, p, last, expected):
    assert probe.int(f"atsend {p} {last}") == expected


def test_rate_limit_boundary(probe, cfg):
    iv = cfg["AT_INTERVAL_MS"]
    assert probe.int(f"ge {1000 + iv - 1} 1000 {iv}") == 0
    assert probe.int(f"ge {1000 + iv} 1000 {iv}") == 1
    # across the 2^32 ms millis() wrap
    last = 2**32 - 10
    assert probe.int(f"ge {(last + iv - 1) % 2**32} {last} {iv}") == 0
    assert probe.int(f"ge {(last + iv) % 2**32} {last} {iv}") == 1


@pytest.mark.parametrize("loop_ms", [1, 4, 7, 15, 20])
def test_rate_limit_timeline(probe, cfg, loop_ms):
    """Mirror of the sketch: pressureDue then lastPressureMs = now. Gaps are >= interval."""
    iv = cfg["AT_INTERVAL_MS"]
    last, sent = 0, []
    for now in range(0, 1000, loop_ms):
        if probe.int(f"ge {now} {last} {iv}"):
            last = now
            sent.append(now)
    gaps = [b - a for a, b in zip(sent, sent[1:])]
    assert sent and all(g >= iv for g in gaps)
    # the first due loop iteration after each interval is taken: gap < interval + loop period
    assert all(g < iv + loop_ms for g in gaps)


@pytest.mark.parametrize("last,expected", [(0, 0), (1, 1), (2, 1), (127, 1)])
def test_reset_on_release(probe, last, expected):
    assert probe.int(f"atreset {last}") == expected


def padsim(probe, cfg, samples):
    toks = " ".join(f"{int(t)}:{d}" for t, d in samples)
    out = probe.one(f"padsim {cfg['DEBOUNCE_MS']} {cfg['AT_INTERVAL_MS']} "
                    f"{cfg['TOUCH_THRESHOLD']} {cfg['AT_MAX_DELTA']} {toks}")
    return out.split() if out else []


def at_values(events):
    return [int(e.split(":")[2]) for e in events if ":AT:" in e]


def test_release_after_pressure_sends_one_zero_before_note_off(probe, cfg):
    # touch 100..399 at delta 66 (p = 63), release at 400
    s = [(100 <= t < 400, 66 if 100 <= t < 400 else 0) for t in range(600)]
    ev = padsim(probe, cfg, s)
    assert ev[0] == "100:ON:60"
    assert at_values(ev) == [63, 0]
    i_zero = ev.index("400:AT:0")
    assert ev[i_zero + 1] == "400:OFF:60"          # AT 0 immediately before Note Off
    assert ev[-1] == "400:OFF:60"


def test_release_without_pressure_sends_no_zero(probe, cfg):
    # delta at the threshold -> p = 0 throughout -> no AT at all, plain Note Off
    s = [(100 <= t < 400, cfg["TOUCH_THRESHOLD"]) for t in range(600)]
    assert padsim(probe, cfg, s) == ["100:ON:60", "400:OFF:60"]


def test_slow_fall_to_floor_ends_at_exactly_one_zero(probe, cfg):
    # pressure ramps down 1 count of delta per ms from 66 to 0 while the pad stays touched
    s = [(True, max(0, 66 - t)) for t in range(300)] + [(False, 0)] * 50
    ev = padsim(probe, cfg, s)
    vals = at_values(ev)
    assert vals[-1] == 0 and vals.count(0) == 1, vals
    # the zero is sent while still touched; release (t=300) then sends only Note Off
    zero_t = int(next(e for e in ev if e.endswith(":AT:0")).split(":")[0])
    assert zero_t < 300
    assert ev[-1] == "300:OFF:60" and "300:AT:0" not in ev


def test_fall_from_1_to_0_is_sent(probe, cfg):
    # delta 13 -> p = 1 (not sent, |1-0| < 2); delta 14 -> p = 2 (sent); delta 13 -> 1 (not sent);
    # delta 0 -> 0 (sent: floor). Exactly one zero.
    seq = [13] * 30 + [14] * 30 + [13] * 30 + [0] * 30
    s = [(True, d) for d in seq] + [(False, 0)] * 30
    vals = at_values(padsim(probe, cfg, s))
    assert vals == [2, 0], vals


def test_rate_limit_still_applies_to_zero(probe, cfg):
    s = [(True, 120)] * 100 + [(True, 0)] * 100 + [(False, 0)] * 50
    ev = padsim(probe, cfg, s)
    times = [int(e.split(":")[0]) for e in ev if ":AT:" in e]
    assert at_values(ev) == [127, 0]
    assert all(t % cfg["AT_INTERVAL_MS"] == 0 for t in times)   # only on due ticks
