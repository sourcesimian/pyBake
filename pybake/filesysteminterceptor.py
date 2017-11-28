import errno
import os
from StringIO import StringIO


class FileSystemInterceptor(object):
    def __init__(self, intercept_list):
        self._intercept_list = intercept_list
        self._oldhooks = {}

    def __enter__(self):
        self._install()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._uninstall()

    def _install(self):
        for fullpath in self._intercept_list:
            method_name = self._method_name(fullpath)
            try:
                method = getattr(self, method_name)
                self._oldhooks[fullpath] = self._hook(fullpath, method)
            except AttributeError:
                def make_dummy(fullpath):
                    def dummy(*args, **kwargs):
                        return self._shim(fullpath, *args, **kwargs)
                    return dummy
                self._oldhooks[fullpath] = self._hook(fullpath, make_dummy(fullpath))
                pass

    def _uninstall(self):
        for fullpath, oldhook in self._oldhooks.items():
            self._oldhooks[fullpath] = self._hook(fullpath, oldhook)

    @classmethod
    def _method_name(cls, fullpath):
        return '_%s' % fullpath.replace('_', '').replace('.', '_')

    @classmethod
    def _hook(cls, fullpath, newhook):
        s = fullpath.split('.')
        path, base = '.'.join(s[:-1]), s[-1]
        mod = __import__(path, globals(), locals(), [base])
        try:
            oldhook = getattr(mod, base)
        except AttributeError:
            raise AttributeError("'%s' has no attribute '%s'" % (path, base))
        setattr(mod, base, newhook)
        return oldhook

    def _shim(self, fullpath, *args, **kwargs):
        ret = self._oldhooks[fullpath](*args, **kwargs)
        return ret


class DictFileSystemInterceptor(FileSystemInterceptor):
    def __init__(self, reader):
        intercept_list = [
            '__builtin__.open',
            'os.path.isfile',
            'os.path.isdir',
            'os.listdir',
            'os.stat',
            'os.access',
        ]
        super(DictFileSystemInterceptor, self).__init__(intercept_list)
        self._reader = reader

    def _builtin_open(self, path, mode='r'):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['__builtin__.open'](path, mode)
        if 'w' in mode:
            raise IOError(errno.EROFS, 'Read-only file system', path)
        content = self._reader.read(tpath)

        class OFile(StringIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return OFile(content)

    def _os_path_isfile(self, path):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.path.isfile'](path)
        print 'isfile', path
        return self._reader.isfile(tpath)

    def _os_path_isdir(self, path):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.path.isdir'](path)
        print 'isdir', path
        return self._reader.isdir(tpath)

    def _os_listdir(self, path):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.listdir'](path)
        print 'listdir', path
        return self._reader.listdir(tpath)

    def _os_stat(self, path):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.stat'](path)
        print 'os.stat', path
        return self._reader.stat(tpath)

    def _os_access(self, path, mode):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.access'](path, mode)
        print 'os.access', path
        if mode & (os.W_OK):
            return False
        return True
