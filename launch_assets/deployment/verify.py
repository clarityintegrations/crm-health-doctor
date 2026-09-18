"""Bounded deployment-route checks. Never make a live model request."""
import hashlib
from html.parser import HTMLParser
from http.client import HTTPConnection
import json
import os
import re
from threading import Thread
import unittest
from unittest.mock import patch

from .server import create_server, PUBLIC_FILES, PLAYBACK


class Controls(HTMLParser):
    def __init__(self):
        super().__init__()
        self.disabled_fieldset = False
        self.buttons = []
        self.selects = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'fieldset':
            self.disabled_fieldset = 'disabled' in attrs
        if tag == 'button':
            self.buttons.append((attrs, self.disabled_fieldset))
        if tag == 'select':
            self.selects.append((attrs, self.disabled_fieldset))

    def handle_endtag(self, tag):
        if tag == 'fieldset':
            self.disabled_fieldset = False


class DeploymentChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = patch.dict(os.environ, {'OPENAI_API_KEY': ''})
        cls.env.start()
        cls.server = create_server(('127.0.0.1', 0), 'demo.example', 'https://demo.example')
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.env.stop()

    def request(self, path, method='GET', body=None, host='demo.example', origin=None):
        conn = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        headers = {'Host': host}
        if origin is not None:
            headers['Origin'] = origin
        if body is not None:
            headers['Content-Type'] = 'application/json'
        conn.request(method, path, body, headers)
        response = conn.getresponse()
        result = response.status, response.read()
        conn.close()
        return result

    def test_public_routes_and_exposure(self):
        paths = ['/', '/ui.js', '/v1', '/demo', PLAYBACK,
                 '/evidence?alias=C-008', '/evidence?alias=C-001', *PUBLIC_FILES]
        forbidden = rb'/Users/|/home/|file://|https?://(?:localhost|127\.0\.0\.1)|sk-[A-Za-z0-9_-]{20,}|gh[opusr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY'
        for path in paths:
            with self.subTest(path=path):
                status, data = self.request(path)
                self.assertEqual(status, 200)
                self.assertIsNone(re.search(forbidden, data))
        for alias, count, priority in [('C-008', 3, 95), ('C-001', 0, 0)]:
            data = json.loads(self.request('/evidence?alias=' + alias)[1])
            self.assertEqual(data['audit_metadata']['source'], 'fixture')
            self.assertEqual(data['audit_metadata']['finding_count'], count)
            self.assertEqual(data['audit_metadata']['highest_priority'], priority)

    def test_preserved_captures_and_labels(self):
        hashes = {'c008': '7d8bbeff8cf4b3bc302543d0b890401063645d74ef8c604e6706506fbc7d566e',
                  'c001': 'c7c9000f6a6b41ed13c1731a808025b2a24605ce65555fe37976abd3c2adddbe'}
        for alias, expected in hashes.items():
            data = self.request('/demo_artifacts/' + alias + '_real_astra_sanitized.json')[1]
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected)
            html = self.request(PLAYBACK + alias + '.html')[1].decode()
            self.assertIn('Previously generated real GPT-6 Astra assessment', html)
            self.assertIn('Real inference over synthetic CRM evidence — playback, not live inference.', html)

    def test_assess_capability_presentation_only(self):
        # Non-credential sentinel exercises HTML rendering only. Never POST here.
        for key in ('', '   ', 'non-credential-render-test'):
            with self.subTest(configured=bool(key.strip())):
                with patch.dict(os.environ, {'OPENAI_API_KEY': key}):
                    status, body = self.request('/')
                self.assertEqual(status, 200)
                html = body.decode()
                controls = Controls()
                controls.feed(html)
                button, inherited_disabled = next(b for b in controls.buttons if b[0].get('id') == 'assess')
                selector, selector_disabled = next(s for s in controls.selects if s[0].get('id') == 'alias')
                self.assertNotIn('disabled', selector)
                self.assertFalse(selector_disabled)
                self.assertEqual(inherited_disabled, not bool(key.strip()))
                self.assertEqual('disabled' in button, not bool(key.strip()))
                self.assertIn('<script src="/ui.js"></script>', html)
                self.assertIn(PLAYBACK + 'c008.html', html)
                self.assertIn(PLAYBACK + 'c001.html', html)
                self.assertNotIn('non-credential-render-test', html)
                if not key.strip():
                    self.assertEqual(button['aria-describedby'], 'live-assessment-notice')
                    self.assertEqual(html.count('Live Astra assessment is not enabled on this public demo.'), 1)
                else:
                    self.assertNotIn('<fieldset', html)
                    self.assertIn('Live assessment is configured; it makes a new API request.', html)

    def test_no_directory_or_private_file_serving(self):
        for path in ['/.env', '/.git/config', '/readiness/astra.py', '/fixtures/health_matrix.json',
                     '/outputs/hubspot-report.html', '/fixtures/hubspot-integration-sanitized.json',
                     PLAYBACK + 'README.md', '/demo_artifacts/', '/demo_artifacts/../README.md']:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(self.request('/evidence?alias=C-999')[0], 400)

    def test_host_origin_and_existing_no_key_path(self):
        self.assertEqual(self.request('/', host='attacker.example')[0], 403)
        body = json.dumps({'alias': 'C-008'})
        for origin in [None, 'https://attacker.example', 'http://demo.example']:
            self.assertEqual(self.request('/assess', 'POST', body, origin=origin)[0], 403)
        status, data = self.request('/assess', 'POST', body, origin='https://demo.example')
        self.assertEqual(status, 200)
        result = json.loads(data)
        self.assertEqual(result['status'], 'unavailable')
        self.assertIsNone(result['assessment'])
        self.assertEqual(result['evidence']['record']['alias'], 'C-008')


if __name__ == '__main__':
    unittest.main()
