import os
import json


def get_package_dir(package_name: str, package_version: str) -> str:
    packages_dir = get_packages_dir()
    package_dir = os.path.join(packages_dir, package_name, package_version)
    return package_dir


def get_packages_dir() -> str:
    tip_home = get_tip_home()
    packages_dir = os.path.join(tip_home, "site-packages")
    if not os.path.isdir(packages_dir):
        os.makedirs(packages_dir)
    return packages_dir


def get_links_dir() -> str:
    tip_home = get_tip_home()
    links_dir = os.path.join(tip_home, "package-links")
    if not os.path.isdir(links_dir):
        os.makedirs(links_dir)
    return links_dir


def get_environments_dir() -> str:
    tip_home = get_tip_home()
    environments_dir = os.path.join(tip_home, "environments")
    if not os.path.isdir(environments_dir):
        os.makedirs(environments_dir)
    return environments_dir


def get_tip_home() -> str:
    user_config = _get_user_config()
    return user_config['home_dir']


def get_active_environment_name() -> str | None:
    """Get active environment name if it's set."""
    user_config = _get_user_config()
    return user_config['active_environment_name']


def _get_user_config():
    home_dir = os.path.expanduser('~')
    tiprc_path = os.path.join(home_dir, '.tip')
    with open(tiprc_path, mode='r') as tiprc_file:
        return json.load(tiprc_file)
