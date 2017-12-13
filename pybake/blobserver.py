import sys


class BlobServer(object):
    @classmethod
    def check_run(cls):
        try:
            i = sys.argv.index('--pybake-server')
            cls().run(*sys.argv[i+1 : i+2])
        except ValueError:
            pass

    def run(self, port=None):
        port = int(port or 8080)
        from SimpleHTTPServer import SimpleHTTPRequestHandler
        from BaseHTTPServer import HTTPServer

        class Server(HTTPServer):
            def __init__(self, *args, **kwargs):
                HTTPServer.__init__(self, *args, **kwargs)
                self.RequestHandlerClass.base_path = sys.argv[0]

        class Handler(SimpleHTTPRequestHandler):
            def translate_path(self, path):
                ret = sys.argv[0] + path
                return ret

        httpd = Server(('', port), Handler)
        sys.stdout.write('Serving PyBake file system on http://localhost:%d/ hit CTRL+C to exit\n' % port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print
            exit(0)

