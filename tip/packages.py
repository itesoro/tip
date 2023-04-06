import os
import shutil
import subprocess

from tip import config, environment


def install(package_specifiers: tuple[str] | None = None, environment_path: str = None):
    """Install packages from `package_specifiers` and/or from environment."""
    if package_specifiers is None:
        package_specifiers = []
    for package_specifier in package_specifiers:
        if is_valid(package_specifier):
            continue
        raise RuntimeError(f"Invalid package specifier: '{package_specifier}'")
    if environment_path is not None:
        env = environment.get_environment_by_path(environment_path)
        env_package_specifiers = [f"{name}=={version}" for name, version in env.items()]
    else:
        env_package_specifiers = []
    package_specifiers = list(package_specifiers) + env_package_specifiers
    for package_specifier in package_specifiers:
        _install(package_specifier)


def make_link(package_specifier: str):
    """Creates link to a package conent within `site-packages` directory."""
    package_dir = locate(package_specifier)
    links_dir = config.get_links_dir()
    for folder_name in os.listdir(package_dir):
        folder_path = os.path.join(package_dir, folder_name)
        link_path = os.path.join(links_dir, folder_name)
        if os.path.exists(link_path):
            os.unlink(link_path)
        os.symlink(folder_path, link_path)


def is_installed(package_specifier: str) -> bool:
    """Check if package is installed."""
    package_dir = locate(package_specifier)
    return os.path.isdir(package_dir)


def locate(package: str) -> str:
    """Find package directory path."""
    package_name, package_version = parse(package)
    packages_dir = config.get_site_packages_dir()
    os.makedirs(packages_dir, exist_ok=True)
    package_dir = os.path.join(packages_dir, package_name, package_version)
    return package_dir


def uninstall(package_specifier: str):
    """Uninstall package."""
    package_dir = locate(package_specifier)
    shutil.rmtree(package_dir)


def make_package_specifier(package_name: str, package_version: str) -> str:
    """Make package specifier from package name and package version."""
    return f"{package_name}=={package_version}"


def parse(package_specifier: str) -> tuple[str, str]:
    """Parse package specifier into package name and package version."""
    split = package_specifier.split('==')
    if len(split) != 2:
        raise ValueError("Package specifier must be '<package_name>==<package_version>'")
    return split


def is_valid(package_specifier: str) -> bool:
    """Check if `package` is valid package specifier."""
    try:
        parse(package_specifier)
    except ValueError:
        return False
    return True


def _install(package_specifier: str):
    """Install new package identified by `package_specifier` to make it available for environments."""
    package_dir = locate(package_specifier)
    if os.path.exists(package_dir):
        return
    os.makedirs(package_dir)
    command = f"pip install --target={package_dir} {package_specifier}"
    try:
        subprocess.check_output(command, shell=True)
    except Exception as ex:
        shutil.rmtree(package_dir)
        raise RuntimeError(f"Error while installing package '{package_specifier}'") from ex
    make_link(package_specifier)
