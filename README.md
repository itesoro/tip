# Tesoro Installer of Packages

**TIP** (Tesoro Installer of Packages) is a package manager built around PIP. It allows to keep only one copy of a
package and to use it in different environments.

## Installation

Install this package using `pip install`. It will create [TIP Directory](#glossary) `~/.tip`, but if you want to
override its path set it in `TIP_DIR` environment variable.

## Usage

TIP has several commands:

- `add` new package by it's package specifier to the environment
- `create` create new environment
- `install` download, install and add package(-s) so it's can be used within environment
- `list` installed or added packages and their versions
- `run` is used as `python` command with ability to import packages added to the environment
- `uninstall` removes previously installed package(-s)
- `info` current installation and environment info

Show more info using `--help` with `tip` or concrete command.

## VSCode Integration

In order to use tip with VSCode you must install `tip` and then provide path to `tipython` executable as current
interpreter. It will use **all installed libraries** in current tip directory. Read more in `tipython --help`.

## Configuration

Some settings can be configured using the `tip config set <key> <value>` command. Here is a list of keys you may want to
change:

| Setting             | Description                           |
| ------------------- | ------------------------------------- |
| `cache_dir`         | Directory where the packages cache is stored. When not set, cache is disabled. |
| `site_packages_dir` | Directory where the packages are stored. |

There are additional keys in the config that are not listed here, as they are handled by special commands.

You can remove a setting by using `tip cache unset <key>`.

## Glossary

**Package Specifier** - package name and version in format of `<package_name>==<package_version>`.

**Environment** - a set of packages with their versions used when running python modules to import hook them. Packages
are determined by environment file.

**TIP Directory** - a directory which contains all installed packages, environment definitions and other system files.

**Add Package** - append new package to the environment or update it's version.

**Install Package** - download and make importable a `pip` package.

**Active Environment** - environment which will be used when running `tip run` on a module without specifying concrete
environment.

## TODO

- When adding packages make sure they are not duplicated
- `tip install package` without package_version (use latest)
- `tip add package` without package_version (use latest)
- Install our libraries:
    - Like `pip install`
    - Like `pip install -e`
- Dependencies of the installed packages may already be installed, avoid their duplication

## Known Issues

- Because of packages links we may reach packages that are not part of current environment but are part of other env
- `tip run -m module` error message when there is no `__main__.py` file may have better formatting
- Uninstalling a package doesn't remove link: we must not just delete it but add link to other package version if it
exists
