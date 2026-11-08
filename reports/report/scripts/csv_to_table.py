#!/usr/bin/env python3
"""Turn requirements/requirements.csv into a LaTeX longtable for the report.

Usage (from anywhere):
    python3 -I reports/report/scripts/csv_to_table.py [CSV] [OUT]

Defaults: CSV = <repo>/requirements/requirements.csv,
          OUT = <repo>/reports/report/generated/requirements_table.tex

Expected columns: id, title, statement, verification, status, evidence.
The output is generated; do not edit it by hand. The script fails (exit 1)
on missing columns, empty ids, duplicate ids, unknown status words, or
characters it cannot typeset, instead of writing a wrong table.
"""
import csv
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DEFAULT_CSV = REPO / "requirements" / "requirements.csv"
DEFAULT_OUT = REPO / "reports" / "report" / "generated" / "requirements_table.tex"

COLUMNS = ["id", "title", "statement", "verification", "status", "evidence"]
STATUS_WORDS = ["PASS", "PARTIAL", "FAIL", "BLOCKED", "NOT RUN"]

# LaTeX special characters (plain text). Backslash first.
SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "<": r"\textless{}",
    ">": r"\textgreater{}",
    "|": r"\textbar{}",
}
# Non-ASCII characters that pdflatex (T1 + utf8) does not set up by default
# or that read better as math.
UNICODE = {
    "→": r"$\rightarrow$",
    "←": r"$\leftarrow$",
    "↔": r"$\leftrightarrow$",
    "≤": r"$\leq$",
    "≥": r"$\geq$",
    "≈": r"$\approx$",
    "≠": r"$\neq$",
    "±": r"$\pm$",
    "×": r"$\times$",
    "·": r"$\cdot$",
    "Ω": r"\textohm{}",
    "µ": r"\textmu{}",
    "μ": r"\textmu{}",
    "°": r"\textdegree{}",
    "²": r"\textsuperscript{2}",
    "…": r"\ldots{}",
    "−": r"$-$",
    " ": "~",
    "§": r"\S{}",
    "τ": r"$\tau$",
}
# Characters T1 handles directly.
SAFE_NON_ASCII = set("–—‘’“”éèêáàâãçíóôõúüñÉÁÇ")


def escape_plain(text: str) -> str:
    out = []
    for ch in text:
        if ch in SPECIALS:
            out.append(SPECIALS[ch])
        elif ch in UNICODE:
            out.append(UNICODE[ch])
        elif ord(ch) < 128 or ch in SAFE_NON_ASCII:
            out.append(ch)
        else:
            raise ValueError(f"unsupported character {ch!r} (U+{ord(ch):04X})")
    return "".join(out)


def escape(text: str) -> str:
    """Escape a cell; `code` spans become \\texttt{} with breakable text."""
    text = " ".join(text.split())  # collapse newlines and runs of spaces
    parts = re.split(r"(`[^`]*`)", text)
    out = []
    for part in parts:
        if len(part) >= 2 and part.startswith("`") and part.endswith("`"):
            inner = escape_plain(part[1:-1])
            inner = (inner.replace("/", r"/\allowbreak{}").replace(r"\_", r"\_\allowbreak{}")
                     .replace(":", r":\allowbreak{}"))
            out.append(r"\texttt{" + inner + "}")
        else:
            # Plain text: allow line breaks after "/" and "_" so long paths and
            # footprint names fit the narrow evidence column.
            plain = escape_plain(part)
            plain = plain.replace("/", r"/\allowbreak{}").replace(r"\_", r"\_\allowbreak{}")
            out.append(plain)
    return "".join(out)


# A longtable row cannot break across pages. Evidence longer than FIRST_CHUNK
# characters is split at sentence ends: the first part stays in the Evidence
# column, the rest goes into full-width continuation rows of at most CONT_CHUNK
# characters each, so the table can break between them.
FIRST_CHUNK = 900
CONT_CHUNK = 1800
CONT_WIDTH = r"\dimexpr0.84\linewidth+6\tabcolsep\relax"


def split_sentences(text: str):
    text = " ".join(text.split())
    parts = re.split(r"(?<=[.;])\s+(?=[A-Z(])", text)
    return [p for p in parts if p]


def chunk_evidence(text: str):
    """Return [first, cont1, cont2, ...] raw-text chunks (unescaped)."""
    sentences = split_sentences(text)
    if len(" ".join(sentences)) <= FIRST_CHUNK:
        return [" ".join(sentences)]
    chunks, cur, limit = [], "", FIRST_CHUNK
    for sent in sentences:
        if cur and len(cur) + 1 + len(sent) > limit:
            chunks.append(cur)
            cur, limit = sent, CONT_CHUNK
        else:
            cur = f"{cur} {sent}" if cur else sent
    if cur:
        chunks.append(cur)
    return chunks


def main(argv):
    csv_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_CSV
    out_path = Path(argv[2]) if len(argv) > 2 else DEFAULT_OUT
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit(f"ERROR: missing columns {missing} in {csv_path}")
        rows = list(reader)

    errors = []
    ids = Counter(r["id"].strip() for r in rows)
    errors += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
    for n, r in enumerate(rows, start=2):
        if not r["id"].strip():
            errors.append(f"line {n}: empty id")
        if r["status"].strip() not in STATUS_WORDS:
            errors.append(f"line {n}: unknown status {r['status']!r}")
    body = []
    for n, r in enumerate(rows, start=2):
        try:
            cells = {c: escape(r[c] or "") for c in COLUMNS if c != "evidence"}
            ev = [escape(c) for c in chunk_evidence(r["evidence"] or "")]
        except ValueError as e:
            errors.append(f"line {n}: {e}")
            continue
        first = ev[0] + (r" \textit{(continued below)}" if len(ev) > 1 else "")
        body.append(
            f"{cells['id']} & \\textbf{{{cells['title']}}}\\newline {cells['statement']} & "
            f"{cells['verification']} & {cells['status']} & {first} \\\\"
        )
        for k, part in enumerate(ev[1:], start=1):
            body.append(
                f"& \\multicolumn{{4}}{{>{{\\raggedright\\arraybackslash}}p{{{CONT_WIDTH}}}}}"
                f"{{\\textit{{{cells['id']} evidence, continued ({k}/{len(ev) - 1}):}} {part}}} \\\\"
            )
    if errors:
        sys.exit("ERROR:\n  " + "\n  ".join(errors))

    counts = Counter(r["status"].strip() for r in rows)
    summary = ", ".join(f"{s} {counts[s]}" for s in STATUS_WORDS if counts[s])
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    try:
        src = csv_path.resolve().relative_to(REPO)
    except ValueError:
        src = csv_path
    lines = [
        "% GENERATED by reports/report/scripts/csv_to_table.py. Do not edit.",
        f"% Source: {src} (sha256 {digest})",
        f"% Rows: {len(rows)}. Status counts: {summary}.",
        r"{\footnotesize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{longtable}{@{}>{\raggedright\arraybackslash}p{0.08\linewidth}>{\raggedright\arraybackslash}p{0.37\linewidth}>{\raggedright\arraybackslash}p{0.11\linewidth}>{\raggedright\arraybackslash}p{0.09\linewidth}>{\raggedright\arraybackslash}p{0.27\linewidth}@{}}",
        r"\caption{Requirements and verification status (generated from "
        + escape(str(src)) + r").}\label{tab:requirements}\\",
        r"\toprule",
        r"ID & Requirement & Verification & Status & Evidence \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"ID & Requirement & Verification & Status & Evidence \\",
        r"\midrule",
        r"\endhead",
        r"\bottomrule",
        r"\endlastfoot",
        *body,
        r"\end{longtable}",
        r"}",
        f"\\noindent Status counts ({len(rows)} requirements): {escape(summary)}.",
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path} with {len(rows)} rows; status counts: {summary}")


if __name__ == "__main__":
    main(sys.argv)
