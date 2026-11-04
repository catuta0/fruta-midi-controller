"""Shared-note reference counting (fm_notes.h, review F-004) and sensor presence
monitoring with a failing-bus stub (fm_sensor_health.h, review F-005)."""
import pytest


def notes(probe, ops):
    out = probe.one("notes " + " ".join(ops))
    return [] if out == "none" else out.split()


def test_reviewer_sequence_f004(probe):
    # Major scale, octave 0: pad 7 = 48 + 12 = 60. Octave +1: pad 0 = 48 + 12 = 60.
    assert probe.int("note 3 0 7") == 60 and probe.int("note 3 1 0") == 60
    assert notes(probe, ["P7:60"]) == ["ON:60"]
    assert notes(probe, ["P7:60", "P0:60"]) == ["ON:60"]               # no second Note On
    assert notes(probe, ["P7:60", "P0:60", "R7"]) == ["ON:60"]         # no Note Off while pad 0 holds
    assert notes(probe, ["P7:60", "P0:60", "R7", "R0"]) == ["ON:60", "OFF:60"]


def test_release_all_sends_one_note_off_per_note(probe):
    assert notes(probe, ["P1:60", "P2:60", "P3:62", "A"]) == ["ON:60", "ON:62", "OFF:60", "OFF:62"]
    assert notes(probe, ["A"]) == []


def test_distinct_notes_unchanged_behaviour(probe):
    assert notes(probe, ["P0:48", "P1:50", "R0", "R1"]) == ["ON:48", "ON:50", "OFF:48", "OFF:50"]
    assert notes(probe, ["P0:48", "P0:48", "R0", "R0"]) == ["ON:48", "OFF:48"]   # idempotent


def test_shared_aftertouch_is_max_and_final_zero_on_last_release(probe):
    ev = notes(probe, ["P0:60", "P1:60", "U0:40", "U1:90", "U0:100", "U1:10", "R0", "R1"])
    # max(40,0)=40; max(40,90)=90; max(100,90)=100; max(100,10)=100 (no send);
    # pad 0 releases -> remaining holder 10 -> AT 10; last release -> AT 0, then Note Off
    assert ev == ["ON:60", "AT:60:40", "AT:60:90", "AT:60:100", "AT:60:10", "AT:60:0", "OFF:60"]


def test_no_zero_when_pressure_never_sent(probe):
    assert notes(probe, ["P0:60", "P1:60", "R0", "R1"]) == ["ON:60", "OFF:60"]


def test_new_holder_inherits_sent_value(probe):
    # pad 0 sent 80; pad 1 joins with 0 -> max still 80, nothing new; release pad 0 -> pad 1 at 0
    ev = notes(probe, ["P0:60", "U0:80", "P1:60", "U1:0", "R0", "R1"])
    assert ev == ["ON:60", "AT:60:80", "AT:60:0", "OFF:60"]


# ---- F-005 -----------------------------------------------------------------------------

def test_health_constants(probe):
    assert probe.one("healthconsts") == "3 250 2000"


def hs(probe, T, ff, ft, reset_at=-1):
    return probe.one(f"healthsim {T} {ff} {ft} {reset_at}").split()


def test_healthy_bus_plays_normally(probe):
    assert hs(probe, 3000, -1, -1) == ["0:START_OK", "15:ON"]


def test_bus_failure_releases_notes_and_retries(probe):
    ev = hs(probe, 6000, 1000, 3500)
    # 3 consecutive failed status reads (1000, 1001, 1002) -> lost, note off, error LED
    assert ev[:5] == ["0:START_OK", "15:ON", "1002:LOST", "1002:OFF", "1002:LED_ERR"]
    # retry period > 2000 ms since the last start attempt (t=0): 2001 fails (bus still down),
    # 4002 succeeds; the held pad sounds again at once (its lockout expired long ago)
    assert ev[5:] == ["2001:START_FAIL", "4002:START_OK", "4002:ON", "4002:LED_OK"]


def test_short_glitch_is_tolerated(probe):
    # 2 failed transactions (< SENSOR_FAIL_LIMIT) -> no loss, note stays on
    assert hs(probe, 3000, 1000, 1002) == ["0:START_OK", "15:ON"]


def test_chip_reset_detected_by_ecr_check(probe):
    # chip resets at 1100 (still ACKs, ECR = 0, stop mode -> no touches, so the pad releases);
    # the next 250 ms ECR check (1250) declares it lost; one Note Off only
    ev = hs(probe, 1400, -1, -1, 1100)
    assert ev == ["0:START_OK", "15:ON", "1100:OFF", "1250:LOST", "1250:LED_ERR"]


def test_missing_sensor_at_boot_is_retried(probe):
    ev = hs(probe, 5000, 0, 2500)
    assert ev == ["0:START_FAIL", "1:LED_ERR", "2001:START_FAIL", "4002:START_OK", "4002:ON", "4002:LED_OK"]


def test_sketch_wiring_f005_f006():
    from conftest import INO
    text = INO.read_text(encoding="utf-8")
    loop = text[text.index("void loop()"):]
    assert "touched()" not in text                      # NACK would read as 12 touches
    assert "health[s].retry_due(" in loop and "for (uint8_t s = 0; s < NUM_SENSORS; s++) if (health[s].retry_due" in loop
    assert "health[s].report(readOk)" in loop and "health[s].report_check(" in loop
    assert "health[s].report(dataOk)" in loop
    start = text[text.index("void startSensor(uint8_t s)"):text.index("void startSensors()")]
    assert start.index(".begin(") < start.index("I2C_BUS.setClock(400000)") < start.index("configureSensor(s)")


def test_intermittent_failures_never_accumulate(probe):
    # fails must be consecutive: 2 fails, 1 success, 2 fails ... never lost; 3 in a row -> lost once
    assert probe.one("hreport 0 0 1 0 0 1 0 0 1") == "0 0 0 0 0 0 0 0 0"
    assert probe.one("hreport 0 0 0 0 0 0") == "0 0 1 0 0 0"


@pytest.mark.parametrize("lsb,msb,expected", [
    (0x00, 0x00, 0), (0x01, 0x00, 1), (0xFF, 0x0F, 0x0FFF), (0xFF, 0xFF, 0x0FFF),  # bit 15 OVCF etc. masked
    (0x00, 0x10, 0), (0x34, 0x82, 0x0234),
])
def test_touch_bits(probe, lsb, msb, expected):
    assert probe.int(f"touchbits {lsb} {msb}") == expected
