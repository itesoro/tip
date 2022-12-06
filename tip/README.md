# Tesoro Installer of Packages

**TIP** (Tesoro Installer of Packages) is a package manager built around PIP. It allows to keep only one copy of a package
to use it in different environments.

## Installation

Install this package using `pip install`. After that run:

```bash
tip init <path-to-tip-home>
```

Value of `path-to-tip-home` must be a path to TIP home (see Glossary).

## Usage

TIP has several commands:

- `add` new package by it's package string to the current environment (or specify environment using `-e`)
- `create` create new environment
- `init` create tip home and user configuration file at `~/.tip`
- `install` download and install package(-s) so it's can be used within environment
- `list` print installed packages and their versions
- `run` is used as `python` command except it uses active environment to import hook packages added into it
- `uninstall` removes previously installed package(-s)

Show more info using `--help` with `tip` or concrete command.

## VSCode Integration

In order to use tip with VSCode you must install `tip` and then provide path to `tipr` executable as current
interpreter. It will use **all installed libraries** in current tip home.

## Glossary

**Package String** - string containing package name and version in format of `<package_name>==<package_version>`.

**Environment** - a set of packages with their versions used when running python modules to import hook them. Packages
are determined by environment file.

**TIP Home** - a directory which contains all installed packages, environment definitions and other system files.

**Add Package** - append new package to the environment or update it's version.

**Install Package** - download and make importable a `pip` package.

**Active Environment** - environment which will be used when running `tip run` on a module without specifying concrete
environment.

## TODO

- When adding packages make sure they are not duplicated
- `tipr` calls REPL

## Known Issues

- Because of packages links we may reach packages that are not part of current environemnt but are part of other env
- `tip run -m module` error message when there is no `__main__.py` file may have better formatting
- Uninstalling a package doesn't remove link: we must not just delete it but add link to other package version if it
exists
