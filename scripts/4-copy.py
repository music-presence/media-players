#
# 4-static.py
# Copies static files and schemas to the output directory
#
# Input:
# - /src/schemas
# - /vendor/icons
# Output:
# - /out/public/static
# - /out/public/schemas
#

import os
import pathlib
import re
from PIL import Image
from dotenv import dotenv_values

import core
from core import warn, log, error

DOTENV = dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))
API_BASE_URL = DOTENV["API_BASE_URL"]
API_SCHEMA_BASE_URL = f"{API_BASE_URL}/schemas"

ROOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
VENDOR_ICONS_DIR = os.path.join(ROOT_DIR, "vendor", "icons", "dist")
OUT_PUBLIC_DIR = os.path.join(ROOT_DIR, "out", "public")
OUT_STATIC_DIR = os.path.join(OUT_PUBLIC_DIR, "static")
OUT_SCHEMAS_DIR = os.path.join(OUT_PUBLIC_DIR, "schemas")
SRC_SCHEMAS_DIR = os.path.join(SRC_DIR, "schemas")


def copy_static():
    pathlib.Path(OUT_STATIC_DIR).mkdir(parents=True, exist_ok=True)
    static_files = core.read_yaml(os.path.join(SRC_DIR, "static.yaml"))
    for file in static_files:
        result_name = file["name"]
        abs_source_path = pathlib.Path(file["from"])
        source_path = os.path.join(ROOT_DIR, abs_source_path.relative_to("/"))
        if not os.path.exists(source_path):
            error(f"source path does not exist: {source_path}")
        if not "sizes" in file:
            error("missing sizes attribute")
        for size in file["sizes"]:
            image = Image.open(source_path)
            if image.size[0] != image.size[1]:
                warn(f"Static image is not a square: {source_path}")
            image.thumbnail((size, size), Image.Resampling.LANCZOS)
            out_path = pathlib.Path(os.path.join(OUT_STATIC_DIR, result_name))
            size_out_path = os.path.join(
                out_path.parent, out_path.stem + "." + str(size) + out_path.suffix
            )
            image.save(size_out_path)
            log(pathlib.Path(size_out_path).name)


def copy_and_fix_schemas():
    pathlib.Path(OUT_SCHEMAS_DIR).mkdir(parents=True, exist_ok=True)
    for path in pathlib.Path(SRC_SCHEMAS_DIR).glob("*.schema.json"):
        with open(path, "rt") as f:
            text = f.read()
        text = re.sub(
            r"(?im)(\"\$ref\":\s*)\"([^\"]+\.schema\.json)\"",
            f'\\1"{API_SCHEMA_BASE_URL}/\\2"',
            text,
        )
        result_path = os.path.join(OUT_SCHEMAS_DIR, path.name)
        with open(result_path, "wt") as f:
            f.write(text)
        log(path.name)


def main():
    copy_static()
    copy_and_fix_schemas()


if __name__ == "__main__":
    main()
