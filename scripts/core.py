import contextlib
import datetime
import json
import sys
import yaml


class ValidationError(RuntimeError):
    pass


def log(message=""):
    print(message, file=sys.stdout)


def error(message):
    raise ValidationError(message)


def read_json(filename):
    with open(filename) as file:
        try:
            return json.load(file)
        except ValueError as e:
            error(f"Failed to parse {filename}: {e}")


def read_yaml(filename):
    with open(filename) as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as e:
            error(f"Failed to parse {filename}: {e}")


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
