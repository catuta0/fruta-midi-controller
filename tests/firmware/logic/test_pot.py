"""Potentiometer -> octave with hysteresis (fm_pot.h). 10-bit ADC (0..1023)."""
import pytest


def reference(adc, cur):
    """Independent integer model: pos = 5*adc/1024 zones; switch when |pos - centre| > 0.7.
    |5*adc/1024 - (cur+2.5)| > 0.7  <=>  |5*adc - 1024*(cur+2) - 512| > 716.8  (>= 717)."""
    if abs(5 * adc - 1024 * (cur + 2) - 512) >= 717:
        return min(4, (5 * adc) >> 10) - 2
    return cur


def test_exhaustive_against_reference(probe):
    lines, exp = [], []
    for cur in range(-2, 3):
        for adc in range(1024):
            lines.append(f"pot {adc} {cur}")
            exp.append(reference(adc, cur))
    got = [int(x) for x in probe.run(lines)]
    bad = [(l, g, e) for l, g, e in zip(lines, got, exp) if g != e]
    assert not bad, bad[:10]


# Hand-calculated switching thresholds (CALCULATION, see coverage.md).
@pytest.mark.parametrize("adc,cur,expected", [
    (655, 0, 0), (656, 0, 1),      # up: pos > 3.2  <=> adc > 655.36
    (369, 0, 0), (368, 0, -1),     # down: pos < 1.8 <=> adc < 368.64
    (574, 1, 1), (573, 1, 0),      # +1 down: pos < 2.8 <=> adc < 573.44
    (860, 1, 1), (861, 1, 2),      # +1 up: pos > 4.2 <=> adc > 860.16
    (0, -2, -2), (1023, 2, 2),     # ends never leave the end zones
    (1023, -2, 2), (0, 2, -2),     # large jump goes straight to the zone under the wiper
    (512, 0, 0),                   # centre
])
def test_boundaries(probe, adc, cur, expected):
    assert probe.int(f"pot {adc} {cur}") == expected


@pytest.mark.parametrize("k", [1, 2, 3, 4])
@pytest.mark.parametrize("noise", [1, 3, 5, 10])
def test_noise_at_border_does_not_chatter(probe, k, noise):
    border = -(-1024 * k // 5)          # first ADC count of zone k: 205, 410, 615, 820
    for start in (k - 3, k - 2):        # octave of the zone below / above the border
        cur = start
        for k in range(200):
            adc = border + (noise if k % 2 else -noise)
            cur = probe.int(f"pot {adc} {cur}")
        assert cur == start, (border, noise, start, cur)


def test_slow_ramp_with_noise_switches_once_per_border(probe):
    cur, changes = -2, []
    seq = [a + (3 if i % 2 else -3) for i, a in enumerate(range(3, 1021))]
    seq += [a + (3 if i % 2 else -3) for i, a in enumerate(range(1020, 2, -1))]
    for adc in seq:
        nxt = probe.int(f"pot {adc} {cur}")
        if nxt != cur:
            changes.append(nxt)
        cur = nxt
    assert changes == [-1, 0, 1, 2, 1, 0, -1, -2]
