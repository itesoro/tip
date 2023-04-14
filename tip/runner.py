import os
import sys
import code
import importlib
import contextlib
from importlib.util import module_from_spec, spec_from_file_location

import click

from tip.config import pass_config
from tip import environment, packages
from tip.tip_meta_finder import TipMetaFinder


@click.command()
@click.option('-m', '--module', 'module_name', type=str)
@click.option('-c', 'command')
@click.option('--install-missing', 'install_missing', is_flag=True)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@pass_config
def tipython(module_name: str, command: str, install_missing: bool, args: tuple[str], config):
    """
    Run a module, file, or command with access to all packages installed in the current TIP installation.

    The common use case for this utility is as a VSCode interpreter. Instead of creating multiple executables for each
    environment, this single utility can access all the packages.
    """
    if (tip_home := config.get('tip_home')) is None:
        raise click.ClickException("No user configuration found, run `tip init` first")
    sys.path.insert(0, packages.get_links_dir(tip_home))
    return run(tip_home, module_name, command, None, install_missing, args)


def run_in_env(
        module_name: str,
        command: str,
        tip_home: str,
        environment_name: str,
        install_missing: bool,
        args: tuple[str]
    ):
    """Run given module, command or file using environment `environment_name`."""
    environment_path = environment.get_environment_by_name(tip_home, environment_name)
    run(tip_home, module_name, command, environment_path, install_missing, args)


def run(
        tip_home: str,
        module_name: str,
        command: str,
        environment_path: str | None,
        install_missing: bool,
        args: tuple[str]
    ):
    """Run given module, command or file using environment at `environment_path`."""
    is_module_name_given = isinstance(module_name, str) and len(module_name) > 0
    is_command_given = isinstance(command, str) and len(command) > 0
    is_python_file_path_given = not (is_module_name_given or is_command_given) and len(args) > 0
    if is_python_file_path_given:
        python_file_path = args[0]
    env = environment.get_environment_by_path(environment_path) if environment_path is not None else {}
    if install_missing:
        package_specifiers = [packages.make_package_specifier(name, version) for name, version in env.items()]
        packages.install(tip_home, package_specifiers)
    packages_to_folders = _map_packages_to_folders(tip_home, env)
    finder = TipMetaFinder(packages_to_folders)
    sys.meta_path.insert(0, finder)
    _remove_external_imports()
    if is_python_file_path_given:
        _run_file(python_file_path, args)
    elif is_module_name_given:
        _run_module(module_name, args)
    elif is_command_given:
        ns = {}
        exec(command, ns, ns)
    else:
        code.InteractiveConsole(locals=globals()).interact()


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
    sys.argv = list(args)
    spec = spec_from_file_location(module_name, filename)
    with _disable_pycache():
        module_to_run = module_from_spec(spec)
        sys.modules[module_name] = module_to_run
        _remove_external_imports()
        spec.loader.exec_module(module_to_run)


def _remove_external_imports():
    cached_modules = list(sys.modules)
    for module_name in cached_modules:
        if module_name.startswith('rich'):
            del sys.modules[module_name]
        elif module_name.startswith('click'):
            del sys.modules[module_name]


@contextlib.contextmanager
def _disable_pycache():
    old_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.dont_write_bytecode = old_dont_write_bytecode


def _map_packages_to_folders(tip_home: str, env: dict) -> dict:
    packages_to_folders = {}
    for package_name, package_version in env.items():
        package_dir = packages.locate(tip_home, f"{package_name}=={package_version}")
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
