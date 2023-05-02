import os
import sys
from typing import no_type_check

import rich
import click
import rich.tree

from tip import config, packages, runner
from tip.config import LINKS_DIR
from tip.environment import Environment


@click.group()
def app():
    """TIP package manager."""


@app.command()
@click.argument('environment_name', type=str)
def activate(environment_name: str):
    """Make environment ENVIRONMENT_NAME active."""
    environment_path = Environment.locate(environment_name)
    if not os.path.isfile(environment_path):
        raise click.ClickException(f"Environment {environment_name} doesn't exist")
    config['active_environment_name'] = environment_name  # pylint: disable=unsupported-assignment-operation


@app.command()
def info():
    """Display information about current tip environment."""
    site_packages_dir = config.get('site_packages_dir')
    active_env_name = config.get('active_environment_name')
    active_env_path = Environment.locate(active_env_name)
    click.echo(f"active env: {active_env_name}")
    click.echo(f"active env location: {active_env_path}")
    click.echo(f"site-packages directory: {site_packages_dir}")


@app.command()
@click.option('--env', '-e', 'environment_path', type=str, default=None)
@click.argument('package_specifiers', type=str, nargs=-1)
def install(package_specifiers: list[str], environment_path: str | None):
    """Download and install packages by PACKAGE_SPECIFIERS to make them runnable with `tip run`."""
    if environment_path is not None:
        env = Environment.load(path=environment_path)
    else:
        env = Environment.load(name=config.get('active_environment_name'))
    try:
        packages.install(package_specifiers)
        for package_specifier in package_specifiers:
            env.add_package(package_specifier)
        env.save()
    except Exception as ex:
        raise click.ClickException(str(ex))


@app.command()
@click.argument('package_specifiers', type=str, nargs=-1)
def uninstall(package_specifiers: tuple[str]):
    """Uninstall packages identified by package specifiers from site-packages."""
    existing_package_specifiers = []
    for package_specifier in package_specifiers:
        if not packages.is_valid(package_specifier):
            raise click.ClickException(f"Incorrect package specifier {package_specifier}")
        if not packages.is_installed(package_specifier):
            click.echo(f"Package '{package_specifier}' is not installed, skipping")
        else:
            existing_package_specifiers.append(package_specifier)
    for package_specifier in existing_package_specifiers:
        packages.uninstall(package_specifier)


@app.command(name='list')
@click.option('--active-env', '-a', 'active_env', is_flag=True)
@click.option('--path', '-p', 'env_path', type=str, default="")
@click.option('--name', '-n', 'env_name', type=str, default="")
@no_type_check
def list_(active_env: bool, env_path: str, env_name: str):
    """Displays tree: ACTIVE_ENV, ENV_PATH or ENV_NAME environment packages or installed packages without options."""
    if not _at_most_one(active_env, env_path != "", env_name != ""):
        raise click.ClickException("At most one of ACTIVE_ENV, ENV_PATH or ENV_NAME should be specified")
    if active_env:
        tree = _make_environment_packages_tree(Environment.locate(config.get('active_environment_name')))
    elif env_path != "":
        tree = _make_environment_packages_tree(env_path)
    elif env_name != "":
        tree = _make_environment_packages_tree(Environment.locate(env_name))
    else:
        tree = _make_installed_packages_tree()
    rich.print(tree)


@app.command(context_settings={'ignore_unknown_options': True})
@click.option('-m', '--module', 'module_name', type=str)
@click.option('--env', '-e', 'environment_path', type=str)
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
        Environment({}, Environment.locate(environment_name)).save()
    except RuntimeError as ex:
        raise click.ClickException(ex)  # type: ignore


@app.command()
@click.option('--from_path', '-f', 'from_path', type=str, help="Environment to add all packages from")
@click.argument('package_specifiers', type=str, nargs=-1)
@click.option(
    '--environment_path', '-e', 'environment_path', type=str,
    help="Path of the environment to add packages to", required=False, default=None
)
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
@click.option('--environment_path', '-e', 'environment_path', type=str, default=None)
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
            click.echo(f"Package {package_specifier} not in environment")
        except ValueError:
            click.echo(f"Package {package_specifier} is in environment with different version")


def _at_most_one(*args: bool) -> bool:
    """Returns True if at most one of the arguments is True."""
    return sum(args) <= 1


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
