#!/usr/bin/env python3
"""Build a LaTeX longtable of corpus texts from a texts.jsonl file.

Texts are grouped by author (authors sorted alphabetically, case-insensitive;
titles within an author sorted alphabetically). Author and gender are shown
once per author group via \\multirow. Emits a self-contained LaTeX
`longtable` environment with a \\caption and \\label so it can be \\input
directly and cross-referenced with \\ref{<label>} elsewhere in the paper.
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

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


def escape(text: str) -> str:
    return LATEX_SPECIAL_RE.sub(lambda m: LATEX_SPECIAL_CHARS[m.group()], str(text))


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return [json.loads(line) for line in f if line.strip()]


SURNAME_PARTICLES = {"de", "van", "von", "der", "den", "le", "du"}


def first_author_surname(author: str) -> str:
    """Best-effort extraction of the first author's surname for sorting.

    Handles "and"-joined co-authors (e.g. "Charles Dickens and Wilkie
    Collins"), trailing editor credits (e.g. "Thomas Gray, ed. William
    Mason"), and titles/prefixes (e.g. "Sir Walter Scott"). A shared-surname
    pair like "Adam and Charles Black" is detected by the first segment
    being a single given name, in which case the surname is taken from the
    second segment instead. Compound surnames with a leading particle (e.g.
    "Thomas De Quincey") sort under the particle rather than the final token.
    """
    name = author.split(",", 1)[0]
    if " and " in name:
        before, after = name.split(" and ", 1)
        name = after if len(before.split()) == 1 else before
    tokens = name.split()
    if not tokens:
        return name
    if len(tokens) >= 2 and tokens[-2].lower() in SURNAME_PARTICLES:
        return " ".join(tokens[-2:])
    return tokens[-1]


def group_by_author(texts: list[dict]) -> list[tuple[str, list[dict]]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for t in texts:
        groups[t["author"]].append(t)
    ordered_authors = sorted(groups, key=lambda a: (first_author_surname(a).lower(), a.lower()))
    return [(a, sorted(groups[a], key=lambda t: t["title"].lower())) for a in ordered_authors]


def build_longtable(groups: list[tuple[str, list[dict]]], caption: str, label: str) -> str:
    lines = []
    lines.append(r"\begin{longtable}{@{}p{3.2cm} p{5.0cm} c c p{3.2cm}@{}}")
    lines.append(rf"\caption{{{caption}}}\label{{{label}}} \\")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Author} & \textbf{Title} & \textbf{Year} & \textbf{Gender} & \textbf{Genre} \\")
    lines.append(r"\midrule")
    lines.append(r"\endfirsthead")
    lines.append(rf"\multicolumn{{5}}{{l}}{{\textit{{{caption} (continued)}}}} \\")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Author} & \textbf{Title} & \textbf{Year} & \textbf{Gender} & \textbf{Genre} \\")
    lines.append(r"\midrule")
    lines.append(r"\endhead")
    lines.append(r"\bottomrule")
    lines.append(r"\endfoot")
    lines.append(r"\bottomrule")
    lines.append(r"\endlastfoot")

    for author, texts in groups:
        n = len(texts)
        gender = texts[0]["gender"]
        for i, t in enumerate(texts):
            title = escape(t["title"])
            year = escape(t.get("year", ""))
            genre = escape(t.get("genre", ""))
            if i == 0:
                author_cell = rf"\multirow[t]{{{n}}}{{3.2cm}}{{{escape(author)}}}" if n > 1 else escape(author)
                gender_cell = rf"\multirow[t]{{{n}}}{{*}}{{{gender}}}" if n > 1 else gender
            else:
                author_cell = ""
                gender_cell = ""
            lines.append(f"{author_cell} & {title} & {year} & {gender_cell} & {genre} \\\\")

    lines.append(r"\end{longtable}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", type=Path, nargs="?",
        default=Path("../data/raw/cldw2/claude-code/texts.jsonl"),
        help="path to texts.jsonl (default: %(default)s)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="write LaTeX to this file instead of stdout",
    )
    parser.add_argument(
        "--caption", default="Texts comprising the corpus, grouped by author.",
        help="table caption (default: %(default)s)",
    )
    parser.add_argument(
        "--label", default="tab:corpus-texts",
        help="LaTeX label for cross-referencing (default: %(default)s)",
    )
    args = parser.parse_args()

    texts = load_jsonl(args.input)
    groups = group_by_author(texts)
    latex = build_longtable(groups, args.caption, args.label)

    if args.output:
        args.output.write_text(latex + "\n", encoding="utf-8")
        print(f"Wrote {args.output} ({len(texts)} texts, {len(groups)} authors)")
    else:
        print(latex)


if __name__ == "__main__":
    main()
