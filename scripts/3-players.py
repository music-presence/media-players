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
from dotenv import dotenv_values
import warnings

import core
from core import log, warn, error

# ignore jsonschema warnings for now
warnings.filterwarnings("ignore", category=DeprecationWarning)

DOTENV = dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))
API_VERSION = int(DOTENV["API_VERSION"])
API_BASE_URL = DOTENV["API_BASE_URL"]

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "out")
PLAYERS_DIR = os.path.join(SRC_DIR, "players")
GENERATED_ICONS_FILE = os.path.join(OUT_DIR, "icons.json")
OUT_PLAYERS_JSON_FILE = os.path.join(OUT_DIR, "public", "players.json")
OUT_PLAYERS_MIN_JSON_FILE = os.path.join(OUT_DIR, "public", "players.min.json")
SCHEMA_PATH = os.path.join(SRC_DIR, "schemas")
PLAYERS_SCHEMA = core.read_json(os.path.join(SCHEMA_PATH, "players.schema.json"))


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


def generate(root: str):
    icons = core.read_json(GENERATED_ICONS_FILE)
    paths = pathlib.Path(root).rglob("*.yaml")
    paths = sorted(paths, key=lambda p: p.stem)
    result = {
        "$schema": f"players.schema.json",
        "version": VERSION,
        "latest": API_VERSION == VERSION,
        "players": [],
        "icons": {},
    }
    for path in paths:
        content = core.read_yaml(path)
        assert "id" in content
        player = content["id"]
        if player not in icons:
            log(f"WARN No icons for {player}")
            continue
        result["players"].append(content)
        result["icons"][player] = icons[player]
    # validate the result
    validate_players(result)
    # fix the schema reference
    fix_schema_reference(result)
    # write the outputs
    output = json.dumps(result, indent=2)
    with open(OUT_PLAYERS_JSON_FILE, "wt") as f:
        f.write(output)
    output_min = json.dumps(result, separators=(",", ":"))
    with open(OUT_PLAYERS_MIN_JSON_FILE, "wt") as f:
        f.write(output_min)


if __name__ == "__main__":
    generate(PLAYERS_DIR)
