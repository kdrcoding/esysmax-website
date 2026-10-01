"""Local preview of the site with the same clean addresses as .htaccess (/buy serves buy.html).

    python tools/serve.py [port]
"""
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def send_head(self):
        path = self.path.split('?', 1)[0].split('#', 1)[0]
        local = os.path.join(ROOT, path.lstrip('/'))
        if path != '/' and not os.path.exists(local) and os.path.exists(local.rstrip('/') + '.html'):
            self.path = path.rstrip('/') + '.html' + (self.path[len(path):] if len(self.path) > len(path) else '')
        elif path != '/' and not os.path.exists(local):
            self.path = '/404.html'
        return super().send_head()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8790
    http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
