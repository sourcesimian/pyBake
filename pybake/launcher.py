_ = 'placeholder'
# -- inline cut --
import base64, json, zlib
_ = json.loads(zlib.decompress(base64.b64decode(_))); exec(_[0])
# -- obscure cut --
del base64, json, zlib
import imp, sys

sys.modules.setdefault('pybake', imp.new_module('pybake'))

for name in ('abstractimporter', 'dictfilesystem', 'filesysteminterceptor',
             'dictfilesysteminterceptor', 'blobserver'):
    mod = sys.modules.setdefault('pybake.%s' % name, imp.new_module('pybake.%s' % name))
    exec compile(_[1]['pybake'][name + '.py'],
                 sys.argv[0] + '/pybake/%s.py' % name,
                 'exec') in mod.__dict__

from pybake.dictfilesystem import DictFileSystem
from pybake.abstractimporter import AbstractImporter

reader = DictFileSystem(sys.argv[0], _[1])
importer = AbstractImporter(sys.argv[0], reader)
importer.install()

from pybake.dictfilesysteminterceptor import DictFileSystemInterceptor
filesystem = DictFileSystemInterceptor(reader)
filesystem.install()

from pybake.blobserver import BlobServer
BlobServer.check_run()

del _, imp, sys, mod, name
del DictFileSystem, AbstractImporter, DictFileSystemInterceptor
del reader, importer ,filesystem
