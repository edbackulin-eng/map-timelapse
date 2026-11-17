"""Topic selection: environment variable TOPIC (default us-population) picks mapviz/topics/<slug>.py."""
import importlib
import os

SLUG = os.environ.get("TOPIC", "us-population")


def load():
    return importlib.import_module("mapviz.topics." + SLUG.replace("-", "_"))
