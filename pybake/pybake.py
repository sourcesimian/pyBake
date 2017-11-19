import inspect

import base64
import json
import os
import os.path
import zlib

import dictimporter

import textwrap
from moduletree import ModuleTree

src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



class PyBake(object):
    def __init__(self, header, footer, width=80, suffix='##', python='python2'):
        self._header = header
        self._footer = footer
        self._width = width
        self._suffix = suffix
        self._python = python
        self._module_tree = ModuleTree()

    def load_module(self, module):
        self._module_tree.load(module)

    def write_dist(self,  path, user_data=None):
        path = os.path.expanduser(path)
        with open(path, 'wb') as fh:
            self._dump_dist(fh, user_data)
        os.chmod(path, 0o755)
        print("Wrote: %s" % path)

    def _dump_dist(self, fh, user_data):
        self._dump_header(fh)
        self._dump_blob(fh, user_data)
        self._dump_loader(fh)
        self._dump_footer(fh)
        self._dump_eof(fh)

    def _dump_header(self, fh):
        fh.write('#!/usr/bin/env %s\n' % self._python)
        fh.write(self._s(self._header))

    def _read_loader_script(self):
        with open(inspect.getsourcefile(dictimporter), 'rt') as fh:
            return fh.read()

    def _dump_footer(self, fh):
        fh.write(self._s(self._footer))
        
    def _dump_eof(self, fh):
        fh.write('#' * (self._width - 3 - len(self._suffix)) + 'END' + self._suffix + '\n')

    def _dump_blob(self, fh, user_data):
        data = (user_data,
                (self._get_exec(), self._read_loader_script(), self._module_tree.get_tree()))

        fh.write("e = '''")
        fh.write(self.b64e(zlib.compress(json.dumps(data, sort_keys=True, separators=(',', ':')), 9),
                           self._width, 7))
        fh.write("'''\n")

    def _dump_loader(self, fh):
        fh.write(self._s(self.dedent('''\
        import base64, json, zlib
        user, e = json.loads(zlib.decompress(base64.b64decode(e))); exec(e[0])
        ''')))

    def _get_exec(self):
        return self.dedent('''\
        del base64, json, zlib

        import imp
        import tempfile
        import sys

        sys.modules['pybake'] = imp.new_module('pybake')

        with tempfile.NamedTemporaryFile() as t:
            t.write(e[1])
            t.flush()
            imp.load_source('pybake.dictimporter', t.name).DictImport(e[2]).load()

        del e, t
        del imp, tempfile, sys
        ''')

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
