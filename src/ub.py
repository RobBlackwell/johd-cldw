#!/usr/bin/env python3
"""Compare the two claude-code universe-balanced runs: how much did they agree?

``universe-balanced`` is the one experiment that was run twice under identical
conditions (``claude-code`` and ``claude-code-run2``), so the two corpora are a
direct measure of run-to-run variation: given the same prompt and the same 80
texts to avoid, how much of what a run finds would it find again?

Answering that means matching texts, not counting lines. The two runs describe
the same work differently -- different titles ("The Lakes of England" against
"The Lakes of England, illustrated with Eighteen Coloured Etchings"), different
forms of an author's name, and different editions and so different years -- so a
literal comparison of title strings would report almost no overlap and would be
wrong. This script merges near-duplicates first, within each run and then
across the pair, and reports the overlap over *distinct works*.

The judgement that two records are the same work is ``same_work`` below. It is
deliberately this script's own and not the one ``find-female.py`` uses, because
that one was calibrated on the 112 female-authored records and does not survive
the move to all 645: its "same author, same year" fallback merges Wordsworth's
*The Waggoner* with his *Peter Bell*, both 1819, and Ferguson's *Cumberland and
Westmorland M.P.'s* with his *Early Cumberland and Westmorland Friends*, both
1871. Whole-string similarity alone will not separate those either -- the
Ferguson pair scores 0.60 on the shared topical words "Cumberland and
Westmorland" while the genuine Topham pair above scores 0.48 -- so the rule adds
a negative gate on the words that actually distinguish a title. See ``same_work``.

The overlap is sensitive to that rule, so the script does not report a single
number and leave it there: ``--sensitivity`` re-runs the count under a stricter
and a looser rule, and ``--audit`` prints every merge and every cross-run pair
it made, so each judgement can be checked by eye rather than trusted.

Run from anywhere:
    ./ub.py [--audit] [--sensitivity] [--list] [--csv out.csv]
"""

import argparse
import csv
import importlib.util
import os
import sys

# The two runs being compared: (label, variant, run directory). Both are the
# same experiment, which is the point -- the only difference is that one was run
# after the other.
RUNS = [
    ("run1", "universe-balanced", "claude-code"),
    ("run2", "universe-balanced", "claude-code-run2"),
]
TEXTS_NAME = "texts.jsonl"

# The normalisation and scoring primitives come from find-female.py rather than
# being copied: the stop-word and common-word lists, the volume stripping and
# the title score are calibrated against hand-checked pairs from this same
# corpus, and a second copy of them here would drift from the first. Only the
# *rule* built on top of them is local -- see the module docstring. The import
# goes through importlib because the file name carries a hyphen.
_FF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "find-female.py")


def _load_helpers(path=_FF_PATH):
    """find-female.py as a module, for the primitives listed above."""
    if not os.path.exists(path):
        sys.exit(f"cannot find {path}, which this script borrows its "
                 f"title-matching primitives from")
    spec = importlib.util.spec_from_file_location("_ff_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ff = _load_helpers()

# Borrowed, and named here so the debt is explicit and a rename upstream fails
# loudly at import instead of silently changing a published number.
normalise = ff.normalise
reference_surnames = ff.reference_surnames
key_words = ff.key_words
numbers = ff.numbers
title_score = ff.title_score
parse_year = ff.parse_year
read_jsonl = ff.read_jsonl
lookup = ff.lookup
NAME_NOISE = ff.NAME_NOISE

TITLE_ONLY_MIN = ff.TITLE_ONLY_MIN

TITLE_FIELD = ff.TITLE_FIELD
AUTHOR_FIELD = ff.AUTHOR_FIELD
YEAR_FIELD = ff.YEAR_FIELD

# --- The rule ----------------------------------------------------------------
# A title clearing this on similarity alone is the same work whatever the years
# say, because the runs cite different editions of one text and the year is the
# field most likely to differ. find-female.py's own threshold, calibrated there
# against hand-checked pairs where the author already agrees.
TITLE_MIN = ff.TITLE_MIN
# Below it, an agreeing year can still carry a pair -- but only if the titles are
# at least loosely alike. An unconditional year rule is what merges *The
# Waggoner* with *Peter Bell*. The floor sits between the genuine pairs it has
# to keep (Topham's two Lakes of England editions, 0.48) and the false ones it
# has to drop (Waggoner/Peter Bell, 0.31; Knight's Life of Wordsworth against
# his Wordsworthiana, 0.28). It is the loosest of the three gates and the one
# --sensitivity varies, because the pairs nearest it are the ones a reader
# should not have to take on trust: George Fox's Journal under its short and its
# full title scores 0.345 and so falls just outside, counted as two works here.
YEAR_TITLE_MIN = 0.40
# How many distinctive words of its own a title needs before the absence of any
# shared one is taken as evidence against a match, rather than as a title too
# short to tell. Two: on one word a single stray adjective would veto a pair.
DISTINCTIVE_MIN = 2


def candidate_surnames(record):
    """Every word that could be this record's author's surname.

    find-female.py's ``surname`` returns one, because the merge there buckets
    records by it and a record can sit in only one bucket. Comparing a pair
    affords several, and this pair needs them: the two runs name the same author jointly and singly ("John
    Brownbill" against "John Brownbill and J. C. Atkinson"), and one adds a
    pseudonym or a maiden name in brackets that becomes the last word ("Alexander
    Hay Japp" against "Alexander Hay Japp ('H. A. Page')", "Joseph Budworth"
    against "Joseph Budworth (Palmer)"). Keyed on the last word alone, each of
    those pairs lands in two buckets and is counted as two works.
    """
    return reference_surnames(record["author"])


def same_author(one, other):
    """Do the two records credit the same author?"""
    return bool(candidate_surnames(one) & candidate_surnames(other))


def author_words(author):
    """The name's own words, to be discounted from a title's distinctive set.

    A title that names its author -- "The Journal of George Fox", "The Life of
    William Wordsworth" -- gets no distinguishing power from doing so, because
    the records being compared already share a surname. Left in, "wordsworth"
    counts as a shared distinctive word between a life of him and a volume of
    papers about him, and the negative gate below never fires.
    """
    return frozenset(word for word in normalise(author).split()
                     if word not in NAME_NOISE)


def distinctive(record):
    """The words that could tell this title apart from another by the author."""
    return key_words(record["title"]) - author_words(record["author"])


def same_work(one, other, year_title_min=YEAR_TITLE_MIN, use_year=True):
    """Are these two records the same text?

    Four gates, in order:

    1. Counting words must not disagree: "in Three Familiar Dialogues" is not
       "in Four Familiar Dialogues", however alike the rest reads.
    2. If both titles carry distinctive words of their own and share none, they
       are different works -- whatever the whole-string score says. This is the
       gate that separates Ferguson's two 1871 Cumberland books, which share
       only the county names every text here has, and Knight's life of
       Wordsworth from his Wordsworthiana.
    3. If the authors agree, similarity decides: over TITLE_MIN on its own, or
       over ``year_title_min`` with an agreeing year.
    4. If they do not, an identical title and an identical year can still carry
       the pair, at the higher TITLE_ONLY_MIN bar. This is needed because the
       runs disagree about authorship more often than one would expect -- the
       1757 *Account of the Effects of a Storm at Wigton* is Thomlinson's in one
       run and Philip Miller's in the other, the 1879 *Memoirs of Dr Richard
       Gilpin* is credited once to its editor and once to its subject, the 1780
       *Choice Collection of Poems in the Cumberland Dialect* is anonymous in one
       and Robert Nelson's in the other, and Thomas Machell's surname is spelt
       with one L and with two. Those are the same text twice over, and filing
       them as four works would understate the agreement between the runs.
    """
    mine, theirs = numbers(one["title"]), numbers(other["title"])
    if mine and theirs and mine != theirs:
        return False

    ours, yours = distinctive(one), distinctive(other)
    if len(ours) >= DISTINCTIVE_MIN and len(yours) >= DISTINCTIVE_MIN \
            and not (ours & yours):
        return False

    score = title_score(one["title"], other["title"])
    if not same_author(one, other):
        # The year is required here, not optional: it is the only other evidence
        # left once the names have failed to agree, and generic guide titles
        # recur across the century under different authors.
        return score >= TITLE_ONLY_MIN and one["year"] is not None \
            and one["year"] == other["year"]

    if score >= TITLE_MIN:
        return True
    if not use_year:
        return False
    return one["year"] is not None and one["year"] == other["year"] \
        and score >= year_title_min


# --- Loading -----------------------------------------------------------------
def load_run(label, path):
    """One run's records, in the shape this script compares."""
    loaded = []
    for index, record in enumerate(read_jsonl(path)):
        title = str(lookup(record, TITLE_FIELD) or "").strip()
        loaded.append({
            "run": label,
            "index": index,
            "title": title,
            "author": str(lookup(record, AUTHOR_FIELD) or "").strip(),
            "year": parse_year(lookup(record, YEAR_FIELD)),
        })
    return loaded


def resolve_sources(root):
    """(label, path) for each of the two runs."""
    return [(label, os.path.join(root, "data", "raw", variant, run, TEXTS_NAME))
            for label, variant, run in RUNS]


# --- Merging within a run ----------------------------------------------------
def group_records(records, **rule):
    """Merge a list of records into distinct works.

    Every pair is compared, rather than only pairs bucketed together by surname.
    Bucketing on a single surname would undo the two gates ``same_work`` adds for
    exactly this data: a pair the runs credit to different authors, or to a joint
    and a single author, never meets to be compared and is counted twice. Three
    hundred records is fifty thousand pairs, which ``title_score`` clears in a
    second or two, so the blocking buys nothing worth that.

    The union-find makes merging transitive, so a record matching any member of a
    group joins the whole group.
    """
    parent = list(range(len(records)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            if find(i) != find(j) and same_work(records[i], records[j], **rule):
                parent[find(i)] = find(j)

    clusters = {}
    for index, record in enumerate(records):
        clusters.setdefault(find(index), []).append(record)
    return list(clusters.values())


def work_year(work):
    """The earliest year any record in the work carries."""
    years = [r["year"] for r in work if r["year"] is not None]
    return min(years) if years else None


def work_label(work):
    """The longest title and author in the group -- the fullest description."""
    title = max((r["title"] for r in work), key=len, default="")
    author = max((r["author"] for r in work), key=len, default="")
    return author, title


# --- Matching across the two runs --------------------------------------------
def match_runs(works_one, works_two, **rule):
    """Pair up the works of two runs, one to one.

    Every pair the rule accepts is scored, the pairs are taken best
    first, and each work is spent once -- so a run that lists two editions the
    other lists as one cannot have both counted as agreements. Scoring a pair of
    *groups* means taking the best title score over their records, since either
    run may hold the form of the title that matches.
    """
    candidates = []
    for i, one in enumerate(works_one):
        for j, two in enumerate(works_two):
            if not any(same_work(a, b, **rule) for a in one for b in two):
                continue
            score = max(title_score(a["title"], b["title"]) for a in one for b in two)
            candidates.append((score, i, j))

    candidates.sort(key=lambda c: -c[0])
    taken_one, taken_two, pairs = set(), set(), []
    for score, i, j in candidates:
        if i in taken_one or j in taken_two:
            continue
        taken_one.add(i)
        taken_two.add(j)
        pairs.append((i, j, score))

    only_one = [i for i in range(len(works_one)) if i not in taken_one]
    only_two = [j for j in range(len(works_two)) if j not in taken_two]
    return pairs, only_one, only_two


def compare(runs, **rule):
    """Distinct works per run, the pairs between them, and what is unique."""
    works = {label: group_records(records, **rule) for label, records in runs}
    labels = [label for label, _ in runs]
    pairs, only_one, only_two = match_runs(works[labels[0]], works[labels[1]], **rule)
    return works, labels, pairs, only_one, only_two


# --- Reporting ---------------------------------------------------------------
def print_summary(runs, works, labels, pairs, only_one, only_two):
    one, two = labels
    n_one, n_two = len(works[one]), len(works[two])
    common = len(pairs)
    union = n_one + n_two - common
    raw = {label: len(records) for label, records in runs}

    print("Two runs of the universe-balanced experiment, compared as works")
    print("=" * 66)
    for label, _, directory in RUNS:
        print(f"  {label:<6} {directory:<18} {raw[label]:>4} records "
              f"-> {len(works[label]):>4} distinct works "
              f"({raw[label] - len(works[label])} merged within the run)")
    print()
    print(f"  common to both runs      {common:>4}")
    print(f"  only in {one}             {len(only_one):>4}")
    print(f"  only in {two}             {len(only_two):>4}")
    print(f"  union (distinct works)   {union:>4}")
    print()
    print(f"  overlap as a share of {one}   {common / n_one:6.1%}")
    print(f"  overlap as a share of {two}   {common / n_two:6.1%}")
    print(f"  Jaccard (common / union)     {common / union:6.1%}")
    print()
    print(f"So the two runs agree on {common} works. Each run found roughly "
          f"{(n_one + n_two) / 2:.0f}\nworks, of which about "
          f"{common / ((n_one + n_two) / 2):.0%} were found by the other run too; "
          f"pooling the\ntwo runs yields {union} distinct works rather than "
          f"{n_one + n_two}.")


def print_list(works, labels, pairs, only_one, only_two, width):
    one, two = labels

    def row(work):
        author, title = work_label(work)
        year = work_year(work)
        return f"    {year or '????'}  {author[:28]:<28}  {title[:width]}"

    print(f"\n\nWorks common to both runs ({len(pairs)})")
    print("-" * 66)
    for i, j, score in sorted(pairs, key=lambda p: work_year(works[one][p[0]]) or 0):
        print(row(works[one][i]))
        other_author, other_title = work_label(works[two][j])
        if normalise(other_title) != normalise(work_label(works[one][i])[1]):
            print(f"      {two} as: {other_title[:width]}  [{score:.2f}]")

    for label, indexes in ((one, only_one), (two, only_two)):
        print(f"\n\nOnly in {label} ({len(indexes)})")
        print("-" * 66)
        for index in sorted(indexes, key=lambda k: work_year(works[label][k]) or 0):
            print(row(works[label][index]))


def print_audit(works, labels, pairs):
    print("\n\nAudit: records merged within a run")
    print("-" * 66)
    for label in labels:
        groups = [w for w in works[label] if len(w) > 1]
        print(f"\n  {label}: {len(groups)} group(s) of more than one record")
        for work in sorted(groups, key=lambda w: work_year(w) or 0):
            print(f"    {work_year(work) or '????'}  {work_label(work)[0]}")
            for record in work:
                print(f"        line {record['index'] + 1:>3}  {record['year']}  "
                      f"{record['title']}")

    print("\n\nAudit: cross-run pairs, weakest title score first")
    print("-" * 66)
    one, two = labels
    for i, j, score in sorted(pairs, key=lambda p: p[2]):
        a, b = works[one][i], works[two][j]
        print(f"  [{score:.3f}] {work_label(a)[0]}")
        print(f"        {one}: {work_year(a) or '????'}  {work_label(a)[1]}")
        print(f"        {two}: {work_year(b) or '????'}  {work_label(b)[1]}")


def print_sensitivity(runs):
    """The count under a stricter and a looser rule than the default.

    The point is not that one of these is right, but how far the answer moves
    when the loosest gate is tightened or dropped: a headline number that swings
    wildly under it should be reported as a range, and one that barely moves can
    be quoted as it stands.
    """
    variants = [
        ("title only, no year rule", {"use_year": False}),
        (f"year rule, title >= {YEAR_TITLE_MIN:.2f}  (default)", {}),
        ("year rule, title >= 0.30", {"year_title_min": 0.30}),
        ("year rule, any title  (find-female.py's)", {"year_title_min": 0.0}),
    ]
    print("\n\nSensitivity of the overlap to the matching rule")
    print("-" * 66)
    print(f"  {'rule':<42}{'run1':>6}{'run2':>6}{'common':>8}")
    for name, rule in variants:
        works, labels, pairs, _, _ = compare(runs, **rule)
        print(f"  {name:<42}{len(works[labels[0]]):>6}"
              f"{len(works[labels[1]]):>6}{len(pairs):>8}")
    print("\n  'any title' drops the gate that separates The Waggoner from Peter")
    print("  Bell, so its counts are the ones to distrust; it is shown because it")
    print("  is what find-female.py's rule would give.")


def write_csv(works, labels, pairs, only_one, only_two, path):
    """One row per distinct work in the pooled pair, saying which runs hold it."""
    one, two = labels
    rows = []
    for i, j, score in pairs:
        author, title = work_label(works[one][i])
        rows.append([work_year(works[one][i]) or "", author, title, "both",
                     f"{score:.3f}", work_label(works[two][j])[1],
                     len(works[one][i]), len(works[two][j])])
    for label, indexes in ((one, only_one), (two, only_two)):
        for index in indexes:
            author, title = work_label(works[label][index])
            rows.append([work_year(works[label][index]) or "", author, title,
                         label, "", "", len(works[label][index]), ""])
    rows.sort(key=lambda r: (r[0] or 0, r[1], r[2]))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["year", "author", "title", "found_by", "title_score",
                         "other_run_title", "n_records_run1", "n_records_run2"])
        writer.writerows(rows)


def main(argv=None):
    default_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=default_root,
                        help="repo root holding data/raw (default: %(default)s)")
    parser.add_argument("--width", type=int, default=58,
                        help="title column width (default: %(default)s)")
    parser.add_argument("--list", action="store_true",
                        help="list the common works and the ones unique to each run")
    parser.add_argument("--audit", action="store_true",
                        help="print every merge and every cross-run pair, weakest "
                             "first, to check the judgements")
    parser.add_argument("--sensitivity", action="store_true",
                        help="re-count under a stricter and a looser matching rule")
    parser.add_argument("--csv", default=None,
                        help="also write one row per distinct work to this CSV")
    args = parser.parse_args(argv)

    runs = []
    for label, path in resolve_sources(args.root):
        if not os.path.exists(path):
            sys.exit(f"no {TEXTS_NAME} under {os.path.dirname(path)}; pass --root")
        runs.append((label, load_run(label, path)))

    works, labels, pairs, only_one, only_two = compare(runs)
    print_summary(runs, works, labels, pairs, only_one, only_two)

    if args.list:
        print_list(works, labels, pairs, only_one, only_two, args.width)
    if args.audit:
        print_audit(works, labels, pairs)
    if args.sensitivity:
        print_sensitivity(runs)
    if args.csv:
        directory = os.path.dirname(os.path.abspath(args.csv))
        os.makedirs(directory, exist_ok=True)
        write_csv(works, labels, pairs, only_one, only_two, args.csv)
        print(f"\nwrote {args.csv}")


if __name__ == "__main__":
    main()
