import os
import json
import click

from .cli import _run


@click.command()
@click.option('-m', '--module', 'module_name', type=str)
@click.option('--env', '-e', 'environment_path')
@click.option('-c', 'command')
@click.option('--install-missing', 'install_missing', is_flag=True)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def tipr(module_name: str, command: str, environment_path: str, install_missing: bool, args: tuple[str]):
    return _run(module_name, command, environment_path, install_missing, args)
