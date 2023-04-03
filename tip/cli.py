import os
import sys
import code
import json
import importlib
import contextlib
from importlib.util import module_from_spec, spec_from_file_location

import rich
import rich.tree
import click

from tip import config, environment, packages
from tip.tip_meta_finder import TipMetaFinder


@click.group()
def app():
    """TIP package manager."""
    pass


@app.command()
@click.argument('home', type=str)
def init(home):
    """
    Initialize user configuration file and tip home folder at HOME.
    """
    if os.path.isfile(home):
        raise click.ClickException(f"{home} is a file")
    if not os.path.exists(home):
        os.makedirs(home)
    else:
        click.echo('Home directory already exists')
    user_config_path = config.get_config_path()
    if os.path.isdir(user_config_path):
        raise click.ClickException(f"{user_config_path} must be a file, found directory")
    if not config.exists():
        base_environment_path = os.path.join(home, "environments", "base.json")
        os.makedirs(os.path.dirname(base_environment_path), exist_ok=True)
        if not os.path.exists(base_environment_path):
            environment.create_environment_file({}, base_environment_path)
        config.update(
            active_environment_name='base',
            tip_home=home
        )
    else:
        with open(user_config_path, mode='r') as user_config_file:
            try:
                user_config = json.load(user_config_file)
            except Exception as ex:
                raise click.ClickException(f"Invalid user configuration file: {ex}")
        user_config['home_dir'] = home
        with open(user_config_path, mode='w') as user_config_file:
            json.dump(user_config, user_config_file)
    

@app.command()
@click.argument('environment_name', type=str)
def activate(environment_name: str):
    """Make environment ENVIRONMENT_NAME active."""
    if not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    try:
        user_config = config.get_user_config()
    except Exception as ex:
        raise click.ClickException(f"User Config is invalid: {ex}")
    if not environment.exists(environment_name):
        raise click.ClickException(f"Environment {environment_name} not found, create with `tip create`")
    config.update(
        active_environment_name=environment_name,
        tip_home=user_config['home_dir']
    )


@app.command()
def active_env():
    """Print currently acitve env."""
    if not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    try:
        user_config = config.get_user_config()
        click.echo(user_config['active_environment_name'])
    except Exception as ex:
        raise click.ClickException(f"Invalid user configuration file: {ex}")


@app.command()
@click.option('--env', '-e', 'environment_path', type=str)
@click.argument('package_strings', type=str, nargs=-1)
def install(package_strings: tuple[str], environment_path: str):
    """
    Download and install packages by PACKAGE_STRINGS to make them runnable with `tip run`.

    PACKAGE_STRINGS is an array of package strings "<package_name>==<package_version>". In order to run this command
    make sure you have set the TIP_HOME environment variable. It must contain an absolute path to a folder where the
    packages will be downloaded.
    """
    if not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    _install(package_strings, environment_path)


@app.command()
@click.argument('package_strings', type=str, nargs=-1)
def uninstall(package_strings: tuple[str]):
    """
    Remove packages identified by package strings from site-packages.
    """
    existing_package_strings = []
    for package_string in package_strings:
        if not packages.is_valid(package_string):
            click.ClickException("Incorrect package string '%s'", package_string)
        if not packages.is_installed(package_string):
            click.echo(f"Package '{package_string}' is already removed, skipping")
        else:
            existing_package_strings.append(package_string)
    for package_string in existing_package_strings:
        packages.uninstall(package_string)


@app.command(name='list')
def list_():
    """
    Show installed packages.
    """
    if not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    site_packages_path = config.get_packages_dir()
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
@click.option('-c', 'command')
@click.option('--install-missing', 'install_missing', is_flag=True)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def run(module_name: str, command: str, environment_path: str, install_missing: bool, args: tuple[str]):
    """
    Run a module or a script using given environment at ENVIRONMENT_PATH.

    In order to use environment all packages must be installed.
    """
    if not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    return _run(module_name, command, environment_path, install_missing, args)


@app.command()
@click.argument('environment_name', type=str)
def create(environment_name: str):
    """Create new environment."""
    if not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    path = os.path.join(config.get_environments_dir(), environment_name + '.json')
    try:
        environment.create_environment_file(None, path)
    except RuntimeError as ex:
        raise click.ClickException(ex)


@app.command()
@click.option('--from_path', '-f', 'from_path', type=str, help="Environment to add all packages from")
@click.argument('package_strings', type=str, nargs=-1)
@click.option(
    '--environment_path', '-e', 'environment_path', type=str,
    help="Path of the environment to add packages to"
)
def add(package_strings: tuple[str], environment_path: str, from_path: str):
    """
    Add packages to the environment.

    If ENVIRONMENT_PATH is specified, then packages are added to that environment, otherwise activated environment is
    used. If FROM_PATH is specified, then all packages from that environment are also added to the target environment.
    """
    packages_to_add = []
    if from_path:
        env = environment.get_environment_by_path(from_path)
        for package_name, package_version in env.items():
            packages_to_add.append(f"{package_name}=={package_version}")
    packages_to_add.extend(package_strings)
    maybe_environment_path = environment_path if environment_path else None
    for package_string in packages_to_add:
        environment.add_to_environment(package_string, path=maybe_environment_path, replace=True)


def _run(module_name: str, command: str, environment_path: str, install_missing: bool, args: tuple[str]):
    is_module_name_given = isinstance(module_name, str) and len(module_name) > 0
    is_command_given = isinstance(command, str) and len(command) > 0
    is_python_file_path_given = not (is_module_name_given or is_command_given) and len(args) > 0
    if is_python_file_path_given:
        python_file_path = args[0]
    if environment_path:
        env = environment.get_environment_by_path(environment_path)
    else:
        env = environment.get_active_environment()
    if env is None:
        raise click.ClickException("Activate environment or provide environment path using `--env`")
    if install_missing:
        package_strings = [f"{name}=={version}" for name, version in env.items()]
        _install(package_strings)
    packages_to_folders = _map_packages_to_folders(env)
    finder = TipMetaFinder(packages_to_folders)
    sys.path.append(config.get_links_dir())
    sys.meta_path.insert(0, finder)
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
        spec.loader.exec_module(module_to_run)


def _install(package_strings: tuple[str], environment_path: str = None):
    for package_string in package_strings:
        if packages.is_valid(package_string):
            continue
        raise click.ClickException("Invalid package string: '%s'", package_string)
    if environment_path is not None:
        env = environment.get_environment_by_path(environment_path)
        env_package_strings = [f"{name}=={version}" for name, version in env.items()]
    else:
        env_package_strings = []
    package_strings = list(package_strings) + env_package_strings
    for package_string in package_strings:
        packages.install(package_string)


@contextlib.contextmanager
def _disable_pycache():
    old_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.dont_write_bytecode = old_dont_write_bytecode


def _map_packages_to_folders(env: dict) -> dict:
    packages_to_folders = {}
    for package_name, package_version in env.items():
        package_dir = packages.locate(f"{package_name}=={package_version}")
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
