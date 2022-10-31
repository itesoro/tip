Tesoro Installer of Packages
----------------------------

TIP (Tesoro Installer of Packages) is a package manager built around PIP. It allows to keep only one copy of a package
to use it in different environments.

Installation
~~~~~~~~~~~~

To install TIP you need to install this package using PIP. After that you want to add shortcut for ``tip.sh`` script:

.. code-block:: bash

    alias tip="source /path/to/tip.sh"

You will also need to set path where tip will create metadata files and store packages:

.. code-block:: bash

    export TIP_HOME="path/to/tip/home"

Basic Usage
~~~~~~~~~~~

Before you start installing packages you want to create an environment:

.. code-block:: bash

    tip create my_env

You can activate this environment:

.. code-block:: bash

    tip activate my_env

Add packages to the environment:

.. code-block:: bash

    tip add numpy==1.12.0 pandas==1.5.1

Now you are set to run your script:

.. code-block:: bash

    tip run ./my_script.py

Or a module:

.. code-block:: bash

    tip run -m my_module.app

First time run should be used with option ``--install-missing`` in order to download and install packages added to the
environment.

Additional Options
~~~~~~~~~~~~~~~~~~

Environment by path
*******************

You can explicitly provide path when executing commands.

Install packages from environment:

.. code-block:: bash

    tip install -e=/path/to/environment.json

Add packages to the environment:

.. code-block:: bash

    tip add -e=/path/to/environment.json

Add packages from existing environment:

.. code-block:: bash

    tip add -f=/path/to/environment.json

Run using environment located by path:

.. code-block:: bash

    tip run -e=/path/to/environment.json ./my_script.py

Another commands
****************

Show all installed packages and their versions:

.. code-block:: bash

    tip list


TODO
~~~~

- Make an installation script, preferably using ``setup.py``.
- Create default environment in installation script.
- Uninstall checks if uninstalled packages are in environments and proposes to remove them (maybe that's not necessary).
- Print current environment name, path and package list.
- When adding packages make sure they are not duplicated.
