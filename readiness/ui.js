(() => {
  const el = id => document.getElementById(id);
  const add = (parent, tag, text) => {
    const child = document.createElement(tag);
    child.textContent = text;
    parent.appendChild(child);
    return child;
  };
  function showEvidence(p) {
    el('evidence').replaceChildren();
    add(el('evidence'), 'p', `${p.record.alias} · ${p.audit_metadata.finding_count} findings · priority ${p.audit_metadata.highest_priority}`);
    if (!p.findings.length) add(el('evidence'), 'p', 'No detected issues under the implemented checks. This does not prove agent readiness.');
    const list = add(el('evidence'), 'ul', '');
    for (const f of p.findings) add(list, 'li', `${f.finding_type}: ${f.evidence.detail} [${f.finding_id}]`);
    for (const o of p.observations) add(el('evidence'), 'small', `${o.detail} [${o.evidence_id}]`);
  }
  function showAssessment(a, provenance) {
    const root = el('assessment');
    root.replaceChildren();
    const summary = add(root, 'section', '');
    add(summary, 'h2', `Agent Readiness Assessment · ${a.overall_readiness_score ?? 'Unknown overall readiness'}`);
    add(summary, 'p', `Confidence: ${a.confidence}. Human review required. Scores, when present, are model estimates limited to supplied checks.`);
    add(summary, 'small', `${provenance.model} · ${provenance.duration_seconds}s · ${provenance.completed_at}`);
    const table = add(summary, 'table', '');
    for (const [dimension, score] of Object.entries(a.dimension_scores)) {
      const row = add(table, 'tr', '');
      add(row, 'th', dimension);
      add(row, 'td', score === null ? 'Unknown — insufficient evidence' : `${score}/100 (estimate)`);
      const c = a.dimension_assessments[dimension];
      add(row, 'td', `${c.statement} [${c.basis}; ${c.evidence_references.join(', ')}]`);
    }
    for (const name of ['critical_blockers', 'viable_agent_opportunities', 'conditional_agent_opportunities', 'not_ready_agent_opportunities', 'remediation_priorities', 'recommended_next_actions']) {
      const section = add(root, 'section', '');
      add(section, 'h2', name.replaceAll('_', ' '));
      if (!a[name].length) add(section, 'p', 'None established from the supplied evidence.');
      const list = add(section, 'ul', '');
      for (const c of a[name]) {
        const item = add(list, 'li', c.statement);
        add(item, 'small', `${c.basis}: ${c.rationale}`);
        add(item, 'small', `Evidence: ${c.evidence_references.join(', ')} · human review required`);
      }
    }
    const gaps = add(root, 'section', '');
    add(gaps, 'h2', 'Evidence gaps and limitations');
    for (const g of a.evidence_gaps) add(gaps, 'p', `${g.dimension}: ${g.detail} [${g.evidence_references.join(', ')}]`);
    for (const l of a.limitations) add(gaps, 'p', l);
  }
  async function load() {
    el('assessment').replaceChildren();
    el('evidence').replaceChildren();
    el('assess').disabled = true;
    const selected = el('alias').value;
    try {
      const response = await fetch(`/evidence?alias=${encodeURIComponent(selected)}`);
      if (!response.ok) throw new Error('Unavailable');
      const p = await response.json();
      if (selected !== el('alias').value) return;
      showEvidence(p);
      el('status').textContent = 'Deterministic evidence ready. Select Assess to request model reasoning.';
      el('assess').disabled = false;
    } catch {
      el('status').textContent = 'Could not load evidence. The unchanged V1 report remains available.';
    }
  }
  el('alias').addEventListener('change', load);
  el('assess').addEventListener('click', async () => {
    el('assessment').replaceChildren();
    el('assess').disabled = true;
    el('alias').disabled = true;
    el('status').textContent = 'GPT-6 Astra is assessing the supplied evidence…';
    try {
      const response = await fetch('/assess', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({alias: el('alias').value})});
      if (!response.ok) throw new Error('Unavailable');
      const result = await response.json();
      showEvidence(result.evidence);
      el('status').textContent = result.message;
      if (result.status === 'available') showAssessment(result.assessment, result.provenance);
    } catch {
      el('status').textContent = 'AI readiness assessment unavailable. Deterministic findings remain visible.';
    } finally { el('assess').disabled = false; el('alias').disabled = false; }
  });
  load();
})();
