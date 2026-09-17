"""Offline generation/validator alignment; no provider request is made."""
import copy
import json
import os
import unittest
from unittest.mock import patch

from readiness import support_policy
from readiness.astra import AstraAdapter, PROMPT
from readiness.contracts import DIMENSIONS, SECTIONS, OUTPUT_SCHEMA
from readiness.evidence import build_payload, reference_map
from readiness.generation import build_generation_contract, generation_instructions
from readiness.validation import validate_assessment


def assessment(contract, payload):
    dimensions = {d: next(o['claim'] for o in contract['locations']['dimension:' + d]
                         if not o['numeric_data_scores']) for d in DIMENSIONS}
    return {'overall_readiness_score': None, 'dimension_scores': {d: None for d in DIMENSIONS},
            'dimension_assessments': copy.deepcopy(dimensions), **{s: [] for s in SECTIONS},
            'evidence_references': list(reference_map(payload)),
            'evidence_gaps': contract['allowed_evidence_gaps'],
            'confidence': 'low', 'limitations': contract['allowed_limitations']}


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payloads = {a: build_payload(a) for a in ('C-008', 'C-001')}
        cls.contracts = {a: build_generation_contract(p) for a, p in cls.payloads.items()}

    def test_catalog_is_the_single_source_of_reviewed_pairs(self):
        catalog = copy.deepcopy(support_policy.CATALOG)
        entry = next(c for c in catalog['claims'] if c['class'] == 'findings_review')
        entry['statement'] = 'Catalog mutation sentinel.'
        entry['rationale'] = 'Catalog rationale sentinel.'
        with patch.object(support_policy, 'CATALOG', catalog):
            contract = build_generation_contract(self.payloads['C-008'])
        option = contract['locations']['viable_agent_opportunities'][0]
        self.assertEqual(option['claim']['statement'], entry['statement'])
        self.assertEqual(option['claim']['rationale'], entry['rationale'])

    def test_only_relevant_classes_are_exposed(self):
        def classes(alias):
            return {o['class'] for options in self.contracts[alias]['locations'].values() for o in options}
        self.assertTrue({'data_risk', 'findings_review', 'activity_no_autonomy'} <= classes('C-008'))
        self.assertFalse({'data_unscored', 'observations_review', 'observations_verify'} & classes('C-008'))
        self.assertTrue({'data_unscored', 'observations_review'} <= classes('C-001'))
        self.assertFalse({'data_risk', 'findings_review', 'name_cleanup', 'activity_no_autonomy',
                          'owner_first', 'activity_second', 'name_third'} & classes('C-001'))

    def test_c001_never_receives_numeric_score_permission(self):
        for options in self.contracts['C-001']['locations'].values():
            self.assertTrue(all(o['numeric_data_scores'] == [] for o in options))
        self.assertIsNone(self.contracts['C-001']['overall_readiness_score'])

    def test_direct_claims_quote_only_concrete_evidence(self):
        for alias, payload in self.payloads.items():
            refs = reference_map(payload)
            direct = [o for o in self.contracts[alias]['locations']['recommended_next_actions']
                      if o['claim']['basis'] == 'direct']
            self.assertEqual(len(direct), len(payload['findings']) + len(payload['observations']))
            for option in direct:
                c = option['claim']
                self.assertEqual(c['statement'], refs[c['evidence_references'][0]])
                self.assertEqual(c['rationale'], support_policy.DIRECT_RATIONALE)
                self.assertFalse(c['evidence_references'][0].startswith('scope:'))

    def test_inference_disappears_when_required_evidence_is_removed(self):
        payload = copy.deepcopy(self.payloads['C-008'])
        payload['findings'] = [f for f in payload['findings'] if f['finding_type'] != 'weak_activity']
        contract = build_generation_contract(payload)
        kinds = {o['class'] for items in contract['locations'].values() for o in items}
        self.assertFalse({'data_risk', 'activity_no_autonomy', 'findings_review'} & kinds)

    def test_unsupported_catalog_class_is_not_exposed(self):
        catalog = copy.deepcopy(support_policy.CATALOG)
        catalog['claims'].append({'class': 'invented_permission', 'statement': 'Permission granted.',
                                  'rationale': 'Unsupported.', 'basis': 'inference'})
        with patch.object(support_policy, 'CATALOG', catalog):
            text = generation_instructions(self.payloads['C-008'])
        self.assertNotIn('Permission granted.', text)
        self.assertNotIn('invented_permission', text)

    def test_gaps_authority_and_compactness(self):
        for alias, contract in self.contracts.items():
            self.assertEqual({g['dimension'] for g in contract['allowed_evidence_gaps']}, set(DIMENSIONS))
            self.assertTrue(contract['human_review_required'])
            instructions = generation_instructions(self.payloads[alias])
            self.assertIn('Do not paraphrase', instructions)
            self.assertIn('human review is always required', instructions)
            self.assertIn('strict validator remains authoritative', instructions)
            self.assertLess(len(instructions), 16000)

    def test_every_advertised_option_and_score_passes_production_validation(self):
        for alias, contract in self.contracts.items():
            payload = self.payloads[alias]
            validate_assessment(assessment(contract, payload), payload)
            for location, options in contract['locations'].items():
                for option in options:
                    for score in option['numeric_data_scores'] or [None]:
                        with self.subTest(alias=alias, location=location, kind=option['class'], score=score):
                            result = assessment(contract, payload)
                            c = copy.deepcopy(option['claim'])
                            self.assertTrue(c['human_review_required'])
                            self.assertEqual(len(option['required_evidence_types']), len(c['evidence_references']))
                            if location.startswith('dimension:'):
                                d = location.split(':')[1]
                                result['dimension_scores'][d] = score
                                if score is not None:
                                    c['statement'] = c['statement'].replace('40/100', str(score) + '/100')
                                result['dimension_assessments'][d] = c
                            else:
                                result[location] = [c]
                            validate_assessment(result, payload)

    def test_adapter_sends_guidance_with_unchanged_evidence_and_schema(self):
        for alias, payload in self.payloads.items():
            result = assessment(self.contracts[alias], payload)
            def transport(request, timeout):
                body = json.loads(request.data)
                self.assertEqual(body['instructions'], PROMPT + '\n\n' + generation_instructions(payload))
                self.assertEqual(json.loads(body['input']), payload)
                self.assertEqual(body['text']['format']['schema'], OUTPUT_SCHEMA)
                self.assertEqual(body['model'], 'gpt-6-astra')
                self.assertEqual(body['reasoning'], {'effort': 'medium'})
                return {'status': 'completed', 'model': 'gpt-6-astra', 'id': 'resp_offline',
                        'output': [{'type': 'message', 'content': [{'type': 'output_text',
                                                                  'text': json.dumps(result)}]}]}
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-secret-sentinel',
                                         'ASTRA_REASONING_EFFORT': 'medium'}), \
                    patch('readiness.astra.build_opener', side_effect=AssertionError('Live network forbidden')):
                actual, _ = AstraAdapter(transport).assess(payload)
            self.assertEqual(actual, result)
