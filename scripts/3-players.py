#
# 3-deploy.py
# Generates the final players.json file
#
# Input:
# - /src/players
# - /out/icons.json
# Output: /out/public/players.json
#
#

VERSION = 3

import os
import json
import jsonschema
import pathlib
from typing import Optional
from dotenv import dotenv_values
import warnings

import core
from core import log, warn, error

# ignore jsonschema warnings for now
warnings.filterwarnings("ignore", category=DeprecationWarning)

DOTENV = dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))
API_VERSION = int(DOTENV["API_VERSION"])
API_BASE_URL = DOTENV["API_BASE_URL"]

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
OUT_DIR = os.path.join(ROOT_DIR, "out")
PLAYERS_DIR = os.path.join(SRC_DIR, "players")
GENERATED_ICONS_FILE = os.path.join(OUT_DIR, "icons.json")
OUT_PLAYERS_DIRECTORY = os.path.join(OUT_DIR, "public")
OUT_PLAYERS_BASENAME = "players"
OUT_PLAYERS_MIN_SUFFIX = "min"
OUT_PLAYERS_EXTENSION = "json"
SCHEMA_PATH = os.path.join(SRC_DIR, "schemas")
PLAYERS_SCHEMA = core.read_json(os.path.join(SCHEMA_PATH, "players.schema.json"))


class Subset:
    def __init__(self, name: str, prefixes: list[str]):
        self.name = name
        self.prefixes = prefixes

    def includes(self, source_name: str):
        return any(source_name.startswith(p) for p in self.prefixes)

    def filter(self, source_names: list[str]) -> set[str]:
        return set(s for s in source_names if self.includes(s))


# subsets of the players for specific platforms
# the prefixes are prefixes of platform identifiers (e.g. "win_winrt")
# "web" is in every subset, since websites can be accessed on any platform
SUBSET_PLATFORM_PREFIXES = [
    Subset("win", ["win", "web"]),
    Subset("mac", ["mac", "web"]),
    Subset("lin", ["lin", "web"]),
    Subset("web", ["web"]),
]

for subset in SUBSET_PLATFORM_PREFIXES:
    assert subset.name != OUT_PLAYERS_MIN_SUFFIX


def validate_players(object: dict):
    jsonschema.validate(
        object,
        PLAYERS_SCHEMA,
        resolver=jsonschema.RefResolver(
            base_uri=f"{pathlib.Path(SCHEMA_PATH).as_uri()}/",
            referrer=PLAYERS_SCHEMA,
        ),
    )


def fix_schema_reference(object: dict):
    object["$schema"] = f'{API_BASE_URL}/schemas/{object["$schema"]}'


def get_output_file(subset: Optional[Subset] = None, minified=False):
    filename = OUT_PLAYERS_BASENAME
    if subset is not None:
        filename += "." + subset.name
    if minified:
        filename += "." + OUT_PLAYERS_MIN_SUFFIX
    filename += "." + OUT_PLAYERS_EXTENSION
    return os.path.join(OUT_PLAYERS_DIRECTORY, filename)


def generate(root: str, subset: Optional[Subset] = None):
    output_filename = get_output_file(subset, False)
    log(f"Compiling {pathlib.Path(output_filename).name}")
    icons = core.read_json(GENERATED_ICONS_FILE)
    paths = pathlib.Path(root).rglob("*.yaml")
    paths = sorted(paths, key=lambda p: p.stem)
    result = {
        "$schema": f"players.schema.json",
        "version": VERSION,
        "latest": API_VERSION == VERSION,
        "subset": subset.name if subset is not None else "",
        "players": [],
        "icons": {},
    }
    if subset is None:
        del result["subset"]
    total = 0
    for path in paths:
        content = core.read_yaml(path)
        assert "id" in content
        player = content["id"]
        if subset is not None:
            source_names = set(content["sources"].keys())
            to_include = subset.filter(source_names)
            if len(to_include) == 0:
                continue  # nothing to include, skip
            for source_name in source_names - to_include:
                del content["sources"][source_name]
        result["players"].append(content)
        total += 1
        if player not in icons:
            log(f"WARN No icons for {player}")
            continue
        result["icons"][player] = icons[player]
    log(f"Compiled {total} players")
    # validate the result
    validate_players(result)
    # fix the schema reference
    fix_schema_reference(result)
    # write the outputs
    with open(output_filename, "wt") as f:
        f.write(json.dumps(result, indent=2))
    with open(get_output_file(subset, True), "wt") as f:
        f.write(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    generate(PLAYERS_DIR)
    for subset in SUBSET_PLATFORM_PREFIXES:
        generate(PLAYERS_DIR, subset=subset)
