#!/usr/bin/env python3
import sys
from pathlib import Path

import jinja2


def read_file(path: str) -> str:
    return Path(path).read_text().rstrip("\n")


def main(template_path: str, output_path: str) -> None:
    template_src = Path(template_path).read_text()
    env = jinja2.Environment(keep_trailing_newline=True)
    env.globals["read_file"] = read_file
    rendered = env.from_string(template_src).render()
    Path(output_path).write_text(rendered)


if __name__ == "__main__":
    main(*sys.argv[1:3])
