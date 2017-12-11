import errno
import os


class DictFileSystem(object):
    def __init__(self, base_dir, dict_tree):
        self._base_dir = base_dir
        self._base_stat = os.stat(base_dir)
        self._dict_tree = dict_tree

    def tpath(self, path):
        try:
            if isinstance(path, basestring) and path.startswith(self._base_dir):
                subpath = path[len(self._base_dir):]
                # if not subpath:
                #     return None
                subpath = subpath.strip(os.sep)
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

    def exists(self, tpath):
        try:
            self._node(tpath)
            return True
        except IOError:
            return False

    def stat(self, tpath):
        node = self._node(tpath)

        from collections import namedtuple
        stat_result = namedtuple('stat_result', ['st_mode', 'st_ino', 'st_dev', 'st_nlink',
                                                 'st_uid', 'st_gid', 'st_size', 'st_atime',
                                                 'st_mtime', 'st_ctime'])
        st_mode = self._base_stat.st_mode
        st_ino = self._base_stat.st_ino
        st_dev = self._base_stat.st_dev
        st_nlink = self._base_stat.st_nlink
        st_uid = self._base_stat.st_uid
        st_gid = self._base_stat.st_gid
        st_size = len(node)
        st_mtime, st_atime, st_ctime = self._base_stat.st_mtime, self._base_stat.st_atime, self._base_stat.st_ctime

        return stat_result(st_mode, st_ino, st_dev, st_nlink,
                           st_uid, st_gid, st_size, st_atime,
                           st_mtime, st_ctime)


