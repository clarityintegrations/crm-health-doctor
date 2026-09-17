"""Stable safe response envelope for CLI and UI, including deterministic evidence."""
from datetime import datetime, timezone
import time
from .astra import AstraAdapter, Unavailable
from .evidence import build_payload


def assess(alias, adapter=None):
    payload = build_payload(alias)
    start = time.monotonic()
    base = {'evidence': payload, 'assessment': None, 'status': 'unavailable',
            'message': 'AI readiness assessment unavailable. Deterministic findings remain available.',
            'error_code': None, 'provenance': None}
    try:
        result, provenance = (adapter or AstraAdapter()).assess(payload)
        base.update(status='available', assessment=result, message='Model assessment requires human review.',
                    provenance={**provenance, 'completed_at': datetime.now(timezone.utc).isoformat(),
                                'duration_seconds': round(time.monotonic() - start, 2),
                                'audit_id': payload['audit_id']})
    except Unavailable as error:
        base['error_code'] = error.code
    except Exception:
        base['error_code'] = 'assessment_error'
    return base
