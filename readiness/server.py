"""Local demonstration server. No public deployment or CRM mutation surface."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse, parse_qs
from .evidence import ROOT, build_payload
from .service import assess

ASSETS = Path(__file__).parent


class ReadinessServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, adapter=None):
        self.adapter = adapter
        self.assessment_lock = Lock()
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Never log request bodies or arbitrary URLs.

    def allowed(self, post=False):
        port = self.server.server_port
        hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
        host = self.headers.get('Host')
        origin = self.headers.get('Origin')
        return host in hosts and (not post or origin == 'http://' + host)

    def send(self, code, body, kind='application/json'):
        data = json.dumps(body).encode() if kind == 'application/json' else body
        self.send_response(code)
        self.send_header('Content-Type', kind + '; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError): pass

    def do_GET(self):
        if not self.allowed(): return self.send(403, {'error': 'Local host required'})
        url = urlparse(self.path)
        files = {'/': (ASSETS / 'page.html', 'text/html'), '/ui.js': (ASSETS / 'ui.js', 'text/javascript'),
                 '/v1': (ROOT / 'outputs/index.html', 'text/html')}
        if url.path in files:
            path, kind = files[url.path]
            return self.send(200, path.read_bytes(), kind)
        if url.path == '/evidence':
            query = parse_qs(url.query)
            if set(query) != {'alias'} or len(query['alias']) != 1:
                return self.send(400, {'error': 'Invalid selection'})
            try: return self.send(200, build_payload(query['alias'][0]))
            except ValueError: return self.send(400, {'error': 'Invalid selection'})
        self.send(404, {'error': 'Not found'})

    def do_POST(self):
        if not self.allowed(post=True): return self.send(403, {'error': 'Same-origin request required'})
        if self.path != '/assess': return self.send(404, {'error': 'Not found'})
        if self.headers.get('Content-Type') != 'application/json': return self.send(415, {'error': 'JSON required'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 128: raise ValueError()
            self.connection.settimeout(5)
            body = json.loads(self.rfile.read(length))
            if type(body) is not dict or set(body) != {'alias'} or body['alias'] not in ('C-008', 'C-001'):
                raise ValueError()
        except (ValueError, TypeError, OSError): return self.send(400, {'error': 'Invalid selection'})
        if not self.server.assessment_lock.acquire(blocking=False): return self.send(409, {'error': 'Assessment in progress'})
        try: self.send(200, assess(body['alias'], self.server.adapter))
        finally: self.server.assessment_lock.release()


def serve(port=8766):
    server = ReadinessServer(('127.0.0.1', port))
    print(f'Agent Readiness Edition: http://127.0.0.1:{port}', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
