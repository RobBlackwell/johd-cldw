#!/usr/bin/env python3
"""List every female-authored text the claude-code runs found, once each.

Pools the ``texts.jsonl`` of all five claude-code runs -- the same five as
``EXPERIMENTS`` in ``01-reb-analyse.py`` -- keeps the records whose ``gender``
field reads F, and prints them as one list of *distinct works*, each with its
date, its author, its title, a tick under every experiment whose corpus
contains it and, under ``cldw``, whether the work was in the original CLDW to
begin with. So the list answers three things at once: which
women the runs found between them, which of them a given run found on its own,
and which of them are new to the corpus rather than recovered from it.

A second table then turns the ``cldw`` column around and lists the CLDW's own
female-authored texts that the first table does *not* hold -- the women the
runs were given and lost. A cell there carries the gender a run recorded
instead of a tick, because a woman can go missing from the list above two ways:
no run found her text at all, or a run found it and filed its author as a man.

The runs overlap heavily, so the list is only meaningful once near-duplicates
are merged: 112 female-authored records across the five runs are about 45
distinct works. The same work reaches this script under different titles
("Lizzie Lorton of Greyrigg: A Novel" / "...., Volume 1" / bare), under
different names for its author ("Eliza Lynn Linton" / "Elizabeth Lynn
Linton", and Sara Coleridge's memoir under her daughter Edith, who edited
it), and under different years, because a run dates a text by the edition it
points at and the runs picked different editions -- Eliza Fletcher's
autobiography comes in at both 1875 and 1876, Elizabeth Smith's *Fragments*
at 1808, 1810 and 1818. ``same_work`` below is the judgement that merges
them, and it errs towards merging: every distinct title, author and year in a
group is printed under it, so a merge that should not have happened is
visible on the face of the output rather than hidden inside a count.

Dates are the year each run recorded. Where a record's own title or reason
names an earlier year -- the date a text was written, as against the date of
the edition the run cites -- that year is shown in brackets after it, which
is how Celia Fiennes, recorded at 1888, is shown as having ridden north in
1698. Grouping always uses the recorded year, never the bracketed one, so
re-dating can never silently split or merge a work.

Run from anywhere:
    ./find-female.py [--runs LABEL,...] [--csv out.csv] [--audit]
"""

import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from functools import lru_cache

# (column label, variant, run directory) -- the same five runs, under the same
# labels, as EXPERIMENTS in 01-reb-analyse.py, in the order
# plot_year_distributions.py and tabulate_genre_balance.py use: within each
# corpus family the unbalanced run comes first, so each column is read against
# the plainer run to its left and the effect of the balancing instruction falls
# out as the difference.
EXPERIMENTS = [
    ("cldw2-unbalanced", "cldw2-unbalanced", "claude-code"),
    ("cldw2-balanced", "cldw2-balanced", "claude-code"),
    ("universe-unbalanced", "universe-unbalanced", "claude-code"),
    ("universe-balanced", "universe-balanced", "claude-code"),
    ("universe-balanced-run2", "universe-balanced", "claude-code-run2"),
]

# Column heads for the tick matrix. Spelling the labels above out in full would
# make the table twice the width of the titles it is meant to annotate, so each
# gets an abbreviation and the legend above the table carries the mapping.
COLUMN_HEADERS = {
    "cldw2-unbalanced": "c2-u",
    "cldw2-balanced": "c2-b",
    "universe-unbalanced": "un-u",
    "universe-balanced": "un-b",
    "universe-balanced-run2": "un-b2",
}

TEXTS_NAME = "texts.jsonl"

# The corpus the runs were asked to reconstruct, for the ``cldw`` column and the
# second table. Dated by year of *publication*, which is the date the runs
# themselves report and so the only one that compares like with like, with
# ``Year_Comp`` supplying the bracketed composition year that ``evidence_year``
# digs out of a run's prose. Its author and gender columns need no names of
# their own: ``lookup`` folds case, so "Author" and "Gender" answer to the run
# field names below.
LD80_LABEL = "Original CLDW"
LD80_HEADER = "cldw"
LD80_PATH = ("data", "interim", "ld80-metadata", "ld80-metadata.jsonl")
LD80_YEAR_FIELD = "Year_Pub"
LD80_COMP_FIELD = "Year_Comp"
LD80_TITLE_FIELDS = ("Title_short", "Title_full")

YEAR_FIELD = "year"
GENDER_FIELD = "gender"
TITLE_FIELD = "title"
AUTHOR_FIELD = "author"
REASON_FIELD = "reason"

PRESENT = "x"  # tick for "this run's corpus holds this work"
ABSENT = "."

# --- Merging near-duplicates -------------------------------------------------
# Two records are the same work if they agree on the author's surname *and* on
# either the title or the year. Both gates are needed and neither is enough:
#
# Title alone misses the Martineau autobiography, which one run titles
# "Harriet Martineau's Autobiography" and another "Autobiography, with
# Memorials by Maria Weston Chapman, Volume 2" -- no shared distinctive words
# beyond "autobiography", but both are dated 1877 and both are hers.
#
# Year alone misses the editions: Fletcher at 1875 and 1876, Smith at 1808,
# 1810 and 1818, the Coleridge memoir at 1873 and 1874. And year alone would
# merge, for instance, Gaskell's "Half a Life-Time Ago" with anything else of
# hers in that year.
#
# TITLE_MIN is the threshold plot_year_distributions.py calibrated against
# hand-checked pairs for the case where the author already agrees: titles of
# works that really are the same scored 0.63-0.81, same-author-different-work
# pairs 0.46-0.49.
TITLE_MIN = 0.60
# The same threshold serves the match against the original CLDW, where the
# author is checked rather than assumed, and a pair whose names do not agree --
# or whose names cannot be read, LD80 recording several texts under their
# publisher -- has to clear a higher bar on the title alone. Both numbers are
# plot_year_distributions.py's, which counts the same match over all 80 texts;
# matching LD80 against itself there returns all 80, the test that they are not
# too tight.
TITLE_ONLY_MIN = 0.85

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
    "anonymous", "editor",
}

# "Volume 2", "Vol. ii", "Part 1": which slice of a work a run chose to point
# at, not a different work, so it comes off the title before comparison.
VOLUME_RE = re.compile(r"\b(?:volume|vol|part|book|no)\s+(?:\d+|[ivxl]+)\b")
# ...but the counting words that survive that do tell works apart, and nothing
# else here does: Ann Wheeler's "Westmorland Dialect, in Three Familiar
# Dialogues" (1790) and her "...in Four Familiar Dialogues" (1802) share every
# other word and score a perfect title match.
NUMBER_WORDS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "first", "second", "third", "fourth", "fifth",
    "sixth", "seventh", "eighth", "ninth", "tenth",
}

YEAR_RE = re.compile(r"\d{4}")
# A year named inside a title or reason, for the composition-date hint. Bounded
# below because a run's prose mentions page counts and print runs too, and
# above by the corpus's own horizon.
ANY_YEAR_RE = re.compile(r"\b1[5-9]\d{2}\b")
YEAR_FLOOR = 1500


# --- Loading -----------------------------------------------------------------
def read_jsonl(path):
    """Records from a JSONL file, skipping blank and unparseable lines."""
    with open(path, encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                print(f"note: {path}: skipped an unparseable line", file=sys.stderr)


def lookup(record, field):
    """``record[field]``, tolerating a BOM-prefixed or differently-cased key."""
    if field in record:
        return record[field]
    wanted = field.lower()
    for key, value in record.items():
        if key.strip().lstrip("﻿").lower() == wanted:
            return value
    return None


def parse_year(value):
    """Coerce a year field to an int; ``None`` if it holds no 4-digit year.

    Handles ints, plain strings, and the ranged or approximate forms a run may
    emit ("1598-1622", "c. 1722-1727") by taking the first 4-digit number.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    if not isinstance(value, str):
        return None
    match = YEAR_RE.search(value)
    return int(match.group()) if match else None


def classify_gender(value):
    """Bucket a gender field into M / F / U, tolerating padding and long forms."""
    if isinstance(value, str):
        token = value.strip().upper()
        if token in ("M", "MALE"):
            return "M"
        if token in ("F", "FEMALE"):
            return "F"
    return "U"


def evidence_year(record, recorded):
    """Earliest year the record's own title or reason names, if it is earlier.

    ``None`` unless it beats ``recorded``. This is what catches a text dated by
    a later edition: both cldw2 runs put Celia Fiennes at 1888, the year Field
    and Tuer printed her, while saying 1698 in the reason field -- the year she
    actually rode north.
    """
    prose = " ".join(str(lookup(record, field) or "")
                     for field in (TITLE_FIELD, REASON_FIELD))
    years = [int(y) for y in ANY_YEAR_RE.findall(prose) if int(y) >= YEAR_FLOOR]
    earliest = min(years, default=None)
    if earliest is None or recorded is None or earliest >= recorded:
        return None
    return earliest


def resolve_sources(root, wanted=None):
    """(label, path) per run, in EXPERIMENTS order.

    ``wanted`` filters the runs, keeping EXPERIMENTS order whatever order it
    names them in, so the columns never depend on how --runs was typed.
    """
    sources = []
    for label, variant, run in EXPERIMENTS:
        if wanted and label not in wanted:
            continue
        sources.append((label, os.path.join(root, "data", "raw", variant, run,
                                            TEXTS_NAME)))
    return sources


def load_run(label, path):
    """One run's records, as dicts this script can group and match.

    Every record, not only the female-authored ones. The second table has to
    know whether a run's corpus holds a CLDW text at all before it can say the
    run lost her, and a run that found the text and recorded its author as a man
    holds it just as much as one that got the gender right. ``load_female``
    below takes the F ones for the first table.
    """
    loaded = []
    for record in read_jsonl(path):
        year = parse_year(lookup(record, YEAR_FIELD))
        title = str(lookup(record, TITLE_FIELD) or "").strip()
        loaded.append({
            "run": label,
            "gender": classify_gender(lookup(record, GENDER_FIELD)),
            "year": year,
            "composed": evidence_year(record, year),
            "title": title,
            "titles": (title,),
            "author": str(lookup(record, AUTHOR_FIELD) or "").strip(),
        })
    return loaded


def load_female(records):
    """The female-authored records among them."""
    return [record for record in records if record["gender"] == "F"]


def mend(text):
    """Undo one round of mis-decoding, in a string carrying the marks of it.

    LD80's metadata reaches this repo double-encoded, the accented letter in Ann
    Radcliffe's maiden name arriving as two characters, and these authors and
    titles get printed, so the accents are put back for display. Only strings holding the telltale characters are touched, and only
    if the second decode succeeds and leaves nothing unrepresentable behind, so
    a name that merely happens to hold one of them comes through unaltered. The
    file itself is left as it is: the doubling happens upstream, in the corpus's
    own metadata CSV, and is that file's to fix.
    """
    if not any(ch in text for ch in "\u00c2\u00c3\u00e2"):
        return text
    try:
        mended = text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    return text if "\ufffd" in mended else mended


def load_cldw(root):
    """The original CLDW, all 80 texts, in the same record shape.

    All 80 and not just the six by women, because the match is a competition:
    whether a record is Martineau's *Complete Guide to the English Lakes*
    depends on there being nothing in the reference it fits better, and dropping
    the 74 would let a record settle on the nearest woman to hand. The women are
    picked out afterwards, by ``gender``, once every record has been matched
    against the whole corpus it was drawn from.

    ``None``, rather than an empty list, if the metadata is not there: an
    absent file means the columns below cannot be filled, which is not the same
    claim as a corpus holding no women, and ``main`` reports the two differently.

    ``titles`` keeps both of LD80's title columns -- the catalogue short form
    and the title-page full one -- because a run may have copied either and the
    match takes the better of the two. On most rows the two are the same string,
    where the duplicate costs nothing and is dropped.
    """
    path = os.path.join(root, *LD80_PATH)
    if not os.path.exists(path):
        return None
    originals = []
    for record in read_jsonl(path):
        year = parse_year(lookup(record, LD80_YEAR_FIELD))
        composed = parse_year(lookup(record, LD80_COMP_FIELD))
        titles = [mend(str(lookup(record, field) or "").strip())
                  for field in LD80_TITLE_FIELDS]
        kept = [title for title in dict.fromkeys(titles) if title]
        originals.append({
            "run": LD80_LABEL,
            "gender": classify_gender(lookup(record, GENDER_FIELD)),
            "year": year,
            # Shown in brackets on the same terms as a run's: only where it is
            # earlier than the date the row is filed under.
            "composed": composed if composed and year and composed < year else None,
            "title": kept[0] if kept else "",
            "titles": tuple(kept) or ("",),
            "author": mend(str(lookup(record, AUTHOR_FIELD) or "").strip()),
        })
    return originals


# --- Comparison --------------------------------------------------------------
# The match below compares every record in every run with all 80 originals, so
# these four run into the hundreds of thousands of calls over a couple of
# thousand distinct strings. They are pure functions of their argument, so they
# are cached, which is the difference between the script taking a second and
# taking a quarter of a minute. The word sets come back frozen, so a caller
# cannot alter another caller's answer.
@lru_cache(maxsize=None)
def normalise(text):
    """Fold case, accents and punctuation away: "Wesmorland" still differs."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = text.replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def surname(author):
    """A grouping key for an author: the last real word of the name.

    "Ann Coward Wheeler" and "Ann Wheeler" both key on "wheeler", and "Mary
    Augusta Ward (Mrs Humphry Ward)" on "ward". An anonymous attribution keys
    on whatever identifying words the phrase carries -- "Anon. ('Editor of The
    Letters of Maria')" gives "maria" -- and a bare "Anon." keys on the empty
    string, which ``same_work`` then treats with extra care.
    """
    words = [word for word in normalise(author).split() if word not in NAME_NOISE]
    return words[-1] if words else ""


@lru_cache(maxsize=None)
def bare_title(title):
    """The title with its volume and part markers taken off."""
    return VOLUME_RE.sub(" ", normalise(title)).strip()


@lru_cache(maxsize=None)
def key_words(title):
    """The words of a title that could identify it."""
    return frozenset(word for word in bare_title(title).split()
                     if word not in STOP_WORDS and word not in COMMON_WORDS
                     and len(word) > 2)


@lru_cache(maxsize=None)
def numbers(title):
    """Counting words and figures left in a title once volumes are stripped."""
    return frozenset(word for word in bare_title(title).split()
                     if word in NUMBER_WORDS or word.isdigit())


def title_score(one, other, floor=0.0):
    """Whole-string similarity, or shared-distinctive-word containment.

    Containment is what catches a short title inside a long title-page one --
    "Robert Elsmere" against "Robert Elsmere, Volume 1". It needs at least two
    shared words and three a side: on one word it scores a perfect 1.0 off
    "Cumberland" alone.

    ``floor`` is the score the caller is looking for, and it buys speed without
    changing an answer: at or above the floor the score is exact, and below it
    the function may return any value that is also below, which lets it drop the
    whole-string comparison as soon as difflib's own cheap upper bounds on that
    comparison rule the floor out. Matching every record against all 80 of the
    CLDW's texts otherwise spends practically its whole time inside difflib, on
    pairs that are not remotely the same title.
    """
    mine, theirs = key_words(one), key_words(other)
    shared = mine & theirs
    containment = 0.0
    if len(shared) >= 2 and min(len(mine), len(theirs)) >= 3:
        containment = len(shared) / min(len(mine), len(theirs))
    matcher = SequenceMatcher(None, bare_title(one), bare_title(other))
    for bound in (matcher.real_quick_ratio, matcher.quick_ratio):
        if floor and max(containment, bound()) < floor:
            return containment
    return max(containment, matcher.ratio())


def same_work(one, other):
    """Are these two records versions of the same text?

    Called only on records already sharing a surname key, so the author is
    settled and what is left is title and date -- see the note on TITLE_MIN.
    """
    mine, theirs = numbers(one["title"]), numbers(other["title"])
    if mine and theirs and mine != theirs:
        return False  # "Three Familiar Dialogues" is not "Four Familiar Dialogues"
    if title_score(one["title"], other["title"]) >= TITLE_MIN:
        return True
    # Same author, same year, unlike titles: the same work under the title of a
    # volume that contains it, or of the edition it was reprinted in. Held back
    # from the anonymous bucket, where the shared key is an absence of a name
    # rather than a name, so a shared year would merge unrelated works.
    return bool(surname(one["author"])) and one["year"] is not None \
        and one["year"] == other["year"]


def group_works(records):
    """Merge the records into distinct works, earliest first.

    Surname first, to keep the comparison local -- no two records by different
    authors are ever compared -- then a union-find within each surname, so
    merging is transitive: a title that matches one member of a group joins the
    whole group, however it scores against the rest.
    """
    by_surname = {}
    for record in records:
        by_surname.setdefault(surname(record["author"]), []).append(record)

    works = []
    for members in by_surname.values():
        parent = list(range(len(members)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                if find(i) != find(j) and same_work(members[i], members[j]):
                    parent[find(i)] = find(j)

        clusters = {}
        for index, record in enumerate(members):
            clusters.setdefault(find(index), []).append(record)
        works.extend(clusters.values())

    works.sort(key=sort_key)
    return works


def sort_key(work):
    """Earliest recorded year, then author, then title -- and never a None year.

    A record with no readable year sorts last rather than crashing the sort;
    none of the five runs currently has one, but a re-run could.
    """
    years = [r["year"] for r in work if r["year"] is not None]
    return (min(years) if years else 10**4, best_author(work), best_title(work))


# --- Matching against the original CLDW --------------------------------------
# Whether a work was in the CLDW already is a different question from whether
# two of the runs found the same work, and it takes a different match. Grouping
# above compares records that already share a surname key, so the author is
# settled before a title is looked at; here nothing is settled, and the author
# has to be checked rather than assumed -- hence the two gates and the second,
# higher threshold for a pair whose names do not agree.
@lru_cache(maxsize=None)
def reference_surnames(author):
    """Every word that could be this author's surname.

    ``surname`` returns one, because grouping buckets records by it and a record
    can sit in only one bucket. Matching compares a pair at a time and can
    afford several candidates, which is what LD80's own spelling needs: it
    records Ann Radcliffe as "Ann Radcliffe (nee Ward)", where the last real
    word is her maiden name and not the name any run files her under. So a
    bracketed or parenthesised form yields its own candidate beside the plain
    one, and either may be the one that matches.
    """
    found = set()
    for chunk in re.split(r"[;/]| and ", author or ""):
        inner = re.findall(r"[\[(]([^\])]*)[\])]", chunk)
        plain = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", chunk)
        for piece in [plain] + inner:
            words = [word for word in normalise(piece).split()
                     if word not in NAME_NOISE and len(word) > 2]
            if words:
                found.add(words[-1])
    return frozenset(found)


@lru_cache(maxsize=None)
def given_initials(author):
    """First letters of the given names -- what tells two namesakes apart."""
    found = set()
    for chunk in re.split(r"[;/]| and ", author or ""):
        piece = re.sub(r"\([^)]*\)", " ", chunk)
        words = [word for word in normalise(piece).split()
                 if word not in NAME_NOISE]
        found.update(word[0] for word in words[:-1])
    return frozenset(found)


def same_author(one, other):
    """Shared surname *and* compatible given names.

    The surname on its own would put Ann Radcliffe, whom LD80 files under her
    maiden name Ward, together with Mary Augusta Ward. Initials settle it,
    except where one side gives none ("Mrs Linton" against "Eliza Lynn Linton"),
    where the surname has to stand alone and the title gate does the rest.
    """
    if not (reference_surnames(one) & reference_surnames(other)):
        return False
    mine, theirs = given_initials(one), given_initials(other)
    return not mine or not theirs or bool(mine & theirs)


def titles_score(one, other, floor=0.0):
    """The best title score over every pairing of two records' titles.

    A record may carry more than one title -- LD80 gives a short and a full
    form -- and any pairing counts, because a run may have copied either.
    ``floor`` is passed straight through, on the same terms as above.
    """
    return max(title_score(mine, theirs, floor)
               for mine in one["titles"] for theirs in other["titles"])


def match_original(record, originals):
    """Index of the CLDW text this record is a version of, or ``None``."""
    best_score, best_index = 0.0, None
    for index, original in enumerate(originals):
        # The name settles which threshold the title has to clear, so it is
        # read first and then handed to the title as the floor to beat.
        agrees = same_author(record["author"], original["author"])
        needed = TITLE_MIN if agrees else TITLE_ONLY_MIN
        score = titles_score(record, original, needed)
        if score < needed:
            continue
        # An author match outranks any title-only one, however close.
        ranked = score + (1.0 if agrees else 0.0)
        if ranked > best_score:
            best_score, best_index = ranked, index
    return best_index


def match_work(work, originals):
    """Index of the CLDW text a whole group is a version of, or ``None``.

    The records in a group disagree about title and author -- that is what made
    them worth grouping -- so one of them matching is enough. Where they match
    different originals, the reading most of them support wins, and the earlier
    original breaks a tie, so the answer never depends on the order the runs
    happened to be read in.
    """
    votes = Counter(index for index in (match_original(r, originals) for r in work)
                    if index is not None)
    if not votes:
        return None
    return max(votes, key=lambda index: (votes[index], -index))


def lost_originals(originals, matched, records):
    """The CLDW women the first table does not hold, and who holds them anyway.

    ``matched`` says which original each grouped work was matched to, so an
    original named there was found *and* recorded as female by at least one run
    and belongs in the first table. What is left over is either a text no run
    found at all or -- the more interesting case -- one a run found and filed
    under a male or unknown author, which is why each row carries the genders
    each run recorded rather than a tick.

    Every record is matched against the whole reference and then read off by
    original, rather than each original being offered the records on its own:
    the match is a competition, and a reference of one always wins it. Offered
    Martineau's *Lights of the English Lakes* alone, her *Complete Guide to the
    English Lakes* clears the title gate against it and the CLDW's two Martineaus
    come out looking like one text found twice.
    """
    holders = {}
    for record in records:
        index = match_original(record, originals)
        if index is None:
            continue
        holders.setdefault(index, {}).setdefault(record["run"], set()) \
            .add(record["gender"])
    recovered = {index for index in matched if index is not None}
    return [(original, holders.get(index, {}))
            for index, original in enumerate(originals)
            if original["gender"] == "F" and index not in recovered]


# --- Presenting a group ------------------------------------------------------
def commonest(values, prefer=None):
    """The value most of the runs used, then ``prefer``, then the fullest.

    Frequency leads because the runs disagree about names and titles far more
    often than they are wrong together: three records say "Sara Coleridge" and
    one says "Edith Coleridge", who edited the memoir rather than wrote it, and
    the majority is the better label for the row. Length breaks a tie, on the
    same reasoning as before -- the fuller form identifies the work -- so a
    two-way split still gives the more informative of the two.
    """
    counts = Counter(values)
    return max(counts, key=lambda v: (counts[v], bool(prefer and prefer(v)), len(v), v))


def best_title(work):
    """The title that best stands for the group.

    Volume markers are broken out of the tie-break rather than left to length:
    "Robert Elsmere, Volume 1" is longer than "Robert Elsmere" but names one
    half of the work the row is about, so a title without such a marker wins
    over one with it whenever they are equally common.
    """
    return commonest((r["title"] for r in work),
                     prefer=lambda t: not VOLUME_RE.search(normalise(t)))


def best_author(work):
    """The name that best stands for the group."""
    return commonest(r["author"] for r in work)


def date_cell(work):
    """The group's date: its recorded year, its span if the runs disagree.

    A bracketed year follows where the records name an earlier one of their
    own -- 1888 (1698) for Fiennes. It is the earliest such year in the group,
    and it is shown only as an annotation: nothing here is grouped or sorted
    by it.
    """
    years = sorted({r["year"] for r in work if r["year"] is not None})
    if not years:
        return "?"
    cell = str(years[0]) if len(years) == 1 else f"{years[0]}-{years[-1]}"
    composed = [r["composed"] for r in work if r["composed"] is not None]
    return f"{cell} ({min(composed)})" if composed else cell


def variants(work, field):
    """The distinct values of ``field`` across a group, fullest first."""
    seen = []
    for value in sorted({r[field] for r in work}, key=lambda v: (-len(v), v)):
        if value not in seen:
            seen.append(value)
    return seen


def truncate(text, width):
    return text if len(text) <= width else text[:width - 1] + "…"


# --- Output ------------------------------------------------------------------
def row_cells(marks, heads):
    """Tick cells laid out under their column heads."""
    return "".join(mark.rjust(len(head) + 2) for mark, head in zip(marks, heads))


def print_table(works, labels, width, matched=None, out=sys.stdout):
    """The pooled list: one row per distinct work, one tick column per run.

    ``matched`` is the index of the CLDW text each work was matched to, or
    ``None`` for each work that matches none; passing ``None`` for the whole
    list drops the ``cldw`` column, which is what happens when the metadata is
    not there to match against. It leads the tick columns, being the corpus the
    runs were working from rather than one of them.
    """
    heads = [COLUMN_HEADERS.get(label, label) for label in labels]
    legend = ", ".join(f"{head} = {label}" for head, label in zip(heads, labels))
    if matched is not None:
        heads = [LD80_HEADER] + heads
        legend = f"{LD80_HEADER} = {LD80_LABEL}, {legend}"
    print("Runs: " + legend, file=out)
    print(file=out)

    date_w = max([len(date_cell(w)) for w in works] + [len("date")]) + 2
    author_w = min(max([len(best_author(w)) for w in works] + [len("author")]), 34) + 2
    cols = "".join(head.rjust(len(head) + 2) for head in heads)
    header = (f"{'date':<{date_w}}{'author':<{author_w}}"
              f"{'title':<{width}}{cols}")
    print(header, file=out)
    print("-" * len(header), file=out)

    for index, work in enumerate(works):
        runs = {r["run"] for r in work}
        marks = [PRESENT if label in runs else ABSENT for label in labels]
        if matched is not None:
            marks = [PRESENT if matched[index] is not None else ABSENT] + marks
        print(f"{date_cell(work):<{date_w}}"
              f"{truncate(best_author(work), author_w - 2):<{author_w}}"
              f"{truncate(best_title(work), width - 2):<{width}}"
              f"{row_cells(marks, heads)}", file=out)

    print("-" * len(header), file=out)
    counts = [sum(1 for w in works if any(r["run"] == label for r in w))
              for label in labels]
    if matched is not None:
        counts = [sum(1 for index in matched if index is not None)] + counts
    print(f"{'':<{date_w}}{'':<{author_w}}"
          f"{f'{len(works)} distinct works':<{width}}"
          f"{row_cells([str(n) for n in counts], heads)}", file=out)


def print_lost(lost, labels, width, out=sys.stdout):
    """The CLDW's own women that the pooled list above does not hold.

    The cells are the ``cldw`` column read the other way: a dot where the run's
    corpus does not hold the text at all, and otherwise the gender that run
    recorded for it -- M where the run found her and filed her as a man, U where
    it left the author unknown. A row that is all dots is a text every run
    missed outright.
    """
    print("\nFemale-authored texts in the original CLDW that the list above does "
          "not hold.", file=out)
    if not lost:
        print("  None: the runs' female-authored records account for every one "
              "of them.", file=out)
        return
    print("A cell is the gender the run recorded, where the run holds the text "
          "at all:", file=out)
    print(file=out)

    heads = [COLUMN_HEADERS.get(label, label) for label in labels]
    date_w = max([len(date_cell([o])) for o, _ in lost] + [len("date")]) + 2
    author_w = min(max([len(o["author"]) for o, _ in lost] + [len("author")]), 34) + 2
    cols = "".join(head.rjust(len(head) + 2) for head in heads)
    header = (f"{'date':<{date_w}}{'author':<{author_w}}"
              f"{'title':<{width}}{cols}")
    print(header, file=out)
    print("-" * len(header), file=out)

    for original, holders in lost:
        marks = ["".join(sorted(holders.get(label, ()))) or ABSENT
                 for label in labels]
        print(f"{date_cell([original]):<{date_w}}"
              f"{truncate(original['author'], author_w - 2):<{author_w}}"
              f"{truncate(original['title'], width - 2):<{width}}"
              f"{row_cells(marks, heads)}", file=out)

    print("-" * len(header), file=out)
    counts = [sum(1 for _, holders in lost if label in holders) for label in labels]
    print(f"{'':<{date_w}}{'':<{author_w}}"
          f"{f'{len(lost)} lost, of which the run holds:':<{width}}"
          f"{row_cells([str(n) for n in counts], heads)}", file=out)


def print_audit(works, out=sys.stdout):
    """Every group with more than one form of its title, author or date.

    The merges are a judgement call -- see ``same_work`` -- and this is how to
    check it: each line below is a record this script decided was another
    record's twin. A group whose variants are not in fact the same text is a
    merge to tighten, and one work appearing as two groups is one to loosen.
    """
    print("\nMerged records, group by group "
          "(only groups holding more than one distinct form):", file=out)
    for work in works:
        titles, authors = variants(work, "title"), variants(work, "author")
        years = sorted({r["year"] for r in work if r["year"] is not None})
        if len(titles) == 1 and len(authors) == 1 and len(years) <= 1:
            continue
        print(f"\n  {date_cell(work)}  {best_author(work)}", file=out)
        for record in sorted(work, key=lambda r: (r["year"] or 0, r["run"])):
            print(f"    {record['year']}  {record['run']:<23}"
                  f"{record['author']}  --  {record['title']}", file=out)
        duplicated = sorted({r["run"] for r in work
                             if sum(1 for o in work if o["run"] == r["run"]) > 1})
        for label in duplicated:
            print(f"    note: {label} holds this work more than once", file=out)


def print_cldw_audit(works, matched, originals, out=sys.stdout):
    """Every work matched to a text in the original CLDW, beside its match.

    The ``cldw`` column is a judgement call in the same way the merges are --
    see ``match_original`` -- so it is checkable the same way: each pair below is
    a work this script decided was one of the CLDW's own texts. A pair that is
    not in fact the same text is a match to tighten; a CLDW text listed as lost
    that the runs plainly did hold is one to loosen.
    """
    print("\nWorks matched to the original CLDW, and what they matched:", file=out)
    pairs = [(work, originals[index])
             for work, index in zip(works, matched) if index is not None]
    if not pairs:
        print("  None.", file=out)
        return
    for work, original in pairs:
        print(f"\n  {date_cell(work)}  {best_author(work)}  --  "
              f"{best_title(work)}", file=out)
        print(f"    CLDW  {date_cell([original])}  {original['author']}  --  "
              f"{original['title']}", file=out)


def write_csv(works, labels, path, matched=None, originals=None):
    """One row per distinct work, with a column per run and the variants kept.

    The presence columns hold 1/0 rather than a tick, so the file drops
    straight into a spreadsheet or a dataframe. ``in_cldw`` is the table's
    ``cldw`` column, and the two trailing columns name the CLDW text it matched,
    so a match can be checked from the file as well as from ``--audit``. All
    three are left empty, rather than filled with a 0 that would read as "not in
    the CLDW", where there was no metadata to match against.
    """
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["year", "year_last", "composed", "author", "title",
                         "n_runs", "n_records", "in_cldw"]
                        + list(labels)
                        + ["titles_seen", "authors_seen",
                           "cldw_author", "cldw_title"])
        for index, work in enumerate(works):
            years = sorted({r["year"] for r in work if r["year"] is not None})
            composed = [r["composed"] for r in work if r["composed"] is not None]
            runs = {r["run"] for r in work}
            original = None if matched is None or matched[index] is None \
                else originals[matched[index]]
            writer.writerow([
                years[0] if years else "",
                years[-1] if years else "",
                min(composed) if composed else "",
                best_author(work), best_title(work), len(runs), len(work),
                "" if matched is None else int(matched[index] is not None),
            ] + [1 if label in runs else 0 for label in labels]
                + [" | ".join(variants(work, "title")),
                   " | ".join(variants(work, "author")),
                   original["author"] if original else "",
                   original["title"] if original else ""])


def write_lost_csv(lost, labels, path):
    """One row per CLDW woman the pooled list does not hold.

    A run column holds the gender that run recorded for the text, empty where
    the run does not hold it at all -- the printed table's cells, unabbreviated.
    """
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["year", "composed", "author", "title", "n_runs_holding"]
                        + list(labels))
        for original, holders in lost:
            writer.writerow([
                original["year"] or "", original["composed"] or "",
                original["author"], original["title"],
                sum(1 for label in labels if label in holders),
            ] + ["/".join(sorted(holders.get(label, ()))) for label in labels])


def main(argv=None):
    default_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=default_root,
                        help="repo root holding data/raw (default: %(default)s)")
    parser.add_argument("--runs", default=None,
                        help="comma-separated run labels to include "
                             f"(default: all of {', '.join(l for l, _, _ in EXPERIMENTS)})")
    parser.add_argument("--width", type=int, default=62,
                        help="title column width (default: %(default)s)")
    parser.add_argument("--csv", default=None,
                        help="also write the list to this CSV, one row per work; "
                             "the CLDW texts the list misses go beside it, in "
                             "<name>-cldw-lost.csv")
    parser.add_argument("--audit", action="store_true",
                        help="print every group this script merged and every CLDW "
                             "text it matched, to check the judgements")
    args = parser.parse_args(argv)

    wanted = None
    if args.runs:
        wanted = [label.strip() for label in args.runs.split(",") if label.strip()]
        known = {label for label, _, _ in EXPERIMENTS}
        unknown = [label for label in wanted if label not in known]
        if unknown:
            sys.exit(f"unknown run(s): {', '.join(unknown)}\n"
                     f"known runs: {', '.join(sorted(known))}")

    # Every record of every run, so the second table can tell a text no run
    # found from one a run found and mis-gendered; the first table takes the
    # female-authored ones out of the same pile.
    holdings, records, labels = [], [], []
    for label, path in resolve_sources(args.root, wanted):
        if not os.path.exists(path):
            print(f"skipping {label}: no {TEXTS_NAME} under {os.path.dirname(path)}",
                  file=sys.stderr)
            continue
        loaded = load_run(label, path)
        found = load_female(loaded)
        if not found:
            print(f"note: {label}: no female-authored records in {path}", file=sys.stderr)
        labels.append(label)
        holdings.extend(loaded)
        records.extend(found)

    if not records:
        sys.exit("no female-authored texts found; pass --root")

    originals = load_cldw(args.root)
    if originals is None:
        print(f"note: no CLDW metadata under "
              f"{os.path.join(args.root, *LD80_PATH[:-1])}; "
              f"the {LD80_HEADER} column and the list of texts the runs lost "
              f"are both left out", file=sys.stderr)

    works = group_works(records)
    matched = None if originals is None \
        else [match_work(work, originals) for work in works]
    print_table(works, labels, args.width, matched)
    print(f"\n{len(records)} female-authored records across {len(labels)} run(s), "
          f"merging to {len(works)} distinct works.")

    lost = []
    if originals is not None:
        lost = lost_originals(originals, matched, holdings)
        print_lost(lost, labels, args.width)
        women = sum(1 for original in originals if original["gender"] == "F")
        print(f"\n{women} of the original CLDW's {len(originals)} texts are "
              f"female-authored; the list above holds {women - len(lost)} "
              f"of them.")

    if args.audit:
        print_audit(works)
        if originals is not None:
            print_cldw_audit(works, matched, originals)

    if args.csv:
        os.makedirs(os.path.dirname(os.path.abspath(args.csv)), exist_ok=True)
        write_csv(works, labels, args.csv, matched, originals)
        print(f"\nwrote {args.csv}")
        if originals is not None:
            stem, extension = os.path.splitext(args.csv)
            lost_path = f"{stem}-cldw-lost{extension or '.csv'}"
            write_lost_csv(lost, labels, lost_path)
            print(f"wrote {lost_path}")


if __name__ == "__main__":
    main()
