#!/usr/bin/env python3
"""Pool every corpus in the project into one list of distinct works.

The project holds six corpora of Lake District writing: the original CLDW --
the 80 texts of the LD80 metadata -- and the five claude-code runs of
``01-reb-analyse.py``, two of which rebuilt a corpus of 80 from scratch
(``cldw2-*``) while three were given the original's 80 and asked for more
(``universe-*``). Between them they name 1176 records, which are 549 distinct
works. This script merges the records that are the same text and prints what
is left: one row per distinct work, earliest first, with its date, author,
title, the gender and genre the corpora recorded for it, and a tick under every
corpus that holds it. The CSV beside it carries the same rows with every
variant form, download URL and reason the records gave, so the list is a
working inventory of the texts this project has seen rather than only a count
of them.

The merge is the whole difficulty. The same work reaches this script under
different titles ("The Lakes of England" / "The Lakes of England, illustrated
with Eighteen Coloured Etchings"), under different forms of its author's name
("Eliza Lynn Linton" / "Mrs Lynn Linton", "Joseph Budworth" / "Joseph Budworth
(Palmer)"), under different attributions altogether (the 1780 *Choice
Collection of Poems in the Cumberland Dialect* is anonymous in one run and
Robert Nelson's in another), and under different years, because a run dates a
text by the edition it points at and the runs picked different editions.

``same_work`` below is the judgement that merges them. It is this script's
own, and it is stricter than either of the two already in the repo, because
pooling six corpora rather than two makes over-merging the expensive mistake:
a missed merge shows up as two adjacent rows a reader can see are one work,
while a wrong merge silently deletes a text from an inventory that is supposed
to hold everything. Run over all 1176 records, ``ub.py``'s rule -- calibrated
on the 645 records of two universe runs -- chains whole families of an author's
work into one row: Rawnsley's *Sonnets at the English Lakes*, *Literary
Associations of the English Lakes* and *Life and Nature at the English Lakes*
become one work, as do Ferguson's *History of Cumberland* and his *History of
Westmorland*, and Black's *Picturesque Guide* and *Economical Guide*. Each of
those pairs is alike in every word the corpus repeats everywhere -- lakes,
English, guide, history, Cumberland -- and differs in one or two that actually
name the book.

So this script's rule turns on those words rather than on whole-string
similarity: see ``conflicting``. Titles that each carry a substantial word the
other lacks are different works, whatever they otherwise share. The comparison
of words is deliberately fuzzy, because the alternative is to split on a
spelling: LD80 gives Budworth's *Fortnight's Ramble to the Lakes in
Wesmorland*, the runs give *Westmorland*, and the corpus writes Westmoreland
both ways throughout.

Erring that way leaves a handful of pairs in the list that a reader will see
are one work: Camden's *Britannia* under two of its translations, Todd's 1710
letter to Halley described once by its recipient and once by his office,
Marshall's *Review of the Reports to the Board of Agriculture* against the same
book as a *Review and Abstract of the County Reports*, Lonsdale's life of John
Heysham under two of its appendices, and Hudson's 1842 guide in the editions
carrying three and five of Sedgwick's letters. Each of those differs in a
clause the other does not have, which is exactly what the gate is there to
notice, and the alternative rule that joins them also joins Ferguson's *History
of Cumberland* to his *History of Westmorland*. ``--audit`` prints every merge
the script did make, so the judgement can be read rather than trusted.

Run from anywhere:
    ./union.py [--csv out.csv] [--audit] [--sensitivity] [--runs LABEL,...]
"""

import argparse
import csv
import importlib.util
import os
import sys
from collections import Counter
from difflib import SequenceMatcher
from functools import lru_cache

TEXTS_NAME = "texts.jsonl"

# The normalisation and scoring primitives come from find-female.py, and the
# author-name handling from ub.py, rather than being copied: the stop-word and
# common-word lists, the volume stripping, the title score and the surname
# candidates are all calibrated against hand-checked pairs from this same
# corpus, and a third copy of them here would drift from the first two. Only
# the *rule* built on top of them is local -- see the module docstring. The
# imports go through importlib because one of the two file names carries a
# hyphen, and ub.py is loaded rather than find-female.py directly so that all
# three scripts share one set of primitives and one set of caches.
_UB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ub.py")


def _load_helpers(path=_UB_PATH):
    """ub.py as a module, and find-female.py through it."""
    if not os.path.exists(path):
        sys.exit(f"cannot find {path}, which this script borrows its "
                 f"matching primitives from")
    spec = importlib.util.spec_from_file_location("_ub_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ub = _load_helpers()
ff = ub.ff

# Borrowed, and named here so the debt is explicit and a rename upstream fails
# loudly at import instead of silently changing a published number.
normalise = ff.normalise
bare_title = ff.bare_title
numbers = ff.numbers
title_score = ff.title_score
read_jsonl = ff.read_jsonl
lookup = ff.lookup
parse_year = ff.parse_year
classify_gender = ff.classify_gender
evidence_year = ff.evidence_year
mend = ff.mend
author_words = ub.author_words
same_author = ub.same_author
STOP_WORDS = ff.STOP_WORDS
VOLUME_RE = ff.VOLUME_RE

TITLE_MIN = ff.TITLE_MIN            # 0.60: alike enough on their own
TITLE_ONLY_MIN = ff.TITLE_ONLY_MIN  # 0.85: alike enough without an agreeing name
YEAR_TITLE_MIN = ub.YEAR_TITLE_MIN  # 0.40: alike enough given an agreeing year

# The five runs, under the labels and in the order the other scripts use, with
# the corpus they were all working from at the head of the list: it is the one
# corpus here that was not generated, so it leads the columns.
EXPERIMENTS = ff.EXPERIMENTS
CLDW_LABEL = "cldw"
CLDW_NAME = "Original CLDW"
COLUMN_HEADERS = dict(ff.COLUMN_HEADERS)
COLUMN_HEADERS[CLDW_LABEL] = CLDW_LABEL

CLDW_PATH = ff.LD80_PATH
CLDW_ID_FIELD = "ID"
CLDW_YEAR_FIELD = ff.LD80_YEAR_FIELD
CLDW_COMP_FIELD = ff.LD80_COMP_FIELD
CLDW_TITLE_FIELDS = ff.LD80_TITLE_FIELDS
CLDW_GENRE_FIELD = "Genre"
CLDW_NOTE_FIELD = "Notes & Additional Information"

TITLE_FIELD = ff.TITLE_FIELD
AUTHOR_FIELD = ff.AUTHOR_FIELD
YEAR_FIELD = ff.YEAR_FIELD
GENDER_FIELD = ff.GENDER_FIELD
REASON_FIELD = ff.REASON_FIELD
GENRE_FIELD = "genre"
REPOSITORY_FIELD = "repository"
URL_FIELD = "download_url"

PRESENT = "x"
ABSENT = "."


# --- The rule ----------------------------------------------------------------
# Two words are the same word if they are spelt nearly alike. The threshold has
# to clear the spelling variants this corpus is full of -- Westmorland against
# Wesmorland (0.96) and against Westmoreland (0.96), Machell against Machel
# (0.93) -- without reaching the county names that tell two books apart:
# Cumberland against Westmorland scores 0.63, Cumberland against Northumberland
# 0.80. The length guard keeps a short word from matching a long one on a
# shared stem ("lake" against "lakeland") before the ratio is ever computed.
WORD_MIN = 0.85
SPELLING_SLACK = 3
# A title with fewer words of its own than this cannot veto a match on its own: a
# bare "Poems" or "Odes" says too little to be evidence that two records are
# different works, and the similarity gates below are left to decide.
CONTENT_MIN = 1
# A word of five letters or more inside another word is the same word split or
# joined: Howitt's "Battle Fields" against his "Battlefields", a "Note-book"
# against a "notebook". Shorter than that and the containment is an accident --
# "lake" sits inside "lakeland", "moor" inside "moorland".
COMPOUND_MIN = 5
# Two titles this alike as whole strings are one title however their words
# differ, and a conflict between them is a slip rather than evidence: the runs
# give the same 1873 Geological Survey memoir as covering "the Furness District"
# and "the Lake District" (0.95), the same 1888 anthology as taking in Durham
# and Yorkshire (0.95), and MacRitchie's 1795 tour as a Diary and a Journal
# (0.89). The threshold sits above every pair of genuinely different works this
# corpus holds that the gates otherwise separate -- Jefferson's histories of
# Leath Ward and of Allerdale Ward score 0.86, Ward's glaciation memoir against
# his geology of the same ground 0.84 -- with the one exception the counting
# gate above catches first, Ann Wheeler's Three and Four Familiar Dialogues
# (0.92).
NEAR_IDENTICAL = 0.89


@lru_cache(maxsize=None)
def title_words(title):
    """Everything a title carries but its volume markers and grammatical words.

    Unlike ``key_words``, the words this corpus repeats everywhere are *kept*.
    That is the point of the set: "lakes" and "English" identify nothing on
    their own, but *Sonnets at the English Lakes* and *Life and Nature at the
    English Lakes* are told apart by "sonnets" against "life" and "nature",
    and *A History of Cumberland* from *A History of Westmorland* by the county
    alone. Dropping the common words, as a search for distinctive ones must,
    leaves the second pair with nothing left to differ in.
    """
    return frozenset(word for word in bare_title(title).split()
                     if word not in STOP_WORDS and len(word) > 2)


@lru_cache(maxsize=None)
def names_of(author):
    """The author's own words, ``author_words`` cached for the pair loop."""
    return author_words(author)


@lru_cache(maxsize=None)
def close_words(one, other):
    """Are these two words the same word, allowing for how it may be spelt?"""
    if one == other:
        return True
    if len(one) >= COMPOUND_MIN and one in other:
        return True
    if len(other) >= COMPOUND_MIN and other in one:
        return True
    if abs(len(one) - len(other)) > SPELLING_SLACK:
        return False
    return SequenceMatcher(None, one, other).ratio() >= WORD_MIN


@lru_cache(maxsize=None)
def near_identical(one, other):
    """Are the two titles the same string but for a word or a spelling?

    Whole-string similarity, which is the measure that ``conflicting`` refuses
    to trust on its own and the right one to overrule it with: a conflict
    matters where the titles are merely alike, and says nothing where they are
    the same sentence with a word changed.
    """
    return SequenceMatcher(None, bare_title(one),
                           bare_title(other)).ratio() >= NEAR_IDENTICAL


def unmatched(mine, theirs):
    """The words of one title that nothing in the other answers to."""
    return frozenset(word for word in mine
                     if not any(close_words(word, other) for other in theirs))


def conflicting(one, other):
    """Does each title carry a word of its own that the other lacks?

    This is the gate that does the work here, and it is a negative one: it
    never joins two records, it only refuses to let the similarity gates in
    ``same_form`` join them. A title that merely says *more* than another does
    not conflict
    with it -- "The Lakes of England" against "The Lakes of England,
    illustrated with Eighteen Coloured Etchings", or LD80's short title against
    its own title-page full one -- because everything the shorter one says, the
    longer one says too. Two titles conflict only when each names something the
    other does not, which is what an author's two different books do and what
    two records of one book, however differently they abbreviate it, do not.

    The name the two records *agree* on comes off both titles first. A work
    that names its author in its title -- "Harriet Martineau's Autobiography"
    against the same book as "Autobiography, with Memorials by Maria Weston
    Chapman" -- would otherwise conflict on the author's own name, which is the
    one thing here that is not in dispute. Only the shared part goes: where the
    records name different authors, the names are exactly what tells the titles
    apart, and stripping each record's own would merge the *Transactions of the
    Wordsworth Society* into the *Transactions of the Cumberland and
    Westmorland Antiquarian and Archaeological Society*, and Sara Coleridge's
    *Memoir and Letters* into the *Letters of Samuel Taylor Coleridge*.

    A title with nothing left after all that cannot conflict with anything: it
    is not evidence, and it is not treated as any.
    """
    shared = names_of(one["author"]) & names_of(other["author"])
    mine = title_words(one["title"]) - shared
    theirs = title_words(other["title"]) - shared
    if len(mine) < CONTENT_MIN or len(theirs) < CONTENT_MIN:
        return False
    return bool(unmatched(mine, theirs)) and bool(unmatched(theirs, mine))


def same_form(one, other, year_title_min=YEAR_TITLE_MIN, use_year=True,
              use_conflict=True):
    """Are these two (title, author, year) readings the same text?

    Three gates, in order:

    1. Counting words must not disagree: Ann Wheeler's dialect dialogues come
       "in Three Familiar Dialogues" (1790) and "in Four Familiar Dialogues"
       (1802) and share every other word, and Hudson's guide of 1842 carries
       three of Sedgwick's letters in one edition and five in another. A title
       that merely names a number the other leaves out does not disagree with
       it: "December 16, 1772" against "December 1772" is the same day.
    2. The titles must be alike enough. Where the corpora agree about the
       author, that is TITLE_MIN on its own, or ``year_title_min`` with an
       agreeing year, which is what carries a record filed under the title of
       the volume that contains it. Where they do not agree about the author,
       it is the higher TITLE_ONLY_MIN *and* an agreeing year: the corpora
       disagree about authorship more often than one would expect -- a work
       credited once to its editor and once to its subject, once to a publisher
       and once to "Anon." -- but the century is also full of guides whose
       titles differ only in whose they are, so the name failing leaves the
       year as the only other evidence there is.
    3. The titles must not then conflict -- see ``conflicting`` -- unless they
       are near enough identical for the conflict to be a slip. This gate is
       consulted last because it can only ever refuse a merge, so a pair the
       similarity gates have already rejected need not be put to it.
    """
    mine, theirs = numbers(one["title"]), numbers(other["title"])
    if mine and theirs and not (mine <= theirs or theirs <= mine):
        return False

    agreed_year = one["year"] is not None and one["year"] == other["year"]
    if not same_author(one, other):
        if not agreed_year:
            return False
        needed = TITLE_ONLY_MIN
    elif agreed_year and use_year:
        needed = year_title_min
    else:
        needed = TITLE_MIN
    if title_score(one["title"], other["title"], needed) < needed:
        return False

    return not use_conflict or not conflicting(one, other) \
        or near_identical(one["title"], other["title"])


def same_work(one, other, **rule):
    """The same, over records that may carry more than one form of their title.

    LD80 gives each text a catalogue short title and a title-page full one, and
    a run may have copied either or neither, so every pairing of the two
    records' title forms counts and one of them agreeing is enough.
    """
    return any(same_form(mine, theirs, **rule)
               for mine in one["forms"] for theirs in other["forms"])


# --- Loading -----------------------------------------------------------------
def forms(titles, author, year):
    """The (title, author, year) readings a record offers the rule."""
    return tuple({"title": title, "author": author, "year": year}
                 for title in titles)


def resolve_sources(root, wanted=None):
    """(label, path) per run, in EXPERIMENTS order.

    ``wanted`` filters the runs, keeping that order whatever order it names
    them in, so the columns never depend on how --runs was typed.
    """
    sources = []
    for label, variant, run in EXPERIMENTS:
        if wanted and label not in wanted:
            continue
        sources.append((label, os.path.join(root, "data", "raw", variant, run,
                                            TEXTS_NAME)))
    return sources


def load_run(label, path):
    """One run's records, in the shape this script merges and prints.

    Everything the run recorded is kept, not only the fields the merge reads:
    the genre, the repository and download URL where the run gave one, and the
    reason it gave for including the text. The list this script prints is meant
    to be usable as an inventory, and those are what make a row actionable.
    """
    loaded = []
    for index, record in enumerate(read_jsonl(path)):
        year = parse_year(lookup(record, YEAR_FIELD))
        title = str(lookup(record, TITLE_FIELD) or "").strip()
        author = str(lookup(record, AUTHOR_FIELD) or "").strip()
        loaded.append({
            "source": label,
            "line": index + 1,
            "title": title,
            "titles": (title,),
            "forms": forms((title,), author, year),
            "author": author,
            "year": year,
            "composed": evidence_year(record, year),
            "gender": classify_gender(lookup(record, GENDER_FIELD)),
            "genre": str(lookup(record, GENRE_FIELD) or "").strip(),
            "repository": str(lookup(record, REPOSITORY_FIELD) or "").strip(),
            "url": str(lookup(record, URL_FIELD) or "").strip(),
            "reason": str(lookup(record, REASON_FIELD) or "").strip(),
            "cldw_id": "",
        })
    return loaded


def load_cldw(root):
    """The original CLDW's 80 texts, in the same shape.

    ``None``, rather than an empty list, if the metadata is not there: an
    absent file means the ``cldw`` column cannot be filled, which is a
    different claim from a column of dots, and ``main`` reports the two
    differently.

    Both of LD80's title columns are kept -- the catalogue short form and the
    title-page full one -- because a run may have copied either and the merge
    takes the better of the two. On most rows they are the same string, where
    the duplicate costs nothing and is dropped. ``mend`` puts back the accents
    that the metadata lost to a double encoding upstream; the file itself is
    left as it is.
    """
    path = os.path.join(root, *CLDW_PATH)
    if not os.path.exists(path):
        return None
    loaded = []
    for index, record in enumerate(read_jsonl(path)):
        year = parse_year(lookup(record, CLDW_YEAR_FIELD))
        composed = parse_year(lookup(record, CLDW_COMP_FIELD))
        author = mend(str(lookup(record, AUTHOR_FIELD) or "").strip())
        titles = [mend(str(lookup(record, field) or "").strip())
                  for field in CLDW_TITLE_FIELDS]
        kept = tuple(title for title in dict.fromkeys(titles) if title) or ("",)
        loaded.append({
            "source": CLDW_LABEL,
            "line": index + 1,
            "title": kept[0],
            "titles": kept,
            "forms": forms(kept, author, year),
            "author": author,
            "year": year,
            # Shown in brackets on the same terms as a run's: only where it is
            # earlier than the year the row is filed under.
            "composed": composed if composed and year and composed < year else None,
            "gender": classify_gender(lookup(record, GENDER_FIELD)),
            "genre": str(lookup(record, CLDW_GENRE_FIELD) or "").strip(),
            "repository": "",
            "url": "",
            "reason": str(lookup(record, CLDW_NOTE_FIELD) or "").strip(),
            "cldw_id": str(lookup(record, CLDW_ID_FIELD) or "").strip(),
        })
    return loaded


# --- Merging -----------------------------------------------------------------
def group_records(records, **rule):
    """Merge the records into distinct works, earliest first.

    Every pair is compared, rather than only pairs bucketed together by
    surname, for ub.py's reason: bucketing on one surname would undo the gate
    that matches records the corpora credit to different authors, and those
    pairs would never meet to be compared. Twelve hundred records is seven
    hundred thousand pairs, which the gates clear in well under a minute.

    The union-find makes merging transitive, so a record matching any member of
    a group joins the whole group. Transitivity is why the conflict gate has to
    be as strict as it is: with six corpora describing the same author's shelf,
    a rule that lets one loose pair through merges everything either record
    would have matched separately.
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
    works = list(clusters.values())
    works.sort(key=sort_key)
    return works


def sort_key(work):
    """Earliest recorded year, then author, then title -- and never a None year.

    A record with no readable year sorts last rather than crashing the sort.
    """
    years = [r["year"] for r in work if r["year"] is not None]
    return (min(years) if years else 10**4, best_author(work), best_title(work))


# --- Presenting a group ------------------------------------------------------
def commonest(values, prefer=None):
    """The value most of the corpora used, then ``prefer``, then the fullest.

    Frequency leads because the corpora disagree about names and titles far
    more often than they are wrong together, and the majority reading is the
    better label for a row. Length breaks a tie, the fuller form being the more
    identifying one.
    """
    counts = Counter(values)
    return max(counts, key=lambda v: (counts[v], bool(prefer and prefer(v)),
                                      len(v), v))


def best_title(work):
    """The title that best stands for the group.

    Volume markers are broken out of the tie-break rather than left to length:
    "Robert Elsmere, Volume 1" is longer than "Robert Elsmere" but names one
    third of the work the row is about, so a title without such a marker wins
    over one with it whenever they are equally common.
    """
    return commonest((r["title"] for r in work),
                     prefer=lambda t: not VOLUME_RE.search(normalise(t)))


def best_author(work):
    """The name that best stands for the group."""
    return commonest(r["author"] for r in work)


def best_genre(work):
    """The genre most of the corpora gave it, ignoring the ones that gave none.

    The corpora name genres in their own words -- "Travelogue", "Travel
    writing", "Travel narrative" -- so this is a label for the row and not a
    classification; the CSV keeps every form that was used.
    """
    named = [r["genre"] for r in work if r["genre"]]
    return commonest(named) if named else ""


def best_gender(work):
    """The gender most of the corpora recorded, preferring a definite answer.

    A row where one corpus says F and another U is female-authored as far as
    this list is concerned: U is an absence of a reading, not a competing one.
    A row where one says F and another M is a genuine disagreement, and
    ``gender_note`` marks it so the CSV can carry both.
    """
    known = [r["gender"] for r in work if r["gender"] != "U"]
    return commonest(known) if known else "U"


def gender_note(work):
    """The genders recorded for a work, where the corpora disagree about it."""
    recorded = {r["gender"] for r in work if r["gender"] != "U"}
    return "/".join(sorted(recorded)) if len(recorded) > 1 else ""


def date_cell(work):
    """The group's date: its recorded year, or its span if the corpora disagree.

    A bracketed year follows where the records name an earlier one of their
    own -- 1888 (1698) for Celia Fiennes, printed by Field and Tuer two
    centuries after she rode north. It is an annotation only: nothing here is
    grouped or sorted by it.
    """
    years = sorted({r["year"] for r in work if r["year"] is not None})
    if not years:
        return "?"
    cell = str(years[0]) if len(years) == 1 else f"{years[0]}-{years[-1]}"
    composed = [r["composed"] for r in work if r["composed"] is not None]
    return f"{cell} ({min(composed)})" if composed else cell


def variants(work, field):
    """The distinct values of ``field`` across a group, fullest first."""
    return order(r[field] for r in work)


def title_variants(work):
    """Every form of the title in a group, LD80's two columns included."""
    return order(title for record in work for title in record["titles"])


def order(values):
    """The distinct values, fullest first, with the empty ones dropped."""
    seen = []
    for value in sorted(set(values), key=lambda v: (-len(v), v)):
        if value and value not in seen:
            seen.append(value)
    return seen


def truncate(text, width):
    return text if len(text) <= width else text[:width - 1] + "…"


# --- Output ------------------------------------------------------------------
def row_cells(marks, heads):
    """Tick cells laid out under their column heads."""
    return "".join(mark.rjust(len(head) + 2) for mark, head in zip(marks, heads))


def print_table(works, labels, width, genre_width, out=sys.stdout):
    """The pooled list: one row per distinct work, one tick column per corpus."""
    heads = [COLUMN_HEADERS.get(label, label) for label in labels]
    names = {CLDW_LABEL: CLDW_NAME}
    legend = ", ".join(f"{head} = {names.get(label, label)}"
                       for head, label in zip(heads, labels))
    print("Corpora: " + legend, file=out)
    print(file=out)

    date_w = max([len(date_cell(w)) for w in works] + [len("date")]) + 2
    author_w = min(max([len(best_author(w)) for w in works] + [len("author")]),
                   30) + 2
    cols = "".join(head.rjust(len(head) + 2) for head in heads)
    header = (f"{'date':<{date_w}}{'author':<{author_w}}{'title':<{width}}"
              f"{'g':<3}{'genre':<{genre_width}}{cols}")
    print(header, file=out)
    print("-" * len(header), file=out)

    for work in works:
        held = {r["source"] for r in work}
        marks = [PRESENT if label in held else ABSENT for label in labels]
        print(f"{date_cell(work):<{date_w}}"
              f"{truncate(best_author(work), author_w - 2):<{author_w}}"
              f"{truncate(best_title(work), width - 2):<{width}}"
              f"{best_gender(work):<3}"
              f"{truncate(best_genre(work), genre_width - 2):<{genre_width}}"
              f"{row_cells(marks, heads)}", file=out)

    print("-" * len(header), file=out)
    counts = [sum(1 for w in works if any(r["source"] == label for r in w))
              for label in labels]
    print(f"{'':<{date_w}}{'':<{author_w}}"
          f"{f'{len(works)} distinct works':<{width}}{'':<3}{'':<{genre_width}}"
          f"{row_cells([str(n) for n in counts], heads)}", file=out)


def print_summary(works, labels, totals, out=sys.stdout):
    """What each corpus contributed to the pool, and what only it holds."""
    print(file=out)
    print(f"{'corpus':<26}{'records':>9}{'works':>8}{'only here':>11}"
          f"{'shared':>8}", file=out)
    print("-" * 62, file=out)
    for label in labels:
        held = [w for w in works if any(r["source"] == label for r in w)]
        alone = [w for w in held if {r["source"] for r in w} == {label}]
        name = CLDW_NAME if label == CLDW_LABEL else label
        print(f"{name:<26}{totals[label]:>9}{len(held):>8}{len(alone):>11}"
              f"{len(held) - len(alone):>8}", file=out)
    print("-" * 62, file=out)
    print(f"{'union':<26}{sum(totals.values()):>9}{len(works):>8}", file=out)


def print_audit(works, out=sys.stdout):
    """Every group holding more than one record, with every form it was given.

    The merges are a judgement call -- see ``same_work`` -- and this is how to
    check it: each line below is a record this script decided was another
    record's twin. A group whose records are not in fact the same text is a
    merge to tighten, and one work appearing as two groups is one to loosen.
    """
    print("\nMerged records, group by group "
          "(every group holding more than one record):", file=out)
    for work in works:
        if len(work) == 1:
            continue
        print(f"\n  {date_cell(work)}  {best_author(work)}", file=out)
        for record in sorted(work, key=lambda r: (r["year"] or 0, r["source"])):
            print(f"    {record['year']}  {record['source']:<23}"
                  f"{record['author']}  --  {record['title']}", file=out)
        repeated = sorted({r["source"] for r in work
                           if sum(1 for o in work if o["source"] == r["source"]) > 1})
        for label in repeated:
            print(f"    note: {label} holds this work more than once", file=out)


def print_sensitivity(records, out=sys.stdout):
    """How many distinct works the pool holds under looser and stricter rules.

    The union count is this script's headline number and it is a function of
    the rule, so it is not reported alone. The point is not that one of these
    rows is right: it is how far the answer moves when a gate is dropped or
    loosened. Dropping the conflict gate leaves roughly ub.py's rule, and the
    45 works it takes off the count are the over-merging the module docstring
    describes; the year rule, which ub.py's --sensitivity varies for the same
    reason, moves the count by a work either way.
    """
    variants = [
        ("conflict gate dropped  (near ub.py's rule)", {"use_conflict": False}),
        ("conflict gate, year rule  (default)", {}),
        ("conflict gate, year title >= 0.30", {"year_title_min": 0.30}),
        ("conflict gate, no year rule", {"use_year": False}),
    ]
    print("\nSensitivity of the count to the matching rule", file=out)
    print("-" * 62, file=out)
    print(f"  {'rule':<44}{'works':>8}", file=out)
    for name, rule in variants:
        print(f"  {name:<44}{len(group_records(records, **rule)):>8}", file=out)


def write_csv(works, labels, path):
    """One row per distinct work, with every variant the corpora gave it.

    The presence columns hold 1/0 rather than a tick, so the file drops
    straight into a spreadsheet or a dataframe, and the trailing columns keep
    what the printed table has to leave out: every title, author, genre and
    year the record-set contains, the CLDW identifier where the work is one of
    the original 80, and the first download URL any run gave, which is what
    makes the row fetchable.
    """
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["year", "year_last", "composed", "author", "title",
                         "gender", "gender_disputed", "genre", "in_cldw",
                         "cldw_id", "n_corpora", "n_records"]
                        + list(labels)
                        + ["titles_seen", "authors_seen", "genres_seen",
                           "years_seen", "url", "repository", "reason"])
        for work in works:
            years = sorted({r["year"] for r in work if r["year"] is not None})
            composed = [r["composed"] for r in work if r["composed"] is not None]
            held = {r["source"] for r in work}
            ids = [r["cldw_id"] for r in work if r["cldw_id"]]
            urls = [r["url"] for r in work if r["url"]]
            reasons = sorted((r["reason"] for r in work if r["reason"]),
                             key=len, reverse=True)
            writer.writerow([
                years[0] if years else "",
                years[-1] if years else "",
                min(composed) if composed else "",
                best_author(work), best_title(work), best_gender(work),
                gender_note(work), best_genre(work),
                int(CLDW_LABEL in held), ids[0] if ids else "",
                len(held), len(work),
            ] + [1 if label in held else 0 for label in labels]
                + [" | ".join(title_variants(work)),
                   " | ".join(variants(work, "author")),
                   " | ".join(variants(work, "genre")),
                   " ".join(str(year) for year in years),
                   urls[0] if urls else "",
                   commonest([r["repository"] for r in work if r["repository"]])
                   if any(r["repository"] for r in work) else "",
                   reasons[0] if reasons else ""])


def main(argv=None):
    default_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=default_root,
                        help="repo root holding data/raw (default: %(default)s)")
    parser.add_argument("--runs", default=None,
                        help="comma-separated run labels to pool, besides the "
                             "original CLDW (default: all of "
                             f"{', '.join(l for l, _, _ in EXPERIMENTS)})")
    parser.add_argument("--no-cldw", action="store_true",
                        help="pool the runs only, leaving the original corpus out")
    parser.add_argument("--width", type=int, default=58,
                        help="title column width (default: %(default)s)")
    parser.add_argument("--genre-width", type=int, default=20,
                        help="genre column width (default: %(default)s)")
    parser.add_argument("--csv", default=None,
                        help="also write the list to this CSV, one row per work, "
                             "with every variant form the corpora gave it")
    parser.add_argument("--audit", action="store_true",
                        help="print every group this script merged, to check the "
                             "judgements")
    parser.add_argument("--sensitivity", action="store_true",
                        help="re-count the pool under looser and stricter rules")
    args = parser.parse_args(argv)

    wanted = None
    if args.runs:
        wanted = [label.strip() for label in args.runs.split(",") if label.strip()]
        known = {label for label, _, _ in EXPERIMENTS}
        unknown = [label for label in wanted if label not in known]
        if unknown:
            sys.exit(f"unknown run(s): {', '.join(unknown)}\n"
                     f"known runs: {', '.join(sorted(known))}")

    records, labels, totals = [], [], {}
    if not args.no_cldw:
        originals = load_cldw(args.root)
        if originals is None:
            print(f"note: no CLDW metadata under "
                  f"{os.path.join(args.root, *CLDW_PATH[:-1])}; the {CLDW_LABEL} "
                  f"column is left out and the pool is the runs alone",
                  file=sys.stderr)
        else:
            records.extend(originals)
            labels.append(CLDW_LABEL)
            totals[CLDW_LABEL] = len(originals)

    for label, path in resolve_sources(args.root, wanted):
        if not os.path.exists(path):
            print(f"skipping {label}: no {TEXTS_NAME} under "
                  f"{os.path.dirname(path)}", file=sys.stderr)
            continue
        loaded = load_run(label, path)
        records.extend(loaded)
        labels.append(label)
        totals[label] = len(loaded)

    if not records:
        sys.exit("no records found; pass --root")

    works = group_records(records)
    print_table(works, labels, args.width, args.genre_width)
    print_summary(works, labels, totals)
    print(f"\n{len(records)} records across {len(labels)} corpora, merging to "
          f"{len(works)} distinct works.")

    if args.audit:
        print_audit(works)
    if args.sensitivity:
        print_sensitivity(records)

    if args.csv:
        directory = os.path.dirname(os.path.abspath(args.csv))
        os.makedirs(directory, exist_ok=True)
        write_csv(works, labels, args.csv)
        print(f"\nwrote {args.csv}")


if __name__ == "__main__":
    main()
