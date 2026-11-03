"""Guards: the sketch calls the tested headers, and the headers stay Arduino-free and C++11."""
import re
import subprocess

import pytest

from conftest import FW, INO, cxx

HEADERS = sorted(FW.glob("fm_*.h"))


def test_headers_exist():
    assert {h.name for h in HEADERS} == {
        "fm_time.h", "fm_scales.h", "fm_debounce.h", "fm_aftertouch.h",
        "fm_button.h", "fm_pot.h", "fm_midi.h", "fm_blink.h", "fm_mpr121.h"}


@pytest.mark.parametrize("h", HEADERS, ids=lambda p: p.name)
def test_header_has_no_arduino_dependency(h):
    text = h.read_text(encoding="utf-8")
    includes = re.findall(r'#include\s*[<"]([^>"]+)[>"]', text)
    assert all(i == "stdint.h" or i.startswith("fm_") for i in includes), includes


@pytest.mark.parametrize("std", ["c++11", "c++17"])
def test_headers_compile_standalone(tmp_path, std):
    src = tmp_path / "all.cpp"
    src.write_text("".join(f'#include "{h.name}"\n' for h in HEADERS) + "int main() { return 0; }\n")
    subprocess.run([cxx(), f"-std={std}", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(FW), str(src), "-o", str(tmp_path / "a.out")], check=True)


@pytest.mark.parametrize("call", [
    "fm::note_for_pad(", "fm::next_scale_index(", "fm::pad_step(", "fm::pad_touched(",
    "fm::pressure_from_delta(", "fm::pressure_should_send(", "fm::elapsed_at_least(",
    "fm::elapsed_more_than(", "fm::ButtonClassifier", "fm::octave_from_adc(", "fm::channel_status(",
    "fm::Blinker", "led.level_or(", "fm::pressure_reset_on_release(", "fm::BLINK_SCALE_MS", "fm::BLINK_RECAL_MS", "fm::BLINK_READY_MS",
])
def test_sketch_calls_tested_logic(call):
    assert call in INO.read_text(encoding="utf-8")


@pytest.mark.parametrize("pattern", [
    r"steps\[pad % sc\.len\]",       # note mapping
    r"\bmap\(",                       # aftertouch scaling
    r"fabsf\(",                       # pot hysteresis
    r"now - downAt",                  # long press
])
def test_sketch_has_no_duplicate_logic(pattern):
    assert not re.search(pattern, INO.read_text(encoding="utf-8"))


def test_no_blocking_blink_left():
    """DOC-1: the only delay() left is the 10 ms USB re-attach in midiBegin()."""
    text = INO.read_text(encoding="utf-8")
    assert "void blink(" not in text
    assert re.findall(r"\bdelay\(\s*(\w+)\s*\)", text) == ["10"]


FIRMWARE_FILES = sorted(FW.glob("*.h")) + [INO]
# Portuguese words that appeared in the e4668d4 sketch (ADR-000: project files in English).
PT_WORDS = r"\b(escalas?|oitavas?|notas?|pinos?|bot[aã]o|toque|premido|pisca[a-z]*|placas?|" \
           r"sensores|frutas|encontrado|cromatica|pentatonica|maior|menor|ligares|defeito|" \
           r"el[eé]trodo|capacidade|pronto|camada|estado|entradas|ajudantes|configura[cç][aã]o|" \
           r"obrigat[oó]rio|ferramentas|bibliotecas|montagem|nao|n[aã]o|mais|menos)\b"


@pytest.mark.parametrize("f", FIRMWARE_FILES, ids=lambda p: p.name)
def test_firmware_is_ascii_english(f):
    text = f.read_text(encoding="utf-8")
    non_ascii = sorted({c for c in text if ord(c) > 127})
    assert not non_ascii, non_ascii
    hits = re.findall(PT_WORDS, text, flags=re.IGNORECASE)
    assert not hits, hits
