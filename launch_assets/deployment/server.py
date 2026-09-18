"""Render transport and launch links around the frozen readiness runtime.

No directory serving, copied assessment logic, prompt changes, or CRM writes.
TLS terminates at Render. Only its configured service hostname is accepted.
"""
import os
from urllib.parse import urlparse

from readiness.evidence import ROOT
from readiness.server import Handler, ReadinessServer, ASSETS


PLAYBACK = '/launch_assets/demo_playback/'
PUBLIC_FILES = {
    PLAYBACK + name: (ROOT / 'launch_assets/demo_playback' / name, kind)
    for name, kind in (
        ('index.html', 'text/html'), ('c008.html', 'text/html'),
        ('c001.html', 'text/html'), ('styles.css', 'text/css'),
        ('script.js', 'text/javascript'),
    )
}
for name in ('c008_real_astra_sanitized.json', 'c001_real_astra_sanitized.json'):
    PUBLIC_FILES['/demo_artifacts/' + name] = (ROOT / 'demo_artifacts' / name, 'application/json')


class PublicHandler(Handler):
    server_version = 'CRMHealthDoctor'
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def allowed(self, post=False):
        # No wildcard hosts, forwarded-header trust, or cross-origin POSTs.
        return (self.headers.get_all('Host') == [self.server.public_host]
                and (not post or self.headers.get_all('Origin') == [self.server.public_origin]))

    def do_GET(self):
        if not self.allowed():
            return self.send(403, {'error': 'Service host required'})
        path = urlparse(self.path).path
        if path == '/':
            live = bool(os.environ.get('OPENAI_API_KEY', '').strip())
            notice = ('Live assessment is configured; it makes a new API request.' if live else
                      'Live Astra assessment is not enabled on this public demo. Use the preserved real Astra assessments above.')
            notice_tag = '<p>' if live else '<p id="live-assessment-notice">'
            links = (f'<nav aria-label="Challenge demonstration"><p>'
                     f'<a href="{PLAYBACK}c008.html">C-008 preserved Astra assessment</a> · '
                     f'<a href="{PLAYBACK}c001.html">C-001 preserved Astra assessment</a> · '
                     f'<a href="{PLAYBACK}index.html">Demo index</a></p></nav>'
                     '<p>The deployed Python runtime includes the real GPT-6 Astra integration. '
                     'The Assess button calls its server-side /assess route. '
                     'Preserved assessments are playback, not live inference.</p>'
                     f'{notice_tag}{notice}</p>')
            page = (ASSETS / 'page.html').read_text(encoding='utf-8')
            page = page.replace('<label for="alias">', links + '<label for="alias">', 1)
            if not live:
                # Native fieldset disabling survives the frozen UI's evidence-load
                # callback clearing button.disabled. Record selection stays outside.
                button = '<button id="assess" type="button">Assess with GPT-6 Astra</button>'
                page = page.replace(button,
                    '<fieldset disabled style="display:inline-block;border:0;padding:0;margin:0">'
                    '<button id="assess" type="button" disabled '
                    'aria-describedby="live-assessment-notice" style="cursor:not-allowed">'
                    'Assess with GPT-6 Astra</button></fieldset>', 1)
            return self.send(200, page.encode(), 'text/html')
        if path in (PLAYBACK, '/demo'):
            path = PLAYBACK + 'index.html'
        if path in PUBLIC_FILES:
            file, kind = PUBLIC_FILES[path]
            data = file.read_bytes()
            if kind == 'text/html':
                # Navigation only; the original playback and capture files remain unchanged.
                data = data.replace(b'</main>', b'<p><a href="/">Open product and deterministic evidence</a></p></main>', 1)
            # Handler.send JSON-encodes objects. Preserve capture bytes verbatim instead.
            if kind == 'application/json':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('X-Frame-Options', 'DENY')
                self.end_headers()
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            return self.send(200, data, kind)
        # Original evidence, UI script, V1 snapshot and 404 behavior.
        return super().do_GET()


def create_server(address, public_host, public_origin):
    server = ReadinessServer(address)
    server.RequestHandlerClass = PublicHandler
    server.public_host = public_host
    server.public_origin = public_origin
    return server


def main():
    host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
    if not host or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-.' for c in host):
        raise SystemExit('A valid RENDER_EXTERNAL_HOSTNAME is required.')
    server = create_server(('0.0.0.0', int(os.environ.get('PORT', '10000'))), host, 'https://' + host)
    print('Agent Readiness challenge server ready.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
