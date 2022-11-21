import os
import json
import click

from .cli import _run
from .config import get_environments_dir, get_tip_home


@click.command()
@click.option('-m', '--module', 'module_name', type=str)
@click.option('--env', '-e', 'environment_path')
@click.option('-c', 'command')
@click.option('--install-missing', 'install_missing', is_flag=True)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def tip_run(module_name: str, command: str, environment_path: str, install_missing: bool, args: tuple[str]):
    with open(os.path.join(get_tip_home(), 'metadata.json')) as metadata_file:
        metadata = json.load(metadata_file)
    active_env = metadata['active_env']
    activated_environment_path = os.path.join(get_environments_dir(), active_env + '.json')
    return _run(module_name, command, activated_environment_path, install_missing, args)
