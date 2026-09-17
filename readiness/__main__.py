"""Run without a key for deterministic evidence and a safe unavailable result."""
import argparse
import json
from pathlib import Path
from .astra import AstraAdapter, Unavailable
from .contracts import INPUT_SCHEMA, OUTPUT_SCHEMA
from .service import assess
from .server import serve


def main():
    parser = argparse.ArgumentParser(description='Synthetic Agent Readiness Edition')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('assess'); p.add_argument('alias', choices=('C-008', 'C-001'))
    p.add_argument('--output', type=Path, help='Explicitly save the sanitized response envelope')
    p = sub.add_parser('serve'); p.add_argument('--port', type=int, default=8766)
    sub.add_parser('check-access')
    p = sub.add_parser('schema'); p.add_argument('kind', choices=('input', 'output'))
    args = parser.parse_args()
    if args.command == 'serve': serve(args.port); return 0
    if args.command == 'schema':
        print(json.dumps(INPUT_SCHEMA if args.kind == 'input' else OUTPUT_SCHEMA, indent=2)); return 0
    if args.command == 'check-access':
        try: AstraAdapter().check_access(); print('gpt-6-astra model access confirmed'); return 0
        except Unavailable as e: print('Model access unavailable: ' + e.code); return 1
    result = assess(args.alias)
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(text + '\n', encoding='utf-8')
        print('Sanitized assessment saved; status=' + result['status'])
    else: print(text)
    return 0 if result['status'] == 'available' else 1


if __name__ == '__main__': raise SystemExit(main())
