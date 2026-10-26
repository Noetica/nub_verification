"""Render the standalone progress report from its single dated status snapshot."""

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "done": "Done / recorded",
    "in_progress": "In progress",
    "todo": "To do",
    "blocked": "Blocked",
    "deferred": "Deferred",
}


def esc(value):
    return html.escape(str(value), quote=True)


def link(target, label=None):
    return f'<a href="{esc(target)}">{esc(label or target)}</a>'


def render(data):
    rows = []
    for point in data["planned_points"]:
        status = point["status"]
        if status not in LABELS:
            raise ValueError(f"Unknown status: {status}")
        evidence = " ".join(link(x) for x in point["evidence"])
        gate = f'<p><strong>Gate:</strong> {esc(point["gate"])}</p>' if point["gate"] else ""
        rows.append(
            f'<article class="point" data-status="{esc(status)}">'
            f'<div class="point-title"><h3>{esc(point["id"])} · {esc(point["title"])}</h3>'
            f'<span class="status {esc(status)}">{esc(LABELS[status])}</span></div>'
            f'<p>{esc(point["summary"])}</p>'
            f'<details><summary>Next step and evidence</summary>'
            f'<p><strong>Next:</strong> {esc(point["next_action"])}</p>'
            f'<p><strong>Owner:</strong> {esc(point["owner"])}</p>{gate}'
            f'<p class="evidence">{evidence}</p></details></article>'
        )

    findings = "".join(
        f'<details class="finding"><summary>{esc(x["id"])} · {esc(x["finding"])}</summary>'
        f'<p><strong>Source:</strong> {esc(x["source"])}</p>'
        f'<p>{esc(x["resolution"])}</p><p class="muted">{esc(x["state"])}</p></details>'
        for x in data["findings"]
    )
    prerequisites = "".join(
        f'<li><strong>{esc(x["id"])} — {esc(x["owner"])}</strong>: {esc(x["completion"])}'
        f'<br><span class="muted">Blocks: {esc(x["blocks"])}</span></li>'
        for x in data["prerequisites"]
    )
    decisions = "".join(f'<li>{esc(x)}</li>' for x in data["accepted_decisions"])
    reviews = "".join(
        f'<li>{link(x["url"], x["issue"])}<br>{esc(x["disposition"])}</li>'
        for x in data["review_findings"]
    )
    validation = "".join(
        f'<li><strong>{esc(x["status"])}</strong> — {esc(x["name"])}: {esc(x["detail"])}</li>'
        for x in data["validation"]
    ) or '<li>Consolidation checks have not yet been recorded.</li>'
    agent_state = {
        "issue": data["issue"],
        "observed_at_utc": data["observed_at_utc"],
        "sources": data["sources"],
        "accepted_decisions": data["accepted_decisions"],
        "planned_points": data["planned_points"],
        "prerequisites": data["prerequisites"],
        "resume": data["agent_handover"],
    }
    agent_json = esc(json.dumps(agent_state, ensure_ascii=False, indent=2))
    options = '<option value="all">All planned points</option>' + "".join(
        f'<option value="{esc(key)}">{esc(value)}</option>' for key, value in LABELS.items()
    )
    spec = data["sources"]["spec"]
    product = data["sources"]["report_manager"]
    verification = data["sources"]["verification"]
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ENG-824 · Consolidated progress</title>
<style>
:root {{ color-scheme:light dark; --bg:light-dark(#f7f7f4,#171b20); --fg:light-dark(#17212b,#edf0f3); --muted:light-dark(#465766,#b6c1cb); --line:light-dark(#c9d1d8,#46525c); --surface:light-dark(#ffffff,#212830); --link:light-dark(#165d9c,#8ac8ff); }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.6 system-ui,sans-serif; }}
main {{ max-width:1080px; padding:32px 24px 64px; margin:auto; }}
h1 {{ font-size:clamp(1.8rem,5vw,2.8rem); line-height:1.15; font-weight:600; max-width:800px; margin:12px 0 20px; }}
h2 {{ font-size:1.4rem; margin:0 0 16px; }}
h3 {{ font-size:1rem; margin:0; font-weight:600; }}
p {{ margin:10px 0; }}
a {{ color:var(--link); overflow-wrap:anywhere; }}
section {{ margin-top:40px; }}
header {{ border-bottom:2px solid var(--line); padding-bottom:24px; }}
.eyebrow,.muted {{ color:var(--muted); }}
.eyebrow {{ letter-spacing:.06em; font-size:.85rem; text-transform:uppercase; }}
.lead {{ font-size:1.1rem; max-width:850px; }}
nav {{ display:flex; flex-wrap:wrap; gap:8px 22px; margin-top:16px; }}
.toolbar,.point-title {{ display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }}
select,button {{ color:var(--fg); background:var(--surface); font:inherit; padding:8px 12px; border:1px solid var(--line); border-radius:4px; }}
.point {{ padding:20px 0; border-bottom:1px solid var(--line); }}
.status {{ padding:2px 10px; border:1px solid var(--line); border-radius:3px; white-space:nowrap; font-size:.85rem; }}
.status.blocked {{ border-color:light-dark(#a55c19,#e0a86f); }}
.status.todo {{ border-style:dashed; }}
details {{ margin-top:12px; }}
summary {{ font-weight:500; padding:4px 0; }}
.finding {{ border-bottom:1px solid var(--line); padding:10px 0; }}
.evidence {{ display:flex; gap:8px 18px; flex-wrap:wrap; font-size:.9rem; }}
li {{ margin:10px 0; }}
pre {{ white-space:pre-wrap; overflow-wrap:anywhere; padding:16px; background:var(--surface); border:1px solid var(--line); font:13px/1.6 ui-monospace,monospace; }}
footer {{ margin-top:40px; padding-top:20px; border-top:1px solid var(--line); font-size:.9rem; }}
[hidden] {{ display:none !important; }}
@media(max-width:480px) {{ main {{ padding:24px 16px; }} select {{ width:100%; }} }}
@media print {{ body {{ background:white;color:black; }} main {{ max-width:none; }} .toolbar,button {{ display:none; }} details {{ break-inside:avoid; }} a {{ color:inherit; }} }}
</style>
</head>
<body><main>
<header>
<div class="eyebrow">ENG-824 · {esc(data["observed_at_utc"])}</div>
<h1>{esc(data["title"])}</h1>
<p class="lead">{esc(data["summary"])}</p>
<p>Consolidation of the two sessions is complete. Product implementation and acceptance remain at the stages below.</p>
<nav aria-label="Report sections"><a href="#plan">By planned point</a><a href="#findings">Findings from each workflow</a><a href="#evidence">Evidence</a><a href="#handover">Agent handover</a></nav>
</header>
<section aria-labelledby="agreed"><h2 id="agreed">What is agreed</h2><ul>{decisions}</ul>
<p>{link(spec["url"],"Canonical spec")} · {link(spec["grill_url"],"Grill record")} · status: <strong>draft, not approved</strong></p></section>
<section aria-labelledby="workflows"><h2 id="workflows">What each session contributed</h2>
<p><strong>Hermes:</strong> {esc(data["sources"]["hermes"]["outcome"])}</p>
<p><strong>Codex:</strong> {esc(data["sources"]["codex"]["outcome"])}</p>
<p>The overlap was in the shared spec and delivery records. The existing product harness remains in its own PR; there is no second database implementation to merge.</p></section>
<section aria-labelledby="plan"><h2 id="plan">Done, in progress and still to do</h2>
<div class="toolbar"><label for="status-filter">Show planned points <select id="status-filter">{options}</select></label><output id="visible-count" aria-live="polite">{len(rows)} planned points</output></div>
<div id="points">{"".join(rows)}</div></section>
<section aria-labelledby="findings"><h2 id="findings">Findings from each workflow</h2>{findings}</section>
<section aria-labelledby="gates"><h2 id="gates">Remaining prerequisites</h2><ul>{prerequisites}</ul>
<p>These are delivery gates, not new questions about the already agreed scope.</p></section>
<section aria-labelledby="evidence"><h2 id="evidence">What the evidence actually shows</h2>
<p><strong>Contoso baseline, 26 Oct at 13:05 UTC: overall verification failed.</strong> Smoke: 1 passed test. Verification: 2 passed, 5 failed and 15 unexecuted. The Daily Outbound grid observation was inside a test that later failed; deployed builds were unknown.</p>
<p>{link("results/20261026T130500Z-verification-run/audit.md","Baseline audit and count clarification")}. No live tenant tests were rerun during consolidation.</p>
<p>Report Manager {link(product["pr"],"PR #267")} is <strong>open</strong>; its {link(product["run"],"smoke preflight failed on missing configuration")}. That confirms visible blockage, not a passing suite or final video/trace proof.</p>
<p>The separate {link(data["sources"]["merged_documentation_pr"]["url"],"verification documentation PR #1")} merged. This {link(verification["pr"],"consolidation PR #2")} still needs re-review.</p></section>
<section aria-labelledby="handover"><h2 id="handover">Agent handover</h2>
<p>{link("HANDOVER.md","Read the resume sequence")} · {link("DECISIONS.md","Read settled decisions")} · <a href="consolidation-status.json" download>Download status JSON</a></p>
<details><summary>Open agent-optimized source, decisions, gates and task state</summary>
<button id="copy-handover" type="button">Copy handover JSON</button><span id="copy-status" role="status" aria-live="polite"></span>
<pre id="agent-state">{agent_json}</pre></details></section>
<section aria-labelledby="reviews"><h2 id="reviews">Prior review findings</h2>
<details><summary>Documentation changes address {len(data["review_findings"])} recorded observations; reviewer recheck remains pending</summary><ul>{reviews}</ul></details></section>
<section aria-labelledby="validation"><h2 id="validation">Consolidation validation</h2><ul>{validation}</ul></section>
<footer>{esc(data["snapshot_notice"])} Rebuild with <code>python scripts/render-progress.py</code> after updating <code>consolidation-status.json</code>. Source spec revision: {esc(spec["commit"][:7])}.</footer>
</main>
<script>
(() => {{
  const select = document.getElementById('status-filter');
  const points = Array.from(document.querySelectorAll('#points .point'));
  const count = document.getElementById('visible-count');
  select.addEventListener('change', () => {{
    let visible = 0;
    for (const point of points) {{
      point.hidden = select.value !== 'all' && point.dataset.status !== select.value;
      if (!point.hidden) visible += 1;
    }}
    count.textContent = `${{visible}} of ${{points.length}} planned points`;
  }});
  document.getElementById('copy-handover').addEventListener('click', async () => {{
    const status = document.getElementById('copy-status');
    const text = document.getElementById('agent-state').textContent;
    try {{
      await navigator.clipboard.writeText(text);
      status.textContent = ' Handover copied.';
    }} catch (_) {{
      status.textContent = ' Clipboard unavailable; select the text below or download the status JSON.';
    }}
  }});
}})();
</script></body></html>
'''


if __name__ == "__main__":
    source = json.loads((ROOT / "consolidation-status.json").read_text(encoding="utf-8"))
    output = ROOT / "progress-summary.html"
    output.write_text(render(source), encoding="utf-8", newline="\n")
    print(f"Rendered {len(source['planned_points'])} planned points to {output.name}")
