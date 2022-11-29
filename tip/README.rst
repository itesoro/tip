Tesoro Installer of Packages
----------------------------

TIP (Tesoro Installer of Packages) is a package manager built around PIP. It allows to keep only one copy of a package
to use it in different environments.

Installation
~~~~~~~~~~~~

Install this package using `pip install`. After that run:

.. code-block:: bash
    tip init <path-to-tip-home>

Value of `path-to-tip-home` must be a path to TIP home (see Glossary).

Usage
~~~~~

TIP has several commands:

- `add` new package by it's package string to the current environment (or specify environment using `-e`)
- `create` create new environment
- `init` create tip home and user configuration file at `~/.tip`
- `install` download and install package(-s) so it's can be used within environment
- `list` print installed packages and their versions
- `run` is used as `python` command except it uses active environment to import hook packages added into it
- `uninstall` removes previously installed package(-s)

Show more info using `--help` with `tip` or concrete command.

VSCode Integration
~~~~~~~~~~~~~~~~~~

In order to use tip with VSCode you must install `tip` and then provide path to `tipr` executable as current
interpreter. It will use **all installed libraries** in current tip home.

Glossary
~~~~~~~~

**Package String** - string containing package name and version in format of `<package_name>==<package_version>`.

**Environment** - a set of packages with their versions used when running python modules to import hook them. Packages
are determined by environment file.

**TIP Home** - a directory which contains all installed packages, environment definitions and other system files.

**Add Package** - append new package to the environment or update it's version.

**Install Package** - download and make importable a `pip` package.

**Active Environment** - environment which will be used when running `tip run` on a module without specifying concrete
environment.

TODO
~~~~

- Make an installation script, preferably using ``setup.py``.
- Uninstall checks if uninstalled packages are in environments and proposes to remove them (maybe that's not necessary).
- Print current environment name, path and package list.
- When adding packages make sure they are not duplicated.
- Print an error when activating environment that doesn't exist.
- Shouldn't we prohibit addition of packages that are not installed?
