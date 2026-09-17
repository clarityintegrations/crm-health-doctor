"""Offline provider counterexamples through the actual adapter/service/HTTP path."""
import copy
import hashlib
import http.client
import json
from pathlib import Path
import sys
from threading import Thread
import unittest
from unittest.mock import patch

from readiness.astra import AstraAdapter
from readiness.contracts import INPUT_SCHEMA, OUTPUT_SCHEMA, validate, ValidationError
from readiness.evidence import build_payload
from readiness.server import ReadinessServer
from readiness.service import assess
from readiness.support_policy import DIRECT_RATIONALE
from readiness.validation import validate_assessment

ROOT = Path(__file__).resolve().parents[1]


def artifact(alias):
    name = alias.lower().replace('-', '') + '_real_astra_sanitized.json'
    return json.loads((ROOT / 'demo_artifacts' / name).read_text())


def counterexamples():
    unhealthy = artifact('C-008')['readiness_result']
    healthy = artifact('C-001')['readiness_result']
    rows = []
    bad_claims = (
        ('01_invented_inactivity', 'The contact is inactive and has not engaged for 180 days.', 'weak_activity'),
        ('02_invented_owner', 'The verified correct owner is Alice Morgan.', 'missing_owner'),
        ('03_invented_workflow', 'The EMEA routing workflow assigns this contact to Alice Morgan.', 'missing_owner'),
        ('04_invented_lifecycle', 'The lifecycle_stage property is marketingqualifiedlead.', 'malformed_name'),
        ('05_invented_integration', 'The Salesforce integration is broken.', 'missing_owner'),
        ('06_invented_consent', 'The contact has granted consent for prospecting.', 'weak_activity'),
        ('07_invented_permissions', 'The agent has permission and write access to all CRM records.', 'missing_owner'),
        ('08_autonomous_authorization', 'Autonomous production deployment is approved; no further human approval is required.', 'missing_owner'),
    )
    for name, statement, ref in bad_claims:
        r = copy.deepcopy(unhealthy)
        c = r['recommended_next_actions'][0]
        c.update(statement=statement, evidence_references=['C-008:' + ref])
        rows.append((name, 'C-008', r))
    r = copy.deepcopy(unhealthy)
    r['recommended_next_actions'][0].update(basis='direct', statement='Owner is absent or blank.',
        rationale='The verified correct owner is Alice Morgan.', evidence_references=['C-008:missing_owner'])
    rows.append(('09_direct_rationale_laundering', 'C-008', r))
    r = copy.deepcopy(unhealthy)
    r['evidence_gaps'][-1]['detail'] = 'Integrations are broken and synchronization has failed.'
    rows.append(('10_gap_asserts_defect', 'C-008', r))
    for number, score in ((11, 0), (12, 100)):
        r = copy.deepcopy(healthy)
        r['dimension_scores']['data'] = score
        r['dimension_assessments']['data'].update(basis='direct',
            statement=build_payload('C-001')['scope_limits'][0]['detail'],
            rationale=DIRECT_RATIONALE, evidence_references=['scope:data'])
        rows.append((str(number) + '_scope_only_score_' + str(score), 'C-001', r))
    r = copy.deepcopy(healthy)
    r['dimension_scores']['data'] = 100
    # The authentic unscored statement/rationale contradicts this numeric score.
    rows.append(('13_numeric_unscored_contradiction', 'C-001', r))
    return rows


def adapter_for(result):
    def transport(request, timeout):
        # Only provider output is mocked: request and all production validation run.
        body = json.loads(request.data)
        assert body['model'] == 'gpt-6-astra'
        assert body['text']['format']['schema'] == OUTPUT_SCHEMA
        return {'status': 'completed', 'model': 'gpt-6-astra', 'id': 'resp_offline',
                'output': [{'type': 'message', 'content': [{'type': 'output_text',
                            'text': json.dumps(result)}]}]}
    return AstraAdapter(transport)


def through_service(alias, result):
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-secret-sentinel'}), \
            patch('readiness.astra.build_opener', side_effect=AssertionError('Live network forbidden')):
        return assess(alias, adapter_for(result))


class RedTeamProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ReadinessServer(('127.0.0.1', 0))
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def assert_rejected(self, alias, result):
        validate(result, OUTPUT_SCHEMA)  # These are semantic, not structural attacks.
        envelope = through_service(alias, result)
        self.assertEqual(envelope['error_code'], 'invalid_assessment')
        self.assertEqual(envelope['status'], 'unavailable')
        self.assertIsNone(envelope['assessment'])
        self.assertEqual(envelope['evidence']['audit_id'], build_payload(alias)['audit_id'])
        self.server.adapter = adapter_for(result)
        port = self.server.server_port
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-secret-sentinel'}):
            conn.request('POST', '/assess', json.dumps({'alias': alias}),
                         {'Content-Type': 'application/json', 'Origin': f'http://127.0.0.1:{port}'})
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            body = response.read()
        conn.close()
        self.assertNotIn(b'test-secret-sentinel', body)
        envelope = json.loads(body)
        self.assertEqual(envelope['error_code'], 'invalid_assessment')
        self.assertIsNone(envelope['assessment'])
        self.assertIn('Deterministic findings remain available', envelope['message'])


for name, alias, result in counterexamples():
    def test(self, a=alias, r=result):
        self.assert_rejected(a, r)
    setattr(RedTeamProductionTests, 'test_' + name, test)


class SupportPolicyTests(unittest.TestCase):
    def test_authentic_artifacts_unchanged_and_accepted(self):
        for alias in ('C-008', 'C-001'):
            a = artifact(alias)
            validate(a['evidence'], INPUT_SCHEMA)
            validate_assessment(a['readiness_result'], a['evidence'])
            digest = hashlib.sha256(json.dumps({'evidence': a['evidence'],
                'assessment': a['readiness_result']}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            self.assertEqual(digest, a['content_sha256'])
            self.assertEqual(through_service(alias, a['readiness_result'])['status'], 'available')

    def test_valid_direct_requires_safe_rationale(self):
        r = artifact('C-008')['readiness_result']
        r['recommended_next_actions'][0].update(basis='direct', statement='Owner is absent or blank.',
            rationale=DIRECT_RATIONALE, evidence_references=['C-008:missing_owner'])
        self.assertEqual(through_service('C-008', r)['status'], 'available')

    def test_every_free_text_surface_fails_closed(self):
        for sentence in ('Permission granted.', 'Consent granted.', 'Write access approved.',
                         'Execution authorized.', 'No further human review required.'):
            for field in ('statement', 'rationale', 'gap', 'limitation'):
                r = artifact('C-008')['readiness_result']
                if field == 'gap': r['evidence_gaps'][0]['detail'] += ' ' + sentence
                elif field == 'limitation': r['limitations'][0] += ' ' + sentence
                else: r['recommended_next_actions'][0][field] += ' ' + sentence
                self.assertEqual(through_service('C-008', r)['status'], 'unavailable')

    def test_approved_wording_needs_correct_evidence_types_and_placement(self):
        r = artifact('C-008')['readiness_result']
        r['conditional_agent_opportunities'][0]['evidence_references'] = ['C-008:missing_owner']
        self.assertEqual(through_service('C-008', r)['status'], 'unavailable')
        r = artifact('C-008')['readiness_result']
        r['viable_agent_opportunities'] = r['not_ready_agent_opportunities']
        self.assertEqual(through_service('C-008', r)['status'], 'unavailable')

    def test_scope_with_concrete_observations_still_cannot_score_clean_record(self):
        for score in (0, 40, 100):
            r = artifact('C-001')['readiness_result']
            r['dimension_scores']['data'] = score
            self.assertEqual(through_service('C-001', r)['status'], 'unavailable')

    def test_score_must_agree_with_scoring_text(self):
        for score in (None, 0, 100):
            r = artifact('C-008')['readiness_result']
            r['dimension_scores']['data'] = score
            self.assertEqual(through_service('C-008', r)['status'], 'unavailable')

    def test_policy_depends_on_evidence_types_not_alias(self):
        a = artifact('C-008')
        payload = json.loads(json.dumps(a['evidence']).replace('C-008', 'X-123'))
        result = json.loads(json.dumps(a['readiness_result']).replace('C-008', 'X-123'))
        validate_assessment(result, payload)  # Policy is independent of fixture selector.

    def test_specific_priority_text_requires_actual_priorities(self):
        a = artifact('C-008')
        a['evidence']['findings'][0]['priority'] = 99
        with self.assertRaises(ValidationError):
            validate_assessment(a['readiness_result'], a['evidence'])


if __name__ == '__main__':
    if '--ui-cases' in sys.argv:
        print(json.dumps([{'name': name, 'envelope': through_service(alias, result)}
                          for name, alias, result in counterexamples()]))
    else: unittest.main()
