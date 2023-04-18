import os
from importlib.abc import MetaPathFinder
from importlib.util import spec_from_file_location


class TipMetaFinder(MetaPathFinder):
    """Finder which accepts a list of packages in custom directories to import them from there."""

    def __init__(self, packages_to_mount):
        self.packages_to_mount = packages_to_mount

    def find_spec(self, fullname, path, target=None):
        path = []
        if fullname in self.packages_to_mount:
            path.append(self.packages_to_mount[fullname])
        if len(path) == 0:
            path.append(os.getcwd())
        if "." in fullname:
            *_, name = fullname.split(".")
        name = fullname
        for entry in path:
            if os.path.isdir(os.path.join(entry, name)):
                filename = os.path.join(entry, name, "__init__.py")
                submodule_locations = [os.path.join(entry, name)]
            else:
                filename = os.path.join(entry, name + ".py")
                submodule_locations = None
            if not os.path.exists(filename):
                continue
            return spec_from_file_location(fullname, filename, submodule_search_locations=submodule_locations)
        return None
