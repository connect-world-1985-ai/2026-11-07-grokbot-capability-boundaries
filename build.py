"""Build the offline capability reference from reviewed source-backed rows."""
import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATUSES = ('Supported', 'Unsupported', 'Unverified')
STYLE = {'Supported': ('yes', '✓'), 'Unsupported': ('no', '✕'), 'Unverified': ('pending', '?')}

CSS = '''
:root{color-scheme:light;--ink:#14283c;--muted:#536477;--line:#d3dce4;--green:#166534;--red:#991b1b;--amber:#854d0e}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#eef3f7;color:var(--ink);font:13px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:2400px;margin:auto;padding:36px 28px 48px}h1{font-size:clamp(26px,2.5vw,42px);line-height:1.15;letter-spacing:-.03em;margin:10px 0 16px}h2{font-size:22px;line-height:1.25;margin:0 0 10px}h3{font-size:16px;margin:0 0 8px}.eyebrow{font-size:12px;font-weight:800;letter-spacing:.13em;text-transform:uppercase;color:#365a7a}.intro{max-width:1000px;font-size:15px}.meta{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}.pill{border:1px solid #b6c9da;background:white;border-radius:8px;padding:7px 12px}.pending-total{background:#fff2bb;border-color:#c28d24;color:#684400;font-weight:750}code{overflow-wrap:anywhere;font:12px/1.5 ui-monospace,monospace}.source{color:var(--muted);margin:10px 0}.legend{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:18px 0}.status{display:inline-flex;gap:4px;align-items:center;border:1px solid currentColor;border-radius:5px;padding:2px 5px;font-weight:750;font-size:11px;white-space:nowrap}.yes .status,.status.yes{color:var(--green);background:#e2f5e8}.no .status,.status.no{color:var(--red);background:#ffe5e4}.pending .status,.status.pending{color:var(--amber);background:#fff2b9}.legend-note{color:var(--muted)}
.overview{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:20px 0 34px}.tile{border:1px solid #c7d5e2;border-top:4px solid var(--accent);border-radius:10px;padding:17px 18px;text-decoration:none;color:var(--ink);background:white;min-width:0;overflow-wrap:anywhere}.tile:hover,.tile:focus-visible{outline:2px solid var(--accent);outline-offset:2px}.tile strong{display:block;font-size:16px}.tile .counts{display:flex;gap:12px;flex-wrap:wrap;margin:8px 0;font-size:13px;font-weight:800}.tile .s{color:var(--green)}.tile .u{color:var(--red)}.tile .uv{color:var(--amber)}.key{display:block;color:var(--muted);font-size:12px}
.band-title{font-size:13px;text-transform:uppercase;letter-spacing:.12em;color:#45637e;margin:28px 0 12px}.band{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;align-items:start}.card{min-width:0;background:white;border:1px solid #cbd8e2;border-top:5px solid var(--accent);border-radius:12px;overflow:hidden;scroll-margin-top:18px}.card-head{padding:20px 16px 14px;background:linear-gradient(120deg,#f7fafc,#fff)}.card-head p{margin:8px 0 0;color:var(--muted);font-size:12px}.card-head .tally{font-weight:700;color:#34516a}.card-body{padding:0 12px 12px}.violet{--accent:#7652b0}.teal{--accent:#178579}.blue{--accent:#376fb0}.rose{--accent:#b45378}.ochre{--accent:#ac781a}.indigo{--accent:#505eaf}.slate{--accent:#506a7f}
table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:11px;line-height:1.5}caption{text-align:left;padding:8px 0 12px;font-size:12px;color:var(--muted)}col.cap{width:18%}col.st{width:112px}col.test{width:23%}col.when{width:96px}th,td{border:1px solid var(--line);padding:8px 6px;text-align:left;vertical-align:top;overflow-wrap:anywhere}thead th{background:#eaf0f5;font-size:10px;color:#40596e;text-transform:uppercase;letter-spacing:.02em}tbody th{font-size:11px;font-weight:750}tbody tr.yes{background:#f1faf4}tbody tr.no{background:#fff1f0}tbody tr.pending{background:#fff8d9}.date{min-width:96px}.date span{display:block;white-space:nowrap;font-size:10px}.date small{display:block;color:#596879;font-size:9px}.updated{display:inline-block;font-size:9px;font-weight:650;background:#e6eafa;color:#3f4f85;border:1px solid #ccd5f4;border-radius:3px;padding:1px 4px;margin-top:6px}.ref{display:block;margin-top:7px;color:#597086;font-size:10px}.verify{display:block;margin-top:8px;border-top:1px dashed #d5b45f;padding-top:6px;color:#70500d}.other{margin-top:30px}.other .card-body{padding:0 16px 16px}.other table{font-size:12px}.other col.cap{width:20%}.other col.test{width:24%}.other tbody th{font-size:12px}.revisions{background:white;border:1px solid #cbd8e2;border-radius:12px;padding:22px;margin-top:30px;max-width:1300px}.revisions li{margin:10px 0}.note,footer{font-size:12px;color:var(--muted)}footer{margin-top:20px}a{color:#254f79}
@media(max-width:1300px){.band{grid-template-columns:1fr}.card table{font-size:13px}.card tbody th{font-size:13px}.card col.cap{width:20%}.card col.test{width:24%}.card col.st{width:110px}.card col.when{width:106px}.date span{font-size:11px}}
@media(max-width:600px){main{padding:22px 12px 30px}.overview{grid-template-columns:1fr;gap:9px}.tile{padding:13px 15px}.meta{gap:8px}.pill{max-width:100%;font-size:12px}.legend{gap:8px}.card-head{padding:18px 14px 12px}.card-body,.other .card-body{padding:0 10px 10px}table,tbody{display:block;width:100%}colgroup{display:none}thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}caption{display:block;width:100%}tbody tr{display:block;border:1px solid var(--line);border-radius:7px;margin-bottom:12px;padding:8px}tbody th,tbody td{display:block;border:0;padding:6px 3px;width:100%;font-size:13px!important}.card tbody th{font-size:15px!important;border-bottom:1px solid var(--line);padding-bottom:9px;margin-bottom:4px}tbody td::before{content:attr(data-label);display:block;color:#556477;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px}.date{min-width:96px}.date span{font-size:12px}.date small{font-size:10px}.status{font-size:12px}.updated{font-size:10px;margin-left:5px}.ref{font-size:11px}.revisions{padding:18px 14px}.revisions ol{padding-left:20px}.band{gap:16px}}
@media print{body{background:white}.tile,.card,tbody tr{print-color-adjust:exact}.band{display:block}.card{margin-bottom:20px}}
'''


def esc(value):
    return html.escape(str(value), quote=True)


def counts(section):
    c = Counter(r['status'] for r in section['rows'])
    return {s: c[s] for s in STATUSES}


def make_row(row):
    cls, icon = STYLE[row['status']]
    badge = '<br><span class="updated">updated v1.1</span>' if row['updated'] else ''
    verify = ''
    if row['status'] == 'Unverified':
        assert row['how_to_verify'], row['capability']
        verify = f'<span class="verify"><strong>How to verify:</strong> {esc(row["how_to_verify"])}</span>'
    return (f'<tr class="{cls}" data-status="{esc(row["status"])}">'
            f'<th scope="row">{esc(row["capability"])}{badge}</th>'
            f'<td data-label="Status"><span class="status"><span aria-hidden="true">{icon}</span> {esc(row["status"])}</span></td>'
            f'<td data-label="Limit">{esc(row["limit"])}{verify}<span class="ref">Report: {esc(row["source"])}</span></td>'
            f'<td data-label="Tested with">{esc(row["tested_with"])}</td>'
            f'<td class="date" data-label="Last tested"><span>{esc(row["last_tested"])}</span><small>{esc(row["evidence"])}</small></td></tr>')


def make_card(section, accent, other=False):
    c = counts(section)
    extra = ' other' if other else ''
    headers = ''.join(f'<th scope="col">{h}</th>' for h in ('Capability', 'Status', 'Limit', 'Tested with', 'Last tested'))
    return (f'<section class="card {accent}{extra}" id="{esc(section["id"])}" aria-labelledby="h-{esc(section["id"])}">'
            f'<div class="card-head"><h2 id="h-{esc(section["id"])}">{esc(section["title"])}</h2>'
            f'<p class="tally">{len(section["rows"])} items · Supported {c["Supported"]} / Unsupported {c["Unsupported"]} / Unverified {c["Unverified"]}</p>'
            f'<p>{esc(section["note"])}</p></div><div class="card-body"><table>'
            f'<caption>Evidence snapshot · {esc(section["title"])}</caption>'
            '<colgroup><col class="cap"><col class="st"><col><col class="test"><col class="when"></colgroup>'
            f'<thead><tr>{headers}</tr></thead><tbody>{"".join(make_row(r) for r in section["rows"])}</tbody></table></div></section>')


def build():
    data = json.loads((ROOT / 'data.json').read_text())
    sections = data['sections']
    assert len(sections) == 7
    assert all(r['status'] in STATUSES for s in sections for r in s['rows'])
    pending = sum(counts(s)['Unverified'] for s in sections)
    total = sum(len(s['rows']) for s in sections)
    accents = ['blue', 'teal', 'violet', 'indigo', 'ochre', 'rose']
    tiles = []
    for s, accent in zip(sections[:6], accents):
        c = counts(s)
        tiles.append(f'<a class="tile {accent}" href="#{esc(s["id"])}" data-card="{esc(s["id"])}" data-s="{c["Supported"]}" data-u="{c["Unsupported"]}" data-uv="{c["Unverified"]}"><strong>{esc(s["title"])} ↗</strong><span class="counts"><span class="s">S {c["Supported"]}</span><span class="u">U {c["Unsupported"]}</span><span class="uv">Uv {c["Unverified"]}</span></span><span class="key">{esc(s["key_limit"])}</span></a>')
    cards = [make_card(s, a) for s, a in zip(sections[:6], accents)]
    revisions = ''.join(f'<li><strong>{esc(r["version"])}</strong> — {esc(r["date"])} — {esc(r["note"])}</li>' for r in data['revisions'])
    output = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Grok Bot Multimodal Capability Boundaries</title><style>{CSS}</style></head>
<body><main><header><div class="eyebrow">Capability atlas · evidence before promises</div><h1>Grok Bot Multimodal Capability Boundaries</h1>
<p class="intro">Video understanding is not audio-file understanding. This reference separates six modalities and makes the tested input, documented claim and open question explicit.</p>
<div class="meta"><span class="pill"><strong>{esc(data['version'])}</strong></span><span class="pill">Last updated {esc(data['updated'])}</span><span class="pill pending-total" data-pending="{pending}">{pending} items pending verification</span><span class="pill">{total} evidence items</span></div>
<p class="source">Source report: <code>{esc(data['source_report'])}</code><br>Source tests: same directory, <code>tests/</code>. Research snapshot: 2026-11-06 (Asia/Shanghai). No new capability tests were performed for this page.</p>
<div class="legend"><span class="status yes">✓ Supported</span><span class="status no">✕ Unsupported</span><span class="status pending">? Unverified</span><span class="legend-note">S / U / Uv in the tiles. Colour is paired with text and symbols.</span></div>
<p class="note">Supported = demonstrated or officially documented, as labelled. Unsupported = a confirmed sample failure, schema absence or explicit restriction, scoped to its evidence. Unverified = unresolved or merely not found; each has a verification step. Documentation dates are review dates, not execution dates. Pending count includes Other limits.</p></header>
<nav class="overview" aria-label="Six modality overview">{''.join(tiles)}</nav>
<h2 class="band-title">Understanding · input modalities</h2><div class="band">{''.join(cards[:3])}</div>
<h2 class="band-title">Generation · output modalities</h2><div class="band">{''.join(cards[3:])}</div>
{make_card(sections[6], 'slate', True)}
<section class="revisions" id="revisions"><h2>Revision history / notes</h2><ol>{revisions}</ol><p class="note">Version policy: minor edits are 1.x; future structural changes are 2.0. Append later revisions below the existing entries. Badges mark new or substantively changed content, not rows that only moved. Duplicate questions in the source lists are consolidated without dropping their substance.</p><p class="note">Bot, consumer apps and the developer API are different surfaces. The 5-versus-7 aspect-ratio difference is image versus video, not conflicting image schemas. AAC denominators (5 versus 6/6) remain explicitly unresolved. The freezing sample set mixes direct and relayed evidence.</p></section>
<footer>Built-in native tools and platform workflows only. Local scripts/models are excluded as capabilities. Offline, self-contained HTML: inline CSS, no JavaScript, no remote fonts, images or resource requests.</footer></main></body></html>
'''
    (ROOT / 'index.html').write_text(output, encoding='utf-8')
    for s in sections:
        print(s['id'], counts(s), 'total', len(s['rows']))
    print('TOTAL', total, 'PENDING', pending)


if __name__ == '__main__':
    build()
