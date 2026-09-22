#!/usr/bin/env node
// Builds <runDir>/report.html from <runDir>/results.json.
//
//   node report.mjs <runDir> [--open]
//
// results.json shape (image paths relative to runDir, box in app.png pixels):
// {
//   "feature": "Seller Onboarding V2", "viewport": "1440x900", "createdAt": "2026-09-15T10:00:00Z",
//   "reference": "https://www.figma.com/design/...",
//   "steps": [{
//     "id": "2-goals", "title": "Goals & Essentials", "url": "http://localhost:3000/seller-onboarding",
//     "design": "2-goals/design.png", "app": "2-goals/app.png", "diff": "2-goals/diff.png",
//     "navOk": true, "matchScore": 82, "mismatchPct": 9.4, "notes": "",
//     "issues": [{ "severity": "high", "category": "spacing", "element": "Continue button",
//                  "expected": "right aligned, 48px tall", "actual": "left aligned, 40px tall",
//                  "file": "src/Container/SellerOnboardingV2/screens/GoalsAndEssentials.js:120",
//                  "box": [1080, 760, 200, 48] }]
//   }]
// }

import { readFile, writeFile } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import path from 'node:path';

const [runDir, ...flags] = process.argv.slice(2);
if (!runDir) {
  console.error('Usage: node report.mjs <runDir> [--open]');
  process.exit(1);
}

const results = JSON.parse(await readFile(path.join(runDir, 'results.json'), 'utf8'));
const out = path.join(runDir, 'report.html');
await writeFile(out, render(results));
console.log(path.resolve(out));
if (flags.includes('--open')) execFile('open', [out]);

function render(data) {
  const json = JSON.stringify(data).replace(/</g, '\\u003c');
  const title = String(data.feature || 'UI check').replace(/[&<>"]/g, '');
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UI check · ${title}</title>
<style>
  :root {
    --bg: #f6f7f9; --panel: #fff; --ink: #1d2230; --muted: #667085; --line: #e4e7ec;
    --accent: #3b5bdb; --high: #d92d20; --medium: #dc6803; --low: #1570ef; --ok: #079455;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--ink); }
  header { padding: 20px 24px; background: var(--panel); border-bottom: 1px solid var(--line); }
  header h1 { margin: 0 0 4px; font-size: 20px; }
  .meta { color: var(--muted); font-size: 13px; word-break: break-all; }
  main { padding: 20px 24px 60px; max-width: 1800px; margin: 0 auto; }
  .card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; margin-bottom: 20px; overflow: hidden; }
  .card h2 { margin: 0; padding: 14px 16px; font-size: 15px; border-bottom: 1px solid var(--line); display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  .scroll { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
  th { font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); background: #fafbfc; }
  tr.clickable { cursor: pointer; }
  tr.clickable:hover, tr.active { background: #eef2ff; }
  .pill { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; color: #fff; }
  .pill.high { background: var(--high); } .pill.medium { background: var(--medium); } .pill.low { background: var(--low); }
  .pill.ok { background: var(--ok); } .pill.bad { background: var(--high); }
  .num.high { color: var(--high); font-weight: 600; } .num.medium { color: var(--medium); font-weight: 600; } .num.low { color: var(--low); font-weight: 600; }
  .toolbar { display: flex; gap: 8px; align-items: center; padding: 10px 16px; border-bottom: 1px solid var(--line); flex-wrap: wrap; }
  .toolbar button { border: 1px solid var(--line); background: #fff; padding: 5px 12px; border-radius: 6px; cursor: pointer; font: inherit; }
  .toolbar button.on { background: var(--accent); color: #fff; border-color: var(--accent); }
  .toolbar label { display: flex; gap: 6px; align-items: center; color: var(--muted); margin-left: 8px; }
  .stage { padding: 16px; background: #eceff3; }
  .side { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
  @media (max-width: 900px) { .side { grid-template-columns: 1fr; } }
  figure { margin: 0; }
  figcaption { font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: .04em; }
  .shot { position: relative; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.12); line-height: 0; }
  .shot img { display: block; width: 100%; height: auto; }
  .shot .top { position: absolute; left: 0; top: 0; }
  .overlay { max-width: 1100px; margin: 0 auto; }
  .marker { position: absolute; border: 2px solid var(--high); border-radius: 3px; background: rgba(217,45,32,.08); line-height: 1.2; }
  .marker.medium { border-color: var(--medium); background: rgba(220,104,3,.08); }
  .marker.low { border-color: var(--low); background: rgba(21,112,239,.08); }
  .marker span { position: absolute; top: -11px; left: -11px; width: 22px; height: 22px; border-radius: 50%; background: var(--high); color: #fff; font-size: 12px; font-weight: 700; display: grid; place-items: center; }
  .marker.medium span { background: var(--medium); } .marker.low span { background: var(--low); }
  .marker.flash { outline: 4px solid rgba(59,91,219,.6); }
  .missing { padding: 60px 20px; text-align: center; color: var(--muted); line-height: 1.5; background: #fff; }
  .notes { padding: 12px 16px; color: var(--muted); border-top: 1px solid var(--line); white-space: pre-wrap; }
  code { font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; background: #f2f4f7; padding: 1px 4px; border-radius: 4px; word-break: break-all; }
</style>
</head>
<body>
<header>
  <h1 id="title"></h1>
  <div class="meta" id="meta"></div>
</header>
<main>
  <section class="card">
    <h2>Summary</h2>
    <div class="scroll"><table id="summary"></table></div>
  </section>
  <section class="card" id="step"></section>
</main>
<script type="application/json" id="data">${json}</script>
<script>
const data = JSON.parse(document.getElementById('data').textContent);
const steps = data.steps || [];
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const sev = (s) => ({ h: 'high', m: 'medium', l: 'low' }[String(s || 'low')[0].toLowerCase()] || 'low');
const count = (step, level) => (step.issues || []).filter((i) => sev(i.severity) === level).length;
let current = 0;
let mode = 'side';
let opacity = 50;

document.title = 'UI check · ' + (data.feature || '');
document.getElementById('title').textContent = data.feature || 'UI check';
document.getElementById('meta').innerHTML = [
  data.createdAt && new Date(data.createdAt).toLocaleString(),
  data.viewport && 'Viewport ' + esc(data.viewport),
  data.reference && 'Reference: ' + esc(data.reference),
].filter(Boolean).join(' · ');

function renderSummary() {
  const rows = steps.map((s, i) => '<tr class="clickable' + (i === current ? ' active' : '') + '" data-i="' + i + '">' +
    '<td>' + (i + 1) + '. ' + esc(s.title || s.id) + '</td>' +
    '<td>' + (s.navOk === false ? '<span class="pill bad">Broken</span>' : '<span class="pill ok">OK</span>') + '</td>' +
    '<td>' + (s.matchScore != null ? esc(s.matchScore) + '%' : '–') + '</td>' +
    '<td>' + (s.mismatchPct != null ? esc(s.mismatchPct) + '%' : '–') + '</td>' +
    ['high', 'medium', 'low'].map((l) => '<td class="num ' + (count(s, l) ? l : '') + '">' + count(s, l) + '</td>').join('') +
    '</tr>').join('');
  const table = document.getElementById('summary');
  table.innerHTML = '<tr><th>Step</th><th>Navigation</th><th>Match</th><th>Pixel diff</th><th>High</th><th>Med</th><th>Low</th></tr>' + rows;
  table.querySelectorAll('tr[data-i]').forEach((tr) => tr.onclick = () => { current = Number(tr.dataset.i); render(); });
}

function shot(src, label, withMarkers) {
  if (!src) return '<div class="missing">No ' + label + ' image for this step</div>';
  return '<div class="shot"><img src="' + esc(src) + '" alt="' + label + '"' + (withMarkers ? ' data-markers' : '') + '></div>';
}

function stage(s) {
  if (mode === 'diff') return '<div class="overlay">' + shot(s.diff, 'diff', false) + '</div>';
  if (mode === 'overlay') {
    if (!s.design || !s.app) return '<div class="missing">Overlay needs both design and app images</div>';
    return '<div class="overlay"><div class="shot"><img src="' + esc(s.app) + '" alt="app" data-markers>' +
      '<img class="top" src="' + esc(s.design) + '" alt="design" style="width:100%;opacity:' + opacity / 100 + '"></div></div>';
  }
  return '<div class="side"><figure><figcaption>Design</figcaption>' + shot(s.design, 'design', false) +
    '</figure><figure><figcaption>Implementation</figcaption>' + shot(s.app, 'app', true) + '</figure></div>';
}

function renderStep() {
  const s = steps[current];
  const el = document.getElementById('step');
  if (!s) { el.innerHTML = '<div class="missing">No steps in results.json</div>'; return; }
  const issues = s.issues || [];
  el.innerHTML =
    '<h2>' + (current + 1) + '. ' + esc(s.title || s.id) +
      (s.navOk === false ? ' <span class="pill bad">Flow break</span>' : '') +
      (s.url ? ' <span class="meta">' + esc(s.url) + '</span>' : '') + '</h2>' +
    '<div class="toolbar">' +
      ['side', 'overlay', 'diff'].map((m) => '<button data-mode="' + m + '" class="' + (m === mode ? 'on' : '') + '">' +
        { side: 'Side by side', overlay: 'Overlay', diff: 'Pixel diff' }[m] + '</button>').join('') +
      (mode === 'overlay' ? '<label>Design opacity <input type="range" min="0" max="100" value="' + opacity + '" id="opacity"></label>' : '') +
    '</div>' +
    '<div class="stage">' + stage(s) + '</div>' +
    '<div class="scroll"><table><tr><th>#</th><th>Severity</th><th>Element</th><th>Expected (design)</th><th>Actual (app)</th><th>Where</th></tr>' +
      (issues.length ? issues.map((i, n) => '<tr class="clickable" data-issue="' + n + '">' +
        '<td>' + (n + 1) + '</td><td><span class="pill ' + sev(i.severity) + '">' + sev(i.severity) + '</span></td>' +
        '<td>' + esc(i.element) + (i.category ? '<div class="meta">' + esc(i.category) + '</div>' : '') + '</td>' +
        '<td>' + esc(i.expected) + '</td><td>' + esc(i.actual) + '</td>' +
        '<td>' + (i.file ? '<code>' + esc(i.file) + '</code>' : '–') + '</td></tr>').join('')
        : '<tr><td colspan="6" class="meta">No issues recorded 🎉</td></tr>') +
    '</table></div>' +
    (s.notes ? '<div class="notes">' + esc(s.notes) + '</div>' : '');

  el.querySelectorAll('[data-mode]').forEach((b) => b.onclick = () => { mode = b.dataset.mode; renderStep(); });
  const slider = el.querySelector('#opacity');
  if (slider) slider.oninput = () => { opacity = Number(slider.value); el.querySelector('img.top').style.opacity = opacity / 100; };
  el.querySelectorAll('img[data-markers]').forEach((img) => img.complete ? placeMarkers(img, issues) : img.addEventListener('load', () => placeMarkers(img, issues)));
  el.querySelectorAll('tr[data-issue]').forEach((tr) => tr.onclick = () => {
    const m = el.querySelector('.marker[data-n="' + tr.dataset.issue + '"]');
    if (!m) return;
    m.scrollIntoView({ behavior: 'smooth', block: 'center' });
    m.classList.add('flash');
    setTimeout(() => m.classList.remove('flash'), 1200);
  });
}

function placeMarkers(img, issues) {
  const W = img.naturalWidth, H = img.naturalHeight;
  if (!W || !H) return;
  issues.forEach((i, n) => {
    if (!Array.isArray(i.box) || i.box.length !== 4) return;
    const [x, y, w, h] = i.box;
    const m = document.createElement('div');
    m.className = 'marker ' + sev(i.severity);
    m.dataset.n = n;
    m.title = (n + 1) + '. ' + (i.element || '') + ': ' + (i.actual || '');
    Object.assign(m.style, { left: x / W * 100 + '%', top: y / H * 100 + '%', width: Math.max(w, 4) / W * 100 + '%', height: Math.max(h, 4) / H * 100 + '%' });
    m.innerHTML = '<span>' + (n + 1) + '</span>';
    img.parentElement.appendChild(m);
  });
}

function render() { renderSummary(); renderStep(); }
render();
</script>
</body>
</html>
`;
}
