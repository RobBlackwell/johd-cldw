#!/usr/bin/env python3
"""Compare the genre balance of the Lake District corpora.

Reads the same JSONL corpora as ``print_gender_ratios.py`` and
``plot_year_distributions.py`` and prints a genre x corpus table of counts and
within-corpus shares.

Genre fields:
  * ``texts.jsonl`` files (CLDW2, universe) use ``genre``.
  * the original CLDW metadata uses ``Genre`` (its ``Type 1``/``2``/``3``
    fields carry subject matter, not form, and are ignored here).

The three corpora do not share a genre vocabulary, so everything is normalised
onto the original CLDW's list before counting -- see ``CANONICAL_GENRES`` and
``GENRE_MAP`` below. Two things to know about that mapping:

  * The CLDW's own list is *nearly* canonical already; the only folding done
    inside it is Novel/Fiction/Prose Fiction -> Prose Fiction (one text each,
    plainly the same category) and "Epistle and Journal" -> Epistle.
  * The CLDW's genres describe *form* (travelogue, guide, poetry, essay,
    journal, epistle, drama, ...), whereas the LLM-generated and exhaustive-
    search corpora freely mix form with subject matter ("Geology", "County
    History", "Antiquarian"). Those subject labels are mapped to the closest
    CLDW *form*, which for descriptive/documentary regional prose is Survey.
    Survey therefore absorbs a large and heterogeneous group -- that spread is
    itself a result, so the raw labels behind each canonical genre are printed
    underneath the table.

Anything with no CLDW counterpart at all (life-writing, sermons) lands in
"Other". Unrecognised labels also land there, and are reported loudly so the
mapping can be extended rather than silently mis-counting.

The same table is also emitted as a self-contained LaTeX ``table`` with a
\\caption and \\label, ready to paste (or \\input) into the paper and
cross-reference with \\ref{<label>}. It needs the ``booktabs`` package.

Run from src/:  python3 print_genre_distributions.py [--latex-output FILE]
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

# (label, path, genre field). Paths are relative to src/.
DATASETS = [
    ("Original CLDW", "../data/interim/ld80-metadata/ld80-metadata.jsonl", "Genre"),
    ("CLDW2", "../data/raw/cldw2/claude-code/texts.jsonl", "genre"),
    ("Universe", "../data/raw/cldw-universe/texts.jsonl", "genre"),
]

# The original CLDW's genre list, in its own frequency order, with the three
# fiction labels folded together. "Other" is not a CLDW genre -- it is the
# escape hatch for labels the gold corpus has no slot for.
CANONICAL_GENRES = [
    "Travelogue",
    "Guide",
    "Poetry",
    "Essay",
    "Journal",
    "Epistle",
    "Survey",
    "Prose Fiction",
    "Miscellany",
    "Painting",
    "Drama",
]
OTHER = "Other"

# Raw label (lowercased) -> canonical CLDW genre. Compound labels ("Travel/Art",
# "Essays/Tales") are also resolved by their first component, so only the ones
# whose head word is misleading need listing explicitly.
GENRE_MAP = {
    # --- the CLDW's own vocabulary ---------------------------------------
    "travelogue": "Travelogue",
    "guide": "Guide",
    "poetry": "Poetry",
    "essay": "Essay",
    "journal": "Journal",
    "epistle": "Epistle",
    "epistle and journal": "Epistle",  # Coleridge's Circumcision of the Lakes
    "survey": "Survey",
    "prose fiction": "Prose Fiction",
    "novel": "Prose Fiction",
    "fiction": "Prose Fiction",
    "miscellany": "Miscellany",
    "painting": "Painting",
    "drama": "Drama",

    # --- travel narrative -------------------------------------------------
    "travel": "Travelogue",
    "travel writing": "Travelogue",
    "travel narrative": "Travelogue",
    "travel/topography": "Travelogue",
    "travel/art": "Travelogue",
    "travel/aesthetics": "Travelogue",
    "tour": "Travelogue",
    "walking": "Travelogue",
    "walking literature": "Travelogue",

    # --- practical guides -------------------------------------------------
    "guidebook": "Guide",
    "guidebook/geology": "Guide",
    # Climbing books ("Rock-Climbing in the English Lake District", "A
    # Note-Book for Novices", "British Mountain Climbs") are route guides in
    # all but name. The CLDW files its one climbing book under Essay, but that
    # looks idiosyncratic against these titles.
    "mountaineering": "Guide",
    "rock climbing": "Guide",

    # --- verse ------------------------------------------------------------
    "poetry anthology": "Poetry",
    "dialect poetry": "Poetry",
    "poetry/travel journal": "Poetry",
    "verse": "Poetry",

    # --- discursive prose -------------------------------------------------
    "essays": "Essay",
    "topographical essays": "Essay",
    "essays/tales": "Essay",
    "literary topography": "Essay",   # cf. CLDW's "Wanderings in Wordsworthshire"
    "literary history": "Essay",
    "literary criticism": "Essay",
    "sport": "Essay",                 # angling/hunting reminiscences and colloquies
    "conservation": "Essay",          # railway/reservoir protests and appeals
    "pamphlet": "Essay",

    # --- diaries ----------------------------------------------------------
    "diary": "Journal",
    "travel diary": "Journal",
    "notebooks": "Journal",

    # --- letters ----------------------------------------------------------
    "letters": "Epistle",
    "correspondence": "Epistle",

    # --- descriptive / documentary regional prose -------------------------
    # The CLDW's Survey is James Clarke's "A Survey of the Lakes"; everything
    # here is the same kind of systematic account of a place, its history, its
    # records or its natural features.
    "chorography": "Survey",
    "topography": "Survey",
    "topographical": "Survey",
    "county history": "Survey",
    "local history": "Survey",
    "family history": "Survey",
    "religious history": "Survey",
    "medieval history": "Survey",
    "industrial history": "Survey",
    "natural history": "Survey",
    "antiquarian": "Survey",
    "archaeology": "Survey",
    "records": "Survey",
    "place-names": "Survey",
    "geology": "Survey",
    "agriculture": "Survey",
    "meteorology": "Survey",
    "ecology": "Survey",
    "bibliography": "Survey",
    "statistics": "Survey",

    # --- fiction ----------------------------------------------------------
    "short stories": "Prose Fiction",
    "tales": "Prose Fiction",
    "children's fiction": "Prose Fiction",
    "children's literature": "Prose Fiction",

    # --- collections ------------------------------------------------------
    # The CLDW's Miscellany is Dickinson's "Cumbriana", itself a dialect-and-
    # folklore gathering, which makes it the natural home for these.
    "folklore": "Miscellany",
    "dialect": "Miscellany",
    "dialect literature": "Miscellany",
    "anthology": "Miscellany",
    "periodical": "Miscellany",

    # --- plates and views -------------------------------------------------
    "views": "Painting",
    "art": "Painting",

    # --- staged -----------------------------------------------------------
    "dialogue": "Drama",

    # --- no CLDW counterpart ---------------------------------------------
    "biography": OTHER,
    "autobiography": OTHER,
    "memoir": OTHER,
    "sermon": OTHER,
}

DEFAULT_CAPTION = (
    "Genre balance of each corpus, counted per text and normalised onto the "
    "original CLDW's genre vocabulary. Percentages are within corpus; "
    "``Other'' represents texts whose genre has no direct CLDW counterpart."
)
DEFAULT_LABEL = "tab:genre-balance"

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


def normalise_genre(value):
    """Map a recorded genre to a canonical CLDW genre.

    Returns ``(canonical, raw)``; ``canonical`` is ``OTHER`` for anything the
    mapping does not know about, and ``raw`` is the cleaned-up original label
    so callers can report what went where.
    """
    raw = "" if value is None else str(value).strip()
    if not raw:
        return OTHER, "(none)"
    key = re.sub(r"\s+", " ", raw.lower())
    if key in GENRE_MAP:
        return GENRE_MAP[key], raw
    # "Travel/Art", "Essays and Tales", "Poetry (dialect)": try the head term.
    head = re.split(r"[/;,(]| and | & ", key)[0].strip()
    if head and head in GENRE_MAP:
        return GENRE_MAP[head], raw
    return OTHER, raw


def load_genres(path, field):
    """Return (counts by canonical genre, {canonical: Counter(raw labels)})."""
    counts = Counter()
    detail = defaultdict(Counter)
    with open(path, encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            value = record.get(field)
            if value is None:
                # Tolerate a BOM-prefixed or differently-cased key.
                for key in record:
                    if key.lstrip("﻿").lower() == field.lower():
                        value = record[key]
                        break
            canonical, raw = normalise_genre(value)
            counts[canonical] += 1
            detail[canonical][raw] += 1
    return counts, detail


def unmapped_labels(detail):
    """Raw labels that fell into Other only because nothing matched them."""
    known = {k for k, v in GENRE_MAP.items() if v == OTHER}
    return {
        raw: n
        for raw, n in detail.get(OTHER, {}).items()
        if re.sub(r"\s+", " ", raw.lower()) not in known
    }


def ordered_genres(all_counts):
    """Canonical genres in CLDW order, dropping any nobody used, Other last."""
    used = [g for g in CANONICAL_GENRES if any(c[g] for c in all_counts)]
    if any(c[OTHER] for c in all_counts):
        used.append(OTHER)
    return used


def build_table(labels, genres, all_counts, totals, caption, label):
    """Render the genre x corpus table as self-contained LaTeX (needs booktabs)."""
    columns = "l" + "rr" * len(labels)
    header_top = ["" ] + [rf"\multicolumn{{2}}{{c}}{{\textbf{{{latex_label(name)}}}}}"
                          for name in labels]
    cmids = " ".join(
        rf"\cmidrule(lr){{{2 + 2 * i}-{3 + 2 * i}}}" for i in range(len(labels))
    )
    header_bottom = [r"\textbf{Genre}"] + [r"n & \%"] * len(labels)

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{@{{}}{columns}@{{}}}}",
        r"\toprule",
        " & ".join(header_top) + r" \\",
        cmids,
        " & ".join(header_bottom) + r" \\",
        r"\midrule",
    ]
    for genre in genres:
        cells = [escape(genre)]
        for counts, total in zip(all_counts, totals):
            n = counts[genre]
            cells.append(str(n))
            cells.append(f"{100.0 * n / total:.1f}" if total else "--")
        lines.append(" & ".join(cells) + r" \\")
    lines.append(r"\midrule")
    total_cells = [r"\textbf{Total}"]
    for total in totals:
        total_cells += [rf"\textbf{{{total}}}", r"\textbf{100.0}"]
    lines.append(" & ".join(total_cells) + r" \\")
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


def print_table(labels, genres, all_counts, totals):
    width = max(len(g) for g in genres + ["Total"]) + 2
    header = f"{'genre':<{width}}" + "".join(f"{name:>22}" for name in labels)
    subhead = " " * width + "".join(f"{'n':>10}{'%':>12}" for _ in labels)
    print(header)
    print(subhead)
    print("-" * len(header))
    for genre in genres:
        row = f"{genre:<{width}}"
        for counts, total in zip(all_counts, totals):
            n = counts[genre]
            pct = 100.0 * n / total if total else 0.0
            row += f"{n:>10}{pct:>11.1f}%"
        print(row)
    print("-" * len(header))
    row = f"{'Total':<{width}}"
    for total in totals:
        row += f"{total:>10}{100.0:>11.1f}%"
    print(row)


def print_mapping(labels, details, genres):
    """Show which raw labels fed each canonical genre, per corpus."""
    print()
    print("Raw genre labels behind each canonical genre:")
    for genre in genres:
        contributors = []
        for name, detail in zip(labels, details):
            raws = detail.get(genre)
            if not raws:
                continue
            items = ", ".join(
                f"{raw} ({n})" for raw, n in sorted(raws.items(), key=lambda kv: (-kv[1], kv[0]))
            )
            contributors.append(f"    {name}: {items}")
        if contributors:
            print(f"  {genre}")
            print("\n".join(contributors))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--original-genre-field",
        default="Genre",
        help="genre field to read from the CLDW metadata (default: Genre)",
    )
    parser.add_argument(
        "--latex-output",
        default=None,
        help="also write the LaTeX table to this file",
    )
    parser.add_argument(
        "--caption", default=DEFAULT_CAPTION, help="LaTeX table caption"
    )
    parser.add_argument(
        "--label",
        default=DEFAULT_LABEL,
        help=f"LaTeX label for cross-referencing (default: {DEFAULT_LABEL})",
    )
    parser.add_argument(
        "--no-mapping",
        action="store_true",
        help="suppress the raw-label breakdown printed under the table",
    )
    args = parser.parse_args(argv)

    labels, all_counts, details, totals = [], [], [], []
    for label, path, field in DATASETS:
        if field != "genre":
            field = args.original_genre_field
        if not os.path.exists(path):
            sys.exit(f"missing input: {path}")
        counts, detail = load_genres(path, field)
        if not counts:
            sys.exit(f"no records in {path}")
        labels.append(label)
        all_counts.append(counts)
        details.append(detail)
        totals.append(sum(counts.values()))

    genres = ordered_genres(all_counts)
    print_table(labels, genres, all_counts, totals)
    print()
    print("Genres are normalised onto the original CLDW's vocabulary; percentages")
    print("are within corpus. 'Other' holds genres the CLDW has no slot for.")

    if not args.no_mapping:
        print_mapping(labels, details, genres)

    stray = [(label, unmapped_labels(detail)) for label, detail in zip(labels, details)]
    stray = [(label, extras) for label, extras in stray if extras]
    if stray:
        print()
        print("WARNING: unrecognised genre labels counted as 'Other'"
              " -- add them to GENRE_MAP:")
        for label, extras in stray:
            detail = ", ".join(f"{raw!r}: {n}" for raw, n in sorted(extras.items()))
            print(f"  {label}: {detail}")

    latex = build_table(labels, genres, all_counts, totals, args.caption, args.label)
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
