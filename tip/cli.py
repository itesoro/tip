import os
import sys
import json
import shutil
import importlib
import contextlib
import subprocess
from importlib.util import module_from_spec, spec_from_file_location\

import rich
import rich.tree
import click

from tip.tip_meta_finder import TipMetaFinder


@click.group()
def app():
    """TIP package manager."""
    pass


@app.command()
@click.option('--env', '-e', 'environment_path')
@click.argument('packages', type=str, nargs=-1)
def install(packages: tuple[str], environment_path: str):
    """
    Download and install PACKAGES to make them runnable with `tip run`.

    In order to run this command make sure you have set the TIP_SITE_PACKAGES environment variable. It must contain
    an absolute path to a folder where the packages will be downloaded.
    """
    packages = list(packages)
    if environment_path is not None:
        environment = _read_environment(environment_path)
        packages.extend([f"{package_name}=={package_version}" for package_name, package_version in environment.items()])
    _validate_package_names(packages)
    for package in packages:
        _install_package(package)


@app.command()
@click.option('--env', '-e', 'environment_path')
@click.argument('packages', type=str, nargs=-1)
def remove(packages: tuple[str], environment_path: str):
    """
    Remove PACKAGES from the environment.
    """
    packages = list(packages)
    if environment_path is not None:
        environment = _read_environment(environment_path)
        packages.extend([f"{package_name}=={package_version}" for package_name, package_version in environment.items()])
    if len(packages) == 0:
        click.echo("No packages to remove")
        return
    _validate_package_names(packages)
    for package in packages:
        _remove_package(package)


@app.command(name='list')
def list_():
    """
    Show installed packages.
    """
    site_packages_path = os.environ['TIP_SITE_PACKAGES']
    tree = rich.tree.Tree(site_packages_path)
    package_names = os.listdir(site_packages_path)
    for package_name in package_names:
        package_versions = sorted(os.listdir(os.path.join(site_packages_path, package_name)))
        if len(package_versions) > 0:
            package_tree = tree.add(f"📦 {package_name}")
        for package_version in package_versions:
            package_tree.add(package_version)
    rich.print(tree)


@app.command(context_settings={'ignore_unknown_options': True})
@click.option('-m', '--module', 'module_name', type=str)
@click.option('--env', '-e', 'environment_path')
@click.option('--install-missing', 'install_missing', is_flag=True)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def run(module_name: str, environment_path: str, install_missing: bool, args: tuple[str]):
    """
    Run a module or a script using given environment at ENVIRONMENT_PATH.

    In order to use environment all packages must be installed.
    """
    is_module_name_given = isinstance(module_name, str) and len(module_name) > 0
    is_python_file_path_given = not is_module_name_given and len(args) > 0
    if not (is_module_name_given or is_python_file_path_given):
        raise click.ClickException("Provide one of --module or python_file_path must be given")
    if is_python_file_path_given:
        python_file_path = args[0]
    if environment_path is None:
        environment_path = 'environment.json'
    environment = _read_environment(environment_path)
    if install_missing:
        _install_missing(environment)
    packages_to_folders = _map_packages_to_folders(environment)
    finder = TipMetaFinder(packages_to_folders)
    sys.meta_path.insert(0, finder)
    if is_python_file_path_given:
        _run_file(python_file_path, args)
    else:
        _run_module(module_name, args)


def _run_module(name: str, args):
    module_name = "__main__"
    with _disable_pycache():
        module = importlib.import_module(name)
        main_path = os.path.join(module.__path__[0], "__main__.py")
        sys.argv = [main_path] + list(args)
        main_spec = spec_from_file_location(module_name, main_path)
        main_module = module_from_spec(main_spec)
        sys.modules[module_name] = main_module
        main_spec.loader.exec_module(main_module)


def _run_file(filename: str, args):
    module_name = "__main__"
    sys.argv = [filename] + list(args)
    spec = spec_from_file_location(module_name, filename)
    with _disable_pycache():
        module_to_run = module_from_spec(spec)
        sys.modules[module_name] = module_to_run
        spec.loader.exec_module(module_to_run)


def _remove_package(package: str):
    package_name, package_version = package.split('==')
    package_dir = os.path.join(os.environ['TIP_SITE_PACKAGES'], package_name, package_version)
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
        click.echo(f'Removed {package_name}=={package_version}')
    else:
        click.echo(f'Package {package_name} not found, skipping')


@contextlib.contextmanager
def _disable_pycache():
    old_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.dont_write_bytecode = old_dont_write_bytecode


def _install_missing(environment: dict):
    for package_name, package_version in environment.items():
        _install_package(f"{package_name}=={package_version}")


def _read_environment(environment_path: str) -> dict:
    try:
        with open(environment_path, mode='r') as environment_file:
            return json.load(environment_file)
    except Exception as ex:
        raise click.ClickException(f'Couldn\'t read environment file "{environment_path}": {ex}')


def _install_package(package: str):
    package_name, package_version = package.split('==')
    package_dir = _get_package_dir(package_name, package_version)
    if os.path.exists(package_dir):
        click.echo(f"Package '{package}' is already installed")
        return
    os.makedirs(package_dir, exist_ok=True)
    command = f"pip install --target={package_dir} {package}"
    try:
        subprocess.check_output(command, shell=True)
    except Exception as ex:
        shutil.rmtree(package_dir)
        raise click.ClickException(f'Error while installing package "{package}: {ex}"')


def _map_packages_to_folders(environment: dict) -> dict:
    packages_to_folders = {}
    for package_name, package_version in environment.items():
        package_dir = _get_package_dir(package_name, package_version)
        if not os.path.isdir(package_dir):
            raise click.ClickException(f"Package '{package_name}=={package_version}' is not installed")
        package_files = os.listdir(package_dir)
        package_subpackages = [entry.removesuffix('.py') for entry in package_files
                               if _is_package_or_module(os.path.join(package_dir, entry))]
        for subpackage in package_subpackages:
            packages_to_folders[subpackage] = package_dir
    return packages_to_folders


def _is_package_or_module(name: str) -> bool:
    is_package = os.path.exists(os.path.join(name, '__init__.py'))
    is_module = name.endswith('.py')
    return is_package or is_module


def _validate_package_names(packages: tuple[str]):
    for package_name in packages:
        if '==' not in package_name:
            raise click.ClickException(
                f'Invalid package name: {package_name}, expected format: <package_name>==<package_version>'
            )


def _get_package_dir(package_name: str, package_version: str) -> str:
    packages_dir = os.getenv('TIP_SITE_PACKAGES')
    if packages_dir is None:
        raise click.ClickException("TIP_SITE_PACKAGES environment variable is not set")
    package_dir = os.path.join(packages_dir, package_name, package_version)
    return package_dir
