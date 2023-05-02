# pylint: disable=consider-using-enumerate
import io
import os
import shutil
from contextlib import contextmanager


_CONFIG_TIP_SECTION_BEGIN = "# >>> tip >>>"
_CONFIG_TIP_SECTION_END = "# <<< tip <<<"


def find_rcfile_path() -> str | None:
    """Find rcfile path or return nothing if not found."""
    candidates = ['.zshrc', '.bashrc']
    for candidate in candidates:
        rcfile_path = os.path.expanduser(os.path.join('~', candidate))
        if os.path.isfile(rcfile_path):
            return rcfile_path
    return None


@contextmanager
def patch_config(src_path, dst_path=None):
    section_f = io.StringIO()
    yield section_f
    lines = _read_config(src_path)
    lines = _remove_tip_section(lines)
    mem_f = io.StringIO()
    while len(lines) > 0 and len(lines[-1].strip()) == 0:
        lines.pop()
    mem_f.writelines(lines)
    section_text = section_f.getvalue()
    if len(section_text) != 0:
        print(file=mem_f)
        print(_CONFIG_TIP_SECTION_BEGIN, file=mem_f)
        mem_f.write(section_text)
        if not section_text.endswith('\n'):
            mem_f.write('\n')
        print(_CONFIG_TIP_SECTION_END, file=mem_f)
    if dst_path is None:
        dst_path = src_path
    move_to_path = None
    if src_path == dst_path:
        move_to_path = dst_path
        dst_path = dst_path + '~'
    with open(dst_path, 'w', encoding='utf8') as f:
        f.write(mem_f.getvalue())
    if move_to_path is not None:
        shutil.move(dst_path, move_to_path)


def _read_config(path: str) -> list[str]:
    with open(path, 'r', encoding='utf8') as f:
        return f.readlines()


def _remove_tip_section(config_lines: list[str]) -> list[str]:
    begin_ln = len(config_lines)
    for i in range(len(config_lines)):
        if config_lines[i].strip() == _CONFIG_TIP_SECTION_BEGIN:
            begin_ln = i
    end_ln = begin_ln
    for i in range(begin_ln + 1, len(config_lines)):
        if config_lines[i].strip() == _CONFIG_TIP_SECTION_END:
            end_ln = i + 1
            break
    separator = []
    while begin_ln > 0 and len(config_lines[begin_ln - 1].strip()) == 0:
        begin_ln -= 1
        separator = [os.linesep]
    while end_ln < len(config_lines) and len(config_lines[end_ln].strip()) == 0:
        end_ln += 1
        separator = [os.linesep]
    if begin_ln == 0 or end_ln == len(config_lines):
        separator = []
    return config_lines[:begin_ln] + separator + config_lines[end_ln:]
