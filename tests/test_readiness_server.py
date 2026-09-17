import http.client
import json
from threading import Thread
import unittest
from unittest.mock import patch
from readiness.server import ReadinessServer
from readiness.astra import AstraAdapter
from tests.test_readiness import mock_assessment


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def transport(req, timeout):
            payload = json.loads(json.loads(req.data)['input'])
            return {'status': 'completed', 'model': 'gpt-6-astra', 'id': 'resp_test',
                    'output': [{'type': 'message', 'content': [{'type': 'output_text',
                        'text': json.dumps(mock_assessment(payload))}]}]}
        cls.server = ReadinessServer(('127.0.0.1', 0), AstraAdapter(transport))
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def call(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        conn.request(method, path, body, headers or {})
        response = conn.getresponse()
        status, content = response.status, response.read()
        conn.close()
        return status, content

    def test_local_evidence_and_v1(self):
        for path in ('/', '/v1', '/ui.js', '/evidence?alias=C-001'):
            self.assertEqual(self.call('GET', path)[0], 200)
        self.assertEqual(self.call('GET', '/evidence?alias=unknown')[0], 400)
        self.assertEqual(self.call('GET', '/../../.env')[0], 404)

    def test_post_success_and_missing_key(self):
        headers = {'Content-Type': 'application/json',
                   'Origin': f'http://127.0.0.1:{self.server.server_port}'}
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-secret-sentinel'}):
            code, data = self.call('POST', '/assess', '{"alias":"C-008"}', headers)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(data)['status'], 'available')
        self.assertNotIn(b'test-secret-sentinel', data)
        with patch.dict('os.environ', {}, clear=True):
            _, data = self.call('POST', '/assess', '{"alias":"C-001"}', headers)
        self.assertEqual(json.loads(data)['error_code'], 'missing_key')
        self.assertEqual(json.loads(data)['evidence']['record']['alias'], 'C-001')

    def test_cross_origin_host_and_body_rejected(self):
        self.assertEqual(self.call('GET', '/', headers={'Host': 'evil.example'})[0], 403)
        headers = {'Content-Type': 'application/json', 'Origin': 'https://evil.example'}
        self.assertEqual(self.call('POST', '/assess', '{"alias":"C-008"}', headers)[0], 403)
        headers['Origin'] = f'http://127.0.0.1:{self.server.server_port}'
        for body in ('{}', '{"alias":"C-008","url":"x"}', '{', 'x' * 129):
            self.assertEqual(self.call('POST', '/assess', body, headers)[0], 400)
        self.server.assessment_lock.acquire()
        try: self.assertEqual(self.call('POST', '/assess', '{"alias":"C-008"}', headers)[0], 409)
        finally: self.server.assessment_lock.release()
