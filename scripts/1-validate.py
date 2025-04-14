#
# 1-validate.py
# Validates all player definitions and checks for errors
#
# Input: /src/players
# Output: -
# The script fails with an error message and a non-zero exit code,
# when there are any errors in the input that need attention
#
# Usage: 1-validate.py
#

import dataclasses
import enum
import jsonschema
import os
import pathlib
import sys

import core
from core import log, error


SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
PLAYERS_DIR = os.path.join(SRC_DIR, "players")
PLAYER_SCHEMA_FILE = os.path.join(SRC_DIR, "schemas", "player.schema.json")
PLAYER_SCHEMA = core.read_json(PLAYER_SCHEMA_FILE)


class PlayerCategory(enum.Enum):
    MultimediaPlayers = "multimedia-players"
    MusicStreaming = "music-streaming"
    OfflinePlayers = "offline-players"
    PodcastServices = "podcast-services"
    RadioPlayers = "radio-players"
    ThirdPartyClients = "third-party-clients"
    VideoSharing = "video-sharing"


class ContentType(enum.Enum):
    Audio = "audio"
    AudioMusic = "audio_music"
    AudioPodcast = "audio_podcast"
    AudioRadio = "audio_radio"
    Video = "video"


@dataclasses.dataclass
class ValidationTarget:
    path: str
    category_from_directory: str
    id_from_filename: str
    content: dict

    @property
    def short_path(self) -> str:
        directory = os.path.basename(os.path.dirname(self.path))
        return os.path.join(directory, os.path.basename(self.path))

    @property
    def filename(self) -> str:
        return os.path.basename(self.path)


def get_targets(root: str) -> dict[str, ValidationTarget]:
    for path in pathlib.Path(root).rglob("*.yml"):
        path = path.relative_to(root)
        error(f"YAML definitions must end with the .yaml extension: {path}")
    targets: dict[str, ValidationTarget] = {}
    for path in pathlib.Path(root).rglob("*.yaml"):
        relative_path = path.relative_to(root)
        directory = os.path.dirname(relative_path)
        if len(directory) == 0:
            error(
                f"YAML definitions must be in a subdirectory: {relative_path}")
        if len(os.path.dirname(directory)) > 0:
            error(f"Nested directories are not allowed: {relative_path}")
        target_path = path.resolve()
        target = ValidationTarget(
            path=target_path,
            category_from_directory=directory,
            id_from_filename=path.stem,
            content=core.read_yaml(target_path),
        )
        if target.id_from_filename in targets:
            other_path = targets[target.id_from_filename].path
            other_relative_path = pathlib.Path(other_path).relative_to(root)
            error(f"Duplicate ID: {relative_path} and {other_relative_path}")
        targets[target.id_from_filename] = target
    return targets


def validate_target(target: ValidationTarget):
    if target.category_from_directory not in [c.value for c in PlayerCategory]:
        message = "{target.category_from_directory} for {target.short_path}"
        error(f"Player category not recognized: {message}")
    validate_target_schema(target, PLAYER_SCHEMA)
    if target.content["id"] != target.id_from_filename:
        a = f'"{target.content["id"]}"'
        b = f'"{target.id_from_filename}" in {target.short_path}'
        error(f"Mismatching player ID: {a} and {b}")
    validate_target_category_invariants(target)


def validate_target_schema(target: ValidationTarget, schema: any):
    try:
        jsonschema.validate(instance=target.content, schema=schema)
    except jsonschema.ValidationError as e:
        error(f"Schema validation error:\n\nFile {target.path}:\n\n{e}")


def category_error(target: ValidationTarget, e: str):
    error(f'Category "{target.category_from_directory}": {e}')


def require_content_types(
    target: ValidationTarget, content_types: list[ContentType], strict: bool
):
    player = target.id_from_filename
    for content_type in content_types:
        if content_type.value not in target.content["content"]:
            category_error(
                target,
                f'The "content" attribute for "{player}" must contain '
                f'"{content_type.value}"',
            )
    if strict and len(target.content["content"]) > len(content_types):
        category_error(
            target,
            f'The "content" attribute for "{player}" may only contain '
            + ", ".join(content_type.value for content_type in content_types),
        )


def validate_target_category_invariants(target: ValidationTarget):
    player = target.id_from_filename
    category = target.category_from_directory
    def local_category_error(e): return category_error(target, e)
    if category == PlayerCategory.MultimediaPlayers.value:
        if target.content["attributes"]["service"] != False:
            local_category_error(
                f'The "service" attribute for "{player}" must be false')
    elif category == PlayerCategory.MusicStreaming.value:
        if target.content["attributes"]["service"] != True:
            local_category_error(
                f'The "service" attribute for "{player}" must be true')
        if target.content["attributes"]["pure"] != True:
            # Streaming services usually only stream music and nothing else
            local_category_error(
                f'The "pure" attribute for "{player}" must be true')
    elif category == PlayerCategory.OfflinePlayers.value:
        if target.content["attributes"]["service"] != False:
            local_category_error(
                f'The "service" attribute for "{player}" must be false')
    elif category == PlayerCategory.PodcastServices.value:
        if target.content["attributes"]["service"] != True:
            local_category_error(
                f'The "service" attribute for "{player}" must be true')
        require_content_types(
            target, [ContentType.Audio, ContentType.AudioPodcast], True
        )
    elif category == PlayerCategory.RadioPlayers.value:
        if target.content["attributes"]["pure"] != False:
            # Radio names can contain someone's home town or area of residence
            local_category_error(
                f'The "pure" attribute for "{player}" must be false')
        if target.content["attributes"]["service"] != False:
            local_category_error(
                f'The "service" attribute for "{player}" must be false')
        require_content_types(
            target, [ContentType.Audio, ContentType.AudioRadio], False
        )
    elif category == PlayerCategory.ThirdPartyClients.value:
        if target.content["attributes"]["service"] != False:
            local_category_error(
                f'The "service" attribute for "{player}" must be false')
        if "represents" not in target.content:
            local_category_error(
                f'Player "{player}" must have the "represents" attribute')
    elif category == PlayerCategory.VideoSharing.value:
        if target.content["attributes"]["service"] != True:
            local_category_error(
                f'The "service" attribute for "{player}" must be true')
        if ContentType.Video.value not in target.content["content"]:
            local_category_error(
                f'The "content" attribute for "{player}" must contain '
                f'"{ContentType.Video.value}"'
            )


def validate_cross_target_invariants(targets: dict[str, ValidationTarget]):
    for player_id, target in targets.items():
        if "represents" not in target.content:
            continue
        for other_id in target.content["represents"]:
            if other_id == player_id:
                error(f'Player "{player_id}" may not represent itself')
            if other_id not in targets:
                error(
                    f'Player "{player_id}" represents non-existent player "{other_id}"'
                )
            other = targets[other_id]
            if "represents" in other.content:
                error(
                    f'Player "{player_id}" cannot represent "{other_id}" '
                    f'because "{other_id}" already represents other players'
                )


def validate_targets(targets: dict[str, ValidationTarget]):
    for player_id, target in targets.items():
        assert player_id == target.id_from_filename
        validate_target(target)
    validate_cross_target_invariants(targets)


def validate(root: str):
    log(f"Validating YAML definitions in {root}")
    with core.timed() as timer:
        try:
            targets = get_targets(root)
            validate_targets(targets)
        except core.ValidationError as e:
            print(f"ERROR {e}", file=sys.stderr)
            log(f"Took {timer.elapsed()}")
            exit(-1)
        elapsed = timer.elapsed()
    log(f"Validated {len(targets)} players in {elapsed}")


if __name__ == "__main__":
    validate(PLAYERS_DIR)
