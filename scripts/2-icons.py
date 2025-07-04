#
# 2-icons.py
# Generates icons for media players
#
# Input: /src/icons
# Output: /out/public/icons
# Output artifacts:
# - Directory /out/public/icons: Icons for players in subdirectories
# - File /out/icons.json: A dictionary of objects that contains all generated
#   icons and that satisfies the schema in src/schemas/icon.schema.json
#
# Usage: 2-icons.py [player [player...]]
# - Generates icons for all players in the input directory,
#   when no arguments are provided
# - Generates icons for the specified players otherwise,
#   but does not create the /out/icons.json output artifact
#

import dataclasses
import enum
import os
import pathlib
import sys
import re
import json
import jsonschema
import hashlib
from io import BytesIO
from collections import defaultdict
from typing import Optional
from PIL import Image, ImageDraw
from dotenv import dotenv_values
import warnings

import core
from core import log, warn, error, ValidationError

# ignore jsonschema warnings for now
warnings.filterwarnings("ignore", category=DeprecationWarning)

DOTENV = dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))
GEN_BASE_URL_ICONS = f"{DOTENV["API_BASE_URL"]}/icons"

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT_DIR, "out")
OUT_ICONS_DIR = os.path.join(OUT_DIR, "public", "icons")
OUT_EXCLUDED_ICONS_DIR = os.path.join(OUT_DIR, "excluded-icons")
OUT_JSON_FILE = os.path.join(OUT_DIR, "icons.json")
IN_PLAYERS_DIR = os.path.join(ROOT_DIR, "src", "players")
IN_ICONS_DIR = os.path.join(ROOT_DIR, "src", "icons")
INTERNAL_SCHEMA_PATH = os.path.join(ROOT_DIR, "src", "schemas", "internal")
GEN_SCHEMA = core.read_json(os.path.join(INTERNAL_SCHEMA_PATH, "gen.schema.json"))
OVERRIDES_SCHEMA = core.read_json(
    os.path.join(INTERNAL_SCHEMA_PATH, "gen-overrides.schema.json")
)
# only hash the tray menu logo for now, to not inflate the resulting JSON
LABELS_TO_HASH = set(["tray-menu"])
EXPORT_FORMAT = "PNG"
SLUG_LENGTH = 12


class ImageType(enum.Enum):
    PNG = "PNG"
    JPG = "JPG"
    ICO = "ICO"

    def __hash__(self):
        return [e.value for e in self.__class__].index(self.value)


class ImageShape(enum.Enum):
    Square = "square"
    Circle = "circle"

    def __hash__(self):
        return [e.value for e in self.__class__].index(self.value)


class ColorCode(enum.Enum):
    Transparent = "transparent"
    Black = "black"
    White = "white"


class Color:
    def __init__(self, value: str | ColorCode):
        if value == ColorCode.Transparent or value == ColorCode.Transparent.value:
            self._color = "00000000"
        elif value == ColorCode.Black or value == ColorCode.Black.value:
            self._color = "000"
        elif value == ColorCode.White or value == ColorCode.White.value:
            self._color = "fff"
        else:
            if value.startswith("#"):
                value = value[1:]
            if not re.search(
                "^[#]?([a-zA-Z0-9]{3}|[a-zA-Z0-9]{6}|[a-zA-Z0-9]{8})$", value
            ):
                raise ValueError("not a hex code")
            self._color = value

    def color(self, prefix="#"):
        if prefix == False:
            prefix = ""
        return f"{prefix}{self._color}"

    def __hash__(self) -> int:
        # prepend a "1" so values like "000" and "00000000" hash differently
        return int(f"1{self._color}", 16)


@dataclasses.dataclass(frozen=True)
class GenerationRecipe:
    # image type to produce: jpg, png or ico
    image_type: ImageType = ImageType.PNG
    # a shape to apply as a mask to the image
    image_mask: str = ImageShape.Square
    # the shape of the resulting icon
    output_shape: str = ImageShape.Square
    # the color of the background
    background: Color = Color(ColorCode.Transparent)
    # the factor to scale the image by
    image_scale: float = 1.0
    # the factor to scale the border by
    border_scale: float = 1.0
    # the factor to scale the background by
    background_scale: float = 1.0
    # the size of the resulting image
    # if not set, it's identical to the input image size
    output_size: Optional[int] = None
    # whether to fail the build when there is no sufficiently large input image
    force_output_size: Optional[bool] = None

    def slug(self) -> str:
        return hex(hash(self) % ((sys.maxsize + 1) * 2))[2:]

    def effective_image_scale(self) -> float:
        return self.image_scale * self.border_scale

    def validate(self) -> None:
        if self.image_type == ImageType.ICO and self.output_size != None:
            raise ValidationError("Image type ICO cannot have an output size")
        if self.image_type == ImageType.JPG and self.output_shape != ImageShape.Square:
            raise ValidationError("Image type JPG cannot have a non-square shape")
        if self.image_type == ImageType.JPG and self.background_scale != 1.0:
            raise ValidationError("Background scale not allowed for image type JPG")
        bg = self.background.color(False)
        if self.image_type == ImageType.JPG and len(bg) == 8 and bg[-2:] != "ff":
            raise ValidationError("Image type JPG cannot have a transparent background")
        if self.effective_image_scale() > 1.0:
            raise ValidationError(
                f"The effective image scale would scale up the image: "
                f"{self.effective_image_scale()}"
            )


@dataclasses.dataclass(frozen=True)
class GenerationRule(GenerationRecipe):
    # labels for this generation target
    label: Optional[str] = None
    # image to use for generation
    from_image: Optional[str] = None
    # whether to exclude this from the output
    exclude: bool = False

    def __hash__(self):
        return super().__hash__()

    def update(self, values: dict):
        # TODO iterate over members instead and use a dict?
        image_type = self.image_type
        image_mask = self.image_mask
        output_shape = self.output_shape
        background = self.background
        image_scale = self.image_scale
        border_scale = self.border_scale
        background_scale = self.background_scale
        output_size = self.output_size
        force_output_size = self.force_output_size
        from_image = self.from_image
        label = self.label
        exclude = self.exclude
        if "image_type" in values:
            image_type = ImageType(values["image_type"])
        if "image_mask" in values:
            image_mask = ImageShape(values["image_mask"])
        if "output_shape" in values:
            output_shape = ImageShape(values["output_shape"])
        if "background" in values:
            background = Color(values["background"])
        if "image_scale" in values:
            image_scale = values["image_scale"]
        if "border_scale" in values:
            border_scale = values["border_scale"]
        if "background_scale" in values:
            background_scale = values["background_scale"]
        if "output_size" in values:
            output_size = values["output_size"]
        if "force_output_size" in values:
            force_output_size = values["force_output_size"]
        if "from_image" in values:
            from_image = values["from_image"]
        if "label" in values:
            label = values["label"]
        if "exclude" in values:
            exclude = values["exclude"]
        return GenerationRule(
            image_type=image_type,
            image_mask=image_mask,
            output_shape=output_shape,
            background=background,
            image_scale=image_scale,
            border_scale=border_scale,
            background_scale=background_scale,
            output_size=output_size,
            force_output_size=force_output_size,
            label=label,
            from_image=from_image,
            exclude=exclude,
        )


@dataclasses.dataclass
class IconDefinition:
    player: str
    generation_rules: list[GenerationRule]


@dataclasses.dataclass
class IconResult:
    label: str
    image_type: ImageType
    image_path: str


def read_generation_rules(path: str):
    content = core.read_yaml_with_schema(
        path,
        GEN_SCHEMA,
        resolver=jsonschema.RefResolver(
            base_uri=f"{pathlib.Path(INTERNAL_SCHEMA_PATH).as_uri()}/",
            referrer=GEN_SCHEMA,
        ),
    )
    raw_rules = content["rules"]
    generation_rules: list[GenerationRule] = []
    defaults = GenerationRule()
    for rule in raw_rules:
        res = defaults.update(rule)
        res.validate()
        generation_rules.append(res)
    return generation_rules


def generate_player_icons(root: str, player: str) -> list[IconResult]:
    gen_file = os.path.join(root, "gen.yaml")
    if not os.path.exists(gen_file):
        error(f"File does not exist: {gen_file}")
    image_root = os.path.join(root, "images")
    base_image_file = os.path.join(image_root, f"{player}.png")
    if not os.path.exists(base_image_file):
        base_image_file = os.path.join(image_root, f"{player}.jpg")
        if not os.path.exists(base_image_file):
            base_image_file = None
    generation_rules = read_generation_rules(gen_file)
    overrides_file = os.path.join(root, "overrides", f"{player}.yaml")
    if os.path.exists(overrides_file):
        overrides = core.read_yaml_with_schema(
            overrides_file,
            OVERRIDES_SCHEMA,
            jsonschema.RefResolver(
                base_uri=f"{pathlib.Path(INTERNAL_SCHEMA_PATH).as_uri()}/",
                referrer=OVERRIDES_SCHEMA,
            ),
        )
        new_rules = []
        for rule in generation_rules:
            if "global" in overrides:
                rule = rule.update(overrides["global"])
            if "label" in overrides:
                if rule.label in overrides["label"]:
                    rule = rule.update(overrides["label"][rule.label])
            new_rules.append(rule)
        generation_rules = new_rules
    return generate_icons(
        player=player,
        rules=generation_rules,
        base_image=base_image_file,
        image_root=image_root,
    )


def generate_icons(
    player: str,
    rules: list[GenerationRule],
    base_image: Optional[str],
    image_root: str,
) -> list[IconResult]:
    if len(rules) == 0:
        error(f'Generation rules for player "{player}" are empty')
    out_dir = os.path.join(OUT_ICONS_DIR, player)
    results = []
    labels: dict[str, int] = defaultdict(int)
    for rule in rules:
        labels[rule.label] += 1
    for i, rule in enumerate(rules):
        image_path = None
        if rule.from_image is not None:
            image_path = os.path.join(image_root, rule.from_image)
            if not os.path.exists(image_path):
                error(
                    f"Rule {i} ({rule.label}) for player {player} references "
                    f"a non-existent image: {image_path}"
                )
        else:
            image_path = base_image
        if base_image is None:
            warn(f"No image for rule {i} ({rule.label}) for player {player}")
            return []
        rule_out_dir = out_dir
        out_prefix = rule.label
        if rule.exclude:
            rule_out_dir = os.path.join(OUT_EXCLUDED_ICONS_DIR, rule.label)
            out_prefix = player
        image_path = generate_icon(
            rule=rule,
            image_path=image_path,
            out_directory=rule_out_dir,
            out_prefix=out_prefix,
        )
        if not rule.exclude:
            results.append(
                IconResult(
                    label=rule.label,
                    image_type=rule.image_type,
                    image_path=image_path,
                )
            )
    # Export the Discord application logo variant of the image so that there
    # is a logo that can be uploaded to the Discord Developer portal
    return results


def scale_image(image: Image.Image, factor: float):
    if factor > 1.0:
        raise ValueError("cannot upscale an image")
    size = image.size[0]
    new_size = int(size * factor)
    image.thumbnail((new_size, new_size), Image.Resampling.LANCZOS)
    paste_position = (new_size - size) // 2
    result_image = Image.new(image.mode, (size, size), "#00000000")
    result_image.paste(image, (-paste_position, -paste_position), image)
    return result_image


def sha256sum_combined(*args, **kwargs) -> str:
    combined_str = "+".join(map(str, args))
    result = hashlib.sha256(combined_str.encode("utf-8")).hexdigest()
    limit = kwargs.get("limit", None)
    if limit is not None:
        return result[:limit]
    return result


def generate_icon(
    rule: GenerationRule,
    image_path: str,
    out_directory: str,
    out_prefix: str = "",
):
    # open the image
    image = Image.open(image_path).convert("RGBA")
    # center-paste the image on a transparent background if it's not a square
    if image.size[0] != image.size[1]:
        max_size = max(image.size[0], image.size[1])
        base_image = Image.new("RGBA", (max_size, max_size), "#00000000")
        diff = (max_size - image.size[0], max_size - image.size[1])
        base_image.paste(image, (diff[0] // 2, diff[1] // 2), image)
        image = base_image
    image_size = image.size[0]
    # mask the image
    if rule.image_mask == ImageShape.Square:
        pass  # nothing to do
    elif rule.image_mask == ImageShape.Circle:
        image_mask = Image.new("L", image.size, 0)
        image_draw = ImageDraw.Draw(image_mask)
        image_draw.ellipse((0, 0) + (image_size - 0, image_size - 0), fill=255)
        image = core.apply_mask(image, image_mask)
    # scale the image
    effective_image_scale = rule.image_scale * rule.border_scale
    background_scale = rule.background_scale
    if effective_image_scale > 1.0:
        # Scale the background down when the image would be upscaled.
        down_factor = effective_image_scale
        background_scale /= down_factor
        effective_image_scale = 1.0
    image = scale_image(image, effective_image_scale)
    # create the background
    background_image = Image.new("RGBA", image.size, rule.background.color())
    # mask the result images
    if rule.output_shape == ImageShape.Square:
        pass  # nothing to do
    elif rule.output_shape == ImageShape.Circle:
        image_mask = Image.new("L", image.size, 0)
        image_draw = ImageDraw.Draw(image_mask)
        image_draw.ellipse((0, 0) + (image_size - 0, image_size - 0), fill=255)
        image = core.apply_mask(image, image_mask)
        background_mask = Image.new("L", image.size, 0)
        background_draw = ImageDraw.Draw(background_mask)
        background_draw.ellipse((0, 0) + (image_size - 0, image_size - 0), fill=255)
        background_image = core.apply_mask(background_image, background_mask)
    # scale the background
    background_image = scale_image(background_image, background_scale)
    background_image_format = EXPORT_FORMAT
    # put the image on top of the background
    assert background_image.size == image.size
    background_image = Image.alpha_composite(background_image, image)
    # resize the image to the output size
    if rule.output_size is not None:
        assert background_image.size[0] == background_image.size[1]
        if rule.force_output_size and background_image.size[0] < rule.output_size:
            warn(
                f"Rule {rule.label}: "
                f"{pathlib.Path(image_path).name} has only "
                f"{background_image.size[0]} pixels, but "
                f"{rule.output_size} are needed"
            )
        output_size = (rule.output_size, rule.output_size)
        background_image.thumbnail(output_size, Image.Resampling.LANCZOS)
        image_size = output_size[0]
    # determine the result file and location
    pathlib.Path(out_directory).mkdir(parents=True, exist_ok=True)
    tmp_result_file = f"tmp.{rule.image_type.value.lower()}"
    tmp_result_path = os.path.join(out_directory, tmp_result_file)

    # FIXME
    # if os.path.exists(result_path):
    #     error(f"Output image already exists, duplicate rule? {result_path}")

    # save the image based on result image type
    if rule.image_type == ImageType.PNG:
        background_image.save(tmp_result_path, background_image_format)
    elif rule.image_type == ImageType.JPG:
        # use a prominent color so it's obvious when transparency is removed
        base_image = Image.new("RGB", background_image.size, "#f0f")
        base_image.paste(background_image, (0, 0), background_image)
        base_image.save(tmp_result_path, "JPEG")
    elif rule.image_type == ImageType.ICO:
        background_image.save(tmp_result_path, "ICO")
    else:
        error(f"Unrecognized result image type: {rule.image_type}")
    result_slug = md5sum(tmp_result_path)[:SLUG_LENGTH]
    result_file = f"{out_prefix}.{result_slug}.{rule.image_type.value.lower()}"
    result_path = os.path.join(out_directory, result_file)
    os.rename(tmp_result_path, result_path)
    return result_path


def md5sum(filename: str) -> str:
    with open(filename, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def md5sum_image(image: Image.Image, format: str) -> str:
    with BytesIO() as byte_io:
        image.save(byte_io, format=format)
        data = byte_io.getvalue()
    return hashlib.md5(data).hexdigest()


if __name__ == "__main__":
    output_json = True
    if len(sys.argv) > 1:
        players = sys.argv[1:]
        output_json = False
    else:
        files = list(pathlib.Path(IN_PLAYERS_DIR).rglob("*.yaml"))
        duplicate_files = core.duplicates(files, window=lambda f: f.stem)
        if len(duplicate_files) > 0:
            out = "".join([f.name for f in duplicate_files])
            log(f"ERROR Duplicate players: {out}")
            exit(-1)
        players = sorted(f.stem for f in files)

    output = {}
    for player in players:
        log(player)
        try:
            results = generate_player_icons(IN_ICONS_DIR, player)
        except ValidationError as e:
            log(f"ERROR {player}: {e}")
            exit(-1)
        if len(results) > 0:
            objects = []
            for result in results:
                path = str(
                    pathlib.PurePosixPath(
                        pathlib.Path(result.image_path).relative_to(OUT_ICONS_DIR)
                    )
                )
                assert path == f"{player}/{pathlib.Path(result.image_path).name}"
                o = {
                    "label": result.label,
                    "type": result.image_type.value.lower(),
                    "url": f"{GEN_BASE_URL_ICONS}/{path}",
                }
                if result.label in LABELS_TO_HASH:
                    o["md5"] = md5sum(result.image_path)
                objects.append(o)
            output[player] = objects
    if output_json:
        json_output = json.dumps(output, separators=(",", ":"))
        with open(OUT_JSON_FILE, "wt") as f:
            f.write(json_output)
