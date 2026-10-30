"""Host unit test for midi_math.h: compiles a C++ driver and checks known answers."""
import pathlib
import shutil
import subprocess

import pytest

HERE = pathlib.Path(__file__).resolve().parent

# (root, octave, expected)
CASES = [
    (60, 0, 60),
    (60, 1, 72),
    (60, -6, 0),    # 60 - 72 = -12 -> clamped to 0
    (120, 1, 127),  # 120 + 12 = 132 -> clamped to 127
]

DRIVER = r"""
#include <cstdio>
#include <cstdlib>
#include "midi_math.h"
int main(int argc, char** argv) {
  for (int i = 1; i + 1 < argc; i += 2) {
    int root = std::atoi(argv[i]);
    int octave = std::atoi(argv[i + 1]);
    std::printf("%d\n", (int)midi_note((uint8_t)root, (int8_t)octave));
  }
  return 0;
}
"""


@pytest.fixture(scope="module")
def driver(tmp_path_factory):
    cxx = shutil.which("c++")
    if cxx is None:
        pytest.fail("c++ compiler not found (Xcode Command Line Tools required)")
    build = tmp_path_factory.mktemp("midi_math")
    src = build / "driver.cpp"
    exe = build / "driver"
    src.write_text(DRIVER)
    subprocess.run(
        [cxx, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", str(HERE),
         str(src), "-o", str(exe)],
        check=True,
    )
    return exe


@pytest.mark.parametrize("root,octave,expected", CASES)
def test_midi_note(driver, root, octave, expected):
    out = subprocess.run([str(driver), str(root), str(octave)],
                         check=True, capture_output=True, text=True).stdout
    assert int(out.strip()) == expected
