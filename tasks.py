from invoke import task
from invoke.context import Context

import os
import sys
import pathlib
import shutil


CWD = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.join(CWD, "scripts")
OUTPUT_DIR = os.path.join(CWD, "out")


def find_ordered_scripts() -> list[pathlib.Path]:
    return sorted(
        [
            path
            for path in pathlib.Path(SCRIPTS_DIR).glob("*.py")
            if len(path.stem) > 0 and path.stem[0].isdigit()
        ],
        key=lambda p: p.stem,
    )


@task
def build(c: Context):
    if os.path.exists(OUTPUT_DIR):
        print("Removing existing output directory")
        shutil.rmtree(OUTPUT_DIR)
    scripts = find_ordered_scripts()
    for i, script in enumerate(scripts):
        print_path = pathlib.PurePosixPath(script.relative_to(CWD))
        print(f"[{i+1}/{len(scripts)}] Running {print_path}", file=sys.stderr)
        c.run(f'python -u "{script}"')
    print("Done", file=sys.stderr)
