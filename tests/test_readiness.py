import copy
import json
import os
import unittest
import io
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from readiness.contracts import INPUT_SCHEMA, OUTPUT_SCHEMA, DIMENSIONS, SECTIONS, validate, ValidationError
from readiness.evidence import build_payload, reference_map
from readiness.validation import validate_assessment
from readiness.astra import AstraAdapter, Unavailable, request_json, NoRedirect, MODEL
from readiness.service import assess
from urllib.error import HTTPError


def mock_assessment(payload):
    """Synthetic model output used only in tests; no new CRM facts."""
    alias = payload['record']['alias']
    refs = reference_map(payload)
    def claim(text, ref, basis='inference'):
        return {'statement': text, 'basis': basis, 'rationale': 'Limited to the supplied check and human review.',
                'evidence_references': [ref], 'human_review_required': True}
    result = {'overall_readiness_score': None,
              'dimension_scores': {d: None for d in DIMENSIONS},
              'dimension_assessments': {d: claim(refs['scope:' + d], 'scope:' + d, 'evidence_gap') for d in DIMENSIONS},
              **{s: [] for s in SECTIONS},
              'evidence_references': list(refs),
              'evidence_gaps': [{'dimension': d, 'detail': refs['scope:' + d],
                                'evidence_references': ['scope:' + d]} for d in DIMENSIONS],
              'confidence': 'low', 'limitations': ['One synthetic record; no organizational readiness proven.']}
    result['viable_agent_opportunities'] = [claim('A human-supervised read-only review could inspect supplied evidence.', alias + ':name')]
    if payload['findings']:
        result['critical_blockers'] = [claim('Missing ownership can make autonomous routing unreliable.', alias + ':missing_owner')]
        result['remediation_priorities'] = [claim('Verify intended ownership before assigning.', alias + ':missing_owner')]
    else:
        result['recommended_next_actions'] = [claim('Collect governance evidence before autonomous use.', 'scope:governance', 'evidence_gap')]
    return result


class EvidenceTests(unittest.TestCase):
    def test_unhealthy(self):
        p = build_payload('C-008')
        validate(p, INPUT_SCHEMA)
        self.assertEqual(p['audit_metadata']['highest_priority'], 95)
        self.assertEqual({f['finding_type'] for f in p['findings']}, {'malformed_name', 'missing_owner', 'weak_activity'})
        self.assertNotRegex(json.dumps(p), r'\bowner-a\b|TEST USER|@|hubspot_owner_id')

    def test_healthier_not_proven_ready(self):
        p = build_payload('C-001')
        self.assertEqual(p['findings'], [])
        self.assertEqual(p['audit_metadata']['highest_priority'], 0)
        self.assertIn('not proven agent readiness', p['scope_limits'][0]['detail'])
        self.assertEqual(build_payload('C-001')['audit_id'], p['audit_id'])
        self.assertEqual(len(p['observations']), 3)

    def test_schemas_reject_unknown_and_wrong_types(self):
        p = build_payload('C-008')
        p['extra'] = True
        with self.assertRaises(ValidationError): validate(p, INPUT_SCHEMA)
        p = build_payload('C-008')
        p['audit_metadata']['highest_priority'] = True
        with self.assertRaises(ValidationError): validate(p, INPUT_SCHEMA)
        for a in ('C-001', 'C-008'):
            validate(mock_assessment(build_payload(a)), OUTPUT_SCHEMA)


class AdapterTests(unittest.TestCase):
    def envelope(self, payload, result=None):
        return {'id': 'resp_mock', 'model': MODEL, 'status': 'completed',
                'output': [{'type': 'message', 'content': [{'type': 'output_text',
                             'text': json.dumps(result or mock_assessment(payload))}]}]}

    def test_valid_mock_both_scenarios_and_request_contract(self):
        for alias in ('C-008', 'C-001'):
            def transport(req, timeout):
                body = json.loads(req.data)
                self.assertEqual(body['model'], 'gpt-6-astra')
                self.assertEqual(body['reasoning']['effort'], 'medium')
                self.assertEqual(body['text']['format']['schema'], OUTPUT_SCHEMA)
                self.assertTrue(body['text']['format']['strict'])
                self.assertFalse(body['store'])
                self.assertNotIn('tools', body)
                self.assertLessEqual(timeout, 60)
                return self.envelope(json.loads(body['input']))
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-secret-sentinel', 'ASTRA_REASONING_EFFORT': 'medium'}):
                result = assess(alias, AstraAdapter(transport))
            self.assertEqual(result['status'], 'available')
            self.assertIsNone(result['assessment']['overall_readiness_score'])
            self.assertTrue(all(v is None for v in result['assessment']['dimension_scores'].values()))

    def test_missing_key(self):
        with patch.dict(os.environ, {}, clear=True):
            r = assess('C-008')
        self.assertEqual(r['error_code'], 'missing_key')
        self.assertEqual(len(r['evidence']['findings']), 3)
        self.assertIsNone(r['assessment'])

    def test_transport_and_secret_safe_errors(self):
        for error in [TimeoutError('test-secret-sentinel'), RuntimeError('test-secret-sentinel'),
                      Unavailable('access_denied'), Unavailable('api_error')]:
            def transport(req, timeout): raise error
            logs = io.StringIO()
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-secret-sentinel'}), redirect_stdout(logs), redirect_stderr(logs):
                r = assess('C-008', AstraAdapter(transport))
            self.assertEqual(r['status'], 'unavailable')
            self.assertNotIn('test-secret-sentinel', json.dumps(r))
            self.assertEqual(logs.getvalue(), '')
            self.assertEqual(len(r['evidence']['findings']), 3)

    def test_provider_http_errors_are_sanitized(self):
        for code in (401, 403, 404, 429, 500):
            with patch('readiness.astra.build_opener') as opener:
                opener.return_value.open.side_effect = HTTPError('hidden', code, 'test-secret-sentinel', {}, None)
                with self.assertRaises(Unavailable) as caught:
                    request_json(None)
                self.assertNotIn('test-secret', str(caught.exception))
                self.assertEqual(caught.exception.code, 'access_denied' if code < 405 else 'api_error')

    def test_malformed_partial_refusal_wrong_model_and_secret_echo(self):
        p = build_payload('C-008')
        variants = []
        for text in ('{', '{}', 'test-secret-sentinel'):
            e = self.envelope(p)
            e['output'][0]['content'][0]['text'] = text
            variants.append(e)
        for field, value in (('status', 'incomplete'), ('model', 'other-model')):
            e = self.envelope(p); e[field] = value; variants.append(e)
        e = self.envelope(p); e['output'][0]['content'] = [{'type': 'refusal'}]; variants.append(e)
        for response in variants:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-secret-sentinel'}):
                r = assess('C-008', AstraAdapter(lambda req, timeout: response))
            self.assertEqual(r['status'], 'unavailable')
            self.assertIsNone(r['assessment'])
            self.assertNotIn('test-secret-sentinel', json.dumps(r))

    def test_invalid_evidence_and_human_review(self):
        p = build_payload('C-008')
        cases = []
        r = mock_assessment(p); r['critical_blockers'][0]['evidence_references'] = ['invented']; cases.append(r)
        r = mock_assessment(p); r['critical_blockers'][0]['evidence_references'] = ['scope:integrations']; cases.append(r)
        r = mock_assessment(p); r['critical_blockers'][0]['human_review_required'] = False; cases.append(r)
        r = mock_assessment(p); r['dimension_scores']['knowledge'] = 0; cases.append(r)
        r = mock_assessment(p); r['overall_readiness_score'] = 100; cases.append(r)
        r = mock_assessment(p); r['evidence_gaps'] = []; cases.append(r)
        r = mock_assessment(p); r['critical_blockers'][0].update(basis='direct', statement='An integration is broken.'); cases.append(r)
        r = mock_assessment(p); del r['limitations']; cases.append(r)
        for r in cases:
            with self.assertRaises(ValidationError): validate_assessment(r, p)

    def test_healthy_missing_evidence_is_not_negative_fact(self):
        p = build_payload('C-001')
        r = mock_assessment(p)
        validate_assessment(r, p)
        r['critical_blockers'] = [copy.deepcopy(r['recommended_next_actions'][0])]
        with self.assertRaises(ValidationError): validate_assessment(r, p)

    def test_reasoning_config_and_access_probe(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-secret-sentinel', 'ASTRA_REASONING_EFFORT': 'max'}):
            self.assertEqual(assess('C-008')['error_code'], 'invalid_configuration')
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-secret-sentinel'}):
            self.assertTrue(AstraAdapter(lambda req, timeout: {'id': MODEL}).check_access())

    def test_credit_error_and_redirect_never_expose_secret(self):
        error = HTTPError('hidden', 429, 'test-secret-sentinel', {},
                          io.BytesIO(b'{"error":{"code":"credit_balance_exhausted","message":"test-secret-sentinel"}}'))
        with patch('readiness.astra.build_opener') as opener:
            opener.return_value.open.side_effect = error
            with self.assertRaises(Unavailable) as caught: request_json(None)
            self.assertEqual(caught.exception.code, 'credit_balance_exhausted')
            self.assertNotIn('test-secret-sentinel', str(caught.exception))
        with self.assertRaises(Unavailable):
            NoRedirect().redirect_request(None, None, 302, '', {}, 'https://untrusted.example')

    def test_unknown_fields_numeric_bounds_and_partial_result(self):
        p = build_payload('C-001')
        for score in (-5, 101, True, 91):
            r = mock_assessment(p); r['dimension_scores']['data'] = score
            with self.assertRaises(ValidationError): validate_assessment(r, p)
        r = mock_assessment(p); r['unexpected'] = 'new claim'
        with self.assertRaises(ValidationError): validate_assessment(r, p)
        r = mock_assessment(p); r['dimension_assessments']['knowledge']['basis'] = 'assumption'
        with self.assertRaises(ValidationError): validate_assessment(r, p)


if __name__ == '__main__': unittest.main()
