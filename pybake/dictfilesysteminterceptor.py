import errno
import os
from StringIO import StringIO

from pybake.filesysteminterceptor import FileSystemInterceptor


class DictFileSystemInterceptor(FileSystemInterceptor):
    def __init__(self, reader):
        intercept_list = [
            '__builtin__.open',
            'os.path.isfile',
            'os.path.isdir',
            'os.path.exists',
            'os.listdir',
            'os.stat',
            'os.access',
            'os.fstat',
        ]
        super(DictFileSystemInterceptor, self).__init__(intercept_list)
        self._reader = reader
        self._fileno_path_map = {}
        self._path_fileno_map = {}

    def _path_to_fileno(self, path):
        try:
            return self._path_fileno_map[path]
        except KeyError:
            pass

        fileno = len(self._path_fileno_map) + 65536  # This is very dodgy
        self._path_fileno_map[path] = fileno
        self._fileno_path_map[fileno] = path
        return fileno

    def _builtin_open(self, path, mode='r'):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['__builtin__.open'](path, mode)
        if 'w' in mode:
            raise IOError(errno.EROFS, 'Read-only file system', path)
        content = self._reader.read(tpath)

        return FrozenFile(self, path, content)

    def _os_path_isfile(self, path):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.path.isfile'](path)
        # print 'isfile', path, tpath
        return self._reader.isfile(tpath)

    def _os_path_isdir(self, path):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.path.isdir'](path)
        # print 'isdir', path
        return self._reader.isdir(tpath)

    def _os_path_exists(self, path):
        print 'os.path.exists', path
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.path.exists'](path)
        # print 'os.exists', path
        return self._reader.exists(tpath)

    def _os_listdir(self, path):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.listdir'](path)
        # print 'listdir', path
        return self._reader.listdir(tpath)

    def _os_stat(self, path):
        print 'os.stat', path
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.stat'](path)
        # print 'os.stat', path
        return self._reader.stat(tpath)

    def _os_fstat(self, fileno):
        try:
            tpath = self._reader.tpath(self._fileno_path_map[fileno])
            if tpath:
                return self._reader.stat(tpath)
        except KeyError:
            pass
        # print 'os.fstat', path
        return self._oldhooks['os.fstat'](fileno)

    def _os_access(self, path, mode):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.access'](path, mode)
        # print 'os.access', path
        if mode & (os.W_OK):
            return False
        return True


class FrozenFile(StringIO):
    def __init__(self, ctx, path, content):
        self._ctx = ctx
        self._path = path
        StringIO.__init__(self, content)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fileno(self):
        return self._ctx._path_to_fileno(self._path)
