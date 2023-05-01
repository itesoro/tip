import os
import json

from tip import config
from tip.util import parse_package_specifier


class Environment:
    """A TIP environment."""

    def __init__(self, packages, path):
        self.packages = packages
        self._path = path

    @staticmethod
    def load(path=None, *, name=None):
        """Load environment from `path` or by `name`."""
        assert (path is None) != (name is None), "Load requires only one of `path` or `name`"
        if path is None:
            path = Environment.locate(name)
        with open(path, mode='r', encoding='utf8') as environment_file:
            return Environment(json.load(environment_file), path)

    @staticmethod
    def locate(name):
        """Find the path to the environment with the given `name`."""
        return os.path.join(config.ENVIRONMENTS_DIR, f'{name}.json')

    def save(self):
        """Save the environment to disk."""
        with open(self._path, mode='w+', encoding='utf8') as environment_file:
            json.dump(self.packages, environment_file)

    def add_package(self, package_specifier):
        """Add a package to the environment."""
        name, version = parse_package_specifier(package_specifier)
        self.packages[name] = version

    def remove_package(self, package_specifier):
        """Remove a package from the environment."""
        name, version = parse_package_specifier(package_specifier)
        if self.packages.get(name) != version:
            raise ValueError(f"Package '{package_specifier}' is not installed")
        self.packages.pop(name)
