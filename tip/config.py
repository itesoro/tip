import os
import json


def get_package_dir(package_name: str, package_version: str) -> str:
    """Get path to the package by it's name and version."""
    packages_dir = get_packages_dir()
    package_dir = os.path.join(packages_dir, package_name, package_version)
    return package_dir


def get_packages_dir() -> str:
    """Get path to directory containg sources of all installed packages."""
    tip_home = get_tip_home()
    packages_dir = os.path.join(tip_home, "site-packages")
    if not os.path.isdir(packages_dir):
        os.makedirs(packages_dir)
    return packages_dir


def get_links_dir() -> str:
    """Get path to directory containing links to all installed packages."""
    tip_home = get_tip_home()
    links_dir = os.path.join(tip_home, "package-links")
    if not os.path.isdir(links_dir):
        os.makedirs(links_dir)
    return links_dir


def get_environments_dir() -> str:
    """Get path to the directory containing environment files."""
    tip_home = get_tip_home()
    environments_dir = os.path.join(tip_home, "environments")
    if not os.path.isdir(environments_dir):
        os.makedirs(environments_dir)
    return environments_dir


def get_tip_home() -> str:
    """Get path to tip home directory."""
    return get_user_config()['home_dir']


def get_active_environment_name() -> str | None:
    """Get active environment name if it's set."""
    return get_user_config()['active_environment_name']


def get_user_config():
    """Get user config."""
    with open(get_config_path(), mode='r') as user_config_file:
        return json.load(user_config_file)


def create_user_config(active_environment_name: str, tip_home: str):
    """Create (or overwrite if exists) user config file."""
    user_config = {
        'active_environment_name': active_environment_name,
        'home_dir': tip_home,
    }
    with open(get_config_path(), mode='w') as user_config_file:
        json.dump(user_config, user_config_file)


def exists() -> bool:
    """Check if config file exists."""
    return os.path.isfile(get_config_path())


def get_config_path():
    """Get path to the user config file."""
    home_dir = os.path.expanduser('~')
    return os.path.join(home_dir, '.tip')
