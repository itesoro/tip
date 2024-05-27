import os
import shutil

from tip import config


CACHE_DIR = config.get('cache_dir')


def add(package_dir):
    """Cache a package at `package_dir` and return path to its cache."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
    except TypeError:
        raise RuntimeError("Cache is disabled") from None
    version = os.path.basename(package_dir)
    versions_dir = os.path.dirname(package_dir)
    name = os.path.basename(versions_dir)
    cache_dir = os.path.join(CACHE_DIR, name, version)
    try:
        shutil.copytree(package_dir, cache_dir)
    except FileExistsError:
        pass
    return cache_dir


def clear():
    """Clear cache."""
    try:
        shutil.rmtree(CACHE_DIR)
    except TypeError:
        raise RuntimeError("Cache is disabled") from None


def is_enabled():
    """Check if cache is enabled."""
    return CACHE_DIR is not None
