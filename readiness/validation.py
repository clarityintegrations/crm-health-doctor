"""Structural and traceability checks; semantic claims still need human review."""
from .contracts import OUTPUT_SCHEMA, DIMENSIONS, SECTIONS, ValidationError, validate
from .evidence import reference_map


def validate_assessment(result, payload):
    validate(result, OUTPUT_SCHEMA)
    refs = reference_map(payload)
    used = set()
    def references(items):
        if len(set(items)) != len(items) or not set(items) <= refs.keys():
            raise ValidationError('Unknown or duplicate evidence reference')
        used.update(items)
    def claim(c):
        references(c['evidence_references'])
        if c['basis'] == 'direct' and c['statement'] not in [refs[r] for r in c['evidence_references']]:
            raise ValidationError('Direct claim must quote supplied evidence')
        if c['basis'] == 'inference' and all(r.startswith('scope:') for r in c['evidence_references']):
            raise ValidationError('Scope absence cannot support a factual inference')
    for d in DIMENSIONS:
        c = result['dimension_assessments'][d]
        claim(c)
        score = result['dimension_scores'][d]
        if d != 'data' and score is not None:
            raise ValidationError('Unsupported dimension score')
        if score is not None:
            if score % 5 or c['basis'] not in ('direct', 'inference'):
                raise ValidationError('Score must be a coarse evidence-based estimate')
        if d != 'data' and c['basis'] != 'evidence_gap':
            raise ValidationError('Unsupported dimension must be an evidence gap')
    if result['overall_readiness_score'] is not None:
        raise ValidationError('Overall readiness is unknown for this limited evidence')
    for section in SECTIONS:
        for c in result[section]:
            claim(c)
            if section in ('critical_blockers', 'not_ready_agent_opportunities'):
                finding_ids = {f['finding_id'] for f in payload['findings']}
                if c['basis'] not in ('direct', 'inference') or not finding_ids.intersection(c['evidence_references']):
                    raise ValidationError('Negative conclusion requires a detected finding')
            if section == 'viable_agent_opportunities' and c['basis'] != 'inference':
                raise ValidationError('Viability is a scoped inference, not a proven fact')
    gap_dimensions = set()
    for gap in result['evidence_gaps']:
        references(gap['evidence_references'])
        if 'scope:' + gap['dimension'] not in gap['evidence_references']:
            raise ValidationError('Gap must reference its dimension scope')
        gap_dimensions.add(gap['dimension'])
    if not {d for d in DIMENSIONS if result['dimension_scores'][d] is None} <= gap_dimensions:
        raise ValidationError('Unknown dimension requires an evidence gap')
    references(result['evidence_references'])
    if not used <= set(result['evidence_references']):
        raise ValidationError('Reference index is incomplete')
    return result
