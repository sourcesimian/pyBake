import inspect

import base64
import json
import os
import os.path
import zlib

import textwrap
from dictfilesystembuilder import DictFileSystemBuilder

src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



class PyBake(object):
    def __init__(self, header, footer, width=80, suffix='##', python='python2'):
        self._header = header
        self._footer = footer
        self._width = width
        self._suffix = suffix
        self._python = python
        self._dict_fs = DictFileSystemBuilder()

    def load_module(self, module, base=()):
        self._dict_fs.load(module, base)

    def add_file(self, path, fh):
        if not isinstance(path, (list, tuple)):
            raise TypeError(repr(path))
        self._dict_fs.add_file(path, fh)

    def write_dist(self,  path, user_data=None):
        path = os.path.expanduser(path)
        with open(path, 'wb') as fh:
            self._dump_dist(fh, user_data)
        os.chmod(path, 0o755)
        print("Wrote: %s" % path)

    def _dump_dist(self, fh, user_data):
        self._dump_header(fh)
        self._dump_blob(fh, user_data)
        self._dump_footer(fh)
        self._dump_eof(fh)

    def _dump_header(self, fh):
        fh.write('#!/usr/bin/env %s\n' % self._python)
        fh.write(self._s(self._header))

    def _get_pybake_modules(self):
        d = []
        for name in ('abstractimporter', 'dictfilesystem', 'filesysteminterceptor', 'dictfilesysteminterceptor'):
            with open(os.path.join(os.path.dirname(__file__), name + '.py')) as fh:
                d.append((name, fh.read()))
        return d

    def _dump_footer(self, fh):
        fh.write(self._s(self._footer))
        
    def _dump_eof(self, fh):
        fh.write('#' * (self._width - 3 - len(self._suffix)) + 'END' + self._suffix + '\n')

    def _dump_blob(self, fh, user_data):
        inline, obscured = self._get_launcher()
        fh.write("_='''")

        data = (
            user_data,
            {
                '_': obscured,
                'pybake': self._get_pybake_modules(),
                'fs': self._dict_fs.get_tree()
            }
        )

        fh.write(self.b64e(zlib.compress(json.dumps(data, sort_keys=True, separators=(',', ':')), 9),
                           self._width, 5))
        fh.write("'''\n")
        fh.write(self._s(inline))

    def _get_launcher(self):
        with open(os.path.join(os.path.dirname(__file__), 'launcher.py')) as fh:
            lines = fh.readlines()

        inline = lines.index('# -- inline cut --\n')
        obscure = lines.index('# -- obscure cut --\n')

        return (
            ''.join(lines[inline + 1:obscure]),
            ''.join(lines[obscure + 1:])
        )

    @staticmethod
    def dedent(content, offset=0):
        ret = textwrap.dedent(content)
        if offset:
            ret = ' ' * offset + ret.replace('\n', '\n' + ' ' * offset).rstrip(' ')
        return ret

    def _s(self, content):
        return self.suffix(content, self._suffix, self._width - len(self._suffix))

    @staticmethod
    def suffix(content, suffix, offset=78):
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
    def b64e(str, line, first):
        first = line - first
        out = base64.encodestring(str).replace('\n', '')
        lines = []
        a = 0
        b = first or line
        m = len(out)
        while a < m:
            lines.append(out[a: min(b, m)])
            a, b = b, b + line
        return '\n'.join(lines)
