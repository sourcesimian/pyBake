import glob
import base64
import json
import os
import os.path
import sys
import zlib
import hashlib
from datetime import datetime
from textwrap import dedent

import textwrap
from moduletree import ModuleTree

src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



class PyBake(object):
    def __init__(self, header, footer):
        self._header = header
        self._footer = footer
        self._module_tree = ModuleTree()

    def load_modules(self, path):
        self._module_tree.load(path, types=('.py',))

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

    def _dump_header(self, fh):
        fh.write('#!/usr/bin/env python2\n')
        fh.write(self.suffix(self._header, '##', 78))

    def _read_loader_script(self):
        import dictimporter
        import inspect

        with open(inspect.getsourcefile(dictimporter), 'rt') as fh:
            return fh.read()

    def _dump_footer(self, fh):
        fh.write(self.suffix(self._footer, '##', 78))
        
    def _dump_blob(self, fh, user_data):
        data = (user_data,
                (self._get_exec(), self._read_loader_script(), self._module_tree.get_tree()))

        fh.write("b='''")
        fh.write(self.b64e(zlib.compress(json.dumps(data, sort_keys=True, separators=(',', ':')), 9)))
        fh.write("'''\n")

    def _dump_loader(self, fh):
        fh.write(self.suffix(self.dedent('''\
        import base64, json, zlib                                                     ##
        data, e = json.loads(zlib.decompress(base64.decodestring(b))); exec(e[0])     ##
        '''), '##', 78))

    def _get_exec(self):
        return dedent('''\
        import tempfile
        import imp
        with tempfile.NamedTemporaryFile() as t:
            t.write(e[1])
            t.flush()
            imp.load_source('i', t.name).DictImport(e[2]).load()
        ''')

    @staticmethod
    def dedent(content, offset=0):
        ret = textwrap.dedent(content)
        if offset:
            ret = ' ' * offset + ret.replace('\n', '\n' + ' ' * offset).rstrip(' ')
        return ret

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
    def b64e(str, line=80, first=75):
        first = first or line
        out = base64.encodestring(str).replace('\n', '')
        lines = []
        a = 0
        b = first or line
        m = len(out)
        while a < m:
            lines.append(out[a: min(b, m)])
            a, b = b, b + line
        return '\n'.join(lines)

