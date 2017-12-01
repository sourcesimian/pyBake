import errno
import imp
import os
import sys


class DictImport(object):
    """
    Module finder/loader based on PEP 302 to load Python modules from a filesystem location
    """
    def __init__(self, base_dir, dict_tree, unload=True):
        self._unload = unload
        self._loaded_modules = set()
        self._base_dir = base_dir
        self._fs = DictFileSystemReader(self._base_dir, dict_tree)

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unload()

    def load(self):
        sys.meta_path.append(self)

    def unload(self):
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
        except Exception:
            orig_exc_type, exc, tb = sys.exc_info()
            exc_info = (ImportError, exc, tb)
            raise exc_info[0], "%s: %s, while importing '%s'" % (orig_exc_type.__name__,
                                                                 exc_info[1],
                                                                 fullname), exc_info[2]
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


class DictFileSystemReader(object):
    def __init__(self, base_dir, dict_tree):
        self._base_dir = base_dir
        self._dict_tree = dict_tree
        self._stat = os.stat(sys.argv[0])

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def tpath(self, path):
        try:
            if isinstance(path, basestring) and path.startswith(self._base_dir):
                subpath = path[len(self._base_dir):].strip(os.sep)
                if not subpath:
                    return ()
                ret = tuple(subpath.split(os.sep))
                return ret
        except AttributeError:
            pass
        return None

    def _node(self, tpath):
        try:
            node = self._dict_tree
            for key in tpath:
                node = node[key]
            return node
        except KeyError:
            pass
        raise IOError(errno.ENOENT, "No such file or directory", '%s/%s' % (self._base_dir, os.sep.join(tpath)))

    def listdir(self, tpath):
        return self._node(tpath).keys()

    def read(self, tpath):
        return self._node(tpath)

    def isfile(self, tpath):
        return isinstance(self._node(tpath), basestring)

    def isdir(self, tpath):
        return isinstance(self._node(tpath), dict)

    def stat(self, tpath):
        node = self._node(tpath)

        from collections import namedtuple
        stat_result = namedtuple('stat_result', ['st_mode', 'st_ino', 'st_dev', 'st_nlink',
                                                 'st_uid', 'st_gid', 'st_size', 'st_atime',
                                                 'st_mtime', 'st_ctime'])
        st_mode = self._stat.st_mode
        st_ino = self._stat.st_ino
        st_dev = self._stat.st_dev
        st_nlink = self._stat.st_nlink
        st_uid = self._stat.st_uid
        st_gid = self._stat.st_gid
        st_size = len(node)
        st_mtime, st_atime, st_ctime = self._stat.st_mtime, self._stat.st_atime, self._stat.st_ctime

        return stat_result(st_mode, st_ino, st_dev, st_nlink,
                           st_uid, st_gid, st_size, st_atime,
                           st_mtime, st_ctime)


