import os
import json

from . import packages


def _get_environments_dir(tip_home: str) -> str:
    """Get path to the directory containing environment files."""
    environments_dir = os.path.join(tip_home, "environments")
    if not os.path.isdir(environments_dir):
        os.makedirs(environments_dir)
    return environments_dir


def get_environment_path(tip_home: str, name: str) -> str:
    """Find file of the environment called `name`."""
    return os.path.join(_get_environments_dir(tip_home), f"{name}.json")


def get_environment_by_path(path: str) -> dict:
    """Get package list of the environment at `path`."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Environment file is not found at {path}")
    with open(path, mode='r', encoding='utf8') as environment_file:
        return json.load(environment_file)


def get_environment_by_name(tip_home: str, name: str) -> dict:
    """Get package list of the environment called `name`"""
    path = get_environment_path(tip_home, name)
    return get_environment_by_path(path)


def save_environment(environment: dict | None, path: str, /, *, rewrite: bool = False):
    """Save environment to path, rewriting the file if `rewrite` is True."""
    if os.path.isfile(path) and not rewrite:
        raise RuntimeError("Environment file exists and asked not to rewrite")
    with open(path, mode='w+', encoding='utf8') as environment_file:
        json.dump({} if environment is None else environment, environment_file)


def exists(tip_home: str, name: str) -> bool:
    """Check if file of the environment called `name` exists."""
    path = get_environment_path(tip_home, name)
    return os.path.isfile(path)


def add_to_environment_at_path(package: str, path: str, replace: bool = False):
    """Add package to the environment file at `path`."""
    environment = get_environment_by_path(path)
    package_name, package_version = packages.parse(package)
    if (curr_version := environment.get(package_name)) is not None:
        if curr_version == package_version:
            return
        if not replace:
            raise RuntimeError(f"Package {package_name} is already in environment and has version {curr_version}")
    environment[package_name] = package_version
    save_environment(environment, path, rewrite=True)


def add_to_environment_with_name(tip_home, package: str, environment_name: str, replace: bool = False):
    """Add package to the environment `environment_name`."""
    environment_path = get_environment_by_name(tip_home, environment_name)
    add_to_environment_at_path(package, environment_path, replace)


def remove_from_environment_at_path(package_specifier: str, path: str):
    """Remove package from the environment file at `path`."""
    environment = get_environment_by_path(path)
    package_name, package_version = packages.parse(package_specifier)
    if environment[package_name] != package_version:
        raise ValueError(package_version)
    del environment[package_name]
    save_environment(environment, path, rewrite=True)


def remove_from_environment_with_name(tip_home, package_specifier: str, name: str):
    """Remove package from the environment file at `path`."""
    environment_path = get_environment_path(tip_home, name)
    remove_from_environment_at_path(package_specifier, environment_path)


def remove_environment_file(path: str):
    """Remove environment file at `path`."""
    os.remove(path)
