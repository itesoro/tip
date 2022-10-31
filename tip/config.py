import os


def get_package_dir(package_name: str, package_version: str) -> str:
    packages_dir = get_packages_dir()
    package_dir = os.path.join(packages_dir, package_name, package_version)
    return package_dir


def get_packages_dir() -> str:
    tip_home = get_tip_home()
    packages_dir = os.path.join(tip_home, "site-packages")
    if not os.path.isdir(packages_dir):
        os.makedirs(packages_dir)
    return packages_dir


def get_environments_dir() -> str:
    tip_home = get_tip_home()
    environments_dir = os.path.join(tip_home, "environments")
    if not os.path.isdir(environments_dir):
        os.makedirs(environments_dir)
    return environments_dir


def get_tip_home() -> str:
    tip_home = os.getenv('TIP_HOME')
    if tip_home is None:
        raise RuntimeError("TIP_HOME environment variable is not set")
    if not os.path.isdir(tip_home):
        raise RuntimeError("TIP_HOME is not a directory")
    return tip_home


def get_active_environment_name() -> str | None:
    """Get active environment name if it's set."""
    return os.getenv("TIP_ACTIVE_ENV", None)
