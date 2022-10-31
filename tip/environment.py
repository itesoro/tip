import os
import json
from functools import cache

from . import config, packages


@cache
def get_active_environment() -> dict | None:
    """Get active environment if it's set or return `None`."""
    environments_dir = config.get_environments_dir()
    if (active_environment := config.get_active_environment_name()) is None:
        return None
    environment_path = os.path.join(environments_dir, active_environment + '.json')
    return get_environment(environment_path)


def get_environment(path: str) -> dict:
    """Get package list of the environment at `path`."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Environment file is not found at {path}")
    with open(path, mode='r') as environment_file:
        try:
            return json.load(environment_file)
        except Exception:
            raise RuntimeError("Environment file is corrupted")


def add_to_environment(package: str, path: str | None, replace: bool = False):
    """Add package to the environment file at `path` or into active environment."""
    if path is None:
        path = os.path.join(config.get_environments_dir(), config.get_active_environment_name() + '.json')
    environment = get_environment(path)
    package_name, package_version = packages.parse(package)
    if (curr_version := environment.get(package_name)) is not None and not replace:
        if curr_version == package_version:
            return
        raise RuntimeError("Package %s is already in environment and has version %s", package_name, curr_version)
    environment[package_name] = package_version
    return create_environment_file(environment, path, replace=True)


def missing_packages(environment: dict) -> list[str]:
    """Get list of not yet installed packages for environment."""
    missing_packages = []
    for package_name, package_version in environment.items():
        package_string = packages.make_package_string(package_name, package_version)
        if not packages.is_installed(package_string):
            missing_packages.append(package_string)
    return missing_packages


def create_environment_file(environment: dict | None, path: str, /, *, replace: bool = False):
    """Create new environment files at `path` or `$TIP_HOME/environments`, add `packages` to it if they are given."""
    if os.path.isfile(path) and not replace:
        raise RuntimeError("Environment file exists and asked not to replace")
    with open(path, mode='w+') as environment_file:
        json.dump({} if environment is None else environment, environment_file)


def remove_environment_file(path: str):
    """Remove environment file at `path`."""
    os.remove(path)
