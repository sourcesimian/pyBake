import imp
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
        sys.meta_path.append(self)

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

        mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
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
            exec compile(source, full_path, 'exec') in mod.__dict__
        except ImportError:
            exc_info = sys.exc_info()
            raise exc_info[0], "%s, while importing '%s'" % (exc_info[1], fullname), exc_info[2]
            # raise exc_info[0]  from ex
        except Exception:
            orig_exc_type, exc, tb = sys.exc_info()
            exc_info = (ImportError, exc, tb)
            raise exc_info[0], "%s: %s, while importing '%s'" % (orig_exc_type.__name__,
                                                                 exc_info[1],
                                                                 fullname), exc_info[2]
            # raise exc_info[0] from ex
        self._add_module(fullname)
        return mod

    def get_source(self, fullname):
        full_path = self._full_path(fullname)
        return self._read_file(full_path)

    def is_package(self, fullname):
        print '!!!! is_package',

    def get_code(self, fullname):
        print '!!!! get_code',

    def get_data(self, path):
        print '!!!! get_data',

    def get_filename(self, fullname):
        print '!!!! get_filename',
