

import errno
import os
from io import BytesIO

from pybake.filesysteminterceptor import FileSystemInterceptor, BUILTINS_OPEN


class DictFileSystemInterceptor(FileSystemInterceptor):
    def __init__(self, reader):
        intercept_list = [
            BUILTINS_OPEN,
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
        self._fileno = FileNo()

    def _builtins_open(self, *args, **kwargs):
        return self._builtin_open(*args, **kwargs)

    def _builtin_open(self, path, mode='r', *args, **kwargs):
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks[BUILTINS_OPEN](path, mode, *args, **kwargs)
        if 'w' in mode:
            raise IOError(errno.EROFS, 'Read-only file system', path)
        content = self._reader.read(tpath)

        return FrozenFile(self._fileno, path, content)

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
        tpath = self._reader.tpath(path)
        if tpath is None:
            return self._oldhooks['os.stat'](path)
        # print 'os.stat', path
        return self._reader.stat(tpath)

    def _os_fstat(self, fileno):
        try:
            tpath = self._reader.tpath(self._fileno.fileno_to_path(fileno))
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


class FileNo(object):
    def __init__(self):
        self._current_fileno = 65536  # This is very dodgy
        self._fileno_path_map = {}
        self._path_fileno_map = {}

    def _next_fileno(self):
        self._current_fileno += 1
        return self._current_fileno

    def path_to_fileno(self, path):
        try:
            return self._path_fileno_map[path]
        except KeyError:
            pass

        fileno = self._next_fileno()
        self._path_fileno_map[path] = fileno
        self._fileno_path_map[fileno] = path
        return fileno

    def fileno_to_path(self, fileno):
        return self._fileno_path_map[fileno]

    def close_path(self, path):
        try:
            fileno = self._path_fileno_map[path]
            del self._path_fileno_map[path]
            del self._fileno_path_map[fileno]
        except KeyError:
            pass


class FrozenFile(BytesIO):
    def __init__(self, fileno, path, content):
        self._fileno = fileno
        self._path = path
        BytesIO.__init__(self, content)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fileno.close_path(self._path)

    def fileno(self):
        return self._fileno.path_to_fileno(self._path)
