"""Non-blocking LED blink sequencer (fm_blink.h) and finding DOC-1 (pads live during a blink)."""
import pytest


def test_patterns_unchanged_from_e4668d4(probe):
    # Original calls: blink(2, 120) ready, blink(3, 60) recalibrate, blink(scaleIdx + 1, 90) scale.
    assert probe.one("blinkconsts") == "2 120 3 60 90"


def expected(times, ms):
    ev = []
    for k in range(times):
        ev += [f"{2 * k * ms}:1", f"{(2 * k + 1) * ms}:0"]
    return " ".join(ev) + f" END:{2 * times * ms}"


@pytest.mark.parametrize("times", [1, 2, 3, 6])
@pytest.mark.parametrize("ms", [60, 90, 120])
def test_count_and_timing_1ms_tick(probe, times, ms):
    # 1 ms ticks: ON at 0, OFF at ms, ON at 2ms, ...; finished after 2*times*ms.
    assert probe.one(f"blink {times} {ms} 1 5000") == expected(times, ms)


def test_scale_6_lasts_1080ms(probe):
    out = probe.one("blink 6 90 1 3000").split()
    assert sum(1 for e in out if e.endswith(":1")) == 6
    assert out[-1] == "END:1080"


@pytest.mark.parametrize("tick", [3, 7, 13])
def test_coarse_tick_keeps_count_and_min_duration(probe, tick):
    out = probe.one(f"blink 6 90 {tick} 4000").split()
    edges = [(int(t), int(v)) for t, v in (e.split(":") for e in out if not e.startswith("END"))]
    assert [v for _, v in edges] == [1, 0] * 6
    end = int(out[-1].split(":")[1])
    times = [t for t, _ in edges] + [end]
    for a, b in zip(times, times[1:]):
        assert 90 <= b - a < 90 + tick, (a, b)


def test_zero_times_is_inactive(probe):
    assert probe.one("blink 0 90 1 500") == "0:0 END:0"


def test_pad_step(probe):
    assert probe.one("padstep 1 0 115 100 15") == "P 115"
    assert probe.one("padstep 0 1 115 100 15") == "R 115"
    assert probe.one("padstep 1 0 114 100 15") == "- 100"
    assert probe.one("padstep 1 1 999 100 15") == "- 100"


def scenario(debounce):
    # Button pressed 1000..1199 -> short press sampled at 1200: scale 4 -> 5 (6 blinks, 1200..2280).
    # Pad 0 touched 1500..1699, entirely inside the blink.
    n = 2600
    bb = "".join("1" if 1000 <= t < 1200 else "0" for t in range(n))
    pb = "".join("1" if 1500 <= t < 1700 else "0" for t in range(n))
    return bb, pb


def test_doc1_after_pads_live_during_blink(probe, cfg):
    bb, pb = scenario(cfg["DEBOUNCE_MS"])
    out = probe.one(f"loopsim 0 4 {cfg['DEBOUNCE_MS']} {bb} {pb}").split()
    notes = [e for e in out if ":ON:" in e or ":OFF:" in e]
    assert "1200:SCALE:5" in out
    assert notes == ["1500:ON:48", "1700:OFF:48"]          # chromatic pad 0 = 48, no delay
    leds = [e for e in out if ":LED:" in e]
    assert leds == [f"{1200 + 90 * k}:LED:{1 - k % 2}" for k in range(12)]   # 6 blinks, 90 ms


def test_doc1_before_blocking_model_loses_the_touch(probe, cfg):
    """Model of the old delay()-based blink: the same touch produces no note at all."""
    bb, pb = scenario(cfg["DEBOUNCE_MS"])
    out = probe.one(f"loopsim 1 4 {cfg['DEBOUNCE_MS']} {bb} {pb}").split()
    assert "1200:SCALE:5" in out
    assert [e for e in out if ":ON:" in e or ":OFF:" in e] == []


def test_button_still_works_during_blink(probe, cfg):
    # Two short presses 300 ms apart: the second lands inside the first blink and is honoured.
    n = 2500
    bb = "".join("1" if (1000 <= t < 1100 or 1400 <= t < 1500) else "0" for t in range(n))
    pb = "0" * n
    out = probe.one(f"loopsim 0 0 {cfg['DEBOUNCE_MS']} {bb} {pb}").split()
    assert [e for e in out if ":SCALE:" in e] == ["1100:SCALE:1", "1500:SCALE:2"]
    # blink restarts with the new count (3 blinks from 1500)
    assert [e for e in out if ":LED:" in e and int(e.split(":")[0]) >= 1500] == \
        [f"{1500 + 90 * k}:LED:{1 - k % 2}" for k in range(6)]
