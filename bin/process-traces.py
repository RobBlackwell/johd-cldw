#!/usr/bin/env python3
"""Extract the model's running commentary from a claude-code trace.

``trace.jsonl`` is the full ``--output-format stream-json`` transcript of a run:
every assistant turn, every tool call, every tool result, plus the harness's own
bookkeeping. Most of it is machinery. What a reader wants from a trace -- and
what the paper quotes -- is the thin seam of prose the model writes between its
tool calls to say what it is doing and why ("Gutenberg catalog is productive.
Let me check the IA batch...").

Those are the ``text`` blocks of ``type == "assistant"`` records. This script
pulls them out, in order, and writes them one per paragraph as plain text.

Deliberately left out:
  * ``thinking`` blocks -- private reasoning, not an account addressed to anyone;
  * ``tool_use`` blocks and their results -- the actions themselves, not the
    explanation of them, and orders of magnitude larger;
  * the ``result`` record -- a replay of the final assistant turn, which the
    text blocks already carry, and in these runs the corpus itself.

Run from anywhere:
    ./process-traces.py trace.jsonl [-o trace.txt]
    ./process-traces.py a/trace.jsonl b/trace.jsonl   # concatenated, in order
    cat trace.jsonl | ./process-traces.py -
"""

import argparse
import json
import sys
from pathlib import Path


def narration(line: str):
    """The assistant text blocks of one stream-json line, if it has any.

    A trace is written by a long-running container and can be truncated by a
    killed run, so a line that will not parse is skipped rather than fatal --
    losing the tail of a trace should not cost you the rest of it.
    """
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return

    if not isinstance(record, dict) or record.get("type") != "assistant":
        return

    content = record.get("message", {}).get("content")
    if not isinstance(content, list):
        return

    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text", "").strip()
            if text:
                yield text


def extract(stream) -> list:
    return [text for line in stream for text in narration(line)]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract the model's step-by-step commentary from a "
                    "claude-code stream-json trace."
    )
    parser.add_argument(
        "traces", nargs="+", metavar="TRACE",
        help="trace.jsonl file(s), or - for stdin",
    )
    parser.add_argument(
        "-o", "--output", metavar="FILE",
        help="write here instead of stdout",
    )
    args = parser.parse_args()

    blocks = []
    for trace in args.traces:
        if trace == "-":
            blocks += extract(sys.stdin)
            continue
        with open(trace, encoding="utf-8") as handle:
            blocks += extract(handle)

    if not blocks:
        print(
            f"{parser.prog}: no assistant commentary found in "
            f"{', '.join(args.traces)}",
            file=sys.stderr,
        )
        return 1

    # One blank line between turns: the blocks are paragraphs of prose, and a
    # turn can itself be several paragraphs, so anything tighter runs them
    # together.
    out = "\n\n".join(blocks) + "\n"

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
