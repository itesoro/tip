import os
import shutil
import secrets

from tip import config


CACHE_DIR = config.get('cache_dir')


def get(package_dir):
    """Get path to a cached `package_dir` or return it if can't be cached."""
    if CACHE_DIR is None:
        return package_dir
    version = os.path.basename(package_dir)
    versions_dir = os.path.dirname(package_dir)
    name = os.path.basename(versions_dir)
    cache_dir = os.path.join(CACHE_DIR, name, version)
    try:
        cached_mtime = os.path.getmtime(cache_dir)
    except FileNotFoundError:
        cached_mtime = -1
    if cached_mtime > os.path.getmtime(package_dir):
        return package_dir
    os.makedirs(cache_dir, exist_ok=True)
    temp_dir = os.path.join(CACHE_DIR, name, secrets.token_hex(16) + '~')
    shutil.copytree(package_dir, temp_dir)
    try:
        os.rename(temp_dir, cache_dir)
    except FileExistsError:
        pass
    finally:
        shutil.rmtree(temp_dir)
    return cache_dir


def clear():
    """Clear cache."""
    if CACHE_DIR is not None and os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)


def is_enabled():
    """Check if cache is enabled."""
    return CACHE_DIR is not None
