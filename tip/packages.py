import os
import shutil
import subprocess

from tip import config
from tip.util import parse_package_specifier


def is_valid(package_specifier: str) -> bool:
    """Check if `package` is valid package specifier."""
    try:
        parse_package_specifier(package_specifier)
    except ValueError:
        return False
    return True


def make_package_specifier(package_name: str, package_version: str) -> str:
    """Make package specifier from package name and package version."""
    return f"{package_name}=={package_version}"


def install(package_specifiers: list[str]):
    """Install packages identified by `package_specifiers`."""
    for package_specifier in package_specifiers:
        if is_valid(package_specifier):
            continue
        raise RuntimeError(f"Invalid package specifier: {package_specifier!r}")
    for package_specifier in package_specifiers:
        _install(package_specifier)


def make_link(package_specifier: str):
    """Make link to package identified by `package_specifier` in links directory."""
    package_dir = locate(*parse_package_specifier(package_specifier))
    for folder_name in os.listdir(package_dir):
        folder_path = os.path.join(package_dir, folder_name)
        link_path = os.path.join(config.LINKS_DIR, folder_name)
        if os.path.exists(link_path):
            os.unlink(link_path)
        os.symlink(folder_path, link_path)


def is_installed(package_specifier: str) -> bool:
    """Check if package identified by `package_specifier` is installed."""
    package_dir = locate(*parse_package_specifier(package_specifier))
    return os.path.isdir(package_dir)


def locate(package_name: str, package_version: str) -> str:
    """Locate package identified by `package_name` and `package_version` in site-packages directory."""
    site_packages_dir = config.get('site_packages_dir')
    os.makedirs(site_packages_dir, exist_ok=True)
    package_dir = os.path.join(site_packages_dir, package_name, package_version)
    return package_dir


def uninstall(package_specifier: str):
    """Uninstall package identified by `package_specifier`."""
    package_dir = locate(*parse_package_specifier(package_specifier))
    shutil.rmtree(package_dir)


def _install(package_specifier: str):
    """Install new package identified by `package_specifier` to make it available for environments."""
    package_name, package_version = parse_package_specifier(package_specifier)
    package_dir = locate(package_name, package_version)
    if os.path.exists(package_dir):
        return
    os.makedirs(package_dir)
    command = f"pip install --target={package_dir} {package_specifier}"
    try:
        subprocess.check_output(command, shell=True)
    except Exception as ex:
        shutil.rmtree(package_dir)
        raise RuntimeError(f"Error while installing package {package_specifier!r}") from ex
    make_link(package_specifier)
