# pylint: disable=redefined-outer-name
import os
import sys
import json
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
    config_path = os.path.join(TIP_DIR, "config.json")
    if os.path.exists(config_path):
        return
    config = {
        'site_packages_dir': os.path.join(TIP_DIR, 'site-packages'),
        'active_environment_name': 'base'
    }
    with open(config_path, mode='w+', encoding='utf8') as config_file:
        json.dump(config, config_file)


def ensure_base_exists():
    environments_dir = os.path.join(TIP_DIR, 'environments')
    os.makedirs(environments_dir, exist_ok=True)
    base_env_path = os.path.join(environments_dir, 'base.json')
    if os.path.exists(base_env_path):
        return
    with open(base_env_path, mode='w+', encoding='utf8') as base_env:
        json.dump({}, base_env)


def prepare_scripts():
    _make_script('tip')
    _make_script('tipython')
    _add_tip_to_path()


def _add_tip_to_path():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
    import tip
    rcfile_path = tip.shell.find_rcfile_path()
    if rcfile_path is None:
        return
    with tip.shell.patch_config(rcfile_path) as tip_shell_config:
        tip_shell_config.write(f'export PATH={TIP_DIR}/bin:$PATH')


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
prepare_scripts()
