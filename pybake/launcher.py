# flake8: noqa
_ = ''
# -- inline cut --
import binascii, json, zlib
_ = json.loads(zlib.decompress(binascii.a2b_base64(_))); exec(_[0])
# -- execable cut --
import imp
import sys

sys.modules.setdefault('pybake', imp.new_module('pybake'))

for name in _[1]:
    mod = sys.modules.setdefault('pybake.%s' % name,
                                 imp.new_module('pybake.%s' % name))
    format, content = _[2]['pybake'][name + '.py']
    if format == 'base64':
        content = binascii.a2b_base64(content)
    exec compile(content,
                 sys.argv[0] + '/pybake/%s' % name + '.py',
                 'exec') in mod.__dict__

from pybake.dictfilesystem import DictFileSystem
from pybake.abstractimporter import AbstractImporter

reader = DictFileSystem(sys.argv[0], _[2])
importer = AbstractImporter(sys.argv[0], reader)
importer.install()

from pybake.dictfilesysteminterceptor import DictFileSystemInterceptor
filesystem = DictFileSystemInterceptor(reader)
filesystem.install()

from pybake.blobserver import BlobServer
BlobServer.check_run()

del binascii, json, zlib
del _
del imp, sys
del name, mod, format, content
del DictFileSystem, AbstractImporter, DictFileSystemInterceptor, BlobServer
del reader, importer, filesystem
# -- user init --
# if __name__ == '__main__':
#    from foo.cli.main import main
#    exit(main())
