import sys

if sys.version_info[0] == 3:
    BUILTINS_OPEN = 'builtins.open'
else:
    BUILTINS_OPEN = '__builtin__.open'


class FileSystemInterceptor(object):
    def __init__(self, intercept_list):
        self._intercept_list = intercept_list
        self._oldhooks = {}

    def __enter__(self):
        self.install()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.uninstall()

    def install(self):
        for fullpath in self._intercept_list:
            method_name = self._method_name(fullpath)
            try:
                method = getattr(self, method_name)
                self._oldhooks[fullpath] = self._hook(fullpath, method)
            except AttributeError:
                def make_dummy(fullpath):
                    def dummy(*args, **kwargs):
                        return self._shim(fullpath, *args, **kwargs)
                    return dummy
                self._oldhooks[fullpath] = self._hook(fullpath, make_dummy(fullpath))
                pass

    def uninstall(self):
        for fullpath, oldhook in list(self._oldhooks.items()):
            self._oldhooks[fullpath] = self._hook(fullpath, oldhook)

    @classmethod
    def _method_name(cls, fullpath):
        return '_%s' % fullpath.replace('_', '').replace('.', '_')

    @classmethod
    def _hook(cls, fullpath, newhook):
        s = fullpath.split('.')
        path, base = '.'.join(s[:-1]), s[-1]
        mod = __import__(path, globals(), locals(), [base])
        try:
            oldhook = getattr(mod, base)
        except AttributeError:
            raise AttributeError("'%s' has no attribute '%s'" % (path, base))
        setattr(mod, base, newhook)
        return oldhook

    def _shim(self, fullpath, *args, **kwargs):
        ret = self._oldhooks[fullpath](*args, **kwargs)
        return ret
