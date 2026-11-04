"""Build the host probe for the FrutaMIDI logic headers once per test session."""
import pathlib
import re
import shutil
import subprocess

import pytest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FW = ROOT / "firmware" / "FrutaMIDI"
INO = FW / "FrutaMIDI.ino"
CXXFLAGS = ["-std=c++17", "-Wall", "-Wextra", "-Werror"]


def cxx():
    c = shutil.which("c++")
    if c is None:
        pytest.fail("c++ compiler not found (Xcode Command Line Tools required)")
    return c


class Probe:
    """One long-lived probe process; one command line in, one result line out."""

    def __init__(self, exe):
        self.proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     text=True, bufsize=1)

    def run(self, lines):
        """Send a list of command lines, return the list of result lines."""
        out = []
        for line in lines:
            assert "\n" not in line
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()
            res = self.proc.stdout.readline()
            assert res, f"probe exited (code {self.proc.poll()}) on: {line}"
            res = res.rstrip("\n")
            assert not res.startswith("ERR"), res
            out.append(res)
        return out

    def one(self, line):
        return self.run([line])[0]

    def int(self, line):
        return int(self.one(line))

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=10)


@pytest.fixture(scope="session")
def probe(tmp_path_factory):
    build = tmp_path_factory.mktemp("fm_probe")
    exe = build / "fm_probe"
    subprocess.run([cxx(), *CXXFLAGS, "-I", str(FW), str(HERE / "fm_probe.cpp"), "-o", str(exe)],
                   check=True)
    p = Probe(exe)
    yield p
    p.close()


def ino_const(name):
    """Value of `const <type> NAME = <int>;` in the production sketch."""
    m = re.search(r"const\s+\w+\s+" + re.escape(name) + r"\s*=\s*(0x[0-9A-Fa-f]+|\d+)\s*;",
                  INO.read_text(encoding="utf-8"))
    assert m, f"{name} not found in {INO}"
    return int(m.group(1), 0)


@pytest.fixture(scope="session")
def cfg():
    return {n: ino_const(n) for n in
            ("DEBOUNCE_MS", "TOUCH_THRESHOLD", "RELEASE_THRESHOLD", "AT_MAX_DELTA",
             "AT_INTERVAL_MS", "MIDI_CHANNEL")}
