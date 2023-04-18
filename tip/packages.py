import os
import shutil
import subprocess

from tip import environments
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


def install(tip_home: str, package_specifiers: list[str] | None = None, environment_path: str | None = None):
    """Install packages from `package_specifiers` and/or from environment."""
    if package_specifiers is None:
        package_specifiers = []
    for package_specifier in package_specifiers:
        if is_valid(package_specifier):
            continue
        raise RuntimeError(f"Invalid package specifier: '{package_specifier}'")
    if environment_path is not None:
        env = environments.get_environment_by_path(environment_path)
        env_package_specifiers = [f"{name}=={version}" for name, version in env.items()]
    else:
        env_package_specifiers = []
    package_specifiers = list(package_specifiers) + env_package_specifiers
    for package_specifier in package_specifiers:
        _install(tip_home, package_specifier)


def missing_packages(tip_home: str, environment: dict) -> list[str]:
    """Get list of not yet installed packages for environment."""
    missing_packages = []  # pylint: disable=redefined-outer-name
    for package_name, package_version in environment.items():
        package_specifier = make_package_specifier(package_name, package_version)
        if not is_installed(tip_home, package_specifier):
            missing_packages.append(package_specifier)
    return missing_packages


def make_link(tip_home: str, package_specifier: str):
    """Creates link to a package conent within `site-packages` directory."""
    package_dir = locate(tip_home, package_specifier)
    links_dir = get_links_dir(tip_home)
    for folder_name in os.listdir(package_dir):
        folder_path = os.path.join(package_dir, folder_name)
        link_path = os.path.join(links_dir, folder_name)
        if os.path.exists(link_path):
            os.unlink(link_path)
        os.symlink(folder_path, link_path)


def get_links_dir(tip_home: str) -> str:
    """Get path to directory containing links to all installed packages."""
    links_dir = os.path.join(tip_home, "package-links")
    if not os.path.isdir(links_dir):
        os.makedirs(links_dir)
    return links_dir


def is_installed(tip_home: str, package_specifier: str) -> bool:
    """Check if package is installed."""
    package_dir = locate(tip_home, package_specifier)
    return os.path.isdir(package_dir)


def locate(tip_home: str, package: str) -> str:
    """Find package directory path."""
    package_name, package_version = parse_package_specifier(package)
    packages_dir = get_site_packages_dir(tip_home)
    os.makedirs(packages_dir, exist_ok=True)
    package_dir = os.path.join(packages_dir, package_name, package_version)
    return package_dir


def uninstall(tip_home: str, package_specifier: str):
    """Uninstall package."""
    package_dir = locate(tip_home, package_specifier)
    shutil.rmtree(package_dir)


def get_package_dir(tip_home: str, package_name: str, package_version: str) -> str:
    """Get path to the package by it's name and version."""
    packages_dir = get_site_packages_dir(tip_home)
    package_dir = os.path.join(packages_dir, package_name, package_version)
    return package_dir


def get_site_packages_dir(tip_home) -> str:
    """Get path to directory containg sources of all installed packages."""
    packages_dir = os.path.join(tip_home, "site-packages")
    if not os.path.isdir(packages_dir):
        os.makedirs(packages_dir)
    return packages_dir


def _install(tip_home: str, package_specifier: str):
    """Install new package identified by `package_specifier` to make it available for environments."""
    package_dir = locate(tip_home, package_specifier)
    if os.path.exists(package_dir):
        return
    os.makedirs(package_dir)
    command = f"pip install --target={package_dir} {package_specifier}"
    try:
        subprocess.check_output(command, shell=True)
    except Exception as ex:
        shutil.rmtree(package_dir)
        raise RuntimeError(f"Error while installing package '{package_specifier}'") from ex
    make_link(tip_home, package_specifier)
