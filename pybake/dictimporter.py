import imp
import os
import sys
import pkg_resources


class DictImport(object):
    """
    Module finder/loader based on PEP 302 to load Python modules from a filesystem location
    """
    def __init__(self, dict_tree, unload=True):
        self._unload = unload
        self._loaded_modules = set()
        self._full_path_map = {}
        self._init_full_path_map(dict_tree)

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unload()

    def load(self):
        self._hook = self._new_loader
        sys.path_hooks.append(self._hook)
        for full_path in self._gen_full_paths():
            sys.path.insert(0, full_path)

        # Enable package resource loading from this loader context:
        # When pkg_resources is imported it scans the current `sys.path` and stows it away inside
        # its `working_set`. There is an `add_entry()` however there is no `remove_entry()`.
        # Thus for the purposes of this context class it works out cleaner to simply reload the
        # module on __enter__ and __exit__
        reload(pkg_resources)
        pkg_resources.register_finder(*self._register_finder())

    def unload(self):
        for import_path in self._gen_full_paths():
            try:
                sys.path.remove(import_path)
            except ValueError:
                pass

        try:
            sys.path_hooks.remove(self._hook)
        except ValueError:
            pass

        if self._unload:
            for fullname in self._loaded_modules:
                try:
                    sys.modules.pop(fullname)
                except KeyError:
                    pass

        reload(pkg_resources)

    def loaded_modules(self):
        return list(self._loaded_modules)

    def _new_loader(self, path_entry):
        return ModuleImportLoader(self, path_entry)

    def _register_finder(self):
        return ModuleImportLoader, pkg_resources.find_on_path

    def _add_module(self, fullname):
        self._loaded_modules.add(fullname)

    def _init_full_path_map(self, blob_tree):
        def walk(node, path=()):
            for key in node:
                if isinstance(node[key], dict):
                    for ret in walk(node[key], path + (key,)):
                        yield ret
                else:
                    yield path + (key,)

        def read_blob(path):
            node = blob_tree
            for key in path[:-1]:
                node = node[key]
            return node[path[-1]]

        for path in walk(blob_tree):
            full_path = os.path.join(sys.argv[0], *path)
            self._full_path_map[full_path] = read_blob(path)

    def _gen_full_paths(self):
        for full_path in self._full_path_map:
            yield full_path

    def _full_path(self, fullname):
        def full_paths():
            for suffix in ('.py', '/__init__.py'):
                yield os.path.join(sys.argv[0], *fullname.split('.')) + suffix

        for full_path in full_paths():
            if full_path in self._full_path_map:
                return full_path
        return None

    def _read_file(self, full_path):
        return self._full_path_map[full_path]


class ModuleImportLoader(object):
    def __init__(self, context, path_entry):
        for import_path in context._gen_full_paths():
            if import_path == path_entry or path_entry.startswith(import_path):
                break
        else:
            raise ImportError
        self._context = context
        self._path_entry = path_entry

    def find_module(self, fullname, path=None):
        if self._context._full_path(fullname):
            return self
        return None

    def load_module(self, fullname):
        full_path = self._context._full_path(fullname)

        mod = imp.new_module(fullname)
        mod.__file__ = full_path
        mod.__loader__ = self

        if full_path.endswith('/__init__.py'):
            mod.__package__ = fullname
            path_suffixes = [fullname.split('.'), '']
            mod.__path__ = [os.path.join(self._path_entry, *p) for p in path_suffixes]
        else:
            mod.__package__ = '.'.join(fullname.split('.')[:-1])
        source = self._context._read_file(full_path)
        try:
            exec compile(source, full_path, 'exec') in mod.__dict__
        except ImportError:
            exc_info = sys.exc_info()
            raise exc_info[0], "%s, while importing '%s'" % (exc_info[1], fullname), exc_info[2]
        except Exception:
            orig_exc_type, exc, tb = sys.exc_info()
            exc_info = (ImportError, exc, tb)
            raise exc_info[0], "%s: %s, while importing '%s'" % (orig_exc_type.__name__,
                                                                 exc_info[1],
                                                                 fullname), exc_info[2]
        sys.modules.setdefault(fullname, mod)
        self._context._add_module(fullname)
        return mod

    def get_source(self, fullname):
        full_path = self._context._full_path(fullname)
        return self._context._read_file(full_path)
