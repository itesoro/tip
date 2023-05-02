import os
import sys
import json
import atexit
import inspect
import functools
from types import ModuleType
from typing import Any


BIN_DIR = os.path.dirname(sys.argv[0])
TIP_DIR = os.path.dirname(BIN_DIR)
LINKS_DIR = os.path.join(TIP_DIR, "links")
ENVIRONMENTS_DIR = os.path.join(TIP_DIR, "environments")
CONFIG_PATH = os.path.join(TIP_DIR, "config.json")


class Config:
    """
    A hierarchical configuration class that stores and retrieves settings using a dictionary-like structure.

    Config allows for convenient storage and retrieval of configuration settings using a string-based hierarchical key
    format. Keys are separated using the specified separator (default: '/'). Values can be either simple types or nested
    dictionaries, which are automatically converted to Config instances upon retrieval. If a key does not exist, a
    default value can be provided, which can be a factory (config will return default() in this case). In order to set
    value that is not dumped into the file, use prefix "_".

    Examples
    --------
    >>> config = Config({"app": {"name": "my_app", "version": "1.0"}})
    >>> config.get("app/name")
    'my_app'
    >>> config.get("app/version")
    '1.0'
    >>> config.get("non_existent_key", "default")
    'default'
    >>> config.get("default_factory", lambda: 5 / 2)
    2.5
    >>> config['app/location'] = "path/to/server.sock"
    >>> config.get('app/location')
    'path/to/server.sock'
    """

    SEP = '/'

    def __init__(self, config_dict: dict):
        self._root = config_dict
        self._tmp_root: dict[str, Any] = {}

    def get(self, key, default_value=None):
        x = self.__get_root(key)
        try:
            for e in key.split(self.SEP):
                x = x[e]
            return Config(x) if isinstance(x, dict) else x
        except KeyError:
            pass
        if inspect.isfunction(default_value):
            default_value = default_value()
        if default_value is not None:
            self[key] = default_value
        return default_value

    def __setitem__(self, key, value):
        x = self.__get_root(key)
        *dirs, file = key.split(self.SEP)
        for e in dirs:
            try:
                x = x[e]
            except KeyError:
                x[e] = y = {}
                x = y
        x[file] = value

    def __get_root(self, key: str) -> dict:
        return self._tmp_root if key.startswith('_') else self._root


def get(key, default_value=None):
    """Get a configuration value."""
    return _config.get(key, default_value)


def _load_config_dict():
    config = {}
    try:
        with open(CONFIG_PATH, mode='r', encoding='utf8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        pass
    return config


def _dump_config_dict(config):
    with open(CONFIG_PATH, mode='w', encoding='utf8') as f:
        json.dump(config, f, indent=2)


def _enable_setkey():
    """Enable magic methods for Config."""
    this_module = sys.modules[__name__]

    @functools.wraps(ModuleType, updated=())
    class MagicModule(ModuleType):
        """Tricks module to have class-like functions."""

    def config_setkey(self, key, value):  # pylint: disable=unused-argument
        _config[key] = value

    setattr(MagicModule, "__setitem__", config_setkey)

    this_module.__class__ = MagicModule


_config_dict = _load_config_dict()
_config = Config(_config_dict)
_enable_setkey()
atexit.register(_dump_config_dict, _config_dict)
