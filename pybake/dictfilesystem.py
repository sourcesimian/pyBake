import errno
import os
import binascii


class DictFileSystem(object):
    _base_stat = None

    def __init__(self, base_dir=None, dict_tree=None):
        self._base_dir = self._normalise_path(base_dir or '/pybake/root')
        self._dict_tree = {} if dict_tree is None else dict_tree
        try:
            self._base_stat = os.stat(self._base_dir)
        except OSError:
            pass

    def tpath(self, path):
        path = self._normalise_path(path)
        try:
            if isinstance(path, str) and path.startswith(self._base_dir):
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

    def _get_tpath(self, tpath):
        node = self._dict_tree
        for key in tpath:
            node = node[key]
        return node

    def _set_tpath(self, tpath, value):
        node = self._dict_tree
        for key in tpath[:-1]:
            if key not in node:
                node[key] = {}
            node = node[key]
        node[tpath[-1]] = value

    def _get_node(self, tpath):
        try:
            return self._get_tpath(tpath)
        except KeyError:
            pass
        raise IOError(errno.ENOENT, "No such file or directory", '%s/%s' % (self._base_dir, os.sep.join(tpath)))

    def listdir(self, tpath):
        return sorted(self._get_node(tpath).keys())

    def read(self, tpath):
        type, content = self._get_node(tpath)
        if type == 'base64':
            content = binascii.a2b_base64(content)
            self._set_tpath(tpath, ('raw', content))
        return content

    def write(self, tpath, content):
        self._set_tpath(tpath, ('raw', content))

    def isfile(self, tpath):
        try:
            return isinstance(self._get_tpath(tpath), list)
        except KeyError:
            return False

    def isdir(self, tpath):
        try:
            return isinstance(self._get_tpath(tpath), dict)
        except KeyError:
            return False

    def exists(self, tpath):
        try:
            self._get_tpath(tpath)
            return True
        except KeyError:
            return False

    def stat(self, tpath):
        type, content = self._get_node(tpath)

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
        st_size = len(content)
        st_mtime, st_atime, st_ctime = self._base_stat.st_mtime, self._base_stat.st_atime, self._base_stat.st_ctime

        return stat_result(st_mode, st_ino, st_dev, st_nlink,
                           st_uid, st_gid, st_size, st_atime,
                           st_mtime, st_ctime)

    def get_dict_tree(self):
        def encode(type, content):
            if isinstance(content, str):
                content = content.encode('utf-8')
            return ('base64', binascii.b2a_base64(content).decode('utf-8'))
            # try:
            #     content.decode('ascii')
            #     return ('raw', content)
            # except UnicodeDecodeError:
            #     return ('base64', binascii.b2a_base64(content))

        def walk(src):
            dst = {}
            for key in src:
                if isinstance(src[key], dict):
                    dst[key] = walk(src[key])
                else:
                    dst[key] = encode(*src[key])
            return dst

        tree = walk(self._dict_tree)
        return tree

    @staticmethod
    def _normalise_path(filename):
        return os.path.normcase(os.path.realpath(filename))
