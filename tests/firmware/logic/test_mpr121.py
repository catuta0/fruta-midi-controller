"""MPR121 burst-read decoding (fm_mpr121.h) against hand-decoded byte vectors."""
import pathlib
import re

import pytest

from conftest import INO, ROOT

LIB_H = ROOT / "tools" / "arduino" / "user" / "libraries" / "Adafruit_MPR121" / "Adafruit_MPR121.h"


def test_register_layout(probe):
    # 0x04 filtered E0 LSB, 24 bytes for E0..E11; 0x1E baseline E0, 12 bytes.
    assert probe.one("mprconsts") == f"{0x04} {0x1E} 24 12"
    # the 32-byte AVR Wire buffer limits one transaction; each block must fit
    assert 24 <= 32 and 12 <= 32


@pytest.mark.skipif(not LIB_H.exists(), reason="library not installed in tools/arduino")
def test_addresses_match_linked_library():
    text = LIB_H.read_text(encoding="utf-8", errors="replace")
    assert re.search(r"MPR121_FILTDATA_0L\s*=\s*0x04", text)
    assert re.search(r"MPR121_BASELINE_0\s*=\s*0x1E", text)


def run(probe, filt, base):
    line = "mpr " + " ".join(f"{b:02x}" for b in filt) + " " + " ".join(f"{b:02x}" for b in base)
    return [tuple(int(x) for x in t.split("/")) for t in probe.one(line).split()]


def test_hand_decoded_vector(probe):
    filt = [0] * 24
    base = [0] * 12
    # E0: LSB 0xA5, MSB 0x02 -> 0x2A5 = 677; baseline 0xA9 -> 0xA9 << 2 = 676; delta -1
    filt[0], filt[1], base[0] = 0xA5, 0x02, 0xA9
    # E1: 0x0300 + 0x00 = 768; baseline 0xC8 -> 800; delta 32
    filt[2], filt[3], base[1] = 0x00, 0x03, 0xC8
    # E5: LSB 0xFF, MSB 0x03 -> 1023 (max); baseline 0xFF -> 1020; delta -3
    filt[10], filt[11], base[5] = 0xFF, 0x03, 0xFF
    # E7: reserved high bits set: MSB 0xFD -> only bits 1..0 (=01) used -> 0x100 + 0x10 = 272;
    #     baseline 0x50 -> 320; delta 48
    filt[14], filt[15], base[7] = 0x10, 0xFD, 0x50
    # E11 (last pair, offsets 22/23): 0x01F4 = 500; baseline 0x8C -> 560; delta 60
    filt[22], filt[23], base[11] = 0xF4, 0x01, 0x8C
    got = run(probe, filt, base)
    expected = [(0, 0, 0)] * 12
    expected[0] = (677, 676, -1)
    expected[1] = (768, 800, 32)
    expected[5] = (1023, 1020, -3)
    expected[7] = (272, 320, 48)
    expected[11] = (500, 560, 60)
    assert got == expected


def test_electrodes_do_not_alias(probe):
    # distinct value per electrode: filtered = 100 + 37*e (LSB first), baseline byte = 40 + 5*e
    filt, base = [], []
    for e in range(12):
        v = 100 + 37 * e
        filt += [v & 0xFF, v >> 8]
        base.append(40 + 5 * e)
    got = run(probe, filt, base)
    assert got == [(100 + 37 * e, (40 + 5 * e) * 4, (40 + 5 * e) * 4 - (100 + 37 * e)) for e in range(12)]


def test_delta_matches_old_library_path_for_valid_data(probe):
    """Old path: filteredData() = LSB | MSB << 8 (Adafruit readRegister16, LSB first),
    baselineData() = byte << 2. Identical whenever the reserved high bits are 0."""
    import random
    rng = random.Random(7)
    for _ in range(50):
        f = [rng.randrange(0, 1024) for _ in range(12)]
        b = [rng.randrange(0, 256) for _ in range(12)]
        filt = [x for v in f for x in (v & 0xFF, v >> 8)]
        got = run(probe, filt, b)
        assert [g[2] for g in got] == [(bb << 2) - ((ff & 0xFF) | ((ff >> 8) << 8)) for ff, bb in zip(f, b)]


def test_sketch_uses_burst_read_not_per_pad_reads():
    text = INO.read_text(encoding="utf-8")
    loop = text[text.index("void loop()"):]
    assert "readSensorData(" in loop and "fm::mpr121_delta(" in loop and "fm::mpr121_next_run(" in loop
    assert "baselineData(" not in loop and "filteredData(" not in loop
    assert "setClock(400000)" in text          # I2C clock unchanged (decision pending)


def runs(probe, mask):
    out = probe.one(f"runs {mask}")
    return [] if out == "none" else [tuple(int(x) for x in r.split(":")) for r in out.split()]


@pytest.mark.parametrize("mask,expected", [
    (0, []),
    (1 << 5, [(5, 1)]),                      # 1 pad: 1 run of 1 = 9 bytes, same as before
    (0b11, [(0, 2)]),                        # adjacent
    (0b101, [(0, 3)]),                       # gap 1 -> merged (15 bytes < 18)
    (0b1001, [(0, 1), (3, 1)]),              # gap 2 -> separate (18 bytes = 18, not 21)
    ((1 << 0) | (1 << 11), [(0, 1), (11, 1)]),
    (0xFFF, [(0, 12)]),                      # all 12 -> one run: 42 bytes
    (0xF000, []),                            # bits above electrode 11 ignored
])
def test_runs_hand_cases(probe, mask, expected):
    assert runs(probe, mask) == expected


def cost(rs):
    return sum(6 + 3 * n for _, n in rs)        # bytes on the bus, see fm_mpr121.h


def optimal_cost(mask):
    """Independent DP: cheapest cover of the set bits by intervals costing 6 + 3*len."""
    bits = [e for e in range(12) if mask >> e & 1]
    best = [0] + [None] * len(bits)
    for j in range(1, len(bits) + 1):
        best[j] = min(best[i] + 6 + 3 * (bits[j - 1] - bits[i] + 1) for i in range(j))
    return best[len(bits)]


def test_runs_exhaustive_all_masks(probe):
    masks = list(range(4096))
    outs = probe.run([f"runs {m}" for m in masks])
    worst = 0
    for m, out in zip(masks, outs):
        rs = [] if out == "none" else [tuple(int(x) for x in r.split(":")) for r in out.split()]
        covered = set()
        for lo, n in rs:
            assert n >= 1 and lo + n <= 12
            assert m >> lo & 1 and m >> (lo + n - 1) & 1        # runs start and end on a sounding pad
            covered |= set(range(lo, lo + n))
        assert {e for e in range(12) if m >> e & 1} <= covered
        assert all(b[0] - (a[0] + a[1]) >= 2 for a, b in zip(rs, rs[1:]))   # gaps >= 2 between runs
        c = cost(rs)
        assert c <= 9 * bin(m).count("1")       # never worse than the old per-pad reads
        assert c == optimal_cost(m), (m, rs)    # optimal under the byte-cost model
        worst = max(worst, c)
    assert worst == 42


def test_block_offset_decoding(probe):
    """A run starting at lo is decoded with index e - lo (as the sketch does)."""
    # run of 3 electrodes read from E4: filtered 300, 301, 302; baseline bytes 80, 81, 82
    filt = [300 & 0xFF, 300 >> 8, 301 & 0xFF, 301 >> 8, 302 & 0xFF, 302 >> 8] + [0] * 18
    base = [80, 81, 82] + [0] * 9
    got = run(probe, filt, base)[:3]
    assert got == [(300, 320, 20), (301, 324, 23), (302, 328, 26)]


LIB_CPP = LIB_H.with_suffix(".cpp")


def test_config_register_addresses_match_library(probe):
    assert probe.one("mprregs") == f"{0x5E} {0x7B} {0x7C} {0x7D} {0x7E} {0x7F} 3200"
    if LIB_H.exists():
        text = LIB_H.read_text(encoding="utf-8", errors="replace")
        for name, val in [("ECR", "0x5E"), ("AUTOCONFIG0", "0x7B"), ("AUTOCONFIG1", "0x7C"),
                          ("UPLIMIT", "0x7D"), ("LOWLIMIT", "0x7E"), ("TARGETLIMIT", "0x7F")]:
            assert re.search(rf"MPR121_{name}\s*=\s*{val}", text), name


def test_autoconfig1_byte_has_scts_cleared(probe, ):
    cfg = [int(x) for x in probe.one("mprcfg 3200").split()]
    assert cfg[0] == 0x00 and not cfg[0] & 0x80          # SCTS = 0, interrupts off
    assert probe.int("ac1 0 0 0 0") == 0x00
    assert probe.int("ac1 1 0 0 0") == 0x80
    assert probe.int("ac1 0 1 1 1") == 0x07


@pytest.mark.parametrize("vdd,expected", [
    (3200, (200, 180, 130)),   # design VDD (ADR-010): 2.5/3.2*256 = 200.0; 180.0; 130.0
    (3300, (201, 180, 130)),   # 2.6/3.3*256 = 201.70 -> 201; 180.9 -> 180; 130.65 -> 130
    (3100, (198, 178, 128)),   # 2.4/3.1*256 = 198.19 -> 198; 178.2 -> 178; 128.7 -> 128
    (1800, (156, 140, 101)),   # 1.1/1.8*256 = 156.44 -> 156; 140.4 -> 140; 101.4 -> 101
])
def test_limits_from_vdd(probe, vdd, expected):
    assert tuple(int(x) for x in probe.one(f"mprcfg {vdd}").split()[1:]) == expected


@pytest.mark.skipif(not LIB_CPP.exists(), reason="library not installed in tools/arduino")
def test_library_begin_behaviour_that_the_sketch_relies_on():
    text = LIB_CPP.read_text(encoding="utf-8", errors="replace")
    # AUTOCONFIG0 = 0b00001011: FFI 00, RETRY 00, BVA 10, ARE 1, ACE 1
    m = re.search(r"writeRegister\(MPR121_AUTOCONFIG0,\s*0b([01]{8})\)", text)
    assert m and int(m.group(1), 2) == 0x0B
    ac0 = int(m.group(1), 2)
    assert (ac0 >> 6, (ac0 >> 4) & 3, (ac0 >> 2) & 3, (ac0 >> 1) & 1, ac0 & 1) == (0, 0, 2, 1, 1)
    # BVA must equal CL in ECR: ECR = 0b10000000 + 12 -> CL = 0b10
    assert "0b10000000 + 12" in text and (0b10000000 + 12) >> 6 == 0b10
    assert "MPR121_AUTOCONFIG1" not in text          # library never writes 0x7C -> sketch must
    assert re.search(r"MPR121_UPLIMIT,\s*200\)", text)  # library limit 200 = design-VDD value (ADR-010)


def test_sketch_writes_config_in_stop_mode_after_begin():
    text = INO.read_text(encoding="utf-8")
    body = text[text.index("void configureSensor("):text.index("void startSensors(")]
    order = ["readRegister8(fm::MPR121_REG_ECR)", "writeRegister(fm::MPR121_REG_ECR, 0x00)",
             "MPR121_REG_AUTOCONFIG1, fm::MPR121_AUTOCONFIG1_VALUE", "MPR121_REG_UPLIMIT, usl",
             "MPR121_REG_TARGETLIMIT, fm::mpr121_tl(usl)", "MPR121_REG_LOWLIMIT, fm::mpr121_lsl(usl)",
             "writeRegister(fm::MPR121_REG_ECR, ecr)"]
    pos = [body.index(o) for o in order]
    assert pos == sorted(pos)
    start = text[text.index("void startSensor(uint8_t s)"):]
    assert start.index(".begin(") < start.index("configureSensor(s)")
    assert "AUTOCONFIG0" not in body                  # library value kept
