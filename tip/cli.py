import os

import click
import rich
import rich.tree

from tip.config import pass_config
from tip import environment, packages, runner
    


@click.group()
def app():
    """TIP package manager."""


@app.command()
@click.argument('tip_home_dir', type=str)
@pass_config
def init(tip_home_dir, config):
    """Initialize user configuration file and tip home folder at TIP_HOME_DIR."""
    if os.path.isfile(tip_home_dir):
        raise click.ClickException(f"{tip_home_dir} is a file")
    if not os.path.exists(tip_home_dir):
        os.makedirs(tip_home_dir)
    else:
        click.echo('Home directory already exists')
    config['tip_home'] = tip_home_dir
    config['active_environment_name'] = active_environment_name = config.get('active_environment_name', 'base')
    active_environment_path = environment.get_environment_path(tip_home_dir, active_environment_name)
    environment.save_environment(None, active_environment_path, rewrite=False)


@app.command()
@click.argument('environment_name', type=str)
@pass_config
def activate(environment_name: str, config):
    """Make environment ENVIRONMENT_NAME active."""
    if (tip_home := config.get('tip_home')) is None:
        raise click.ClickException("No user configuration found, run `tip init` first")
    environment_path = environment.get_environment_path(tip_home, environment_name)
    if not os.path.isfile(environment_path):
        raise click.ClickException(f"Environment {environment_name} doesn't exist")
    config['active_environment_name'] = environment_name


@app.command()
@pass_config
def info(config):
    """Display information about current tip environment."""
    if (tip_home := config.get('tip_home')) is None:
        raise click.ClickException("No user configuration found, run `tip init` first")
    active_env_name = config.get('active_environment_name')
    active_env_path = environment.get_environment_path(tip_home, active_env_name)
    click.echo(f"active env: {active_env_name}")
    click.echo(f"active env location: {active_env_path}")
    click.echo(f"home directory: {tip_home}")


@app.command()
@click.option('--env', '-e', 'environment_path', type=str, default=None)
@click.argument('package_specifiers', type=str, nargs=-1)
@pass_config
def install(package_specifiers: tuple[str], environment_path: str | None, config):
    """Download and install packages by PACKAGE_SPECIFIERS to make them runnable with `tip run`."""
    if (tip_home := config.get('tip_home')) is None:
        raise click.ClickException("No user configuration found, run `tip init` first")
    if environment_path is None:
        active_environment_name = config.get('active_environment_name')
        environment_path = environment.get_environment_path(tip_home, active_environment_name)
    try:
        packages.install(tip_home, package_specifiers, environment_path)
    except Exception as ex:
        raise click.ClickException(ex)


@app.command()
@click.argument('package_specifiers', type=str, nargs=-1)
@pass_config
def uninstall(package_specifiers: tuple[str], config):
    """Uninstall packages identified by package specifiers from site-packages."""
    if (tip_home := config.get('tip_home')) is None:
        raise click.ClickException("No user configuration found, run `tip init` first")
    existing_package_specifiers = []
    for package_specifier in package_specifiers:
        if not packages.is_valid(package_specifier):
            raise click.ClickException(f"Incorrect package specifier {package_specifier}")
        if not packages.is_installed(tip_home, package_specifier):
            click.echo(f"Package '{package_specifier}' is not installed, skipping")
        else:
            existing_package_specifiers.append(package_specifier)
    for package_specifier in existing_package_specifiers:
        packages.uninstall(tip_home, package_specifier)


@app.command(name='list')
@click.option('--active-env', '-a', 'is_active_env', is_flag=True)
@click.argument("environment_name_or_path", type=str, required=False, default=None)
@pass_config
def list_(is_active_env: bool, environment_name_or_path: str | None, config):
    """
    Show added or installed packages.

    If IS_ACTIVE_ENV is set, display packages from the active environment. If the ENVIRONMENT option is specified,
    display packages from the chosen environment. Otherwise, display all packages for the current TIP installation.
    """
    if is_active_env and environment_name_or_path is not None:
        raise click.ClickException("Only one of ACTIVE_ENV or ENVIRONMENT_PATH should be specified")
    if (tip_home := config.get('tip_home')) is None:
        raise click.ClickException("No user configuration found, run `tip init` first")
    packages_info = {}
    if environment_name_or_path is None and not is_active_env:
        site_packages_dir = packages.get_site_packages_dir(tip_home)
        tree = rich.tree.Tree(site_packages_dir)
        package_names = os.listdir(site_packages_dir)
        for package_name in package_names:
            package_versions = sorted(os.listdir(os.path.join(site_packages_dir, package_name)))
            packages_info[package_name] = package_versions
    else:
        if is_active_env:
            active_environment_name = config.get('active_environment_name')
            tree = rich.tree.Tree(active_environment_name)
            packages_info = environment.get_environment_by_name(tip_home, active_environment_name)
        else:
            tree = rich.tree.Tree(environment_name_or_path)
            try:
                packages_info = environment.get_environment_by_name(tip_home, environment_name_or_path)
            except FileNotFoundError:
                if os.path.isfile(environment_name_or_path):
                    packages_info = environment.get_environment_by_path(environment_name_or_path)
                else:
                    raise click.ClickException("Environment not found")
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
@click.option('--env', '-e', 'environment_path', type=str)
@click.option('-c', 'command')
@click.option('--install-missing', 'install_missing', is_flag=True)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@pass_config
def run(module_name: str, command: str, environment_path: str, install_missing: bool, args: tuple[str], config):
    """
    Run a module or a script using given environment at ENVIRONMENT_PATH.

    In order to use environment all packages must be installed or run with '--install-missing'.
    """
    if (tip_home := config.get('tip_home')) is None:
        raise click.ClickException("No user configuration found, run `tip init` first")
    if environment_path is None:
        active_environment_name = config.get('active_environment_name')
        environment_path = environment.get_environment_path(tip_home, active_environment_name)
    return runner.run(tip_home, module_name, command, environment_path, install_missing, args)


@app.command()
@click.argument('environment_name', type=str)
@pass_config
def create(environment_name: str, config):
    """Create new environment."""
    if (tip_home := config.get('tip_home')) is None:
        raise click.ClickException("No user configuration found, run `tip init` first")
    path = environment.get_environment_path(tip_home, environment_name)
    try:
        environment.save_environment(None, path)
    except RuntimeError as ex:
        raise click.ClickException(ex)


@app.command()
@click.option('--from_path', '-f', 'from_path', type=str, help="Environment to add all packages from")
@click.argument('package_specifiers', type=str, nargs=-1)
@click.option(
    '--environment_path', '-e', 'environment_path', type=str,
    help="Path of the environment to add packages to", required=False, default=None
)
@pass_config
def add(package_specifiers: tuple[str], environment_path: str | None, from_path: str, config):
    """
    Add packages to the environment.

    If ENVIRONMENT_PATH is specified, then packages are added to it, otherwise activated environment is affected. If
    FROM_PATH is specified, then all its packages are also added to the target environment.
    """
    if (tip_home := config.get('tip_home')) is None:
        raise click.ClickException("No user configuration found, run `tip init` first")
    packages_to_add = []
    if from_path:
        env = environment.get_environment_by_path(from_path)
        for package_name, package_version in env.items():
            packages_to_add.append(f"{package_name}=={package_version}")
    packages_to_add.extend(package_specifiers)
    active_environment_name = config.get('active_environment_name')
    environment_path = environment_path or environment.get_environment_path(tip_home, active_environment_name)
    for package_specifier in packages_to_add:
        environment.add_to_environment_at_path(package_specifier, environment_path, replace=True)


@app.command()
@click.argument('package_specifiers', type=str, nargs=-1)
@click.option('--environment_path', '-e', 'environment_path', type=str, default=None)
@pass_config
def remove(package_specifiers: tuple[str], environment_path: str | None, config):
    """
    Remove packages from the environment.

    If ENVIRONMENT_PATH is specified, then packages are removed from it, otherwise activated environment is affected.
    """
    if (tip_home := config.get('tip_home')) is None:
        raise click.ClickException("No user configuration found, run `tip init` first")
    active_environment_name = config.get('active_environment_name')
    environment_path = environment_path or environment.get_environment_path(tip_home, active_environment_name)
    for package_specifier in package_specifiers:
        try:
            environment.remove_from_environment_at_path(package_specifier, environment_path)
        except KeyError as ex:
            click.echo(f"Package {ex} not in environment")
        except ValueError as ex:
            click.echo(f"Specified version {package_specifier} not found, current version: {ex}")
