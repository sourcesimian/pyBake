import os


class ModuleTree(object):
    def __init__(self):
        self._d = {}

    def load(self, path, types=()):
        base = os.path.join(path, '__init__.py')
        if not os.path.isfile(base):
            raise IOError('Not a module heirachy, expected %s' % base)

        def add(path, value):
            node = self._d
            for key in path[:-1]:
                if key not in node:
                    node[key] = {}
                node = node[key]
            if path[-1] in node:
                raise KeyError('Path already exists: %s' % (path,))
            node[path[-1]] = value

        base_dir = os.path.dirname(path) + os.sep
        for dir, dirs, files in os.walk(path):
            if not dir.startswith(base_dir):
                raise IOError('Unexpected dir: %s' % dir)
            pre = tuple(dir[len(base_dir):].split(os.sep))

            for file in files:
                if file.endswith(types):
                    with open(os.path.join(dir, file), 'rb') as fh:
                        add(pre + (file,), fh.read())

    def get_tree(self):
        return self._d
