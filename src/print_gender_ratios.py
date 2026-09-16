#!/usr/bin/env python3
"""Compare the author gender balance of the Lake District corpora.

Reads the same JSONL corpora as ``plot_year_distributions.py`` and prints, for
each, the male/female author counts and their shares. No figure is produced.

Gender fields:
  * ``texts.jsonl`` files (CLDW2, universe) use ``gender``.
  * the original CLDW metadata uses ``Gender``.

Values are single letters (``M``/``F``, plus ``U`` for unknown in the universe
corpus); longer spellings ("male", "female") and stray whitespace are tolerated.
Unknown/unattributed authors get their own column, and anything else that is
neither male nor female falls into "other"; neither counts towards the
percentages.

Note the counts are *per text*, not per distinct author, and a text's gender is
whatever the corpus recorded for it -- co-authored texts carry a single value.

The same table is also emitted as a self-contained LaTeX ``table`` with a
\\caption and \\label, ready to paste (or \\input) into the paper and
cross-reference with \\ref{<label>}. It needs the ``booktabs`` package.

Run from src/:  python3 print_gender_ratios.py [--latex-output FILE]
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

# (label, path, gender field). Paths are relative to src/.
DATASETS = [
    ("Original CLDW", "../data/interim/ld80-metadata/ld80-metadata.jsonl", "Gender"),
    ("CLDW2", "../data/raw/cldw2/claude-code/texts.jsonl", "gender"),
    ("Universe", "../data/raw/cldw-universe/texts.jsonl", "gender"),
]

MALE = {"m", "male", "man"}
FEMALE = {"f", "female", "woman", "w"}
UNKNOWN = {"u", "unknown", "unattributed", "anonymous", "anon", "n/a", "no data"}

DEFAULT_CAPTION = (
    "Author gender balance of each corpus, counted per text. "
    "Percentages are over texts with an attributed male or female author; "
    "unknown are excluded."
)
# Used in place of the default when some corpus actually fills the "other"
# column, so the caption never claims to exclude a column that is not there.
CAPTION_WITH_OTHER = DEFAULT_CAPTION.replace(
    "unknown are excluded.", "unknown and other are excluded."
)
DEFAULT_LABEL = "tab:gender-balance"

# Corpus labels the paper sets in italics; anything else is escaped verbatim.
LATEX_LABELS = {
    "CLDW2": r"\emph{CLDW2}",
    "Universe": r"\emph{Universe}",
}

LATEX_SPECIAL_CHARS = {
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
}
LATEX_SPECIAL_RE = re.compile("|".join(re.escape(c) for c in LATEX_SPECIAL_CHARS))


def escape(text):
    return LATEX_SPECIAL_RE.sub(lambda m: LATEX_SPECIAL_CHARS[m.group()], str(text))


def latex_label(name):
    """Corpus name as it should appear in the table: italicised if the paper
    italicises it, otherwise escaped like any other cell."""
    return LATEX_LABELS.get(name, escape(name))


def normalise_gender(value):
    """Map a recorded gender to 'male', 'female', 'unknown', or the raw value
    for anything else (mixed, or a spelling this doesn't know about)."""
    if value is None:
        return "unknown"
    text = str(value).strip()
    if not text:
        return "unknown"
    lowered = text.lower()
    if lowered in MALE:
        return "male"
    if lowered in FEMALE:
        return "female"
    if lowered in UNKNOWN:
        return "unknown"
    return text


def load_genders(path, field):
    """Return a Counter of normalised genders for every record in ``path``."""
    counts = Counter()
    with open(path, encoding="utf-8-sig") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            record = json.loads(raw)
            value = record.get(field)
            if value is None:
                # Tolerate a BOM-prefixed or differently-cased key.
                for key in record:
                    if key.lstrip("﻿").lower() == field.lower():
                        value = record[key]
                        break
            counts[normalise_gender(value)] += 1
    return counts


def summarise(label, counts):
    male = counts["male"]
    female = counts["female"]
    unknown = counts["unknown"]
    known = male + female
    other = sum(
        n for gender, n in counts.items() if gender not in ("male", "female", "unknown")
    )
    return {
        "label": label,
        "n": sum(counts.values()),
        "male": male,
        "female": female,
        "unknown": unknown,
        "other": other,
        "male_pct": 100.0 * male / known if known else float("nan"),
        "female_pct": 100.0 * female / known if known else float("nan"),
    }


def build_table(summaries, caption, label, show_other):
    """Render the summaries as a self-contained LaTeX table (needs booktabs).

    The "other" column is dropped unless some corpus actually uses it, so the
    common case gives the paper a table with no dead column.
    """
    # corpus + N/male/female/unknown[/other]/male %/female %
    columns = "l" + "r" * (7 if show_other else 6)
    headings = [r"\textbf{Corpus}", r"\textbf{n}", r"\textbf{Male}", r"\textbf{Female}",
                r"\textbf{Unknown}"]
    if show_other:
        headings.append(r"\textbf{Other}")
    headings += [r"\textbf{Male \%}", r"\textbf{Female \%}"]

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{@{{}}{columns}@{{}}}}",
        r"\toprule",
        " & ".join(headings) + r" \\",
        r"\midrule",
    ]
    for s in summaries:
        cells = [latex_label(s["label"]), str(s["n"]), str(s["male"]), str(s["female"]),
                 str(s["unknown"])]
        if show_other:
            cells.append(str(s["other"]))
        cells += [f"{s['male_pct']:.1f}", f"{s['female_pct']:.1f}"]
        lines.append(" & ".join(cells) + r" \\")
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--original-gender-field",
        default="Gender",
        help="gender field to read from the CLDW metadata (default: Gender)",
    )
    parser.add_argument(
        "--latex-output",
        default=None,
        help="also write the LaTeX table to this file",
    )
    parser.add_argument(
        "--caption",
        default=DEFAULT_CAPTION,
        help="LaTeX table caption",
    )
    parser.add_argument(
        "--label",
        default=DEFAULT_LABEL,
        help=f"LaTeX label for cross-referencing (default: {DEFAULT_LABEL})",
    )
    args = parser.parse_args(argv)

    summaries = []
    leftovers = []
    for label, path, field in DATASETS:
        if field != "gender":
            field = args.original_gender_field
        if not os.path.exists(path):
            sys.exit(f"missing input: {path}")
        counts = load_genders(path, field)
        if not counts:
            sys.exit(f"no records in {path}")
        summaries.append(summarise(label, counts))
        extras = {
            g: n
            for g, n in counts.items()
            if g not in ("male", "female", "unknown")
        }
        if extras:
            leftovers.append((label, extras))

    header = (
        f"{'corpus':<20}{'n':>5}{'male':>7}{'female':>8}{'unknown':>9}{'other':>7}"
        f"{'male %':>9}{'female %':>10}"
    )
    print(header)
    print("-" * len(header))
    for s in summaries:
        print(
            f"{s['label']:<20}{s['n']:>5}{s['male']:>7}{s['female']:>8}"
            f"{s['unknown']:>9}{s['other']:>7}"
            f"{s['male_pct']:>8.1f}%{s['female_pct']:>9.1f}%"
        )
    print()
    print("Percentages are over attributed male/female texts only;")
    print("unknown and other are excluded.")

    if leftovers:
        print()
        print("Values counted as 'other':")
        for label, extras in leftovers:
            detail = ", ".join(f"{g!r}: {n}" for g, n in sorted(extras.items()))
            print(f"  {label}: {detail}")

    caption = args.caption
    if leftovers and caption == DEFAULT_CAPTION:
        caption = CAPTION_WITH_OTHER
    latex = build_table(summaries, caption, args.label, show_other=bool(leftovers))
    print()
    print("LaTeX (requires \\usepackage{booktabs}):")
    print()
    print(latex)

    if args.latex_output:
        directory = os.path.dirname(os.path.abspath(args.latex_output))
        os.makedirs(directory, exist_ok=True)
        with open(args.latex_output, "w", encoding="utf-8") as fh:
            fh.write(latex + "\n")
        print()
        print(f"wrote {args.latex_output}")


if __name__ == "__main__":
    main()
