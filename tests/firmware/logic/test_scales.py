"""Scale table and pad -> note mapping (fm_scales.h). Expected values are hand-written."""
import pytest

# Hand table: (root, len, fixed, steps) as specified in the original sketch @ e4668d4.
SCALE_TABLE = [
    (36, 12, 1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),   # Drum Rack (fixed)
    (48, 5, 0, [0, 2, 4, 7, 9]),                           # major pentatonic
    (48, 5, 0, [0, 3, 5, 7, 10]),                          # minor pentatonic
    (48, 7, 0, [0, 2, 4, 5, 7, 9, 11]),                    # major
    (48, 7, 0, [0, 2, 3, 5, 7, 8, 10]),                    # natural minor
    (48, 12, 0, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),   # chromatic
]

# Hand table: first octave (pads 0..len-1) at octave shift 0, as MIDI notes.
FIRST_OCTAVE = [
    [36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47],
    [48, 50, 52, 55, 57],
    [48, 51, 53, 55, 58],
    [48, 50, 52, 53, 55, 57, 59],
    [48, 50, 51, 53, 55, 56, 58],
    [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59],
]

# Hand table: note of pad `len` (wraps to next octave) and of pad 23 (last pad with 2 sensors).
PAD_LEN_NOTE = [48, 60, 60, 60, 60, 60]
PAD_23_NOTE = [59, 103, 103, 88, 87, 71]


def test_number_of_scales(probe):
    assert probe.int("nscales") == 6


@pytest.mark.parametrize("i", range(6))
def test_scale_table_matches_spec(probe, i):
    root, ln, fixed, steps = SCALE_TABLE[i]
    assert probe.one(f"scale {i}") == " ".join(map(str, [root, ln, fixed, *steps]))


@pytest.mark.parametrize("i", range(6))
def test_first_octave(probe, i):
    expected = FIRST_OCTAVE[i]
    got = [int(x) for x in probe.run([f"note {i} 0 {p}" for p in range(len(expected))])]
    assert got == expected


@pytest.mark.parametrize("i", range(6))
def test_wrap_into_next_octave(probe, i):
    ln = SCALE_TABLE[i][1]
    assert probe.int(f"note {i} 0 {ln}") == PAD_LEN_NOTE[i]
    assert probe.int(f"note {i} 0 23") == PAD_23_NOTE[i]


@pytest.mark.parametrize("i", range(1, 6))
@pytest.mark.parametrize("octave", [-2, -1, 1, 2])
def test_octave_shift_moves_by_12(probe, i, octave):
    for p, base in enumerate(FIRST_OCTAVE[i]):
        assert probe.int(f"note {i} {octave} {p}") == base + 12 * octave


@pytest.mark.parametrize("octave", [-2, -1, 1, 2])
def test_fixed_scale_ignores_octave(probe, octave):
    got = [int(x) for x in probe.run([f"note 0 {octave} {p}" for p in range(12)])]
    assert got == FIRST_OCTAVE[0]


def test_real_table_extremes_inside_midi_range(probe):
    # Lowest: any non-fixed scale, pad 0, octave -2 -> 48 - 24 = 24.
    assert probe.int("note 1 -2 0") == 24
    # Highest: pentatonic pad 23 at +2 -> 103 + 24 = 127 exactly (not clamped).
    assert probe.int("note 1 2 23") == 127
    assert probe.int("note 5 2 23") == 95


@pytest.mark.parametrize("root,fixed,octave,pad,steps,expected", [
    (120, 0, 1, 0, [0], 127),        # 132 -> 127
    (127, 0, 0, 0, [0], 127),        # exactly 127
    (0, 0, -2, 0, [0], 0),           # -24 -> 0
    (60, 0, -6, 0, [0], 0),          # -12 -> 0
    (12, 0, -1, 0, [0], 0),          # exactly 0
    (13, 0, -1, 0, [0], 1),          # 1, not clamped
    (120, 1, 2, 0, [0], 120),        # fixed scale: octave ignored, no clamp
    (100, 0, 2, 23, [0], 127),       # 100 + 24 + 12*23 -> 127
])
def test_note_clamp_0_127(probe, root, fixed, octave, pad, steps, expected):
    assert probe.int(f"notec {root} {fixed} {octave} {pad} {' '.join(map(str, steps))}") == expected


def test_clamp_one_below_max(probe):
    assert probe.int("notec 126 0 0 0 0 1") == 126
    assert probe.int("notec 126 0 0 1 0 1") == 127
    assert probe.int("notec 126 0 0 1 0 2") == 127   # 128 -> 127


def test_next_scale_wraps(probe):
    assert [int(x) for x in probe.run([f"next {i} 6" for i in range(6)])] == [1, 2, 3, 4, 5, 0]


NAMES = ["Drum Rack (notes 36-47)", "Major pentatonic", "Minor pentatonic",
         "Major", "Natural minor", "Chromatic"]


@pytest.mark.parametrize("i", range(6))
def test_scale_names_english(probe, i):
    assert probe.one(f"scalename {i}") == NAMES[i]
