"""Evidence-filtered generation guidance from the authoritative support policy.

No new admissibility rules: candidate placements and numeric choices are probed
through the existing validator. Wording is copied, never paraphrased here.
"""
import copy
import json
from .contracts import DIMENSIONS, SECTIONS, SCORE, ValidationError
from . import support_policy
from .validation import validate_assessment

GUIDANCE = '''Controlled language contract (authoritative for wording):
Select only the approved claims below, at their listed locations. Copy each claim
object exactly, including statement, rationale, basis, references and true human_review_required.
Do not paraphrase, combine pairs, add explanations or invent any other factual text.
The only allowed wording substitution is the declared numeric Data-score substitution.
Do not emit guidance metadata (class, required_evidence_types, numeric_data_scores).
For each dimension choose one supplied claim. Keep its score null unless that choice
has numeric_data_scores; then choose one listed estimate and replace 40/100 in its
statement with that same integer followed by /100. Do not invent a score formula.
Overall readiness is null. Unsupported dimensions are null, not deficient.
Use only supplied evidence-gap objects and exact limitation strings. Include a gap
for every null dimension. Include limitations explaining bounded scope, uncertainty
and human review. Empty opportunity/blocker/remediation lists are valid; omit
unsupported claims. Choose concise nonredundant items, at most three per section.
The top-level evidence_references must include every reference used in claims or gaps.
No consent, permission, write access, execution or autonomous deployment is granted;
human review is always required. No detected issue does not mean proven readiness.
Return the existing response schema only. The strict validator remains authoritative.
'''


def build_generation_contract(payload):
    policy = support_policy.SupportPolicy(payload)
    refs = list(policy.refs)
    catalog = support_policy.CATALOG

    def claim(statement, rationale, basis, cited):
        return {'statement': statement, 'rationale': rationale, 'basis': basis,
                'evidence_references': cited, 'human_review_required': True}

    dimensions = {d: claim(policy.refs['scope:' + d], support_policy.BOUNDED_RATIONALE,
                            'evidence_gap', ['scope:' + d]) for d in DIMENSIONS}
    gaps = [{'dimension': d, 'detail': catalog['gaps'].get(d, [policy.refs['scope:' + d]])[0],
             'evidence_references': ['scope:' + d]} for d in DIMENSIONS]
    limitations = []
    for entry in catalog['limitations']:
        try: policy.limitations([entry['text']])
        except ValidationError: continue
        limitations.append(entry['text'])
    base = {'overall_readiness_score': None, 'dimension_scores': {d: None for d in DIMENSIONS},
            'dimension_assessments': dimensions, **{s: [] for s in SECTIONS},
            'evidence_references': refs, 'evidence_gaps': gaps, 'confidence': 'low',
            'limitations': limitations}
    validate_assessment(base, payload)
    locations = {'dimension:' + d: [] for d in DIMENSIONS}
    locations.update({s: [] for s in SECTIONS})

    def admissible(c, location, score=None):
        candidate = copy.deepcopy(base)
        if location.startswith('dimension:'):
            d = location.split(':')[1]
            candidate['dimension_assessments'][d] = c
            candidate['dimension_scores'][d] = score
        else: candidate[location] = [c]
        try: validate_assessment(candidate, payload)
        except ValidationError: return False
        return True

    def types(cited):
        return [
            'finding:' + policy.findings[r]['finding_type'] if r in policy.findings else
            'observation:' + r.rsplit(':', 1)[-1] if r in policy.observations else
            'scope:' + policy.scopes[r] for r in cited]

    for location in locations:
        seen = set()
        for entry in catalog['claims']:
            kind = entry['class']
            if kind in seen or not policy.supports(kind, refs, location): continue
            # Deterministically shrink to a sufficient set using policy predicates,
            # not a second manually maintained evidence-type table.
            cited = refs[:]
            for ref in refs:
                smaller = [r for r in cited if r != ref]
                if policy.supports(kind, smaller, location): cited = smaller
            c = claim(entry['statement'], entry['rationale'], entry['basis'], cited)
            scores = []
            if location == 'dimension:data':
                for score in range(SCORE['minimum'], SCORE['maximum'] + 1):
                    scored = dict(c, statement=c['statement'].replace('40/100', str(score) + '/100'))
                    if admissible(scored, location, score): scores.append(score)
            if not scores and not admissible(c, location): continue
            option = {'class': kind, 'claim': c, 'required_evidence_types': types(cited),
                      'numeric_data_scores': scores}
            locations[location].append(option)
            seen.add(kind)  # One reviewed wording variant per class saves tokens.
    for d, c in dimensions.items():
        location = 'dimension:' + d
        if not any(x['claim']['basis'] == 'evidence_gap' for x in locations[location]):
            locations[location].append({'class': 'gap_' + d, 'claim': c,
                'required_evidence_types': ['scope:' + d], 'numeric_data_scores': []})
    # Direct quotes use the policy's existing rationale, not duplicated prompt text.
    for ref in list(policy.findings) + list(policy.observations):
        c = claim(policy.refs[ref], support_policy.DIRECT_RATIONALE, 'direct', [ref])
        if admissible(c, 'recommended_next_actions'):
            locations['recommended_next_actions'].append({'class': 'direct', 'claim': c,
                'required_evidence_types': types([ref]), 'numeric_data_scores': []})
    return {'locations': locations, 'allowed_evidence_gaps': gaps,
            'allowed_limitations': limitations, 'overall_readiness_score': None,
            'human_review_required': True}


def generation_instructions(payload):
    return GUIDANCE + json.dumps(build_generation_contract(payload), ensure_ascii=False,
                                 separators=(',', ':'))
