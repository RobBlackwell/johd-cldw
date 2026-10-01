#!/usr/bin/env python3
"""Summarise the claude-code experiment traces.

Reads data/raw/<variant>/<run>/trace.jsonl for each run and prints how long
the run took, what it cost in tokens and dollars, and how many texts it
produced. universe-balanced was run twice, so it contributes two columns.

Usage:
    ./01-reb-analyse.py [--root REPO_ROOT] [--csv]
"""

import argparse
import json
import sys
from pathlib import Path

# (column label, variant, run directory). Most variants were run once, under
# claude-code; universe-balanced was repeated to gauge run-to-run variation.
EXPERIMENTS = [
    ("cldw2-balanced", "cldw2-balanced", "claude-code"),
    ("cldw2-unbalanced", "cldw2-unbalanced", "claude-code"),
    ("universe-balanced", "universe-balanced", "claude-code"),
    ("universe-balanced-run2", "universe-balanced", "claude-code-run2"),
    ("universe-unbalanced", "universe-unbalanced", "claude-code"),
]


def read_result(trace):
    """The single type=result record: the run's own summary of itself."""
    with trace.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") == "result":
                return rec
    raise ValueError(f"no result record in {trace}")


def count_texts(exp_dir, result):
    """Texts in the corpus the run produced.

    The model writes texts.jsonl itself, so that file is the corpus. Older
    runs put the JSONL in the final message instead, so fall back to that.
    """
    texts = exp_dir / "texts.jsonl"
    if texts.exists():
        with texts.open() as fh:
            return sum(1 for line in fh if line.strip())
    n = 0
    for line in (result.get("result") or "").splitlines():
        try:
            if isinstance(json.loads(line), dict):
                n += 1
        except json.JSONDecodeError:
            pass
    return n


def analyse(exp_dir):
    result = read_result(exp_dir / "trace.jsonl")
    usage = result.get("usage", {})
    detail = usage.get("output_tokens_details", {})

    inp = usage.get("input_tokens", 0)
    cache_w = usage.get("cache_creation_input_tokens", 0)
    cache_r = usage.get("cache_read_input_tokens", 0)
    out = usage.get("output_tokens", 0)

    return {
        "ok": not result.get("is_error", False),
        "duration_ms": result.get("duration_ms", 0),
        "api_ms": result.get("duration_api_ms", 0),
        "turns": result.get("num_turns", 0),
        "model": result.get("modelUsage", {}),
        "input": inp,
        "cache_write": cache_w,
        "cache_read": cache_r,
        "output": out,
        "thinking": detail.get("thinking_tokens", 0),
        "total_tokens": inp + cache_w + cache_r + out,
        "cost": result.get("total_cost_usd", 0.0),
        "texts": count_texts(exp_dir, result),
    }


def fmt_duration(ms):
    total = round(ms / 1000)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


ROWS = [
    ("Wall-clock time", lambda r: fmt_duration(r["duration_ms"])),
    ("Time in API calls", lambda r: fmt_duration(r["api_ms"])),
    ("Turns", lambda r: f"{r['turns']:,}"),
    ("Input tokens", lambda r: f"{r['input']:,}"),
    ("Cache write tokens", lambda r: f"{r['cache_write']:,}"),
    ("Cache read tokens", lambda r: f"{r['cache_read']:,}"),
    ("Output tokens", lambda r: f"{r['output']:,}"),
    ("  of which thinking", lambda r: f"{r['thinking']:,}"),
    ("Total tokens", lambda r: f"{r['total_tokens']:,}"),
    ("Cost (USD)", lambda r: f"${r['cost']:,.2f}"),
    ("Texts found", lambda r: f"{r['texts']:,}"),
    ("Cost per text", lambda r: f"${r['cost'] / r['texts']:,.3f}" if r["texts"] else "n/a"),
]


def print_table(results, out=sys.stdout):
    names = list(results)
    label_w = max(len(label) for label, _ in ROWS)
    widths = [max(len(n), max(len(fn(results[n])) for _, fn in ROWS)) for n in names]

    header = " " * label_w + "  " + "  ".join(n.rjust(w) for n, w in zip(names, widths))
    rule = "-" * len(header)
    print(header, file=out)
    print(rule, file=out)
    for label, fn in ROWS:
        cells = "  ".join(fn(results[n]).rjust(w) for n, w in zip(names, widths))
        print(f"{label.ljust(label_w)}  {cells}", file=out)
    print(rule, file=out)

    total_cost = sum(r["cost"] for r in results.values())
    total_tokens = sum(r["total_tokens"] for r in results.values())
    total_texts = sum(r["texts"] for r in results.values())
    total_time = sum(r["duration_ms"] for r in results.values())
    print(
        f"All {len(results)} runs: {fmt_duration(total_time)}, "
        f"{total_tokens:,} tokens, ${total_cost:,.2f}, {total_texts:,} texts",
        file=out,
    )

    failed = [n for n, r in results.items() if not r["ok"]]
    if failed:
        print(f"WARNING: run reported an error: {', '.join(failed)}", file=out)


def print_csv(results, out=sys.stdout):
    import csv

    fields = [
        "experiment", "duration_s", "api_s", "turns", "input_tokens",
        "cache_write_tokens", "cache_read_tokens", "output_tokens",
        "thinking_tokens", "total_tokens", "cost_usd", "texts",
    ]
    w = csv.writer(out)
    w.writerow(fields)
    for name, r in results.items():
        w.writerow([
            name, round(r["duration_ms"] / 1000), round(r["api_ms"] / 1000),
            r["turns"], r["input"], r["cache_write"], r["cache_read"],
            r["output"], r["thinking"], r["total_tokens"],
            f"{r['cost']:.6f}", r["texts"],
        ])


def main():
    default_root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=default_root,
                    help="repo root holding data/raw (default: %(default)s)")
    ap.add_argument("--csv", action="store_true", help="emit CSV instead of a table")
    args = ap.parse_args()

    results = {}
    for label, variant, run in EXPERIMENTS:
        exp_dir = args.root / "data" / "raw" / variant / run
        if not (exp_dir / "trace.jsonl").exists():
            print(f"skipping {label}: no trace.jsonl under {exp_dir}", file=sys.stderr)
            continue
        results[label] = analyse(exp_dir)

    if not results:
        sys.exit("no traces found; pass --root")

    (print_csv if args.csv else print_table)(results)


if __name__ == "__main__":
    main()
