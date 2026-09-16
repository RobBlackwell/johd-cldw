#!/usr/bin/env python3
"""Compare the date distributions of the Lake District corpora.

Each corpus is a JSONL file with one text per line and a year field. This
renders a publication-quality PDF: one stacked dot plot per corpus on a shared
year axis (one dot = one text, dots stacked within 5-year bins), so clusters of
texts in time are directly countable and comparable across corpora -- every dot
is the same size in every panel, so the panel heights carry the corpus sizes.

Year fields:
  * ``texts.jsonl`` files (CLDW2, universe) use ``year``.
  * the original CLDW metadata uses ``Year_id`` -- the corpus's own canonical
    date key (the year in each text's ``ID``), which is what the 80 texts are
    identified and ordered by. Use ``--original-year-field Year_Pub`` to plot
    first-publication years instead; note that a handful of CLDW texts were
    written in the 17th-18th century but only printed in the 20th, so the two
    fields disagree for those.

Run from src/:  python3 plot_year_distributions.py [output.pdf]
"""

import argparse
import json
import math
import os
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

# (label, path, year field). Paths are relative to src/.
DATASETS = [
    ("Original CLDW", "../data/interim/ld80-metadata/ld80-metadata.jsonl", "Year_id"),
    ("CLDW2", "../data/raw/cldw2/claude-code/texts.jsonl", "year"),
    ("Universe", "../data/raw/cldw-universe/texts.jsonl", "year"),
]

DEFAULT_OUTPUT = "../reports/corpus_year_distributions.pdf"

# --- Palette -----------------------------------------------------------------
# Categorical slots 1-3 (blue / orange / aqua), which validate on all pairs for
# both normal vision and simulated CVD. Every series is direct-labelled, which
# is also the relief for aqua sitting just under 3:1 against the surface.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
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
MARGIN_TOP = 0.42
MARGIN_BOTTOM = 0.50
STRIP_GAP = 0.30  # between dot-plot panels

BIN_WIDTH = 5  # years per dot-plot bin
DOT_FILL = 0.82  # dot diameter as a fraction of the bin pitch

YEAR_RE = re.compile(r"\d{4}")


def load_years(path, field):
    """Return the years of every record in ``path`` that has a usable date."""
    years = []
    skipped = 0
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
            year = parse_year(value)
            if year is None:
                skipped += 1
                continue
            years.append(year)
    return np.array(sorted(years), dtype=float), skipped


def parse_year(value):
    """Coerce a year field to an int; ``None`` if it holds no 4-digit year.

    Handles ints, plain strings, and the ranged/approximate forms found in the
    CLDW metadata ("1598-1622", "c. 1722-1727", "No Data") by taking the first
    4-digit number.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    if not isinstance(value, str):
        return None
    match = YEAR_RE.search(value)
    return int(match.group()) if match else None


def stack_positions(years, bin_width, x_min):
    """Wilkinson-style dot plot: bin the years, then stack dots within a bin.

    Returns (x, y) arrays where x is the bin centre and y is 1, 2, 3, ... for
    successive texts in that bin, plus the tallest stack.
    """
    xs, ys = [], []
    counts = {}
    for year in years:
        index = int(math.floor((year - x_min) / bin_width))
        counts[index] = counts.get(index, 0) + 1
        xs.append(x_min + (index + 0.5) * bin_width)
        ys.append(counts[index])
    return np.array(xs), np.array(ys), (max(counts.values()) if counts else 1)


def summarise(label, years):
    q1, median, q3 = np.percentile(years, [25, 50, 75])
    return {
        "label": label,
        "n": len(years),
        "min": int(years.min()),
        "q1": q1,
        "median": median,
        "q3": q3,
        "max": int(years.max()),
    }


def build_figure(datasets, x_min, x_max, bin_width):
    """Lay the figure out explicitly in inches so every dot is the same size."""
    axes_width = FIG_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    pitch = axes_width * bin_width / (x_max - x_min)  # inches per stacked dot

    stacks = []
    for label, years, colour in datasets:
        xs, ys, tallest = stack_positions(years, bin_width, x_min)
        stacks.append((label, years, colour, xs, ys, tallest))

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
    for index, (height, (label, years, colour, xs, ys, tallest)) in enumerate(
        zip(strip_heights, stacks)
    ):
        top -= height
        ax = fig.add_axes((
            MARGIN_LEFT / FIG_WIDTH,
            top / fig_height,
            axes_width / FIG_WIDTH,
            height / fig_height,
        ))
        draw_strip(ax, label, years, colour, xs, ys, tallest, dot_points, x_min, x_max,
                   is_bottom=index == len(stacks) - 1)
        strip_axes.append(ax)
        top -= STRIP_GAP
    return fig, strip_axes


def draw_strip(ax, label, years, colour, xs, ys, tallest, dot_points, x_min, x_max,
               is_bottom=False):
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
        facecolor=colour,
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

    ax.text(
        0.0,
        1.0,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color=colour,
    )
    ax.text(
        1.0,
        1.0,
        f"n = {len(years)}   median {median:.0f}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color=INK_MUTED,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output", nargs="?", default=DEFAULT_OUTPUT,
                        help=f"output PDF (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--original-year-field", default="Year_id",
                        help="year field to read from the CLDW metadata "
                             "(default: Year_id; try Year_Pub)")
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

    datasets = []
    for label, path, field in DATASETS:
        if field != "year":
            field = args.original_year_field
        if not os.path.exists(path):
            sys.exit(f"missing input: {path}")
        years, skipped = load_years(path, field)
        if len(years) == 0:
            sys.exit(f"no usable years in {path} (field {field!r})")
        if skipped:
            print(f"note: {path}: skipped {skipped} record(s) with no usable {field}")
        datasets.append((label, years, SERIES[len(datasets) % len(SERIES)]))

    all_years = np.concatenate([years for _, years, _ in datasets])
    x_min = args.xmin if args.xmin is not None else int(math.floor(all_years.min() / 25) * 25)
    x_max = args.xmax if args.xmax is not None else int(math.ceil(all_years.max() / 25) * 25)

    print(f"{'corpus':<18}{'n':>5}{'min':>7}{'Q1':>7}{'median':>8}{'Q3':>7}{'max':>7}")
    for label, years, _ in datasets:
        s = summarise(label, years)
        print(f"{s['label']:<18}{s['n']:>5}{s['min']:>7}{s['q1']:>7.0f}"
              f"{s['median']:>8.0f}{s['q3']:>7.0f}{s['max']:>7}")

    fig, _ = build_figure(datasets, x_min, x_max, args.bin_width)

    output = args.output
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    fig.savefig(output, format="pdf", facecolor=SURFACE)
    plt.close(fig)
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
