"""Closed-language MVP support policy, not natural-language entailment.

Every model-authored display string must match reviewed wording AND satisfy an
evidence-type/placement predicate. Unknown paraphrases fail closed. The catalog
is application policy, never loaded from demo artifacts or provider output.
No rule grants consent, write access, execution or autonomous deployment.
"""
import json
from pathlib import Path
from .contracts import ValidationError
from .evidence import reference_map

CATALOG = json.loads(Path(__file__).with_name('support_catalog.json').read_text())
FINDINGS = frozenset(('malformed_name', 'missing_owner', 'weak_activity'))
SCOPES = frozenset(('process', 'knowledge', 'governance', 'integrations'))
DIRECT_RATIONALE = 'This is supplied deterministic evidence; human review remains required.'
BOUNDED_RATIONALE = 'Limited to the supplied check and human review.'

# Legacy legitimate test wording is independently reviewed, not a bypass.
EXTRA_CLAIMS = (
    ('name_observation_review', 'inference',
     'A human-supervised read-only review could inspect supplied evidence.', BOUNDED_RATIONALE),
    ('owner_risk', 'inference', 'Missing ownership can make autonomous routing unreliable.', BOUNDED_RATIONALE),
    ('owner_verify', 'inference', 'Verify intended ownership before assigning.', BOUNDED_RATIONALE),
    ('governance_acquire', 'evidence_gap', 'Collect governance evidence before autonomous use.', BOUNDED_RATIONALE),
)


class SupportPolicy:
    def __init__(self, payload):
        self.payload = payload
        self.refs = reference_map(payload)
        self.findings = {f['finding_id']: f for f in payload['findings']}
        self.observations = {o['evidence_id']: o for o in payload['observations']}
        self.scopes = {g['evidence_id']: g['dimension'] for g in payload['scope_limits']}

    def supports(self, kind, cited, location):
        found = {self.findings[r]['finding_type'] for r in cited if r in self.findings}
        observed = {r.rsplit(':', 1)[-1] for r in cited if r in self.observations}
        scopes = {self.scopes[r] for r in cited if r in self.scopes}
        three = found == FINDINGS and len(self.payload['findings']) == 3
        clean = not self.payload['findings']
        # Positive observations establish only their explicitly bounded checks.
        checks = {r.rsplit(':', 1)[-1]: o['detail'] for r, o in self.observations.items() if r in cited}
        clean_checks = clean and observed == {'name', 'owner', 'activity'} and (
            checks.get('owner') == 'Owner field is present; correctness of assignment is unverified.' and
            checks.get('name') == 'No name-format defects detected by the implemented checks; identity is unverified.' and
            checks.get('activity', '').startswith('Latest approved activity signal is '))
        if kind.startswith('gap_'):
            dimension = kind[4:]
            return location == 'dimension:' + dimension and dimension in scopes
        if kind == 'data_risk':
            return location == 'dimension:data' and three and 'data' in scopes
        if kind == 'data_unscored':
            return location == 'dimension:data' and clean_checks and 'data' in scopes
        if kind in ('findings_review', 'findings_verify'):
            section = 'viable_agent_opportunities' if kind == 'findings_review' else 'recommended_next_actions'
            return location == section and three
        if kind in ('observations_review', 'observations_verify'):
            section = 'viable_agent_opportunities' if kind == 'observations_review' else 'recommended_next_actions'
            return location == section and clean_checks and 'data' in scopes
        if kind == 'name_cleanup':
            # Reviewed wording mentions these defects, so all must be detected.
            details = [self.findings[r]['evidence']['detail'] for r in cited
                       if r in self.findings and self.findings[r]['finding_type'] == 'malformed_name']
            return location == 'conditional_agent_opportunities' and any(
                all(term in detail for term in ('whitespace', 'ALL CAPS', 'digits')) for detail in details)
        if kind == 'activity_no_autonomy':
            return location == 'not_ready_agent_opportunities' and 'weak_activity' in found
        if kind in ('owner_first', 'activity_second', 'name_third'):
            # These reviewed phrases assert exact priorities/order: verify them.
            priority = {f['finding_type']: f['priority'] for f in self.payload['findings']}
            expected = {'missing_owner': 40, 'weak_activity': 35, 'malformed_name': 20}
            required = {'owner_first': 'missing_owner', 'activity_second': 'weak_activity',
                        'name_third': 'malformed_name'}[kind]
            return location == 'remediation_priorities' and priority == expected and required in found
        if kind == 'acquire_scope':
            return location == 'recommended_next_actions' and SCOPES <= scopes
        if kind == 'name_observation_review':
            return location == 'viable_agent_opportunities' and 'name' in observed
        if kind == 'owner_risk':
            return location == 'critical_blockers' and 'missing_owner' in found
        if kind == 'owner_verify':
            return location == 'remediation_priorities' and 'missing_owner' in found
        if kind == 'governance_acquire':
            return location == 'recommended_next_actions' and 'governance' in scopes
        return False

    def claim(self, claim, location, score=None):
        cited = claim['evidence_references']
        # Both fields matter: a correct quote cannot launder an invented rationale.
        if claim['basis'] == 'direct':
            concrete = [self.refs[r] for r in cited if r in self.findings or r in self.observations]
            if claim['statement'] in concrete and claim['rationale'] == DIRECT_RATIONALE:
                return 'direct'
            raise ValidationError('Unsupported direct statement or rationale')
        if location.startswith('dimension:') and claim['basis'] == 'evidence_gap':
            dimension = location.split(':')[1]
            scope = 'scope:' + dimension
            if (scope in cited and claim['statement'] == self.refs.get(scope) and
                    claim['rationale'] == BOUNDED_RATIONALE):
                return 'gap_' + dimension
        entries = [(e['class'], e['basis'], e['statement'], e['rationale']) for e in CATALOG['claims']]
        for kind, basis, statement, rationale in entries + list(EXTRA_CLAIMS):
            if kind == 'data_risk' and score is not None:
                statement = statement.replace('40/100', str(score) + '/100')
            if (claim['basis'], claim['statement'], claim['rationale']) == (basis, statement, rationale):
                if self.supports(kind, cited, location):
                    return kind
        raise ValidationError('Claim is outside the supported evidence policy')

    def gap(self, gap):
        dimension = gap['dimension']
        allowed = CATALOG['gaps'].get(dimension, []) + [self.refs.get('scope:' + dimension)]
        if gap['detail'] not in allowed:
            raise ValidationError('Unsupported evidence gap content')

    def limitations(self, values):
        for value in values:
            if value == 'One synthetic record; no organizational readiness proven.':
                continue
            entry = next((e for e in CATALOG['limitations'] if e['text'] == value), None)
            if entry is None:
                raise ValidationError('Unsupported limitation content')
            if entry['requires'] == 'no_findings' and self.payload['findings']:
                raise ValidationError('No-findings limitation contradicts findings')
            if entry['requires'] == 'weak_activity' and not any(
                    f['finding_type'] == 'weak_activity' for f in self.payload['findings']):
                raise ValidationError('Activity limitation lacks supporting finding')
