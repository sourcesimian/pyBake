

import binascii
import json
import os
import os.path
import zlib
import textwrap

from pybake.dictfilesystem import DictFileSystem
from pybake.dictfilesystembuilder import DictFileSystemBuilder

src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BAKED_FILES = (
    'abstractimporter.py',
    'dictfilesystem.py',
    'filesysteminterceptor.py',
    'dictfilesysteminterceptor.py',
    'blobserver.py',
    'launcher.py',
)

PRELOAD_MODULES = (
    'abstractimporter',
    'dictfilesystem',
    'filesysteminterceptor',
    'dictfilesysteminterceptor',
    'blobserver',
)


class PyBake(object):
    def __init__(self, header=None, footer=None, width=80, suffix='##', python='python3'):
        self._header = header
        self._footer = footer
        self._width = width
        self._suffix = suffix
        self._python = python
        self._fs = DictFileSystem()
        self._fs_builder = DictFileSystemBuilder(self._fs)
        self._add_pybake()

    def add_module(self, module, tpath=()):
        """
        Add a module to the filesystem blob. Where `module` can a reference to a Python module or
        a path to a directory. The optional `tpath` is the path at which the module will be stored
        in the filesystem, default is at root which is `()`
        """
        self._fs_builder.add_module(module, tpath)

    def add_file(self, tpath, fh):
        """
        Write the contents of `fh` a file like object to the the `tpath` location in the filesystem
        blob, there `tpath` is a tuple of path elements.
        """
        if not isinstance(tpath, (list, tuple)):
            raise TypeError(repr(tpath))
        self._fs_builder.add_file(tpath, fh)

    def dump_bake(self, fh):
        """
        Write the complete bake to `fh`, a file like object
        """
        self._dump_header(fh)
        self._dump_blob(fh)
        self._dump_footer(fh)
        self._dump_eof(fh)

    def write_bake(self, path):
        """
        Write the complete bake to `path` and make it executable
        """
        path = os.path.expanduser(path)
        with open(path, 'wb') as fh:
            self.dump_bake(fh)
        os.chmod(path, 0o755)

    def _add_pybake(self):
        for name in BAKED_FILES:
            with open(os.path.join(os.path.dirname(__file__), name), 'rb') as fh:
                self.add_file(('pybake', name), fh)

    @staticmethod
    def _write(fh, content):
        fh.write(content.encode('utf-8'))

    def _dump_header(self, fh):
        self._write(fh, '#!/usr/bin/env %s\n' % self._python)
        if self._header:
            self._write(fh, self._s(self._header))

    def _dump_footer(self, fh):
        if self._footer:
            self._write(fh, self._s(self._footer))

    def _dump_eof(self, fh):
        self._write(fh, '#' * (self._width - 3 - len(self._suffix)) + 'END' + self._suffix + '\n')

    def _dump_blob(self, fh):
        inline, execable = self._get_launcher()
        self._write(fh, "_='''")

        blob = (execable, PRELOAD_MODULES, self._fs.get_dict_tree())
        json_blob = json.dumps(blob, sort_keys=True, separators=(',', ':'))
        zlib_blob = zlib.compress(json_blob.encode('utf-8'))
        b64_blob = self._b64e(zlib_blob, self._width, 5)
        self._write(fh, b64_blob)
        self._write(fh, "'''\n")
        self._write(fh, self._s(inline))

    def _get_launcher(self):
        with open(os.path.join(os.path.dirname(__file__), 'launcher.py')) as fh:
            lines = fh.readlines()

        inline = lines.index('# -- inline cut --\n')
        obscure = lines.index('# -- execable cut --\n')

        return (
            ''.join(lines[inline + 1:obscure]),
            ''.join(lines[obscure + 1:])
        )

    @staticmethod
    def _dedent(content, offset=0):
        ret = textwrap.dedent(content)
        if offset:
            ret = ' ' * offset + ret.replace('\n', '\n' + ' ' * offset).rstrip(' ')
        return ret

    def _s(self, content):
        return self._add_suffix(content, self._suffix, self._width - len(self._suffix))

    @staticmethod
    def _add_suffix(content, suffix, offset=78):
        ret = []
        for line in content.splitlines():
            if len(line) <= offset:
                line = line + ' ' * (offset - len(line)) + suffix
            ret.append(line)
        ret = '\n'.join(ret)
        if ret[-1] != '\n':
            ret += '\n'
        return ret

    @staticmethod
    def _b64e(str, line, first):
        first = line - first
        out = binascii.b2a_base64(str)
        out = out.decode('utf-8').replace('\n', '')
        lines = []
        a = 0
        b = first or line
        m = len(out)
        while a < m:
            lines.append(out[a: min(b, m)])
            a, b = b, b + line
        return '\n'.join(lines)
