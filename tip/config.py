import os
import json


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
    return get_user_config()['tip_home']


def get_active_environment_name() -> str | None:
    """Get active environment name."""
    return get_user_config()['active_environment_name']


def get_user_config():
    """Get user config."""
    if _config is None:
        raise RuntimeError("Config wasn't loaded")
    return _config


def update(active_environment_name: str, tip_home: str):
    """Create (or overwrite if exists) user config file."""
    user_config = {
        'active_environment_name': active_environment_name,
        'tip_home': tip_home,
    }
    with open(get_config_path(), mode='w', encoding='utf8') as user_config_file:
        json.dump(user_config, user_config_file)


def exists() -> bool:
    """Check if config file exists."""
    return os.path.isfile(get_config_path())


def get_config_path():
    """Get path to the user config file."""
    tip_home = os.path.expanduser('~')
    return os.path.join(tip_home, '.tip')


def load_config():
    with open(get_config_path(), mode='r', encoding='utf8') as user_config_file:
        global _config
        _config = json.load(user_config_file)


_config = None
