"""Strict JSON Schemas and a validator for exactly the subset used here."""
import math

DIMENSIONS = ('data', 'process', 'knowledge', 'governance', 'integrations')
SECTIONS = ('critical_blockers', 'viable_agent_opportunities',
            'conditional_agent_opportunities', 'not_ready_agent_opportunities',
            'remediation_priorities', 'recommended_next_actions')


def obj(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties),
            'additionalProperties': False}


def string(maximum=800):
    return {'type': 'string', 'minLength': 1, 'maxLength': maximum}


def array(items, maximum=8, minimum=0):
    return {'type': 'array', 'items': items, 'maxItems': maximum, 'minItems': minimum}


SCORE = {'type': ['integer', 'null'], 'minimum': 0, 'maximum': 100}
REFS = array(string(100), 12, 1)
CLAIM = obj({'statement': string(), 'basis': {'type': 'string', 'enum':
             ['direct', 'inference', 'assumption', 'evidence_gap']},
             'rationale': string(), 'evidence_references': REFS,
             'human_review_required': {'type': 'boolean', 'enum': [True]}})
OUTPUT_SCHEMA = obj({
    'overall_readiness_score': SCORE,
    'dimension_scores': obj({d: SCORE for d in DIMENSIONS}),
    'dimension_assessments': obj({d: CLAIM for d in DIMENSIONS}),
    **{s: array(CLAIM, 5) for s in SECTIONS},
    'evidence_references': REFS,
    'evidence_gaps': array(obj({'dimension': {'type': 'string', 'enum': list(DIMENSIONS)},
                              'detail': string(), 'evidence_references': REFS}), 8, 1),
    'confidence': {'type': 'string', 'enum': ['low', 'moderate']},
    'limitations': array(string(), 6, 1),
})
INPUT_SCHEMA = obj({
    'audit_id': string(100),
    'record': obj({'alias': {'type': 'string', 'enum': ['C-008', 'C-001']},
                   'entity_type': {'type': 'string', 'enum': ['contact']}}),
    'findings': array(obj({'finding_id': string(100), 'finding_type': string(80),
                          'severity_points': {'type': 'integer', 'minimum': 0, 'maximum': 100},
                          'priority': {'type': 'integer', 'minimum': 0, 'maximum': 100},
                          'evidence': obj({'detail': string()}),
                          'deterministic_impact': string(),
                          'human_review_required': {'type': 'boolean', 'enum': [True]}}), 10),
    'observations': array(obj({'evidence_id': string(100), 'detail': string()}), 8, 1),
    'scope_limits': array(obj({'evidence_id': string(100), 'dimension': string(30),
                              'detail': string()}), 8, 1),
    'audit_metadata': obj({'finding_count': {'type': 'integer', 'minimum': 0, 'maximum': 10},
                           'highest_priority': {'type': 'integer', 'minimum': 0, 'maximum': 100},
                           'source': {'type': 'string', 'enum': ['fixture']},
                           'evaluation_date': string(40), 'generated_at': string(40)}),
})


class ValidationError(ValueError):
    """Intentionally never contains model text, secrets, or rejected values."""


def validate(value, schema):
    kinds = schema['type']
    kinds = kinds if isinstance(kinds, list) else [kinds]
    checks = {'object': lambda v: type(v) is dict, 'array': lambda v: type(v) is list,
              'string': lambda v: type(v) is str, 'integer': lambda v: type(v) is int,
              'boolean': lambda v: type(v) is bool, 'null': lambda v: v is None}
    if not any(checks[k](value) for k in kinds):
        raise ValidationError('Invalid field type')
    if 'enum' in schema and not any(type(value) is type(x) and value == x for x in schema['enum']):
        raise ValidationError('Invalid enum')
    if value is None:
        return
    if type(value) is dict:
        if set(value) != set(schema['required']):
            raise ValidationError('Missing or unexpected fields')
        for key, child in value.items():
            validate(child, schema['properties'][key])
    elif type(value) is list:
        if not schema.get('minItems', 0) <= len(value) <= schema['maxItems']:
            raise ValidationError('Invalid list length')
        for child in value:
            validate(child, schema['items'])
    elif type(value) is str:
        if not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', 800):
            raise ValidationError('Invalid text length')
    elif type(value) is int:
        if not math.isfinite(value) or not schema['minimum'] <= value <= schema['maximum']:
            raise ValidationError('Invalid number')
