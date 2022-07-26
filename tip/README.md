# Tesoro Installer of Packages

TIP is a package manager that allows user to use the same package file across multiple environments.

## Quick Start

Create and set a path where packages will be downloaded:

```bash
mkdir -p /usr/local/tip/site-packages
export TIP_SITE_PACKAGES=/usr/local/tip/site-packages
```

Create environment file `environment.json` with following content:

```json
{
    "numpy": "1.22.0",
    "pymongo": "4.1.1"
}
```

Install packages from that environment:

```bash
tip install -e environment.json
```

Or simply by providing package names and versions:

```bash
tip install numpy==1.22.0 pymongo==4.1.1
```

And run your script:

```bash
tip run path/to/script.py
```

Or module:

```bash
tip run -m pytest .
```

## Commands Overview

TIP has following commands:

- install
- remove
- list
- run

### Install

`tip install <package>==<version>` downloads and prepares packages to be imported into your script. It uses pip, so
you can expect the same behaviour as `pip install`. Packages are saved into directory you set in
`TIP_SITE_PACKAGES` environment variable. This folder should not be modified in order for TIP to work properly.

`tip install` also takes an option `-e/--env` which is a path to an environment file. When provided, the packages
from that environment will be installed if possible.

### Remove

`tip remove <package>==<version>` removes previously installed package.

### List

`tip list` shows a tree of all installed packages and all versions of that packages.

### Run

`tip run path/to/script.py` or `tip run -m module` executes a python script or module using packages taken from
`environment.json`. If you want to provide another environment file, use `-e` option.

You can also use option `--install-missing` to ensure all environment packages are installed.
