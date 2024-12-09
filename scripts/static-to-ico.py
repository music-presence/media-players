import pathlib
import os
from PIL import Image, ImageDraw

import core
from core import error, warn


ROOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
OUT_DIR = os.path.join(ROOT_DIR, "out", "static-icos")


# Source: https://stackoverflow.com/a/11291419
def add_corners(im, rad):
    circle = Image.new("L", (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
    alpha = Image.new("L", im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    core.apply_mask(im, alpha)  # slower, but preserves original transparency
    return im


def export_icos():
    pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    static_files = core.read_yaml(os.path.join(SRC_DIR, "static.yaml"))
    for file in static_files:
        filename = file["name"]
        abs_source_path = pathlib.Path(file["from"])
        source_path = os.path.join(ROOT_DIR, abs_source_path.relative_to("/"))
        if not os.path.exists(source_path):
            error(f"source path does not exist: {source_path}")
        result_name = os.path.splitext(filename)[0] + ".ico"
        out_path = pathlib.Path(os.path.join(OUT_DIR, result_name))
        image = Image.open(source_path)
        image = image.convert("RGBA")
        add_corners(image, image.size[0] // 3)
        image.save(out_path, "ICO")


if __name__ == "__main__":
    export_icos()
