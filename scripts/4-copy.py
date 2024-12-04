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

from core import warn, log

DOTENV = dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))
API_BASE_URL = DOTENV["API_BASE_URL"]
API_SCHEMA_BASE_URL = f"{API_BASE_URL}/schemas"

ROOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)))
VENDOR_ICONS_DIR = os.path.join(ROOT_DIR, "vendor", "icons", "dist")
OUT_PUBLIC_DIR = os.path.join(ROOT_DIR, "out", "public")
OUT_STATIC_DIR = os.path.join(OUT_PUBLIC_DIR, "static")
OUT_SCHEMAS_DIR = os.path.join(OUT_PUBLIC_DIR, "schemas")
STATIC_IMAGES_RESIZE = 128
STATIC_IMAGES = {
    "music-presence.png": os.path.join(VENDOR_ICONS_DIR, "logo-app-full.png"),
    "discord-status-playing.png": os.path.join(
        VENDOR_ICONS_DIR, "symbol-status-playing.png"
    ),
    "discord-status-paused.png": os.path.join(
        VENDOR_ICONS_DIR, "symbol-status-paused.png"
    ),
}
SRC_SCHEMAS_DIR = os.path.join(ROOT_DIR, "src", "schemas")


def copy_static():
    pathlib.Path(OUT_STATIC_DIR).mkdir(parents=True, exist_ok=True)
    for result_name, source_file in STATIC_IMAGES.items():
        image = Image.open(source_file)
        if image.size[0] != image.size[1]:
            warn(f"Static image is not a square: {source_file}")
        image.thumbnail(
            (STATIC_IMAGES_RESIZE, STATIC_IMAGES_RESIZE), Image.Resampling.LANCZOS
        )
        out_path = os.path.join(OUT_STATIC_DIR, result_name)
        image.save(out_path)
        log(result_name)


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
