import os
import inspect


class ModuleTree(object):
    def __init__(self):
        self._d = {}

    def load(self, module, types=()):
        filepath = inspect.getsourcefile(module)
        basedir = os.path.dirname(filepath)

        package = ()
        if module.__package__ is not None:
            package = tuple(module.__package__.split('.'))
        if os.path.basename(filepath) == '__init__.py':
            if not package:
                package = (os.path.basename(basedir),)
            self._load_tree(package, basedir, types)
        else:
            self._load_single(package, filepath)

    def _load_single(self, package, filepath):
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as fh:
            self._add(package + (filename,), fh.read())

    def _load_tree(self, package, basedir, types):

        for dir, dirs, files in os.walk(basedir):
            if not dir.startswith(basedir):
                raise IOError('Unexpected dir: %s' % dir)

            subdir = dir[len(basedir) + 1:]
            pre = tuple(subdir.split(os.sep)) if subdir else ()

            for filename in files:
                if filename.endswith(types):
                    with open(os.path.join(dir, filename), 'rb') as fh:
                        self._add(package + pre + (filename,), fh.read())

    def _add(self, path, value):
        node = self._d
        for key in path[:-1]:
            if key not in node:
                node[key] = {}
            node = node[key]
        if path[-1] in node:
            raise KeyError('Path already exists: %s' % (path,))
        node[path[-1]] = value

    def get_tree(self):
        return self._d
