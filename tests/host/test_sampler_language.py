"""T-021: source-level check that docs/index.html has no Portuguese UI strings left.

The string list (tests/host/browser/pt_strings.json) was extracted from the old page
(tests/host/browser/fixtures/index_e4668d4.html = docs/index.html @ e4668d4).
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "docs" / "index.html"
OLD = ROOT / "tests" / "host" / "browser" / "fixtures" / "index_e4668d4.html"
STRINGS = json.loads((ROOT / "tests" / "host" / "browser" / "pt_strings.json").read_text("utf-8"))["strings"]


@pytest.mark.parametrize("text", STRINGS)
def test_string_was_in_old_page_and_is_gone(text):
    assert text in OLD.read_text("utf-8"), "list entry not from the old page: %r" % text
    assert text not in PAGE.read_text("utf-8"), "Portuguese string still in docs/index.html: %r" % text


def test_html_lang_is_english():
    assert re.search(r'<html lang="en">', PAGE.read_text("utf-8"))


def test_no_portuguese_letters():
    # These letters occur in Portuguese but in none of the English UI text.
    found = sorted(set(re.findall(r"[ãõçáàâêíóôú]", PAGE.read_text("utf-8"), flags=re.I)))
    assert found == []
