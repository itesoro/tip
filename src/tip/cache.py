import os
import shutil


CACHE_DIR = "/tmp/tip/cache"


def add(package_dir):
    """Cache a package at `package_dir` and return path to its cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
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
    shutil.rmtree(CACHE_DIR)
