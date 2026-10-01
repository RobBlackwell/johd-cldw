#!/usr/bin/env python3
"""Compare the date distributions of the corpora the experiment runs produced.

The top panel is LD80 itself -- the original corpus of Lake District writing the
runs were asked to reconstruct -- read from the interim metadata JSONL and dated
by its own year of publication. Below it, one panel per run in ``01-reb-analyse.py``:
the four variants plus the universe-balanced repeat, read from
``data/raw/<variant>/<run>/texts.jsonl`` (one text per line, with a ``year``
field).

Renders a publication-quality PDF: one stacked dot plot per run on a shared
year axis (one dot = one text, dots stacked within 5-year bins), so clusters of
texts in time are directly countable and comparable across runs -- every dot is
the same size in every panel, so the panel heights carry the corpus sizes.
Every dot is coloured by the gender of its lead author -- blue male, orange
female, grey unknown -- so the gender mix of each corpus is readable in place,
against time, rather than only as a total. Panels are told apart by the direct
label on each one, and each carries the wall-clock time its run took and what
it cost to run, both read from ``data/raw/<variant>/<run>/trace.jsonl``.

Run from anywhere:  python3 plot_year_distributions.py [output.pdf]
"""

import argparse
import datetime
import json
import math
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

# (column label, variant, run directory) -- the same five runs, under the same
# labels, as EXPERIMENTS in 01-reb-analyse.py. universe-balanced was run twice.
# Panel order differs from that script's: within each corpus family the
# unbalanced run comes first, so each panel is read against the plainer run
# above it and the effect of the balancing switch falls out as the difference.
EXPERIMENTS = [
    ("cldw2-unbalanced", "cldw2-unbalanced", "claude-code"),
    ("cldw2-balanced", "cldw2-balanced", "claude-code"),
    ("universe-unbalanced", "universe-unbalanced", "claude-code"),
    ("universe-balanced", "universe-balanced", "claude-code"),
    ("universe-balanced-run2", "universe-balanced", "claude-code-run2"),
]

YEAR_FIELD = "year"
TRACE_NAME = "trace.jsonl"  # the run's own log, beside its texts.jsonl

# The corpus the runs are reconstructing, dated by year of *publication*, which
# is what the runs themselves report and so the only date that compares like
# with like. ``Year_Pub`` is filled for all 80 rows, so it needs no fallback;
# where it holds more than one year ("1747-1748", "1939 and 1957" -- six rows,
# part-issues and later reprints), parse_year takes the first, the year the work
# reached print. Dating LD80 by composition instead moves a handful of texts
# decades earlier -- Fiennes wrote in 1698 and was not published until 1888 --
# so use ``("Year_Comp", "Year_id")`` here to see the corpus that way.
LD80_LABEL = "Original CLDW"
LD80_PATH = ("data", "interim", "ld80-metadata", "ld80-metadata.jsonl")
LD80_YEAR_FIELDS = ("Year_Pub",)
LD80_TITLE_FIELDS = ("Title_short", "Title_full")

TITLE_FIELD = "title"
AUTHOR_FIELD = "author"  # `lookup` is case-insensitive, so LD80's "Author" hits

DEFAULT_OUTPUT = "reports/figures/run_year_distributions.pdf"  # relative to --root

# --- Palette -----------------------------------------------------------------
# Colour carries one comparison: the lead author's gender. Categorical slots 1-2
# (blue / orange) take the two recorded values -- that pair validates on every
# pairing, for normal vision and simulated CVD alike -- and "unknown" takes the
# muted neutral rather than a third hue, because it is an absence of data, not a
# third category, and should recede.
SERIES_BLUE = "#2a78d6"
SERIES_ORANGE = "#eb6834"
NEUTRAL = "#898781"
GENDER_COLOURS = {"M": SERIES_BLUE, "F": SERIES_ORANGE, "U": NEUTRAL}
GENDER_LABELS = {"M": "Male", "F": "Female", "U": "Unknown"}
GENDER_ORDER = ("M", "F", "U")  # summary-table order
STACK_ORDER = ("M", "F", "U")  # within a bin, baseline upwards
GENDER_FIELD = "gender"  # `lookup` is case-insensitive, so LD80's "Gender" hits

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

# --- Geometry (inches) -------------------------------------------------------
FIG_WIDTH = 7.0
MARGIN_LEFT = 0.55
MARGIN_RIGHT = 0.22
MARGIN_TOP = 0.22  # clears the first panel's label
MARGIN_BOTTOM = 0.50
STRIP_GAP = 0.30  # between dot-plot panels

BIN_WIDTH = 5  # years per dot-plot bin
DOT_FILL = 0.82  # dot diameter as a fraction of the bin pitch

YEAR_RE = re.compile(r"\d{4}")


def resolve_sources(root):
    """(label, path, year field, title fields, trace path) per panel, top down.

    The trace path is ``None`` for LD80: it is the corpus the runs were asked to
    reconstruct, not a run, so it has neither a time nor a cost to report.
    """
    sources = [(LD80_LABEL, os.path.join(root, *LD80_PATH), LD80_YEAR_FIELDS,
                LD80_TITLE_FIELDS, None)]
    for label, variant, run in EXPERIMENTS:
        directory = os.path.join(root, "data", "raw", variant, run)
        sources.append((label, os.path.join(directory, "texts.jsonl"), YEAR_FIELD,
                        (TITLE_FIELD,), os.path.join(directory, TRACE_NAME)))
    return sources


# --- Run time and cost -------------------------------------------------------
def run_totals(path):
    """(wall-clock seconds, dollars) the run took, from its trace.

    Either may be ``None`` if the trace does not record it. The trace's closing
    ``result`` record carries ``duration_ms`` and ``total_cost_usd`` for the
    whole session -- the harness's own measurements, list prices summed over
    every model the run used, so that is what we report. Should a trace be cut
    off before that record, the duration falls back to the span from the first
    timestamped record to the last; on every trace here the two agree to within
    a few seconds, because the first stamped record lands milliseconds into the
    run and the last milliseconds before its end. Cost has no such fallback:
    a cut-off trace has no token accounting to sum, so it reports nothing
    rather than a total it cannot stand behind.
    """
    if not path or not os.path.exists(path):
        return None, None
    first = last = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if record.get("type") == "result":
                millis = record.get("duration_ms")
                dollars = record.get("total_cost_usd")
                if isinstance(millis, (int, float)):
                    seconds = millis / 1000.0
                else:
                    seconds = span(first, last)
                return seconds, dollars if isinstance(dollars, (int, float)) else None
            stamp = parse_timestamp(record.get("timestamp"))
            if stamp is not None:
                first = stamp if first is None else min(first, stamp)
                last = stamp if last is None else max(last, stamp)
    return span(first, last), None


def span(first, last):
    """Seconds between the outermost trace timestamps, or ``None`` if unstamped."""
    if first is None or last is None:
        return None
    return (last - first).total_seconds()


def parse_timestamp(value):
    """An ISO-8601 trace timestamp as a datetime; ``None`` if it is not one."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_duration(seconds):
    """Whole minutes: these runs last tens of minutes, so seconds are noise."""
    return None if seconds is None else f"{seconds / 60:.0f} min"


def format_cost(dollars):
    """Cents: these runs cost single-figure dollars, so cents are the detail."""
    return None if dollars is None else f"${dollars:.2f}"


# --- Overlap with the original corpus ----------------------------------------
# How many of the 80 originals a run actually recovered. The match has to be
# fuzzy: the same work turns up as "Wesmorland" for "Westmorland", as a short
# title against a full one, and under "A. and C. Black (pub.)" against "Adam
# and Charles Black". Two gates, both needed -- the author, then the title.
#
# Thresholds were set against hand-checked pairs rather than guessed. Titles of
# works that really are the same scored 0.63-0.81 on whole-string similarity;
# same-author-different-work pairs scored 0.46-0.49. 0.60 splits them. The
# errors that remain are almost all one shape: a prolific author's two similar
# books (Baddeley's "Thorough Guide" against his "Black's Shilling Guide"), so
# the count runs a little high rather than a little low. Matching LD80 against
# itself returns all 80, which is the test that the gates are not too tight.
SURNAME_MIN = 0.60  # title similarity needed when the author already agrees
TITLE_ONLY_MIN = 0.85  # ...and when it does not, or cannot be read

STOP_WORDS = {
    "a", "an", "the", "of", "or", "and", "in", "on", "to", "with", "for", "by",
    "from", "its", "their", "being", "during", "into", "upon", "at", "as", "is",
    "are", "part", "vol", "volume", "new", "edition", "containing", "account",
    "some", "which", "together", "also", "other", "than", "that", "this", "his",
    "her", "two", "three",
}
# The subject matter of every text here, so these words identify nothing.
COMMON_WORDS = {
    "lake", "lakes", "district", "english", "england", "cumberland",
    "westmorland", "guide", "tour", "tours", "description", "descriptive",
    "northern", "north", "counties", "county", "scenery", "mountains",
    "journal", "journey", "visit", "excursion", "observations", "notes",
    "letters", "history", "topographical", "lancashire", "yorkshire",
    "britain", "great", "scotland", "made", "complete", "concise",
    "companion", "hand", "book", "illustrated", "poem", "poems",
}
NAME_NOISE = {
    "mr", "mrs", "miss", "sir", "rev", "dr", "lord", "lady", "duke", "earl",
    "pub", "esq", "jr", "sr", "nee", "the", "of", "and", "st", "anon",
    "anonymous",
}


def normalise(text):
    """Fold case, accents and punctuation away: "Wesmorland" still differs."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = text.replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def surnames(author):
    """Candidate surnames: the last real word of each name, bracketed ones too.

    "Duke of Rutland [John Henry Manners]" yields both "rutland" and "manners";
    "Anon.-T. Ostell (pub.)" yields "ostell".
    """
    found = set()
    for chunk in re.split(r"[;/]| and ", author or ""):
        bracketed = re.findall(r"\[([^\]]*)\]", chunk)
        plain = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", chunk)
        for piece in bracketed + [plain]:
            piece = re.sub(r"^\s*anon\.?\s*-?", " ", piece, flags=re.IGNORECASE)
            words = [w for w in normalise(piece).split()
                     if w not in NAME_NOISE and len(w) > 2]
            if words:
                found.add(words[-1])
    return found


def given_initials(author):
    """First letters of the given names -- what tells two namesakes apart."""
    found = set()
    for chunk in re.split(r"[;/]| and ", author or ""):
        piece = re.sub(r"\([^)]*\)", " ", chunk)
        piece = re.sub(r"^\s*anon\.?\s*-?", " ", piece, flags=re.IGNORECASE)
        words = [w for w in normalise(piece).split() if w not in NAME_NOISE]
        found.update(word[0] for word in words[:-1])
    return found


def same_author(one, other):
    """Shared surname *and* compatible given names.

    The surname alone is not enough: this corpus holds Thomas and John
    Robinson, and Walter Parry Haskett Smith beside George Smith. Initials
    settle it, except where one side gives none ("M. J. B. Baddeley" against
    "Baddeley"), where the surname has to stand on its own.
    """
    if not (surnames(one) & surnames(other)):
        return False
    first, second = given_initials(one), given_initials(other)
    return not first or not second or bool(first & second)


def key_words(title):
    """The words of a title that could identify it."""
    return {word for word in normalise(title).split()
            if word not in STOP_WORDS and word not in COMMON_WORDS and len(word) > 2}


def title_score(one, other):
    """Whole-string similarity, or shared-distinctive-word containment.

    Containment is what catches a short catalogue title inside a long
    title-page one -- LD80's "A Tour thro\' the Whole Island of Great Britain"
    against the run\'s full version. It needs at least two shared words and
    three a side: on one word it scores a perfect 1.0 off "Coniston" alone.
    """
    mine, theirs = key_words(one), key_words(other)
    sequence = SequenceMatcher(None, normalise(one), normalise(other)).ratio()
    shared = mine & theirs
    if len(shared) >= 2 and min(len(mine), len(theirs)) >= 3:
        return max(len(shared) / min(len(mine), len(theirs)), sequence)
    return sequence


def match_reference(work, reference):
    """Index of the reference text ``work`` is a version of, or ``None``."""
    titles, author = work
    best_score, best_index = 0.0, None
    for index, (ref_titles, ref_author) in enumerate(reference):
        # A source may carry a short and a full title; any pairing counts.
        score = max(title_score(title, ref_title)
                    for title in titles for ref_title in ref_titles)
        agrees = same_author(author, ref_author)
        if score < (SURNAME_MIN if agrees else TITLE_ONLY_MIN):
            continue
        # An author match outranks any title-only one, however close.
        ranked = score + (1.0 if agrees else 0.0)
        if ranked > best_score:
            best_score, best_index = ranked, index
    return best_index


def count_shared(works, reference):
    """How many distinct reference texts this corpus recovered."""
    found = set()
    for work in works:
        index = match_reference(work, reference)
        if index is not None:
            found.add(index)
    return len(found)


def load_texts(path, fields, title_fields=(TITLE_FIELD,)):
    """Return (years, genders, works) for records in ``path`` with a usable date.

    ``fields`` is one field name or several in preference order; the first that
    parses to a year wins, so a sparse preferred field can fall back to a
    complete one. All three come back sorted by year and stay aligned, so a
    dot's position, its colour and its identity belong to the same text.
    """
    if isinstance(fields, str):
        fields = (fields,)
    texts = []
    skipped = 0
    with open(path, encoding="utf-8-sig") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            record = json.loads(raw)
            year = None
            for field in fields:
                year = parse_year(lookup(record, field))
                if year is not None:
                    break
            if year is None:
                skipped += 1
                continue
            texts.append((
                year,
                classify_gender(lookup(record, GENDER_FIELD)),
                tuple(lookup(record, name) or "" for name in title_fields),
                lookup(record, AUTHOR_FIELD) or "",
            ))
    texts.sort(key=lambda text: text[0])
    years = np.array([year for year, _, _, _ in texts], dtype=float)
    genders = [gender for _, gender, _, _ in texts]
    works = [(titles, author) for _, _, titles, author in texts]
    return years, genders, works, skipped


def classify_gender(value):
    """Bucket a gender field into M / F / U, tolerating padding and long forms."""
    if isinstance(value, str):
        token = value.strip().upper()
        if token in ("M", "MALE"):
            return "M"
        if token in ("F", "FEMALE"):
            return "F"
    return "U"


def lookup(record, field):
    """``record[field]``, tolerating a BOM-prefixed or differently-cased key."""
    if field in record:
        return record[field]
    for key in record:
        if key.lstrip("﻿").lower() == field.lower():
            return record[key]
    return None


def parse_year(value):
    """Coerce a year field to an int; ``None`` if it holds no 4-digit year.

    Handles ints, plain strings, and the ranged/approximate forms a run may
    emit ("1598-1622", "c. 1722-1727", "No Data") by taking the first 4-digit
    number.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    if not isinstance(value, str):
        return None
    match = YEAR_RE.search(value)
    return int(match.group()) if match else None


def stack_positions(years, genders, bin_width, x_min):
    """Wilkinson-style dot plot: bin the years, then stack dots within a bin.

    Within a bin the dots are grouped by gender, in STACK_ORDER from the
    baseline up, so each colour forms a contiguous band and its share of the
    stack is read as a length rather than counted dot by dot. Female sits on
    top of male, where it caps the stack and reads against the empty space
    above rather than against the mass of blue. Height within a bin carries
    nothing but the count, so this regrouping costs no information.

    Returns (x, y, colour) arrays, one entry per text, plus the tallest stack.
    """
    bins = {}
    for year, gender in zip(years, genders):
        index = int(math.floor((year - x_min) / bin_width))
        bins.setdefault(index, []).append(gender)

    xs, ys, colours = [], [], []
    for index, bin_genders in bins.items():
        bin_genders.sort(key=STACK_ORDER.index)
        for height, gender in enumerate(bin_genders, start=1):
            xs.append(x_min + (index + 0.5) * bin_width)
            ys.append(height)
            colours.append(GENDER_COLOURS[gender])
    tallest = max((len(g) for g in bins.values()), default=1)
    return np.array(xs), np.array(ys), colours, tallest


def percent_female(genders):
    """Female share of the whole panel, unknowns included in the denominator."""
    return 100.0 * genders.count("F") / len(genders) if genders else 0.0


def summarise(label, years, genders, shared, seconds, dollars):
    q1, median, q3 = np.percentile(years, [25, 50, 75])
    return {
        "label": label,
        "n": len(years),
        "min": int(years.min()),
        "q1": q1,
        "median": median,
        "q3": q3,
        "max": int(years.max()),
        **{key: genders.count(key) for key in GENDER_ORDER},
        "pct_f": percent_female(genders),
        "shared": shared,
        "minutes": None if seconds is None else seconds / 60.0,
        "dollars": dollars,
    }


def build_figure(datasets, x_min, x_max, bin_width):
    """Lay the figure out explicitly in inches so every dot is the same size."""
    axes_width = FIG_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    pitch = axes_width * bin_width / (x_max - x_min)  # inches per stacked dot

    stacks = []
    for label, years, genders, shared, total, seconds, dollars in datasets:
        xs, ys, colours, tallest = stack_positions(years, genders, bin_width, x_min)
        stacks.append((label, years, genders, shared, total, seconds, dollars,
                       colours, xs, ys, tallest))

    strip_heights = [pitch * (tallest + 0.6) for *_, tallest in stacks]
    fig_height = (
        MARGIN_TOP
        + sum(strip_heights)
        + STRIP_GAP * (len(stacks) - 1)
        + MARGIN_BOTTOM
    )

    fig = plt.figure(figsize=(FIG_WIDTH, fig_height), facecolor=SURFACE)
    dot_points = pitch * 72.0 * DOT_FILL

    top = fig_height - MARGIN_TOP
    strip_axes = []
    for index, (height, (label, years, genders, shared, total, seconds, dollars,
                         colour, xs, ys, tallest)) in enumerate(zip(strip_heights,
                                                                   stacks)):
        top -= height
        ax = fig.add_axes((
            MARGIN_LEFT / FIG_WIDTH,
            top / fig_height,
            axes_width / FIG_WIDTH,
            height / fig_height,
        ))
        draw_strip(ax, label, years, genders, shared, total, seconds, dollars,
                   colour, xs, ys, tallest, dot_points, x_min, x_max,
                   is_bottom=index == len(stacks) - 1)
        strip_axes.append(ax)
        top -= STRIP_GAP
    return fig, strip_axes


def draw_strip(ax, label, years, genders, shared, total, seconds, dollars, colour,
               xs, ys, tallest, dot_points, x_min, x_max, is_bottom=False):
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(0.1, tallest + 0.7)
    ax.set_facecolor("none")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_yticks([])
    ax.xaxis.set_major_locator(MultipleLocator(50))
    ax.grid(axis="x", color=GRID, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.axhline(0.1, color=BASELINE, linewidth=0.8 if is_bottom else 0.6, zorder=1)

    if is_bottom:
        # Only the last strip carries the year axis; the others share its scale
        # through the gridlines.
        ax.xaxis.set_minor_locator(MultipleLocator(10))
        ax.tick_params(axis="x", which="major", length=3, color=BASELINE,
                       labelsize=8.5, labelcolor=INK_SECONDARY, pad=3)
        ax.tick_params(axis="x", which="minor", length=1.8, color=GRID)
        ax.set_xlabel("Year", fontsize=9, color=INK_SECONDARY, labelpad=4)
    else:
        ax.tick_params(axis="x", length=0, labelbottom=False)

    ax.scatter(
        xs,
        ys,
        s=dot_points**2,
        marker="o",
        facecolor=colour,  # one colour per dot: its lead author's gender
        edgecolor=SURFACE,  # 2px-equivalent surface ring so touching dots read apart
        linewidth=0.5,
        zorder=3,
        clip_on=False,
    )

    median = float(np.median(years))
    ax.plot(
        [median, median],
        [0.1, tallest + 0.45],
        color=INK_SECONDARY,
        linewidth=0.9,
        linestyle=(0, (3, 2)),
        zorder=2,
    )

    # Ink label, not a coloured one: colour is spoken for by gender now, so a
    # tinted panel title would claim a meaning it does not have.
    ax.text(
        0.0,
        1.0,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color=INK,
    )
    # One run-level fact per chunk, in a fixed order, so the same reading runs
    # down the column. Time and cost sit last and adjacent, as the pair of
    # prices the run was bought at. The original corpus is not a run, so it has
    # none of them -- no overlap with itself worth stating, no time, no cost.
    facts = [
        f"n = {len(years)}",
        f"{percent_female(genders):.1f}% female",
    ]
    if shared is not None:
        facts.append(f"{shared}/{total} shared")
    facts.append(f"median {median:.0f}")
    elapsed = format_duration(seconds)
    if elapsed is not None:
        facts.append(elapsed)
    spend = format_cost(dollars)
    if spend is not None:
        facts.append(spend)
    ax.text(
        1.0,
        1.0,
        "   ".join(facts),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color=INK_MUTED,
    )


def main(argv=None):
    default_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output", nargs="?", default=None,
                        help=f"output PDF (default: <root>/{DEFAULT_OUTPUT})")
    parser.add_argument("--root", default=default_root,
                        help="repo root holding data/raw (default: %(default)s)")
    parser.add_argument("--bin-width", type=int, default=BIN_WIDTH,
                        help=f"dot-plot bin width in years (default: {BIN_WIDTH})")
    parser.add_argument("--xmin", type=int, default=None, help="left edge of the year axis")
    parser.add_argument("--xmax", type=int, default=None, help="right edge of the year axis")
    args = parser.parse_args(argv)

    plt.rcParams.update({
        "pdf.fonttype": 42,  # embed TrueType, not Type 3 -- journals require it
        "ps.fonttype": 42,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "text.color": INK,
        "axes.edgecolor": BASELINE,
    })

    loaded = []
    for label, path, field, title_fields, trace in resolve_sources(args.root):
        if not os.path.exists(path):
            print(f"skipping {label}: no {os.path.basename(path)} under "
                  f"{os.path.dirname(path)}", file=sys.stderr)
            continue
        years, genders, works, skipped = load_texts(path, field, title_fields)
        if len(years) == 0:
            print(f"skipping {label}: no usable {field!r} in {path}", file=sys.stderr)
            continue
        if skipped:
            print(f"note: {label}: skipped {skipped} record(s) with no usable date")
        seconds, dollars = run_totals(trace)
        if trace and seconds is None:
            print(f"note: {label}: no run time in {trace}", file=sys.stderr)
        if trace and dollars is None:
            print(f"note: {label}: no run cost in {trace}", file=sys.stderr)
        loaded.append((label, years, genders, works, seconds, dollars))

    # The first panel is the original corpus, so it is what the rest are
    # measured against. It matches itself -- that all 80 come back is the check
    # that the gates are not too tight -- but a corpus sharing every text with
    # itself says nothing about a run, so that panel reports no overlap at all.
    reference = loaded[0][3] if loaded else []
    datasets = [
        (label, years, genders,
         None if index == 0 else count_shared(works, reference), len(reference),
         seconds, dollars)
        for index, (label, years, genders, works, seconds, dollars)
        in enumerate(loaded)
    ]

    if not datasets:
        sys.exit("no corpora found; pass --root")

    all_years = np.concatenate([years for _, years, *_ in datasets])
    x_min = args.xmin if args.xmin is not None else int(math.floor(all_years.min() / 25) * 25)
    x_max = args.xmax if args.xmax is not None else int(math.ceil(all_years.max() / 25) * 25)

    width = max(len(label) for label, *_ in datasets) + 2
    print(f"{'run':<{width}}{'n':>5}{'min':>7}{'Q1':>7}{'median':>8}{'Q3':>7}{'max':>7}"
          f"{'male':>7}{'female':>8}{'unknown':>9}{'%F':>7}{'shared':>8}{'minutes':>9}"
          f"{'USD':>8}")
    for label, years, genders, shared, _, seconds, dollars in datasets:
        stats = summarise(label, years, genders, shared, seconds, dollars)
        minutes = "-" if stats["minutes"] is None else f"{stats['minutes']:.1f}"
        spend = "-" if stats["dollars"] is None else f"{stats['dollars']:.2f}"
        overlap = "-" if stats["shared"] is None else str(stats["shared"])
        print(f"{stats['label']:<{width}}{stats['n']:>5}{stats['min']:>7}"
              f"{stats['q1']:>7.0f}{stats['median']:>8.0f}{stats['q3']:>7.0f}"
              f"{stats['max']:>7}{stats['M']:>7}{stats['F']:>8}{stats['U']:>9}"
              f"{stats['pct_f']:>7.1f}{overlap:>8}{minutes:>9}{spend:>8}")

    fig, _ = build_figure(datasets, x_min, x_max, args.bin_width)

    output = args.output or os.path.join(args.root, DEFAULT_OUTPUT)
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    fig.savefig(output, format="pdf", facecolor=SURFACE)
    plt.close(fig)
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
