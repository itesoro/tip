# pylint: disable=redefined-outer-name
import os
import sys
import stat

from setuptools import setup


TIP_DIR = os.path.expanduser(os.getenv('TIP_DIR', os.path.join('~', '.tip')))
SCRIPT_TEMPLATE = r"""
#!{executable}
# EASY-INSTALL-ENTRY-SCRIPT: 'tip','console_scripts','{entrypoint}'
import re
import sys

# for compatibility with easy_install; see #2198
__requires__ = 'tip'

try:
    from importlib.metadata import distribution
except ImportError:
    try:
        from importlib_metadata import distribution
    except ImportError:
        from pkg_resources import load_entry_point


def importlib_load_entry_point(spec, group, name):
    dist_name, _, _ = spec.partition('==')
    matches = (
        entry_point
        for entry_point in distribution(dist_name).entry_points
        if entry_point.group == group and entry_point.name == name
    )
    return next(matches).load()


globals().setdefault('load_entry_point', importlib_load_entry_point)


if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(load_entry_point('tip', 'console_scripts', '{entrypoint}')())
""".strip()


def init_config():
    from tip.config import pass_config

    @pass_config
    def _init_config(config):
        config['tip_dir'] = TIP_DIR
        config['active_environment_name'] = config.get('active_environment_name', 'base')

    _init_config()  # pylint: disable=no-value-for-parameter


def ensure_base_exists():
    from tip import environments
    base_path = environments.locate(TIP_DIR, "base")
    if not os.path.exists(base_path):
        environments.save_environment({}, base_path)


def make_scripts():
    _make_script('tip')
    _make_script('tipython')


def _make_script(entrypoint):
    bin_dir = os.path.join(TIP_DIR, 'bin')
    os.makedirs(bin_dir, exist_ok=True)
    script_path = os.path.join(bin_dir, entrypoint)
    with open(script_path, mode='w+', encoding='utf8') as script_file:
        script_file.write(SCRIPT_TEMPLATE.format(executable=sys.executable, entrypoint=entrypoint))
    os.chmod(script_path, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)


os.makedirs(TIP_DIR, exist_ok=True)
setup()
init_config()
ensure_base_exists()
make_scripts()
