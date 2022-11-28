import os
import shutil
import subprocess

from . import config


def install(package_string: str):
    """Install new package identified by `package_string` to make it available for environments."""
    package_dir = locate(package_string)
    if os.path.exists(package_dir):
        return
    os.makedirs(package_dir)
    command = f"pip install --target={package_dir} {package_string}"
    try:
        subprocess.check_output(command, shell=True)
    except Exception as ex:
        shutil.rmtree(package_dir)
        raise RuntimeError(f'Error while installing package "{package_string}": "{ex}"')
    make_link(package_string)


def make_link(package_string: str):
    """Creates link to a package conent within `site-packages` directory."""
    package_dir = locate(package_string)
    links_dir = config.get_links_dir()
    for folder_name in os.listdir(package_dir):
        folder_path = os.path.join(package_dir, folder_name)
        link_path = os.path.join(links_dir, folder_name)
        if os.path.exists(link_path):
            os.unlink(link_path)
        os.symlink(folder_path, link_path)


def is_installed(package_string: str) -> bool:
    """Check if package is installed."""
    package_dir = locate(package_string)
    return os.path.isdir(package_dir)


def locate(package: str) -> str:
    """Find package directory path."""
    package_name, package_version = parse(package)
    packages_dir = config.get_packages_dir()
    os.makedirs(packages_dir, exist_ok=True)
    package_dir = os.path.join(packages_dir, package_name, package_version)
    return package_dir


def uninstall(package_string: str):
    """Uninstall package."""
    package_dir = locate(package_string)
    shutil.rmtree(package_dir)


def make_package_string(package_name: str, package_version: str) -> str:
    """Make package string from package name and package version."""
    return f"{package_name}=={package_version}"


def parse(package_string: str) -> tuple[str, str]:
    """Parse package string into package name and package version."""
    split = package_string.split('==')
    if len(split) != 2:
        raise ValueError("Package string must be '<package_name>==<package_version>'")
    return split


def is_valid(package_string: str) -> bool:
    """Check if `package` is valid package string."""
    try:
        parse(package_string)
    except ValueError:
        return False
    return True
