import os
import json
import shutil
import tempfile
import subprocess
from collections import deque

from tip import cache, config
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
    queue = deque(package_specifiers)
    with tempfile.TemporaryDirectory() as temp_dir:
        while len(queue) > 0:
            package_specifier = queue.popleft()
            if not is_valid(package_specifier):
                raise RuntimeError(f"Invalid package specifier: {package_specifier!r}")
            if is_installed(package_specifier):
                continue
            download_output = subprocess.check_output(
                f"pip download --no-deps {package_specifier}",
                shell=True,
                cwd=temp_dir
            )
            wheel_path = os.path.join(temp_dir, download_output.decode('utf8').split('\n')[-3].replace('Saved ', ''))
            dry_run_report_path = os.path.join(temp_dir, 'dry-run-report.json')
            subprocess.run(f"pip install --dry-run {wheel_path} --report {dry_run_report_path}", shell=True, check=True)
            dependencies = []
            with open(dry_run_report_path) as report_file:
                dry_run_report = json.load(report_file)
                for package in dry_run_report['install']:
                    package_metadata = package['metadata']
                    dependencies.append(f"{package_metadata['name']}=={package_metadata['version']}")
            _install(package_specifier, wheel_path=wheel_path, dependencies=dependencies)
            queue.extend(dependencies)


def make_link(package_specifier: str):
    """Make link to package identified by `package_specifier` in links directory."""
    os.makedirs(config.LINKS_DIR, exist_ok=True)
    package_dir = locate(*parse_package_specifier(package_specifier))
    for folder_name in os.listdir(package_dir):
        folder_path = os.path.join(package_dir, folder_name)
        link_path = os.path.join(config.LINKS_DIR, folder_name)
        if os.path.islink(link_path):
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


def _install(package_specifier: str, /, *, wheel_path: str = None, dependencies=None):
    """
    Install new package identified by `package_specifier` to make it available for environments.

    If `wheel_path` it will be used to install the package without redownloading its wheel.
    """
    package_name, package_version = parse_package_specifier(package_specifier)
    package_dir = locate(package_name, package_version)
    if os.path.exists(package_dir):
        return
    os.makedirs(package_dir)
    command = f"pip install --target={package_dir} --no-deps {wheel_path or package_specifier}"
    try:
        subprocess.run(command, shell=True, check=True)
    except Exception as ex:
        shutil.rmtree(package_dir)
        raise RuntimeError(f"Error while installing package {package_specifier!r}") from ex
    with open(os.path.join(package_dir, "dependencies.json"), mode='w') as dependencies_file:
        json.dump(dependencies or {}, dependencies_file)
    cache.get(package_dir)  # Invalidate cache
    make_link(package_specifier)
