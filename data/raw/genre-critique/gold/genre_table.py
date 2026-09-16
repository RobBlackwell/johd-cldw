#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PATH = SCRIPT_DIR / "../../../interim/ld80-metadata/ld80-metadata.jsonl"
OUTPUT_PATH = SCRIPT_DIR / "output.md"


def main():
    counts = Counter()
    total = 0
    with open(INPUT_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            genre = record.get("Genre", "No Data")
            counts[genre] += 1
            total += 1

    lines = [
        "# Texts by Genre",
        "",
        f"Total texts: {total}",
        "",
        "| Genre | Count | Percentage |",
        "| --- | --- | --- |",
    ]
    for genre, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        pct = 100 * count / total
        lines.append(f"| {genre} | {count} | {pct:.1f}% |")

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
