import sys


class BlobServer(object):
    @classmethod
    def check_run(cls):
        try:
            i = sys.argv.index('--pybake-server')
        except ValueError:
            return
        cls().run(*sys.argv[i + 1: i + 2])
        exit(0)

    def run(self, address='8080'):
        if ':' in address:
            bind, port = address.split(':', 1)
        else:
            bind = 'localhost'
            port = address
        port = int(port)

        from http.server import SimpleHTTPRequestHandler, HTTPServer

        class Server(HTTPServer):
            def __init__(self, *args, **kwargs):
                HTTPServer.__init__(self, *args, **kwargs)
                self.RequestHandlerClass.base_path = sys.argv[0]

        class Handler(SimpleHTTPRequestHandler):
            def translate_path(self, path):
                ret = sys.argv[0] + path
                return ret

        httpd = Server((bind, port), Handler)
        sys.stdout.write('Serving PyBake file system on http://%s:%d/ hit CTRL+C to exit\n' % (bind, port))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            sys.stdout.write('\n')
