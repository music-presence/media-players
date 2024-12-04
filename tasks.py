from invoke import task
from invoke.context import Context

import os
import sys
import pathlib
import shutil
import stat
import json
from typing import Optional
from dotenv import dotenv_values

CWD = os.path.dirname(__file__)
DOTENV = dotenv_values(os.path.join(CWD, "scripts", ".env"))
API_VERSION = int(DOTENV["API_VERSION"])

SCRIPTS_DIR = os.path.join(CWD, "scripts")
OUTPUT_DIR = os.path.join(CWD, "out")
BUILD_DIR = os.path.join(CWD, "build")

DEPLOY_INPUT_DIR = os.path.join(OUTPUT_DIR, "public")
DEPLOY_OUTPUT_DIR = f"v{API_VERSION}"
DEPLOY_REPO = os.getenv("DEPLOY_REPO") or "git@github.com:music-presence/live.git"
DEPLOY_BRANCH = "master"


def find_ordered_scripts() -> list[pathlib.Path]:
    return sorted(
        [
            path
            for path in pathlib.Path(SCRIPTS_DIR).glob("*.py")
            if len(path.stem) > 0 and path.stem[0].isdigit()
        ],
        key=lambda p: p.stem,
    )


# https://stackoverflow.com/a/58878271
def clear_directory(path: str):
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), stat.S_IRWXU)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IRWXU)
    shutil.rmtree(path)


@task
def build(c: Context):
    print("Building players")
    if os.path.exists(OUTPUT_DIR):
        print("Removing existing output directory", file=sys.stderr)
        clear_directory(OUTPUT_DIR)
    scripts = find_ordered_scripts()
    for i, script in enumerate(scripts):
        print_path = pathlib.PurePosixPath(script.relative_to(CWD))
        print(f"[{i+1}/{len(scripts)}] Running {print_path}", file=sys.stderr)
        c.run(f'python -u "{script}"')
    print("Build complete", file=sys.stderr)
    print("", file=sys.stderr)


def get_players_from_deployment(directory: str) -> Optional[dict[str, str]]:
    input_path = os.path.join(directory, "players.json")
    if not os.path.exists(input_path):
        return None
    with open(input_path, "rt") as f:
        players = json.loads(f.read())
    return {player["id"]: player["name"] for player in players["players"]}


def get_new_players(old_dir: str, new_dir: str) -> Optional[dict[str, str]]:
    old_players = get_players_from_deployment(old_dir)
    if old_players is None:
        return None
    new_players = get_players_from_deployment(new_dir)
    if new_players is None:
        print("WARN No new players?", file=sys.stderr)
        return None
    result = {}
    for key, value in new_players.items():
        if key not in old_players:
            result[key] = value
    return result


@task(pre=[build])
def deploy(c: Context):
    print("Deploying players", file=sys.stderr)
    if os.path.exists(BUILD_DIR):
        print("Removing existing build directory", file=sys.stderr)
        clear_directory(BUILD_DIR)
    pathlib.Path(BUILD_DIR).mkdir(parents=True)
    clone_dir = os.path.join(BUILD_DIR, "deploy")
    c.run(f'git clone -b "{DEPLOY_BRANCH}" "{DEPLOY_REPO}" "{clone_dir}"')
    deploy_dir = os.path.join(clone_dir, DEPLOY_OUTPUT_DIR)
    new_players = get_new_players(deploy_dir, DEPLOY_INPUT_DIR)
    if os.path.exists(deploy_dir):
        print("Clearing deployment directory", file=sys.stderr)
        clear_directory(deploy_dir)
    print("Copying output files to deployment directory", file=sys.stderr)
    shutil.copytree(DEPLOY_INPUT_DIR, deploy_dir)
    with c.cd(clone_dir):
        c.run("git add -A")
        result = c.run("git diff --cached --exit-code", warn=True)
        if result.return_code != 0:
            commit_message = "Automatic deployment"
            if new_players is not None and len(new_players) > 0:
                player_names = list(new_players.values())
                if len(player_names) > 1:
                    players = f"{', '.join(player_names[:-1])} and {player_names[-1]}"
                else:
                    players = player_names[0]
                commit_message = f"{commit_message}: {players}"
            c.run(f'git commit -m "{commit_message}"')
            c.run(f'git push origin "{DEPLOY_BRANCH}"')
            print("Deployment successful", file=sys.stderr)
        else:
            print("Nothing to deploy", file=sys.stderr)
    print("", file=sys.stderr)
