# pylint: disable=redefined-outer-name
import os

from setuptools import setup


def create_tip_dir():
    tip_dir = os.path.expanduser(os.getenv('TIP_DIR', os.path.join('~', '.tip')))
    os.makedirs(tip_dir, exist_ok=True)
    return tip_dir


def init_config(tip_dir):
    from tip.config import pass_config

    @pass_config
    def _init_config(tip_dir, config):
        config['tip_dir'] = tip_dir
        config['active_environment_name'] = config.get('active_environment_name', 'base')

    _init_config(tip_dir)  # pylint: disable=no-value-for-parameter


def ensure_base_exists(tip_dir):
    from tip import environments
    base_path = environments.locate(tip_dir, "base")
    if not os.path.exists(base_path):
        environments.save_environment({}, base_path)


tip_dir = create_tip_dir()
setup()
init_config(tip_dir)
ensure_base_exists(tip_dir)
