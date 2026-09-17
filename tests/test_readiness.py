import copy
import json
import os
import unittest
from unittest.mock import patch

from readiness.contracts import INPUT_SCHEMA, OUTPUT_SCHEMA, DIMENSIONS, SECTIONS, validate, ValidationError
from readiness.evidence import build_payload, reference_map


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


if __name__ == '__main__':
    unittest.main()
