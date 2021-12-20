

import types
import os
import sys


class AbstractImporter(object):
    """
    Module finder/loader based on PEP 302 to load Python modules from a filesystem location
    """
    def __init__(self, base_dir, fs, unload=True):
        self._unload = unload
        self._loaded_modules = set()
        self._base_dir = base_dir
        self._fs = fs

    def __enter__(self):
        self.install()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.uninstall()

    def install(self):
        sys.meta_path.insert(0, self)

    def uninstall(self):
        try:
            sys.meta_path.remove(self)
        except ValueError:
            pass

        if self._unload:
            for fullname in self._loaded_modules:
                try:
                    sys.modules.pop(fullname)
                except KeyError:
                    pass

    def loaded_modules(self):
        return list(self._loaded_modules)

    def _add_module(self, fullname):
        self._loaded_modules.add(fullname)

    def _full_path(self, fullname):
        dpath = tuple(fullname.split('.'))
        for tpath in (dpath + ('__init__.py',), dpath[:-1] + (dpath[-1] + '.py',)):
            try:
                if self._fs.isfile(tpath):
                    return os.path.join(self._base_dir, *tpath)
            except IOError:
                pass
        return None

    def _read_file(self, full_path):
        tpath = self._fs.tpath(full_path)
        return self._fs.read(tpath)

    def find_module(self, fullname, path=None):
        if self._full_path(fullname):
            return self
        return None

    def load_module(self, fullname):
        full_path = self._full_path(fullname)

        mod = sys.modules.setdefault(fullname, types.ModuleType(fullname))
        mod.__file__ = full_path
        mod.__loader__ = self

        if full_path.endswith('/__init__.py'):
            mod.__package__ = fullname
            path_suffixes = [fullname.split('.'), '']
            mod.__path__ = [os.path.join(self._base_dir, *p) for p in path_suffixes]
        else:
            mod.__package__ = '.'.join(fullname.split('.')[:-1])
        source = self._read_file(full_path)
        try:
            exec(compile(source, full_path, 'exec'), mod.__dict__)
        except ImportError:
            exc_info = sys.exc_info()
            exc_info1 = ImportError("%s, while importing '%s'" % (exc_info[1], fullname))
            reraise(exc_info[0], exc_info1, exc_info[2])
        except Exception:
            exc_info = sys.exc_info()
            exc_info1 = ImportError("%s: %s, while importing '%s'" % (exc_info[0].__name__,
                                                                      exc_info[1], fullname))
            reraise(ImportError, exc_info1, exc_info[2])
        self._add_module(fullname)
        return mod

    def get_source(self, fullname):
        full_path = self._full_path(fullname)
        return self._read_file(full_path)

    def is_package(self, fullname):
        path = self._full_path(fullname)
        if path:
            return path.endswith('__init__.py')
        return False

    def get_code(self, fullname):
        print('!!!! get_code')

    def get_data(self, path):
        print('!!!! get_data')

    def get_filename(self, fullname):
        return self._full_path(fullname)


def reraise(tp, value, tb=None):
    try:
        if value is None:
            value = tp()
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value
    finally:
        value = None
        tb = None
