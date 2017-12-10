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
