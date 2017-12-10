_ = 'placeholder'
# -- inline cut --
import base64, json, zlib
user, _ = json.loads(zlib.decompress(base64.b64decode(_))); exec(_['_'])
# -- obscure cut --
del base64, json, zlib
import imp, sys

sys.modules.setdefault('pybake', imp.new_module('pybake'))
for name, script in _['pybake']:
    mod = sys.modules.setdefault('pybake.%s' % name, imp.new_module('pybake.%s' % name))
    exec compile(script, sys.argv[0] + '/pybake/%s.py' % name, 'exec') in mod.__dict__

from pybake.dictfilesystem import DictFileSystem
from pybake.abstractimporter import AbstractImporter
from pybake.dictfilesysteminterceptor import DictFileSystemInterceptor

reader = DictFileSystem(sys.argv[0], _['fs'])
importer = AbstractImporter(sys.argv[0], reader)
filesystem = DictFileSystemInterceptor(reader)

importer.install()
filesystem.install()

del _, imp, sys, mod, name, script
del DictFileSystem, AbstractImporter, DictFileSystemInterceptor
del reader, importer ,filesystem
