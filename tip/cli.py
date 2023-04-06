import os
import json

import click
import rich
import rich.tree

from tip import config, environment, packages, tipr


@click.group()
def app():
    """TIP package manager."""
    try:
        config.load_config()
    except FileNotFoundError:
        pass


@app.command()
@click.argument('home_dir', type=str)
def init(home_dir):
    """
    Initialize user configuration file and tip home folder at HOME.
    """
    if os.path.isfile(home_dir):
        raise click.ClickException(f"{home_dir} is a file")
    if not os.path.exists(home_dir):
        os.makedirs(home_dir)
    else:
        click.echo('Home directory already exists')
    user_config_path = config.get_config_path()
    if os.path.isdir(user_config_path):
        raise click.ClickException(f"{user_config_path} must be a file, found directory")
    if not config.exists():
        base_environment_path = os.path.join(home_dir, "environments", "base.json")
        os.makedirs(os.path.dirname(base_environment_path), exist_ok=True)
        if not os.path.exists(base_environment_path):
            environment.create_environment_file({}, base_environment_path)
        config.update(
            active_environment_name='base',
            tip_home=home_dir
        )
    else:
        with open(user_config_path, mode='r', encoding='utf8') as user_config_file:
            try:
                user_config = json.load(user_config_file)
            except Exception as ex:
                raise click.ClickException(f"Invalid user configuration file: {ex}")
        user_config['home_dir'] = home_dir
        with open(user_config_path, mode='w', encoding='utf8') as user_config_file:
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
def info():
    """Display information about current tip environment."""
    if not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    tip_home = config.get_tip_home()
    active_env_name = config.get_active_environment_name()
    active_env_path = environment.get_environment_path(active_env_name)
    click.echo(f"active env: {active_env_name}")
    click.echo(f"active env location: {active_env_path}")
    click.echo(f"home directory: {tip_home}")


@app.command()
@click.option('--env', '-e', 'environment_path', type=str)
@click.argument('package_specifiers', type=str, nargs=-1)
def install(package_specifiers: tuple[str], environment_path: str):
    """
    Download and install packages by PACKAGE_SPECIFIERS to make them runnable with `tip run`.

    PACKAGE_SPECIFIERS is an array of package specifiers "<package_name>==<package_version>". In order to run this
    command make sure you have set the TIP_HOME environment variable. It must contain an absolute path to a folder where
    the packages will be downloaded.
    """
    if not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    try:
        packages.install(package_specifiers, environment_path)
    except Exception as ex:
        raise click.ClickException(ex)


@app.command()
@click.argument('package_specifiers', type=str, nargs=-1)
def uninstall(package_specifiers: tuple[str]):
    """
    Remove packages identified by package specifiers from site-packages.
    """
    if not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    existing_package_specifiers = []
    for package_specifier in package_specifiers:
        if not packages.is_valid(package_specifier):
            raise click.ClickException(f"Incorrect package specifier {package_specifier}")
        if not packages.is_installed(package_specifier):
            click.echo(f"Package '{package_specifier}' is already removed, skipping")
        else:
            existing_package_specifiers.append(package_specifier)
    for package_specifier in existing_package_specifiers:
        packages.uninstall(package_specifier)


@app.command(name='list')
@click.option('--active-env', '-a', 'is_active_env', is_flag=True)
@click.argument("environment_name_or_path", type=str, required=False)
def list_(is_active_env: bool, environment_name_or_path: str | None = None):
    """
    Show added or installed packages.

    If IS_ACTIVE_ENV is set, display packages from the active environment. If the ENVIRONMENT option is specified,
    display packages from the chosen environment. Otherwise, display all packages for the current TIP installation.
    """
    if is_active_env and environment_name_or_path is not None:
        raise click.ClickException("Only one of ACTIVE_ENV or ENVIRONMENT_PATH should be specified")
    if not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    packages_info = {}
    if environment_name_or_path is None and not is_active_env:
        site_packages_path = config.get_site_packages_dir()
        tree = rich.tree.Tree(site_packages_path)
        package_names = os.listdir(site_packages_path)
        for package_name in package_names:
            package_versions = sorted(os.listdir(os.path.join(site_packages_path, package_name)))
            packages_info[package_name] = package_versions
    else:
        if is_active_env:
            tree = rich.tree.Tree(config.get_active_environment_name())
            packages_info = environment.get_active_environment()
        else:
            tree = rich.tree.Tree(environment_name_or_path)
            try:
                packages_info = environment.get_environment_by_name(environment_name_or_path)
            except FileNotFoundError:
                packages_info = environment.get_environment_by_path(environment_name_or_path)
        packages_info = {k: [v] for k, v in packages_info.items()}
    if len(packages_info) == 0:
        click.echo("No packages found!")
        return
    for package_name, package_versions in packages_info.items():
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
    return tipr.run(module_name, command, environment_path, install_missing, args)


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
@click.argument('package_specifiers', type=str, nargs=-1)
@click.option(
    '--environment_path', '-e', 'environment_path', type=str,
    help="Path of the environment to add packages to", required=False
)
def add(package_specifiers: tuple[str], environment_path: str | None, from_path: str):
    """
    Add packages to the environment.

    If ENVIRONMENT_PATH is specified, then packages are added to it, otherwise activated environment is affected. If
    FROM_PATH is specified, then all its packages are also added to the target environment.
    """
    if environment_path is None and not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    packages_to_add = []
    if from_path:
        env = environment.get_environment_by_path(from_path)
        for package_name, package_version in env.items():
            packages_to_add.append(f"{package_name}=={package_version}")
    packages_to_add.extend(package_specifiers)
    maybe_environment_path = environment_path or None
    for package_specifier in packages_to_add:
        environment.add_to_environment(package_specifier, path=maybe_environment_path, replace=True)


@app.command()
@click.argument('package_specifiers', type=str, nargs=-1)
@click.option('--environment_path', '-e', 'environment_path', type=str)
def remove(package_specifiers: tuple[str], environment_path: str | None = None):
    """
    Remove packages from the environment.

    If ENVIRONMENT_PATH is specified, then packages are removed from it, otherwise activated environment is affected.
    """
    if environment_path is None and not config.exists():
        raise click.ClickException("No user configuration found, run `tip init` first")
    for package_specifier in package_specifiers:
        try:
            environment.remove_from_environment(package_specifier, path=environment_path)
        except KeyError as ex:
            click.echo(f"Package {ex} not in environment")
        except ValueError as ex:
            click.echo(f"Specified version {package_specifier} not found, current version: {ex}")
