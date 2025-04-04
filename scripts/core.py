import contextlib
import datetime
import json
import jsonschema
import sys
import yaml
from typing import Optional
from PIL import Image


class ValidationError(RuntimeError):
    pass


def log(message=""):
    print(message, file=sys.stderr)


def warn(message=""):
    print(f"WARN {message}", file=sys.stderr)


def error(message):
    raise ValidationError(message)


def read_json(filename):
    with open(filename) as file:
        try:
            return json.load(file)
        except ValueError as e:
            error(f"Failed to parse {filename}: {e}")


def read_yaml(filename):
    with open(filename, "rt", encoding="utf-8") as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as e:
            error(f"Failed to parse {filename}: {e}")


def read_yaml_with_schema(
    filename,
    schema: any,
    resolver: Optional[jsonschema.RefResolver],
) -> any:
    content = read_yaml(filename)
    try:
        jsonschema.validate(instance=content, schema=schema, resolver=resolver)
    except jsonschema.ValidationError as e:
        error(f"Schema validation error:\n\nFile {filename}:\n\n{e}")
    return content


def duplicates(items, window=lambda a: a) -> set[str]:
    s = set()
    return set(x for x in items if window(x) in s or s.add(window(x)))


@contextlib.contextmanager
def timed():
    class Timer:
        def __init__(self):
            self.start = datetime.datetime.now()

        def seconds(self) -> float:
            return (datetime.datetime.now() - self.start).total_seconds()

        def elapsed(self) -> str:
            seconds = self.seconds()
            if seconds < 1.0:
                return "%.1fms" % (1000 * seconds,)
            else:
                return "%.1fs" % (seconds,)

    timer = Timer()
    yield timer


def apply_mask(image: Image.Image, mask: Image.Image) -> Image.Image:
    if image.size != mask.size:
        raise ValueError("the image and the mask must have the same size")
    image_pixels = list(image.getdata())
    mask_pixels = list(mask.getdata())
    assert len(image_pixels) == len(mask_pixels)
    # ensure that transparency in the image is maintained
    for i in range(len(image_pixels)):
        if mask_pixels[i] == 0:
            image_pixels[i] = (
                image_pixels[i][0],
                image_pixels[i][1],
                image_pixels[i][2],
                mask_pixels[i],
            )
    image.putdata(image_pixels)
    return image
