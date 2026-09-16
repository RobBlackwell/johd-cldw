#!/usr/bin/env python3
"""Fuzzy-match entries between two JSONL files by title and author.

Prints texts found only in A, only in B, and in both (high-confidence
matches only).
"""

import argparse
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

TITLE_FIELDS = ("title", "Title_short", "Title_full")
AUTHOR_FIELDS = ("author", "Author")

TITLE_WEIGHT = 0.7
AUTHOR_WEIGHT = 0.3
MATCH_THRESHOLD = 0.85

STOPWORDS = {"a", "an", "the", "of", "and", "or", "in", "on", "to", "with"}


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return [json.loads(line) for line in f if line.strip()]


def first_field(entry: dict, fields: tuple[str, ...]) -> str:
    for field in fields:
        if entry.get(field):
            return entry[field].strip()
    return ""


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if t not in STOPWORDS]
    return " ".join(sorted(tokens))


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def to_record(entry: dict) -> dict:
    title = first_field(entry, TITLE_FIELDS)
    author = first_field(entry, AUTHOR_FIELDS)
    return {
        "title": title,
        "author": author,
        "title_norm": normalize(title),
        "author_norm": normalize(author),
    }


def score_pair(a: dict, b: dict) -> float:
    title_sim = similarity(a["title_norm"], b["title_norm"])
    author_sim = similarity(a["author_norm"], b["author_norm"])
    return TITLE_WEIGHT * title_sim + AUTHOR_WEIGHT * author_sim


def greedy_match(left: list[dict], right: list[dict], threshold: float):
    candidates = []
    for i, l in enumerate(left):
        for j, r in enumerate(right):
            s = score_pair(l, r)
            if s >= threshold:
                candidates.append((s, i, j))
    candidates.sort(key=lambda x: x[0], reverse=True)

    matched_left, matched_right = set(), set()
    matches = []
    for s, i, j in candidates:
        if i in matched_left or j in matched_right:
            continue
        matched_left.add(i)
        matched_right.add(j)
        matches.append((left[i], right[j]))

    left_only = [l for i, l in enumerate(left) if i not in matched_left]
    right_only = [r for j, r in enumerate(right) if j not in matched_right]
    return matches, left_only, right_only


def describe(r: dict) -> str:
    return f"'{r['title']}' by {r['author']}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file_a", type=Path, help="first JSONL file")
    parser.add_argument("file_b", type=Path, help="second JSONL file")
    parser.add_argument(
        "--threshold", type=float, default=MATCH_THRESHOLD,
        help="minimum combined similarity score to count as a match (default: %(default)s)",
    )
    args = parser.parse_args()

    left = [to_record(e) for e in load_jsonl(args.file_a)]
    right = [to_record(e) for e in load_jsonl(args.file_b)]

    matches, left_only, right_only = greedy_match(left, right, args.threshold)

    print(f"--- In {args.file_a.name} only ({len(left_only)}) ---")
    for l in left_only:
        print(f"  {describe(l)}")
    print()

    print(f"--- In both ({len(matches)}) ---")
    for l, r in matches:
        print(f"  {describe(l)}")
    print()

    print(f"--- In {args.file_b.name} only ({len(right_only)}) ---")
    for r in right_only:
        print(f"  {describe(r)}")


if __name__ == "__main__":
    main()
