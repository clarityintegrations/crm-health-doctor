"""Self-contained, escaped HTML report renderer."""

from collections import Counter
from html import escape
from pathlib import Path
from typing import Union

from .adapter import Dataset
from .config import Config
from .rules import Evaluation
from .scoring import QueueRow, Scorecard


LABELS = {
    "missing_owner": "Missing owner",
    "stale_open_deals": "Stale open deals",
    "name_quality": "Name quality",
    "contact_activity": "Contact activity",
    "weak_activity": "Weak activity",
    "stale_activity": "Stale activity",
    "stale_open_deal": "Stale open deal",
    "unknown_deal_activity": "Unknown deal activity",
    "malformed_name": "Malformed name",
}


def _label(value: str) -> str:
    return LABELS.get(value, value.replace("_", " ").title())


def render_html(
    dataset: Dataset,
    config: Config,
    evaluation: Evaluation,
    scorecard: Scorecard,
    queue: tuple[QueueRow, ...],
) -> str:
    counts = Counter(issue.issue_type for issue in evaluation.issues)
    count_cards = "".join(
        f'<div class="card"><span>{escape(_label(kind))}</span><strong>{count}</strong></div>'
        for kind, count in sorted(counts.items())
    ) or '<div class="card"><span>Issues</span><strong>0</strong></div>'

    category_rows = "".join(
        "<tr>"
        f"<td>{escape(_label(item.category))}</td>"
        f"<td>{item.flagged}</td><td>{item.applicable}</td>"
        f"<td>{'Excluded' if item.score is None else f'{item.score:.1f}'}</td>"
        f"<td>{item.normalized_weight * 100:.1f}%</td>"
        "</tr>"
        for item in scorecard.categories
    )

    queue_rows = "".join(
        "<tr>"
        f'<td><span class="priority">{row.priority}</span></td>'
        f"<td>{escape(row.alias)}</td>"
        f"<td>{escape(row.object_type.title())}</td>"
        f"<td>{escape(row.display_name)}</td>"
        "<td>" + "".join(
            f'<div class="issue"><b>{escape(_label(issue.issue_type))}:</b> '
            f"{escape(issue.explanation)}</div>" for issue in row.issues
        ) + "</td></tr>"
        for row in queue
    ) or '<tr><td colspan="5">No records require review.</td></tr>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CRM Health Doctor</title>
<style>
:root{{--ink:#17213a;--muted:#64748b;--line:#dbe4ef;--surface:#fff;--bg:#f3f7fb;--blue:#2563eb;--teal:#0f766e}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,sans-serif}}
main{{max-width:1120px;margin:auto;padding:42px 24px 64px}} header{{display:flex;justify-content:space-between;gap:30px;align-items:end;margin-bottom:28px}}
h1{{font-size:34px;letter-spacing:-.04em;margin:0}} h2{{font-size:20px;margin:34px 0 14px}} p{{color:var(--muted)}}
.badge{{background:#dbeafe;color:#1d4ed8;border-radius:999px;padding:7px 12px;font-weight:700;text-transform:uppercase;font-size:11px;letter-spacing:.08em}}
.hero{{display:grid;grid-template-columns:220px 1fr;gap:20px}} .score{{background:linear-gradient(145deg,#172554,#2563eb);color:#fff;border-radius:18px;padding:28px}}
.score strong{{display:block;font-size:64px;line-height:1}} .score span{{opacity:.8}}
.cards{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}} .card{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:17px}}
.card span{{display:block;color:var(--muted);font-size:12px}} .card strong{{font-size:28px}}
.panel{{background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden}} table{{border-collapse:collapse;width:100%}} th,td{{padding:13px 14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} th{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);background:#f8fafc}} tr:last-child td{{border-bottom:0}}
.priority{{display:inline-grid;place-items:center;width:38px;height:38px;border-radius:10px;background:#fee2e2;color:#991b1b;font-weight:800}} .issue+ .issue{{margin-top:7px}}
.method{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}} .method article{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px}} .method h3{{margin:0 0 6px;font-size:15px}}
footer{{margin-top:30px;color:var(--muted);font-size:12px}} @media(max-width:760px){{.hero,.method{{grid-template-columns:1fr}}.cards{{grid-template-columns:1fr 1fr}}header{{display:block}}.panel{{overflow:auto}}}}
</style>
</head>
<body><main>
<header><div><h1>CRM Health Doctor</h1><p>Deterministic CRM quality assessment with a governed read-only data boundary.</p></div><span class="badge">Source: {escape(dataset.source)}</span></header>
<section class="hero"><div class="score"><span>Overall health</span><strong>{scorecard.overall_score:.1f}</strong><span>out of 100</span></div><div class="cards">{count_cards}</div></section>
<h2>Category score audit</h2><div class="panel"><table><thead><tr><th>Category</th><th>Flagged</th><th>Applicable</th><th>Score</th><th>Normalized weight</th></tr></thead><tbody>{category_rows}</tbody></table></div>
<h2>Top-{config.queue_limit} review queue</h2><div class="panel"><table><thead><tr><th>Priority</th><th>Alias</th><th>Type</th><th>Record</th><th>Why it was flagged</th></tr></thead><tbody>{queue_rows}</tbody></table></div>
<h2>Methodology</h2><section class="method">
<article><h3>Thresholds</h3><p>Open deals are stale after {config.stale_deal_days} days. Contact activity is stale after {config.stale_contact_days} days. Evaluation time: {escape(config.evaluation_date.isoformat())}.</p></article>
<article><h3>Deal timestamp precedence</h3><p>Use the latest of Last Activity Date and Last Contacted. If neither exists, use creation time as an explicitly labeled fallback. If all are absent, return an unknown-activity diagnostic.</p></article>
<article><h3>Scoring</h3><p>Category score = 100 × (1 − flagged ÷ applicable). Empty categories are excluded and remaining weights are renormalized.</p></article>
<article><h3>Prioritization</h3><p>Priority is the sum of explicit issue severity and bounded age bonuses, capped at 100. Ties sort by object type and alias.</p></article>
</section>
<footer>Generated locally. No telemetry, external scripts, CDN assets, or raw HubSpot record IDs.</footer>
</main></body></html>"""


def write_report(path: Union[str, Path], html: str) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")
    return destination
