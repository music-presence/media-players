# This script converts the legacy list of media players
# to the format they are maintained in in the src directory.

import collections
import csv
import os
import yaml

LEGACY_DIR = os.path.join(os.path.dirname(__file__), "..", "legacy")
TARGET_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
TARGET_PLAYERS_DIR = os.path.join(TARGET_DIR, "players")
RELATIVE_SCHEMA_PATH = "../schemas/player.schema.json"
CSV_APPLICATIONS = os.path.join(LEGACY_DIR, "applications.csv")
CSV_PLAYERS = os.path.join(LEGACY_DIR, "players.csv")


def read_csv(filename):
    with open(filename) as file:
        reader = csv.DictReader(file)
        return list(reader)


class YamlDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(YamlDumper, self).increase_indent(flow, False)


def dump_yaml(data):
    return f"# yaml-language-server: $schema={RELATIVE_SCHEMA_PATH}\n\n" + yaml.dump(
        data, Dumper=YamlDumper, default_flow_style=False, sort_keys=False
    )


def create_yamls(
    players: dict[str, str], applications: dict[str, str]
) -> dict[str, dict[str, str]]:
    yamls = {}
    for player in players:
        identifier = player["id"]
        result = {
            "id": identifier,
            "name": player["name"],
            "sources": collections.defaultdict(list),  # populated below
            "attributes": {
                "pure": player["pure"] == "true",
                "service": player["service"] == "true",
            },
            "content": [
                "audio",  # set this by default, must be manually updated!
                "TODO",
            ],
            "extra": {
                "discord_application_id": player["discord_application_id"],
            },
        }
        has_app = False
        for app in applications:
            if app["id"] == identifier:
                has_app = True
                interface = app["interface"]
                result["sources"][interface].append(app["application"])
        result["sources"] = dict(result["sources"])
        if not has_app:
            raise "player has no application: " + identifier
        if identifier in yamls:
            raise "duplicate player identifier: " + identifier
        yamls[identifier] = result
    return yamls


def main():
    players = read_csv(CSV_PLAYERS)
    applications = read_csv(CSV_APPLICATIONS)
    yamls = create_yamls(players, applications)
    created = 0
    for identifier, data in yamls.items():
        content = dump_yaml(data)
        path = os.path.join(TARGET_PLAYERS_DIR, f"{identifier}.yaml")
        if os.path.exists(path):
            print(f"Skipping {identifier}: {path} already exists")
            continue
        with open(path, "wt") as f:
            f.write(content)
        created += 1
    print(f"Created {created} files in {os.path.abspath(TARGET_PLAYERS_DIR)}")


if __name__ == "__main__":
    main()
