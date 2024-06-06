import os
import sys
import json
from collections import deque
from typing import no_type_check

import rich
import click
import rich.tree

from tip import cache, config, packages, runner
from tip.config import LINKS_DIR
from tip.environment import Environment


@click.group()
def app():
    """TIP package manager."""


@app.group(name="config")
def config_():
    """Configuration management."""


@app.command()
@click.argument('environment_name', type=str)
def activate(environment_name: str):
    """Make environment ENVIRONMENT_NAME active."""
    environment_path = Environment.locate(environment_name)
    if not os.path.isfile(environment_path):
        raise click.ClickException(f"Environment {environment_name!r} doesn't exist")
    config['active_environment_name'] = environment_name  # pylint: disable=unsupported-assignment-operation


@app.command()
def info():
    """Display information about current tip state."""
    site_packages_dir = config.get('site_packages_dir')
    active_env_name = config.get('active_environment_name')
    cache_dir = config.get('cache_dir')
    active_env_path = Environment.locate(active_env_name)
    click.echo(f"active env: {active_env_name!r}")
    click.echo(f"active env location: {active_env_path!r}")
    click.echo(f"site-packages directory: {site_packages_dir!r}")
    click.echo(f"cache directory: {cache_dir!r}")


@app.command()
@click.argument('package_specifiers', type=str, nargs=-1)
@click.option('--env', '-e', 'environment_path', type=str, default=None)
def install(package_specifiers: list[str], environment_path: str):
    """
    Download and install packages to make them runnable with `tip run`.

    When PACKAGE_SPECIFIERS is not empty, install all these packages. If given ENVIRONMENT_PATH, install all packages
    from this environment. Otherwise install packages from the active environment.
    """
    if not _at_most_one(package_specifiers, environment_path):
        raise click.ClickException("At most one of PACKAGE_SPECIFIERS or ENVIRONMENT_PATH should be specified")
    if len(package_specifiers) == 0:
        environment_path = environment_path or Environment.locate(config.get('active_environment_name'))
        env = Environment.load(path=environment_path)
        package_specifiers = [packages.make_package_specifier(k, v) for k, v in env.packages.items()]
    cache.clear()
    try:
        packages.install(package_specifiers)
    except Exception as ex:
        raise click.ClickException(str(ex))


@app.command()
@click.argument('package_specifiers', type=str, nargs=-1)
def uninstall(package_specifiers: tuple[str]):
    """Uninstall packages identified by package specifiers from site-packages."""
    cache.clear()
    existing_package_specifiers = []
    for package_specifier in package_specifiers:
        if not packages.is_valid(package_specifier):
            raise click.ClickException(f"Incorrect package specifier {package_specifier!r}")
        if not packages.is_installed(package_specifier):
            click.echo(f"Package {package_specifier!r} is not installed, skipping")
        else:
            existing_package_specifiers.append(package_specifier)
    for package_specifier in existing_package_specifiers:
        packages.uninstall(package_specifier)


@app.command(name='list')
@click.option('--env', '-e', 'environment_path', type=str, default=None)
@click.option('--installed', '-i', 'installed', is_flag=True, default=False)
@no_type_check
def list_(environment_path: str | None, installed: bool):
    """
    Show list of packages.

    If ENVIRONMENT_PATH is set, then display packages in this environment. If used with INSTALLED, displays all
    installed packages. Without these options it displays packages in the active environment
    """
    if not _at_most_one(environment_path, installed):
        raise click.ClickException("At most one of ENVIRONMENT_PATH or INSTALLED should be specified")
    if not installed:
        environment_path = environment_path or Environment.locate(config.get('active_environment_name'))
        tree = _make_environment_packages_tree(environment_path)
    else:
        tree = _make_installed_packages_tree()
    rich.print(tree)


@app.command()
@click.option('--env', '-e', 'environment_path', type=str, default=None)
def dependencies(environment_path: str | None):
    """
    Display dependencies of the dependencies.

    It shows dependencies of the packages that are in the environment  at ENVIRONMENT_PATH or in the active environment.
    It doesn't show packages that are present in the environment. This is helpful when you need to add these packages
    to the environment using `tip add` command.
    """
    if environment_path is None:
        env = Environment.load(name=config.get('active_environment_name'))
    else:
        env = Environment.load(path=environment_path)
    env_packages = [packages.make_package_specifier(k, v) for k, v in env.packages.items()]
    queue = deque(env_packages)
    seen = set(env_packages)
    dependencies_list = []
    while len(queue) > 0:
        package = queue.popleft()
        package_dir = packages.locate(*packages.parse_package_specifier(package))
        try:
            with open(os.path.join(package_dir, "dependencies.json")) as f:
                dependencies = json.load(f)
        except FileNotFoundError:
            click.echo(f"{package} is not installed or corrupted, skipping its dependencies")
            continue
        for dependency in dependencies:
            if dependency in seen:
                continue
            dependencies_list.append(dependency)
            queue.append(dependency)
            seen.add(dependency)
    if len(dependencies_list) > 0:
        click.echo(' '.join(dependencies_list))


@app.command(context_settings={'ignore_unknown_options': True})
@click.option('-m', '--module', 'module_name', type=str)
@click.option('--env', '-e', 'environment_path', type=str, default=None)
@click.option('-c', 'command')
@click.option('--install-missing', 'install_missing', is_flag=True)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def run(module_name: str, command: str, environment_path: str, install_missing: bool, args: tuple[str]):
    """
    Run a module or a script using given environment at ENVIRONMENT_PATH.

    In order to use environment all packages must be installed or run with '--install-missing'.
    """
    if environment_path is None:
        env = Environment.load(name=config.get('active_environment_name'))
    else:
        env = Environment.load(path=environment_path)
    return runner.run(module_name, command, env, install_missing, args)


@click.command()
@click.option('-m', '--module', 'module_name', type=str)
@click.option('-c', 'command')
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def tipython(module_name: str, command: str, args: tuple[str]):
    """
    Run a module, file, or command with access to all packages installed in the current TIP installation.

    The common use case for this utility is as a VSCode interpreter. Instead of creating multiple executables for each
    environment, this single utility can access all the packages.
    """
    sys.path.insert(0, LINKS_DIR)
    return runner.run(module_name, command, None, False, args)


@app.command()
@click.argument('environment_name', type=str)
def create(environment_name: str):
    """Create new environment."""
    try:
        Environment(path=Environment.locate(environment_name)).save()
    except RuntimeError as ex:
        raise click.ClickException(ex)  # type: ignore


@app.command()
@click.option('--from_path', '-f', 'from_path', type=str, help="Environment to add all packages from")
@click.argument('package_specifiers', type=str, nargs=-1)
@click.option('--env', '-e', 'environment_path', type=str, default=None)
def add(package_specifiers: tuple[str], environment_path: str | None, from_path: str):
    """
    Add packages to the environment.

    If ENVIRONMENT_PATH is specified, then packages are added to it, otherwise activated environment is affected. If
    FROM_PATH is specified, then all its packages are also added to the target environment.
    """
    packages_to_add = []
    if from_path:
        another_env = Environment.load(path=from_path)
        for name, version in another_env.packages.items():
            packages_to_add.append(f"{name}=={version}")
    packages_to_add.extend(package_specifiers)
    if environment_path is None:
        env = Environment.load(name=config.get('active_environment_name'))
    else:
        env = Environment.load(path=environment_path)
    for package_specifier in packages_to_add:
        env.add_package(package_specifier)
    env.save()


@app.command()
@click.argument('package_specifiers', type=str, nargs=-1)
@click.option('--env', '-e', 'environment_path', type=str, default=None)
def remove(package_specifiers: tuple[str], environment_path: str | None):
    """
    Remove packages from the environment.

    If ENVIRONMENT_PATH is specified, then packages are removed from it, otherwise activated environment is affected.
    """
    if environment_path is None:
        env = Environment.load(name=config.get('active_environment_name'))
    else:
        env = Environment.load(path=environment_path)
    for package_specifier in package_specifiers:
        try:
            env.remove_package(package_specifier)
        except KeyError:
            click.echo(f"Package {package_specifier!r} not in environment")
        except ValueError:
            click.echo(f"Package {package_specifier!r} is in environment with different version")
    env.save()


@config_.command('set')
@click.argument('key', type=str)
@click.argument('value', type=str)
def set_(key: str, value: str):
    """Set the config `key` to be `value`."""
    config[key] = value


@config_.command('unset')
@click.argument('key', type=str)
def unset(key: str):
    """Remove value of config named `key`."""
    config[key] = None


def _at_most_one(*args: bool) -> bool:
    """Returns True if at most one of the arguments is True."""
    return sum(bool(x) for x in args) <= 1


def _make_installed_packages_tree() -> rich.tree.Tree:
    site_packages_dir = config.get('site_packages_dir')
    tree = rich.tree.Tree(site_packages_dir)
    package_names = os.listdir(site_packages_dir)
    for package_name in package_names:
        package_versions = sorted(os.listdir(os.path.join(site_packages_dir, package_name)))
        if len(package_versions) == 0:
            continue
        package_tree = tree.add(f"📦 {package_name}")
        for version in package_versions:
            package_tree.add(version)
    return tree


def _make_environment_packages_tree(env_path: str) -> rich.tree.Tree:
    try:
        env = Environment.load(path=env_path)
    except FileNotFoundError as ex:
        raise click.ClickException("Environment not found") from ex
    tree = rich.tree.Tree(env_path)
    for name, version in env.packages.items():
        tree.add(f"📦 {name}").add(version)
    return tree
