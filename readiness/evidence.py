"""Build only synthetic, controlled evidence from the unchanged V1 engine."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from src.adapter import load_dataset
from src.config import Config, parse_datetime
from src.rules import evaluate
from src.scoring import build_queue
from src.recommendations import guidance_for
from .contracts import INPUT_SCHEMA, validate

ROOT = Path(__file__).resolve().parents[1]
ALIASES = ('C-008', 'C-001')
EVALUATION_DATE = '2026-08-20T12:00:00Z'


def build_payload(alias, now=None):
    if alias not in ALIASES:
        raise ValueError('Unsupported demo alias')
    data = load_dataset(ROOT / 'fixtures/health_matrix.json', 'fixture')
    config = Config(evaluation_date=parse_datetime(EVALUATION_DATE))
    evaluation = evaluate(data, config)
    record = next(r for r in data.contacts if r.alias == alias)
    issues = [i for i in evaluation.issues if i.alias == alias]
    priority = next((r.priority for r in build_queue(evaluation, config) if r.alias == alias), 0)
    signals = [t for t in (record.notes_last_updated, record.notes_last_contacted,
                           record.last_sales_activity) if t is not None]
    age = max(0, (config.evaluation_date - max(signals)).days) if signals else None
    observations = [
        {'evidence_id': alias + ':owner', 'detail': 'Owner field is ' +
         ('present; correctness of assignment is unverified.' if record.owner_id else 'absent or blank.')},
        {'evidence_id': alias + ':name', 'detail':
         ('Name-format checks flagged defects.' if any(i.issue_type == 'malformed_name' for i in issues)
          else 'No name-format defects detected by the implemented checks; identity is unverified.')},
        {'evidence_id': alias + ':activity', 'detail':
         ('No approved contact activity signal exists in this snapshot.' if age is None else
          f'Latest approved activity signal is {age} days old at evaluation; threshold is 90 days.')},
    ]
    payload = {
        'audit_id': '', 'record': {'alias': alias, 'entity_type': 'contact'},
        'findings': [{'finding_id': alias + ':' + i.issue_type, 'finding_type': i.issue_type,
                      'severity_points': i.severity_points, 'priority': i.severity_points + i.age_bonus,
                      'evidence': {'detail': i.explanation},
                      'deterministic_impact': guidance_for(i.issue_type).impact,
                      'human_review_required': True} for i in issues],
        'observations': observations,
        'scope_limits': [{'evidence_id': 'scope:' + d, 'dimension': d, 'detail': detail} for d, detail in (
            ('data', 'Only owner presence, name formatting and approved activity recency are checked for one synthetic record. No findings is not proven agent readiness.'),
            ('process', 'No business process, lifecycle, routing rules or qualification criteria were supplied.'),
            ('knowledge', 'No knowledge-base, support policy or answer-quality evidence was supplied.'),
            ('governance', 'No consent, permissions, oversight policy or owner-assignment correctness was supplied.'),
            ('integrations', 'No integration configuration, synchronization health or delivery evidence was supplied.'),
        )],
        'audit_metadata': {'finding_count': len(issues), 'highest_priority': priority,
                           'source': 'fixture', 'evaluation_date': config.evaluation_date.isoformat(),
                           'generated_at': ''},
    }
    payload['audit_id'] = 'audit-' + hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]
    payload['audit_metadata']['generated_at'] = (now or datetime.now(timezone.utc)).isoformat()
    validate(payload, INPUT_SCHEMA)
    return payload


def reference_map(payload):
    return {**{f['finding_id']: f['evidence']['detail'] for f in payload['findings']},
            **{o['evidence_id']: o['detail'] for o in payload['observations']},
            **{g['evidence_id']: g['detail'] for g in payload['scope_limits']}}
