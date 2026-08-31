import argparse

from .adapter import load_dataset
from .config import Config, parse_datetime
from .report import render_html, write_report
from .rules import evaluate
from .scoring import build_queue, calculate_score


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic CRM health report")
    parser.add_argument("--source", choices=("fixture", "hubspot"), required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--evaluation-date", required=True)
    parser.add_argument("--stale-deal-days", type=int, default=30)
    parser.add_argument("--stale-contact-days", type=int, default=90)
    return parser


def run(args: argparse.Namespace) -> dict[str, object]:
    dataset = load_dataset(args.input, args.source)
    config = Config(
        evaluation_date=parse_datetime(args.evaluation_date),
        stale_deal_days=args.stale_deal_days,
        stale_contact_days=args.stale_contact_days,
    )
    evaluation = evaluate(dataset, config)
    scorecard = calculate_score(evaluation)
    queue = build_queue(evaluation, config)
    write_report(args.output, render_html(dataset, config, evaluation, scorecard, queue))
    return {
        "source": dataset.source,
        "contacts": len(dataset.contacts),
        "deals": len(dataset.deals),
        "issues": len(evaluation.issues),
        "queue_rows": len(queue),
        "overall_score": scorecard.overall_score,
        "output": args.output,
    }


def main() -> None:
    summary = run(build_parser().parse_args())
    print(" | ".join(f"{key}={value}" for key, value in summary.items()))


if __name__ == "__main__":
    main()
