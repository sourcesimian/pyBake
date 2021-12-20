import binascii
import pytest
import os
try:
    from StringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from pybake.filesysteminterceptor import FileSystemInterceptor, BUILTINS_OPEN
from pybake.dictfilesystem import DictFileSystem
from pybake.dictfilesysteminterceptor import DictFileSystemInterceptor
from pybake.dictfilesystembuilder import DictFileSystemBuilder


class MockFileSystemInterceptor(FileSystemInterceptor):
    def __init__(self, d):
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
        super(MockFileSystemInterceptor, self).__init__(intercept_list)
        self._d = d

    def _builtins_open(self, *args, **kwargs):
        return self._builtin_open(*args, **kwargs)

    def _builtin_open(self, path, mode='r', *args, **kwargs):
        self._d.append(('open', path, mode))

    def _os_path_isfile(self, path):
        self._d.append(('os.path.isfile', path))

    def _os_path_isdir(self, path):
        self._d.append(('os.path.isdir', path))

    def _os_path_exists(self, path):
        self._d.append(('os.path.exists', path))

    def _os_listdir(self, path):
        self._d.append(('os.listdir', path))

    def _os_stat(self, path):
        self._d.append(('os.stat', path))

    def _os_fstat(self, fileno):
        self._d.append(('os.fstat', fileno))

    def _os_access(self, path, mode):
        self._d.append(('os.access', path, mode))


def test_interceptor():
    d = []
    fs = MockFileSystemInterceptor(d)

    with fs:
        open('foo')
        os.path.isfile('bar')
        os.path.isdir('fish')
        os.path.exists('paste')
        os.listdir('bubble')
        os.stat('gum')
        os.fstat(9)
        os.access('flavour', os.W_OK)

    expected = [
        ('open', 'foo', 'r'),
        ('os.path.isfile', 'bar'),
        ('os.path.isdir', 'fish'),
        ('os.path.exists', 'paste'),
        ('os.listdir', 'bubble'),
        ('os.stat', 'gum'),
        ('os.fstat', 9),
        ('os.access', 'flavour', 2)
    ]
    assert expected == d


def test_dictfilesystem():
    dict_tree = {
        'readme.txt': ('raw', 'Glad you did?'.encode()),
        'foo': {
                'bar.txt': ('raw', 'A zebra walks into a bar'.encode('utf-8')),
                'fish.txt': ('base64',  binascii.b2a_base64('A fish called Nemo?'.encode('utf-8')).decode('utf-8')),
        },
    }
    root = '/rootdir'
    fs = DictFileSystem(base_dir=root, dict_tree=dict_tree)

    with DictFileSystemInterceptor(fs):
        expected = ['foo', 'readme.txt']
        actual = os.listdir(root)
        assert expected == actual

        expected = b'Glad you did?'
        with open(root + '/readme.txt', 'rt') as fh:
            actual = fh.read()
        assert expected == actual

        expected = ['bar.txt', 'fish.txt']
        actual = os.listdir(root + '/foo')
        assert expected == actual

        expected = b'A zebra walks into a bar'
        with open(root + '/foo/bar.txt', 'rt') as fh:
            actual = fh.read()
        assert expected == actual

        expected = b'A fish called Nemo?'
        with open(root + '/foo/fish.txt', 'rt') as fh:
            actual = fh.read()
        assert expected == actual


def test_filesystembuilder():
    dict_tree = {}
    root = '/rootdir'
    fs = DictFileSystem(base_dir=root, dict_tree=dict_tree)
    bld = DictFileSystemBuilder(fs)

    text = BytesIO(b'Hello world!')
    bld.add_file(('res', 'msg.txt'), text)

    assert dict_tree['res']['msg.txt'][1] == b'Hello world!'

    import tests.foo
    bld.add_module(tests.foo)

    assert sorted(dict_tree['tests'].keys()) == ['foo']
    assert sorted(dict_tree['tests']['foo'].keys()) == ['__init__.py', 'bad.py', 'foo.py']

    bld.add_module(tests.foo, ('a', '1'))

    assert sorted(dict_tree['a']['1']['tests'].keys()) == ['foo']
    assert sorted(dict_tree['a']['1']['tests']['foo'].keys()) == ['__init__.py', 'bad.py', 'foo.py']

    bld.add_module(os.path.dirname(tests.foo.__file__), ('a', '2'))

    assert sorted(dict_tree['a']['2'].keys()) == ['foo']
    assert sorted(dict_tree['a']['2']['foo'].keys()) == ['__init__.py', 'bad.py', 'foo.py']
