# flake8: noqa
_ = ''
# -- inline cut --
import binascii, json, zlib
_ = json.loads(zlib.decompress(binascii.a2b_base64(_))); exec(_[0], globals())
# -- execable cut --
import types
import sys


sys.modules.setdefault('pybake', types.ModuleType('pybake'))

for name in _[1]:
    mod = sys.modules.setdefault('pybake.%s' % name,
                                 types.ModuleType('pybake.%s' % name))

    format, content = _[2]['pybake'][name + '.py']
    if format == 'base64':
        content = binascii.a2b_base64(content)
    exec(compile(content,
                 __file__ + '/pybake/%s' % name + '.py',
                 'exec'), mod.__dict__)

from pybake.dictfilesystem import DictFileSystem
from pybake.abstractimporter import AbstractImporter

reader = DictFileSystem(__file__, _[2])
importer = AbstractImporter(__file__, reader)
importer.install()

from pybake.dictfilesysteminterceptor import DictFileSystemInterceptor
filesystem = DictFileSystemInterceptor(reader)
filesystem.install()

from pybake.blobserver import BlobServer
BlobServer.check_run()

del binascii, json, zlib
del _
del types, sys
del name, mod, format, content
del DictFileSystem, AbstractImporter, DictFileSystemInterceptor, BlobServer
del reader, importer, filesystem
# -- user init --
# if __name__ == '__main__':
#    from foo.cli.main import main
#    exit(main())
