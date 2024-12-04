# TODO validate the following conditions

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
    ThirdPartyClients = "third-party-clients"
    VideoSharing = "video-sharing"


class ContentType(enum.Enum):
    Audio = "audio"
    AudioMusic = "audio_music"
    AudioPodcast = "audio_podcast"
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
            error(f"YAML definitions must be in a subdirectory: {relative_path}")
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


def validate_target_category_invariants(target: ValidationTarget):
    player = target.id_from_filename
    category = target.category_from_directory
    category_error = lambda e: error(f'Category "{category}": {e}')
    if category == PlayerCategory.MultimediaPlayers.value:
        if target.content["attributes"]["service"] != False:
            category_error(f'The "service" attribute for "{player}" must be false')
        if target.content["attributes"]["pure"] != False:
            category_error(f'The "pure" attribute for "{player}" must be false')
    elif category == PlayerCategory.MusicStreaming.value:
        if target.content["attributes"]["service"] != True:
            category_error(f'The "service" attribute for "{player}" must be true')
        if target.content["attributes"]["pure"] != True:
            category_error(f'The "pure" attribute for "{player}" must be true')
    elif category == PlayerCategory.OfflinePlayers.value:
        if target.content["attributes"]["service"] != False:
            category_error(f'The "service" attribute for "{player}" must be false')
    elif category == PlayerCategory.PodcastServices.value:
        if target.content["attributes"]["service"] != True:
            category_error(f'The "service" attribute for "{player}" must be true')
        if ContentType.AudioPodcast.value not in target.content["content"]:
            category_error(
                f'The "content" attribute for "{player}" must contain '
                f'"{ContentType.AudioPodcast.value}"'
            )
        if (
            ContentType.Audio.value not in target.content["content"]
            or ContentType.AudioPodcast.value not in target.content["content"]
            or len(target.content["content"]) > 2
        ):
            category_error(
                f'The "content" attribute for "{player}" may only contain '
                f'"{ContentType.Audio.value}" and '
                f'"{ContentType.AudioPodcast.value}"'
            )
    elif category == PlayerCategory.ThirdPartyClients.value:
        if target.content["attributes"]["service"] != False:
            category_error(f'The "service" attribute for "{player}" must be false')
        if "represents" not in target.content:
            category_error(f'Player "{player}" must have the "represents" attribute')
    elif category == PlayerCategory.VideoSharing.value:
        if target.content["attributes"]["service"] != True:
            category_error(f'The "service" attribute for "{player}" must be true')
        if ContentType.Video.value not in target.content["content"]:
            category_error(
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
