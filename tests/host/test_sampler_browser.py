"""T-020/T-021: pytest wrapper for the headless-Chrome tests of docs/index.html.

Runs tests/host/browser/sampler.test.mjs with Node's test runner (TAP reporter), once
against the real page and once per deliberate mutation of the page (served in memory,
docs/ is never written). Each Node test becomes one pytest item; each mutation must make
its named test fail, which shows the tests can detect wrong behaviour.

Raw TAP output is kept in reports/software/T-021/ (T-020 results are kept as they were).
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BROWSER_DIR = ROOT / "tests" / "host" / "browser"
SUITE = BROWSER_DIR / "sampler.test.mjs"
RAW_DIR = ROOT / "reports" / "software" / "T-021"

EXPECTED_TESTS = [
    "connected device is auto-selected and shown",
    "port open statechange does not re-open the port",
    "each pad plays on its default note 36..47",
    "note on is logged with name, velocity and channel",
    "pad velocity scales output gain as (v/127)^1.5",
    "kick pad (note 36) starts a sine oscillator",
    "unmapped note starts a two-oscillator synth voice at equal-tempered pitch",
    "synth checkbox off silences unmapped notes",
    "note off (0x80) stops the synth voice",
    "note on velocity 0 acts as note off",
    "retriggering a held synth note replaces the old voice",
    "poly aftertouch opens the synth filter",
    "poly aftertouch on a pad note drives the pad bar; note off resets it",
    "notes on any channel are accepted (omni)",
    "non-note messages are ignored without errors",
    "MIDI access rejected shows the permission error",
    "browser without Web MIDI shows the unsupported error",
    "busy device shows the busy error",
    "busy device next to a free one is listed as busy",
    "no device shows the plug-in hint; hot-plug connects; unplug reverts",
    "learn mode assigns the next note and persists it",
    "learn button pressed twice cancels learning",
    "keyboard fallback plays pads (no MIDI needed)",
    "notes before the audio gate click flash the pad and emphasise the enable-sound hint",
    "learning a note already used by another pad swaps the two pads notes",
    "no Portuguese UI strings in any rendered state",
]

# mutation name (see tests/host/browser/server.mjs) -> test that must fail
MUTATIONS = {
    "vel0_is_note_on": "note on velocity 0 acts as note off",
    "pad_base_note_35": "each pad plays on its default note 36..47",
    "busy_reported_as_ok": "busy device shows the busy error",
    "aftertouch_ignored": "poly aftertouch opens the synth filter",
    "learn_ignored": "learn mode assigns the next note and persists it",
    "learn_no_swap": "learning a note already used by another pad swaps the two pads notes",
    "gate_no_flash": "notes before the audio gate click flash the pad and emphasise the enable-sound hint",
}

# The page before T-021 (docs/index.html @ e4668d4) must fail the ADR-005 tests for the
# behavioural reason, shown by the assertion message in the TAP output.
OLD_PAGE = BROWSER_DIR / "fixtures" / "index_e4668d4.html"
OLD_PAGE_MUST_FAIL = {
    "notes before the audio gate click flash the pad and emphasise the enable-sound hint": "pad 0 flashes even without audio",
    "learning a note already used by another pad swaps the two pads notes": "pad 1 receives pad 0 old note",
    "no Portuguese UI strings in any rendered state": "Portuguese strings found",
}

TAP_LINE = re.compile(r"^(ok|not ok) \d+ - (.+?)(?: # .*)?$")


def run_suite(mutation="", page_file=None, label=None):
    if not (BROWSER_DIR / "node_modules" / "playwright-core").is_dir():
        pytest.fail("playwright-core missing: run `npm ci` in tests/host/browser")
    env = dict(os.environ, SAMPLER_MUTATION=mutation, SAMPLER_FILE=str(page_file or ""))
    proc = subprocess.run(
        ["node", "--test", "--test-reporter=tap", str(SUITE)],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=300,
    )
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    name = "tap_" + (label or mutation or "baseline") + ".txt"
    (RAW_DIR / name).write_text(
        "# exit_code: %d\n%s\n# --- stderr ---\n%s" % (proc.returncode, proc.stdout, proc.stderr)
    )
    results = {}
    for line in proc.stdout.splitlines():
        m = TAP_LINE.match(line)  # top-level results only (no leading indent)
        if m:
            results[m.group(2)] = m.group(1)
    return proc, results


@pytest.fixture(scope="session")
def baseline():
    return run_suite()


@pytest.mark.parametrize("name", EXPECTED_TESTS)
def test_browser_behaviour(baseline, name):
    _, results = baseline
    assert name in results, "test not reported by node: %r" % name
    assert results[name] == "ok", "see reports/software/T-021/tap_baseline.txt"


def test_browser_suite_complete(baseline):
    proc, results = baseline
    assert set(results) == set(EXPECTED_TESTS)
    assert "# fail 0" in proc.stdout
    assert proc.returncode == 0


@pytest.mark.parametrize("mutation", sorted(MUTATIONS))
def test_mutation_is_detected(mutation):
    _, results = run_suite(mutation)
    assert results.get(MUTATIONS[mutation]) == "not ok", (
        "mutation %s was NOT detected by %r" % (mutation, MUTATIONS[mutation])
    )


def test_old_page_fails_adr005_tests():
    proc, results = run_suite(page_file=OLD_PAGE, label="old_page_e4668d4")
    for name, reason in OLD_PAGE_MUST_FAIL.items():
        assert results.get(name) == "not ok", "old page unexpectedly passes %r" % name
        assert reason in proc.stdout, "old page fails %r but not for the reason %r" % (name, reason)
