#!/usr/bin/env python3
"""Tabulate the genre balance of every corpus the experiment runs produced.

One column pair per corpus: LD80 itself -- the original Corpus of Lake District
Writing the runs were asked to reconstruct or extend, read from the interim
metadata JSONL -- then one per claude-code run, read from
``data/raw/<variant>/<run>/texts.jsonl``. Counting is per *text*, not per word.

The runs label genre in free text, so they do not share a vocabulary with each
other or with LD80: 186 distinct labels across the five runs, against LD80's 14.
They are therefore normalised onto LD80's own genre vocabulary before counting,
by GENRE_RULES below -- so the table answers "how does each corpus sit against
the genre scheme the CLDW actually uses", which is the comparison the paper
wants, and not "how many distinct words did each run type into the genre field".
Texts whose label has no counterpart in that vocabulary -- biography, memoir,
dialect writing, folklore, genealogy, none of which LD80's scheme names -- fall
to ``Other``, and that row is a finding in its own right: it measures how far
each corpus reaches outside the original's idea of what a Lake District text is.

Writes a booktabs LaTeX table (``\\toprule``/``\\midrule``/``\\bottomrule``, so
the preamble needs ``booktabs``) and prints the same counts as plain text.

Run from anywhere:
    ./tabulate_genre_balance.py [output.tex] [--audit] [--runs LABEL,...]
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

# (column label, variant, run directory) -- the same five runs, under the same
# labels, as EXPERIMENTS in 01-reb-analyse.py, in the panel order
# plot_year_distributions.py uses: within each corpus family the unbalanced run
# comes first, so each column is read against the plainer run to its left and
# the effect of the balancing instruction falls out as the difference.
EXPERIMENTS = [
    ("cldw2-unbalanced", "cldw2-unbalanced", "claude-code"),
    ("cldw2-balanced", "cldw2-balanced", "claude-code"),
    ("universe-unbalanced", "universe-unbalanced", "claude-code"),
    ("universe-balanced", "universe-balanced", "claude-code"),
    ("universe-balanced-run2", "universe-balanced", "claude-code-run2"),
]

LD80_LABEL = "Original CLDW"
LD80_PATH = ("data", "interim", "ld80-metadata", "ld80-metadata.jsonl")
LD80_GENRE_FIELD = "Genre"

# (corpus family, variant within it) per column, for the LaTeX header only --
# the full labels above are what the stdout table, --runs and the other scripts
# use. The header is two tiers because the columns are: adjacent columns sharing
# a family are spanned by one heading, so the balanced/unbalanced pair a reader
# is meant to compare sits visibly under one rule. It also keeps the table
# narrow enough to set -- spelling each column out in full ("\emph{Universe}
# unbal.") overruns a normal text block by well over an inch.
COLUMN_HEADERS = {
    LD80_LABEL: ("Original", "CLDW"),
    "cldw2-unbalanced": (r"\emph{CLDW2}", "unbal."),
    "cldw2-balanced": (r"\emph{CLDW2}", "bal."),
    "universe-unbalanced": (r"\emph{Universe}", "unbal."),
    "universe-balanced": (r"\emph{Universe}", "bal."),
    "universe-balanced-run2": (r"\emph{Universe}", "bal. 2"),
}

GENRE_FIELD = "genre"  # the runs' texts.jsonl
TEXTS_NAME = "texts.jsonl"

DEFAULT_OUTPUT = "reports/tables/genre_balance.tex"  # relative to --root
TABLE_LABEL = "tab:genre-balance"

OTHER = "Other"

# LD80's Genre column, canonicalised. Its 80 rows carry 14 distinct labels, but
# three of them are the same genre under three names (``Fiction``, ``Novel`` and
# ``Prose Fiction``) and one is a compound (``Epistle and Journal``), which
# leaves the eleven genres below. This is the vocabulary everything is counted
# in; ``assert_covers_ld80`` checks at run time that every LD80 row still lands
# in it, so a change to the rules that stopped honouring the corpus's own scheme
# fails loudly rather than quietly reshaping the table.
CLDW_GENRES = (
    "Travelogue", "Guide", "Poetry", "Essay", "Journal", "Epistle",
    "Survey", "Prose Fiction", "Miscellany", "Painting", "Drama",
)

# --- Normalisation -----------------------------------------------------------
# A label is split into segments on the separators below and each segment tried
# in turn, so a compound label is decided by the first segment that names a genre
# the vocabulary has: "Guide, geology" is a Guide, "Letters and memoir" and
# "Biography and letters" are both Epistle -- memoir and biography name nothing
# in the vocabulary, so letters decides both -- and "Diary, travel" is a Journal.
# LD80's own "Epistle and Journal" resolves the same way, to Epistle.
SEPARATORS = re.compile(r"[,;/]|\band\b|&")

# Within a segment, the first rule here that matches wins, so the order is the
# precedence: *form* before *subject*. A "chorographical poem" is Poetry, not a
# chorography; an "antiquarian letter" is an Epistle, not an antiquarian survey;
# a "travel journal" is a Travelogue, because travel is what makes it one of the
# 27 texts LD80 calls Travelogue rather than one of the 6 it calls Journal.
# Survey sits last of the named genres because it is the widest: LD80 uses it
# for systematic descriptive accounts of a district, which is where topography,
# chorography, county and local history, natural history, geology, archaeology,
# antiquarian writing and agricultural or industrial survey all belong once
# their form has had its chance to claim them first.
GENRE_RULES = [
    ("Poetry", ("poetry", "poem", "poetical", "verse", "song", "ballad",
                "elegy", "sonnet", "lyric")),
    ("Drama", ("drama", "masque", "tragedy", "comedy", "play")),
    ("Painting", ("painting", "view", "illustrated", "engraving", "aquatint",
                  "watercolour", "drawing", "sketchbook")),
    ("Guide", ("guide", "handbook", "companion", "itinerary", "road book")),
    ("Prose Fiction", ("fiction", "novel", "tale", "romance", "short stor")),
    ("Travelogue", ("travelogue", "travel", "tour", "journey", "excursion",
                    "ramble", "mountaineering", "ascent", "voyage", "walking")),
    ("Epistle", ("epistle", "letter", "correspondence")),
    ("Journal", ("journal", "diary", "diaries", "notebook")),
    ("Essay", ("essay", "criticism", "polemic", "tract", "pamphlet", "sermon",
               "discourse", "lecture", "address", "dialogue", "paper",
               "sketch")),
    ("Miscellany", ("miscellan", "anthology", "periodical", "chapbook",
                    "transactions", "magazine", "almanac", "collection")),
    ("Survey", ("survey", "topograph", "chorograph", "gazetteer", "history",
                "antiquarian", "antiquities", "archaeolog", "geolog",
                "agricultur", "mining", "mineral", "meteorolog",
                "palaeontolog", "geograph", "statistic", "industrial",
                "science", "scientific", "account", "description",
                "descriptive", "report", "census")),
]


def normalise_genre(raw):
    """(CLDW genre, the keyword that decided it) for one free-text label.

    Returns ``(OTHER, None)`` for a blank label, and for one whose every segment
    names something LD80's vocabulary has no word for.
    """
    if not raw:
        return OTHER, None
    text = raw.strip().lower()
    if not text or text in {"no data", "n/a", "unknown", "-"}:
        return OTHER, None
    segments = [s.strip() for s in SEPARATORS.split(text) if s.strip()]
    for segment in segments or [text]:
        for genre, keywords in GENRE_RULES:
            for keyword in keywords:
                if keyword in segment:
                    return genre, keyword
    return OTHER, None


# --- Loading -----------------------------------------------------------------
def read_jsonl(path):
    """Records from a JSONL file, skipping blank and unparseable lines."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                print(f"note: {path}: skipped an unparseable line", file=sys.stderr)


def lookup(record, field):
    """``record[field]``, case-insensitively -- LD80's keys are capitalised."""
    if field in record:
        return record[field]
    wanted = field.lower()
    for key, value in record.items():
        if key.strip().lstrip("﻿").lower() == wanted:
            return value
    return None


def count_corpus(path, field):
    """(counts per CLDW genre, raw label -> (genre, keyword, n)) for one corpus."""
    counts = Counter()
    raw_seen = {}
    for record in read_jsonl(path):
        raw = lookup(record, field)
        raw = "" if raw is None else str(raw)
        genre, keyword = normalise_genre(raw)
        counts[genre] += 1
        label = raw.strip() or "(blank)"
        if label in raw_seen:
            raw_seen[label] = (genre, keyword, raw_seen[label][2] + 1)
        else:
            raw_seen[label] = (genre, keyword, 1)
    return counts, raw_seen


def resolve_sources(root, wanted=None):
    """(label, path, genre field) per column, left to right.

    LD80 leads, as the corpus the runs are measured against; ``wanted`` filters
    the run columns after it, keeping EXPERIMENTS order whatever order it names.
    """
    sources = [(LD80_LABEL, os.path.join(root, *LD80_PATH), LD80_GENRE_FIELD)]
    for label, variant, run in EXPERIMENTS:
        if wanted is not None and label not in wanted:
            continue
        path = os.path.join(root, "data", "raw", variant, run, TEXTS_NAME)
        sources.append((label, path, GENRE_FIELD))
    return sources


def assert_covers_ld80(raw_seen):
    """Every LD80 label must normalise into CLDW_GENRES, never to Other.

    The vocabulary is LD80's own, so a label of LD80's falling to ``Other``
    means the rules no longer reproduce the scheme they claim to be counting in.
    """
    stray = sorted(label for label, (genre, _, _) in raw_seen.items()
                   if genre == OTHER)
    if stray:
        sys.exit(f"{LD80_LABEL}: {len(stray)} genre label(s) fall outside "
                 f"CLDW_GENRES: {', '.join(stray)}")


# --- Output ------------------------------------------------------------------
def order_rows(columns):
    """Genre rows, commonest in LD80 first, then alphabetically; Other last.

    Ordering on LD80 rather than on a total keeps the rows in one fixed reading
    order -- the original corpus's own profile, top-heavy -- so a run's column is
    read as a departure from the shape of the column beside it.
    """
    reference = columns[0][1]
    present = [g for g in CLDW_GENRES if any(counts[g] for _, counts in columns)]
    ordered = sorted(present, key=lambda g: (-reference[g], g))
    if any(counts[OTHER] for _, counts in columns):
        ordered.append(OTHER)
    return ordered


def percent(n, total):
    return 100.0 * n / total if total else 0.0


def print_table(columns, rows, out=sys.stdout):
    label_w = max([len(r) for r in rows] + [len("Total")]) + 2
    widths = [max(len(label), 11) for label, _ in columns]
    header = " " * label_w + "".join(label.rjust(w + 2)
                                     for (label, _), w in zip(columns, widths))
    print(header, file=out)
    print("-" * len(header), file=out)
    totals = [sum(counts.values()) for _, counts in columns]
    for genre in rows:
        cells = "".join(f"{counts[genre]:>4} {percent(counts[genre], total):>5.1f}%".rjust(w + 2)
                        for (_, counts), total, w in zip(columns, totals, widths))
        print(f"{genre:<{label_w}}{cells}", file=out)
    print("-" * len(header), file=out)
    cells = "".join(f"{total:>4} {100.0:>5.1f}%".rjust(w + 2)
                    for total, w in zip(totals, widths))
    print(f"{'Total':<{label_w}}{cells}", file=out)


def print_audit(columns_raw, out=sys.stdout):
    """Every distinct raw label, per corpus, and what it normalised to.

    This is the table's audit trail: the mapping is a judgement call made by
    GENRE_RULES, and this is how to check it -- and what to re-read after
    editing them.
    """
    writer = csv.writer(out)
    writer.writerow(["corpus", "raw_genre", "n", "cldw_genre", "matched_keyword"])
    for label, raw_seen in columns_raw:
        for raw, (genre, keyword, n) in sorted(
                raw_seen.items(), key=lambda kv: (kv[1][0], -kv[1][2], kv[0])):
            writer.writerow([label, raw, n, genre, keyword or ""])


def latex_table(columns, rows):
    """The booktabs table, as a list of lines."""
    n = len(columns)
    spec = "@{}l" + "rr" * n + "@{}"
    heads = [COLUMN_HEADERS.get(label, (label, "")) for label, _ in columns]

    # Top tier: one spanning heading per run of adjacent columns sharing a
    # family, with a cmidrule under each. Second tier: the variant within it.
    families, first = [], 0
    for i in range(1, n + 1):
        if i == n or heads[i][0] != heads[first][0]:
            families.append((heads[first][0], first, i - first))
            first = i
    family_row = " & ".join(
        r"\multicolumn{%d}{c}{\textbf{%s}}" % (2 * width, name)
        for name, _, width in families)
    cmids = " ".join(r"\cmidrule(lr){%d-%d}" % (2 + 2 * start, 1 + 2 * (start + width))
                     for _, start, width in families)
    variant_row = " & ".join(r"\multicolumn{2}{c}{%s}" % variant
                             for _, variant in heads)
    totals = [sum(counts.values()) for _, counts in columns]

    lines = [
        r"% Generated by src/tabulate_genre_balance.py -- do not edit by hand.",
        r"% Needs \usepackage{booktabs} in the preamble.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\small",
        r"\setlength{\tabcolsep}{4pt}",
        r"\caption{Genre balance of each corpus, counted per text and "
        r"normalised onto the original CLDW's genre vocabulary. Percentages "
        r"are within corpus; ``Other'' represents texts whose genre has no "
        r"direct CLDW counterpart.}",
        r"\label{%s}" % TABLE_LABEL,
        r"\begin{tabular}{%s}" % spec,
        r"\toprule",
        r" & " + family_row + r" \\",
        cmids,
        r" & " + variant_row + r" \\",
        r"\textbf{Genre} & " + " & ".join([r"n & \%"] * n) + r" \\",
        r"\midrule",
    ]
    for genre in rows:
        cells = " & ".join(
            f"{counts[genre]} & {percent(counts[genre], total):.1f}"
            for (_, counts), total in zip(columns, totals))
        lines.append(f"{genre} & {cells} " + r"\\")
    lines += [
        r"\midrule",
        r"\textbf{Total} & " + " & ".join(
            r"\textbf{%d} & \textbf{100.0}" % total for total in totals) + r" \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return lines


def main(argv=None):
    default_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output", nargs="?", default=None,
                        help=f"output .tex (default: <root>/{DEFAULT_OUTPUT})")
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repo root holding data/raw (default: %(default)s)")
    parser.add_argument("--runs", default=None,
                        help="comma-separated run labels to keep as columns "
                             "(default: all of them). The original CLDW column "
                             "is always first. Twelve numeric columns is a wide "
                             "table; use this to narrow it.")
    parser.add_argument("--audit", action="store_true",
                        help="write the raw-label -> CLDW-genre mapping as CSV "
                             "to stdout instead of writing the table")
    args = parser.parse_args(argv)

    wanted = None
    if args.runs:
        wanted = [label.strip() for label in args.runs.split(",") if label.strip()]
        known = {label for label, _, _ in EXPERIMENTS}
        unknown = [label for label in wanted if label not in known]
        if unknown:
            sys.exit(f"unknown run label(s): {', '.join(unknown)}\n"
                     f"known: {', '.join(sorted(known))}")

    columns, columns_raw = [], []
    for label, path, field in resolve_sources(args.root, wanted):
        if not os.path.exists(path):
            print(f"skipping {label}: no {os.path.basename(path)} under "
                  f"{os.path.dirname(path)}", file=sys.stderr)
            continue
        counts, raw_seen = count_corpus(path, field)
        if not sum(counts.values()):
            print(f"skipping {label}: no records in {path}", file=sys.stderr)
            continue
        if label == LD80_LABEL:
            assert_covers_ld80(raw_seen)
        columns.append((label, counts))
        columns_raw.append((label, raw_seen))

    if not columns:
        sys.exit("no corpora found; pass --root")
    if columns[0][0] != LD80_LABEL:
        sys.exit(f"no {LD80_LABEL} column: rows are ordered on it, so the "
                 f"table cannot be built without it")

    if args.audit:
        print_audit(columns_raw)
        return

    rows = order_rows(columns)
    print_table(columns, rows)
    distinct = sum(len(raw) for _, raw in columns_raw[1:])
    print(f"\n{distinct} distinct free-text genre labels across "
          f"{len(columns) - 1} run(s), normalised onto "
          f"{len(CLDW_GENRES)} CLDW genres + {OTHER}; "
          f"re-run with --audit to see the mapping")

    output = args.output or os.path.join(args.root, DEFAULT_OUTPUT)
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    with open(output, "w", encoding="utf-8") as fh:
        fh.write("\n".join(latex_table(columns, rows)) + "\n")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
