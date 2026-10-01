#!/usr/bin/env python3
import sys
from pathlib import Path

import jinja2

ROOT = Path(__file__).resolve().parent.parent


def read_file(path: str) -> str:
    return Path(path).read_text().rstrip("\n")


def main(template_path: str, output_path: str) -> None:
    template = Path(template_path).resolve()
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([ROOT, template.parent]),
        keep_trailing_newline=True,
    )
    env.globals["read_file"] = read_file
    rendered = env.get_template(
        template.relative_to(ROOT).as_posix()
    ).render()
    Path(output_path).write_text(rendered)


if __name__ == "__main__":
    main(*sys.argv[1:3])
