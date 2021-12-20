import re
import binascii
import json
import zlib
import sys
import subprocess
try:
    from StringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
from textwrap import dedent

import pybake
from pybake import PyBake


def test_bake(tmpdir):
    header = '# HEADER'
    footer = '# FOOTER'
    width = 50
    pb = PyBake(header, footer, width=width, suffix='#|', python='python2')

    text = BytesIO(b'Hello world!')
    pb.add_file(('res', 'msg.txt'), text)

    path = str(tmpdir.join('foobake.py'))
    pb.write_bake(path)

    with open(path, 'rt') as fh:
        bake_content_lines = fh.read().splitlines()

    assert len(bake_content_lines[1]) == width
    assert header in bake_content_lines[1]

    assert len(bake_content_lines[-2]) == width
    assert footer in bake_content_lines[-2]

    assert len(bake_content_lines[-1]) == width

    b64_blob = None
    start, end = "_='''", "'''"
    for line in bake_content_lines:
        if start in line:
            b64_blob = line[len(start):]
            continue
        if end in line:
            i = line.find(end)
            b64_blob += line[:i]
            break
        if b64_blob is not None:
            b64_blob += line + '\n'

    zlib_blob = binascii.a2b_base64(b64_blob)
    json_blob = zlib.decompress(zlib_blob)
    blob = json.loads(json_blob)
    execable, preload, fs = blob

    assert fs['res']['msg.txt'][0] == 'base64'

    expected = b'Hello world!'
    actual = binascii.a2b_base64(fs['res']['msg.txt'][1])
    assert expected == actual


def run_code(cwd, code):
    args = [sys.executable, '-c', code]
    p = subprocess.Popen(args=args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    return p.returncode, p.stdout.read().decode('utf-8'), p.stderr.read().decode('utf-8')


def test_as_module(tmpdir):
    header = '# HEADER'
    footer = '# FOOTER'
    width = 50
    pb = PyBake(header, footer, width=width, suffix='#|', python='python2')

    text = BytesIO(b'')
    pb.add_file(('tests', '__init__.py'), text)

    import tests.foo
    pb.add_module(tests.foo)

    pb.add_module(pybake, ('sub',))

    text = BytesIO(b'Hello world!')
    pb.add_file(('res', 'msg.txt'), text)

    path = str(tmpdir.join('foobake.py'))
    pb.write_bake(path)

    # Test dir() on module
    _, stdout, stderr = run_code(tmpdir.strpath,
        r"import foobake; print('\n'.join(sorted(dir(foobake))))")

    found = stdout.splitlines()
    expected = ('__builtins__', '__doc__', '__file__', '__name__', '__package__')
    for item in expected:
        assert item in found

    # Test module __file__
    _, stdout, _ = run_code(tmpdir.strpath,
        r"import foobake, os; print(foobake.__file__)")

    assert stdout.rstrip().endswith('foobake.pyc') or stdout.rstrip().endswith('foobake.py')

    # Test os.path.exists() on blob file system
    _, stdout, stderr = run_code(tmpdir.strpath,
        r"import foobake, os; print(os.path.exists(foobake.__file__))")

    assert stdout.rstrip() == 'True'


    # Test listdir() on blob file system
    _, stdout, _ = run_code(tmpdir.strpath,
        r"import foobake, os; print('\n'.join(sorted(os.listdir(os.path.join(foobake.__file__, 'sub/pybake')))))")

    found = stdout.splitlines()
    expected = (
        '__init__.py',
        'abstractimporter.py',
        'blobserver.py',
        'dictfilesystem.py',
        'dictfilesystembuilder.py',
        'dictfilesysteminterceptor.py',
        'filesysteminterceptor.py',
        'launcher.py',
        'moduletree.py',
        'pybake.py',
    )
    for item in expected:
        assert item in found

    # Test open() on blob file system
    _, stdout, stderr = run_code(tmpdir.strpath,
        r"import foobake, os; print(open(os.path.join(foobake.__file__, 'res/msg.txt')).read().decode('utf-8'))")

    assert stdout == 'Hello world!\n'

    # Test importing and inspection on blob file system
    _, stdout, _ = run_code(tmpdir.strpath,
        r"import foobake; from tests.foo import Foo; f = Foo(); print(f.file()); print(f.src())")

    actual = stdout.splitlines()
    expected = (
        'foobake.py/tests/foo/foo.py',
        'foobake.pyc/tests/foo/foo.py'
    )
    for item in actual:
        assert item.endswith(expected)

    # Test exception tracebacks on blob files system
    _, _, stderr = run_code(tmpdir.strpath,
        r"import foobake; from tests.foo import Foo; f = Foo(); f.bang()")

    def normalise_traceback(input):
        return re.sub('File ".*foobake.py(c)?', 'File "foobake.py', input)

    stderr = normalise_traceback(stderr)
    expected = dedent('''\
        Traceback (most recent call last):
          File "<string>", line 1, in <module>
          File "foobake.py/tests/foo/foo.py", line 16, in bang
          File "foobake.py/tests/foo/foo.py", line 19, in _bang
        ValueError: from Foo
        ''')

    assert expected == stderr

    _, _, stderr = run_code(tmpdir.strpath,
                            r"import foobake; import tests.foo.bad")
    stderr = normalise_traceback(stderr)

    expected = dedent('''\
        Traceback (most recent call last):
          File "foobake.py/pybake/abstractimporter.py", line 81, in load_module
          File "foobake.py/tests/foo/bad.py", line 2
            x =  # Cause import error
                 ^
        SyntaxError: invalid syntax
        
        During handling of the above exception, another exception occurred:
        
        Traceback (most recent call last):
          File "<string>", line 1, in <module>
          File "foobake.py/pybake/abstractimporter.py", line 90, in load_module
          File "foobake.py/pybake/abstractimporter.py", line 119, in reraise
          File "foobake.py/pybake/abstractimporter.py", line 81, in load_module
        ImportError: SyntaxError: invalid syntax (bad.py, line 2), while importing 'tests.foo.bad'
        ''')

    assert stderr == expected
