#!/usr/bin/env python3
"""Generates mtcna_quiz_standalone.html with both JSONs embedded."""
import json
from pathlib import Path

BASE = Path(__file__).parent
SOURCES = ["complete_all", "mtcna_questions"]

def load(name):
    data = json.loads((BASE / f"{name}.json").read_text(encoding="utf-8"))
    return [{"id": q["number"], "question": q["text"],
             "options": q["options"], "correct": q["correct"]} for q in data]

all_data = {name: load(name) for name in SOURCES}
js_data   = json.dumps(all_data, ensure_ascii=False)
labels    = json.dumps({name: name.replace("_questions","").replace("_"," ").title()
                        for name in SOURCES}, ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="MTCNA Quiz">
<title>MTCNA Quiz</title>
<style>
  :root {{
    --blue:#3b82f6; --green:#22c55e; --red:#ef4444; --yellow:#f59e0b;
    --bg:#f4f6f9; --white:#fff; --gray:#6b7280; --dark:#1f2937;
    --safe-top: env(safe-area-inset-top);
    --safe-bot: env(safe-area-inset-bottom);
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; -webkit-tap-highlight-color:transparent; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--dark);
          min-height:100dvh; padding-top:var(--safe-top); padding-bottom:var(--safe-bot); }}
  #app {{ max-width:680px; margin:0 auto; padding:16px 14px 32px; }}

  /* ── menu ── */
  #menu {{ display:flex; flex-direction:column; align-items:center; gap:10px; padding-top:28px; }}
  #menu h1 {{ font-size:2rem; color:var(--blue); margin-bottom:2px; }}
  .sub {{ color:var(--gray); font-size:.95rem; margin-bottom:4px; }}
  .source-row {{ display:flex; align-items:center; gap:8px; }}
  .source-row label {{ font-weight:600; font-size:.95rem; }}
  .source-row select {{ padding:8px 10px; border-radius:8px; border:2px solid #d1d5db;
                        font-size:1rem; background:white; }}
  .prog-summary {{ background:white; border-radius:10px; padding:10px 18px;
                   font-size:.88rem; box-shadow:0 1px 4px rgba(0,0,0,.1);
                   text-align:center; line-height:1.7; }}
  .ps-good {{ color:#16a34a; font-weight:700; }}
  .ps-bad  {{ color:#dc2626; font-weight:700; }}
  .ps-new  {{ color:var(--gray); }}
  .menu-btn {{
    width:min(320px,100%); padding:15px 12px; font-size:1rem; border:none;
    border-radius:12px; background:white; cursor:pointer;
    box-shadow:0 1px 4px rgba(0,0,0,.12); transition:transform .1s,box-shadow .1s;
    font-weight:600; text-align:center;
  }}
  @media(hover:hover){{ .menu-btn:hover {{ transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,.15); }} }}
  .menu-btn:active {{ transform:scale(.97); }}
  .menu-btn:disabled {{ opacity:.4; cursor:default; transform:none; }}
  .menu-btn.danger {{ background:#111827; color:#ef4444; }}
  .menu-btn.resume {{ background:#eff6ff; color:#1d4ed8; border:2px solid #93c5fd; }}
  .menu-btn.unseen {{ background:#f0fdf4; color:#166534; }}
  .menu-btn.wrongs {{ background:#fff7ed; color:#9a3412; }}
  .menu-btn.muted  {{ background:white; color:var(--gray); font-size:.88rem; font-weight:400; box-shadow:none; border:1px solid #e5e7eb; }}
  .menu-sep {{ width:min(320px,100%); border:none; border-top:1px solid #e5e7eb; }}

  /* ── modal ── */
  .overlay {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.45);
              z-index:100; align-items:center; justify-content:center; padding:20px; }}
  .overlay.show {{ display:flex; }}
  .modal {{ background:white; padding:28px 24px; border-radius:16px; width:100%; max-width:320px; text-align:center; }}
  .modal h2 {{ margin-bottom:18px; font-size:1.2rem; }}
  .modal input[type=number] {{ width:110px; font-size:1.3rem; text-align:center;
                               padding:8px; border:2px solid #d1d5db; border-radius:8px; }}
  .modal-btns {{ display:flex; gap:10px; justify-content:center; margin-top:18px; }}
  .modal-btns button {{ padding:11px 22px; border:none; border-radius:9px; cursor:pointer; font-size:1rem; font-weight:600; }}
  .btn-ok {{ background:var(--blue); color:white; }}
  .btn-cancel {{ background:#e5e7eb; color:var(--dark); }}

  /* ── quiz ── */
  #quiz {{ display:none; }}
  .qheader {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }}
  .qheader .prog  {{ color:var(--gray); font-size:.9rem; font-weight:600; }}
  .qheader .score {{ font-weight:700; color:var(--blue); font-size:.9rem; }}
  .pbar-wrap {{ height:7px; background:#e5e7eb; border-radius:99px; margin-bottom:18px; }}
  .pbar-fill  {{ height:100%; background:var(--blue); border-radius:99px; transition:width .3s; }}
  .sudden-banner {{ background:#111827; color:#ef4444; text-align:center; padding:8px;
                    border-radius:8px; margin-bottom:14px; font-weight:700; }}
  .question-box {{ background:white; border-radius:14px; padding:20px 18px;
                   margin-bottom:14px; box-shadow:0 1px 4px rgba(0,0,0,.1); }}
  .q-text {{ font-size:1.05rem; font-weight:700; line-height:1.5; }}
  .q-hint {{ font-size:.82rem; color:#9ca3af; margin-top:6px; }}
  .options {{ display:flex; flex-direction:column; gap:9px; margin-bottom:14px; }}
  .opt {{
    display:flex; align-items:flex-start; gap:12px;
    background:white; border:2px solid #e5e7eb; border-radius:11px;
    padding:13px 14px; cursor:pointer; transition:border-color .12s,background .12s;
    font-size:.97rem; line-height:1.4; user-select:none;
  }}
  .opt:active:not(.disabled) {{ background:#eff6ff; }}
  .opt.selected {{ border-color:var(--blue); background:#dbeafe; }}
  .opt.correct  {{ border-color:var(--green); background:#dcfce7; }}
  .opt.wrong    {{ border-color:var(--red);   background:#fee2e2; }}
  .opt.missed   {{ border-color:var(--yellow);background:#fef9c3; }}
  .opt.disabled {{ cursor:default; }}
  .opt .letter  {{ font-weight:800; color:var(--blue); min-width:18px; flex-shrink:0; }}
  .opt.correct .letter {{ color:#16a34a; }}
  .opt.wrong   .letter {{ color:#dc2626; }}
  .opt.missed  .letter {{ color:#d97706; }}
  .feedback {{ font-size:1rem; font-weight:700; min-height:26px; margin-bottom:14px; }}
  .feedback.ok  {{ color:var(--green); }}
  .feedback.bad {{ color:var(--red); }}
  .nav {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
  .nav button {{ padding:13px 16px; border:none; border-radius:11px; cursor:pointer;
                 font-size:.93rem; font-weight:600; transition:opacity .15s; flex:1; }}
  .nav button:disabled {{ opacity:.3; cursor:default; }}
  .btn-prev {{ background:#e5e7eb; color:#374151; flex:0 0 auto; padding:13px 14px; }}
  .btn-end  {{ background:#fff3cd; color:#856404; font-size:.82rem; flex:0 0 auto; padding:13px 12px; }}
  .btn-next {{ background:var(--blue); color:white; }}

  /* ── results ── */
  #results {{ display:none; text-align:center; padding-top:32px; }}
  #results h1 {{ font-size:1.7rem; margin-bottom:6px; }}
  .big-pct {{ font-size:4.5rem; font-weight:900; margin:10px 0; }}
  .big-pct.good {{ color:var(--green); }}
  .big-pct.bad  {{ color:var(--red); }}
  .res-detail {{ color:var(--gray); font-size:.95rem; margin-bottom:24px; }}
  .res-btns {{ display:flex; flex-direction:column; align-items:center; gap:10px; }}
  .res-btns button {{ width:min(300px,100%); padding:14px; border:none; border-radius:12px;
                      cursor:pointer; font-size:1rem; font-weight:600; background:white;
                      box-shadow:0 1px 4px rgba(0,0,0,.12); }}
  .res-btns button:active {{ transform:scale(.97); }}
  .res-btns .primary     {{ background:var(--blue); color:white; }}
  .res-btns .warning-btn {{ background:#ffebee; }}
</style>
</head>
<body>
<div id="app">

<div id="menu">
  <h1>MTCNA Quiz</h1>
  <p class="sub" id="total-label">Načítám…</p>
  <div class="source-row">
    <label>Zdroj:</label>
    <select id="source-sel" onchange="onSourceChange()"></select>
  </div>
  <div class="prog-summary" id="prog-summary"></div>
  <button class="menu-btn resume" id="btn-resume" onclick="resumeSession()" style="display:none">
    ▶ Pokračovat od Q<span id="resume-label"></span>
  </button>
  <button class="menu-btn" onclick="startAll()">🚀 Vše popořadě</button>
  <button class="menu-btn unseen" id="btn-unseen" onclick="startUnseen()">
    🆕 Jen neprozkoumané (<span id="unseen-count">?</span>)
  </button>
  <button class="menu-btn wrongs" id="btn-wrongs" onclick="startWrongs()">
    ⚠️ Jen chybné (<span id="wrongs-count">?</span>)
  </button>
  <button class="menu-btn" onclick="showRandomModal('random')">🎲 Náhodný výběr</button>
  <button class="menu-btn" onclick="showRandomModal('study')">📖 Studuj pak testuj</button>
  <button class="menu-btn danger" onclick="startExam()">🎯 Ostrý test (25 ot. / 60 min)</button>
  <button class="menu-btn danger" onclick="startSuddenDeath()">💀 Sudden Death</button>
  <hr class="menu-sep">
  <button class="menu-btn muted" onclick="clearProgress()">🗑 Smazat progress tohoto zdroje</button>
</div>

<div class="overlay" id="random-modal">
  <div class="modal">
    <h2>Kolik otázek?</h2>
    <input type="number" id="rand-count" min="1" value="20">
    <div class="modal-btns">
      <button class="btn-cancel" onclick="closeModal()">Zrušit</button>
      <button class="btn-ok" onclick="startRandom()">Spustit</button>
    </div>
  </div>
</div>

<div id="quiz">
  <div id="sudden-banner" class="sudden-banner" style="display:none">💀 SUDDEN DEATH — jedna chyba = konec!</div>
  <div class="qheader">
    <span class="prog" id="prog-label"></span>
    <span class="score" id="score-label"></span>
  </div>
  <div class="pbar-wrap"><div class="pbar-fill" id="pbar"></div></div>
  <div class="question-box">
    <div class="q-text" id="q-text"></div>
    <div class="q-hint" id="q-hint"></div>
  </div>
  <div class="options" id="opts"></div>
  <div class="feedback" id="feedback"></div>
  <div class="nav">
    <button class="btn-prev" id="btn-prev" onclick="prevQ()">←</button>
    <button class="btn-end" onclick="finishEarly()">🏳 Konec</button>
    <button class="btn-next" id="btn-action" onclick="handleAction()">✔ Potvrdit</button>
  </div>
</div>

<div id="results">
  <h1 id="res-title"></h1>
  <div class="big-pct" id="res-pct"></div>
  <div class="res-detail" id="res-detail"></div>
  <div class="res-btns">
    <button class="primary" onclick="restartSame()">🔄 Restartovat stejný výběr</button>
    <button id="btn-wrong" onclick="practiceWrong()" style="display:none" class="warning-btn"></button>
    <button onclick="showMenu()">🏠 Hlavní menu</button>
  </div>
</div>

</div>
<script>
const DB     = {js_data};
const LABELS = {labels};

let ALL = [], currentSource = '', progress = {{}}, session = null;
let queue = [], idx = 0, history = [], checked = false, suddenDeath = false, selected = new Set();
let modalMode = 'random', studyMode = false, studyPicks = [];
let examMode = false, examTimer = null, examEndTime = 0;

// ── init ──────────────────────────────────────────────────────────────────
function init() {{
  const sources = Object.keys(DB);
  currentSource = sources[0];
  const sel = document.getElementById('source-sel');
  sel.innerHTML = sources.map(s =>
    `<option value="${{s}}">${{LABELS[s] || s}}</option>`
  ).join('');
  loadSource(currentSource);
}}

function onSourceChange() {{
  currentSource = document.getElementById('source-sel').value;
  loadSource(currentSource);
}}

function loadSource(src) {{
  ALL = DB[src];
  const saved = JSON.parse(localStorage.getItem('mtcna_progress_' + src) || '{{}}');
  progress = saved.seen || {{}};
  session  = saved.session || null;
  document.getElementById('rand-count').max   = ALL.length;
  document.getElementById('rand-count').value = Math.min(20, ALL.length);
  updateMenuStats();
}}

function saveProgress() {{
  const histMap = {{}};
  for (const h of history) histMap[h.id] = h.isCorrect ? 'correct' : 'wrong';
  const newProg = Object.assign({{}}, progress, histMap);
  const newSess = (idx < queue.length) ? {{
    queue_ids: queue.map(q => q.id), idx, sudden_death: suddenDeath, history
  }} : null;
  localStorage.setItem('mtcna_progress_' + currentSource,
    JSON.stringify({{ seen: newProg, session: newSess }}));
  progress = newProg;
  session  = newSess;
}}

function updateMenuStats() {{
  const total  = ALL.length;
  const seen   = Object.keys(progress).length;
  const good   = Object.values(progress).filter(v => v === 'correct').length;
  const bad    = seen - good;
  const unseen = total - seen;
  document.getElementById('total-label').textContent = `Databáze: ${{total}} otázek`;
  document.getElementById('prog-summary').innerHTML =
    `<span class="ps-good">✓ ${{good}} správně</span> &nbsp;·&nbsp; ` +
    `<span class="ps-bad">✗ ${{bad}} chybně</span> &nbsp;·&nbsp; ` +
    `<span class="ps-new">— ${{unseen}} nových</span>`;
  document.getElementById('unseen-count').textContent = unseen;
  document.getElementById('wrongs-count').textContent = bad;
  document.getElementById('btn-unseen').disabled = unseen === 0;
  document.getElementById('btn-wrongs').disabled = bad === 0;
  if (session && session.idx < (session.queue_ids || []).length) {{
    document.getElementById('resume-label').textContent = session.queue_ids[session.idx];
    document.getElementById('btn-resume').style.display = 'block';
  }} else {{
    document.getElementById('btn-resume').style.display = 'none';
  }}
}}

// ── views ─────────────────────────────────────────────────────────────────
function showMenu()  {{ updateMenuStats(); s('menu','flex'); s('quiz','none'); s('results','none'); }}
function showQuiz()  {{ s('menu','none');  s('quiz','block'); s('results','none'); }}
function showResults(){{ s('menu','none'); s('quiz','none'); s('results','block'); renderResults(); }}
function s(id, d)    {{ document.getElementById(id).style.display = d; }}

// ── start modes ───────────────────────────────────────────────────────────
function startAll()    {{ begin([...ALL], false); }}
function startUnseen() {{ begin(ALL.filter(q => !progress[q.id]), false); }}
function startWrongs() {{ begin(ALL.filter(q => progress[q.id] === 'wrong'), false); }}

function resumeSession() {{
  if (!session) return;
  const map = Object.fromEntries(ALL.map(q => [q.id, q]));
  queue = session.queue_ids.map(id => map[id]).filter(Boolean);
  idx = session.idx; history = session.history || []; suddenDeath = session.sudden_death || false;
  document.getElementById('sudden-banner').style.display = suddenDeath ? 'block' : 'none';
  showQuiz(); renderQ();
}}

function showRandomModal(mode) {{
  modalMode = mode || 'random';
  document.querySelector('#random-modal h2').textContent =
    modalMode === 'study' ? 'Kolik otázek nastudovat?' : 'Kolik otázek?';
  document.getElementById('random-modal').classList.add('show');
  setTimeout(() => document.getElementById('rand-count').focus(), 50);
}}
function closeModal() {{ document.getElementById('random-modal').classList.remove('show'); }}
function startRandom() {{
  const n = parseInt(document.getElementById('rand-count').value);
  closeModal();
  if (modalMode === 'study') {{
    startStudyTest(n);
  }} else {{
    begin([...ALL].sort(() => Math.random()-.5).slice(0, n), false);
  }}
}}
function startSuddenDeath() {{ begin([...ALL].sort(() => Math.random()-.5), true); }}

// ── ostrý test (simulace reálné MTCNA zkoušky: 25 ot. / 60 min / 60 % k úspěchu) ──
function startExam() {{
  const n = Math.min(25, ALL.length);
  examMode = true;
  queue = [...ALL].sort(() => Math.random()-.5).slice(0, n);
  idx = 0; history = []; suddenDeath = false;
  document.getElementById('sudden-banner').style.display = 'none';
  showQuiz();
  startExamTimer(60*60);
  renderQ();
}}
function startExamTimer(sec) {{
  clearExamTimer();
  examEndTime = Date.now() + sec*1000;
  updateExamTimer();
  examTimer = setInterval(updateExamTimer, 1000);
}}
function clearExamTimer() {{ if (examTimer) clearInterval(examTimer); examTimer = null; }}
function updateExamTimer() {{
  const remain = Math.max(0, Math.round((examEndTime - Date.now())/1000));
  const m = String(Math.floor(remain/60)).padStart(2,'0'), s = String(remain%60).padStart(2,'0');
  document.getElementById('score-label').textContent = `⏱ ${{m}}:${{s}}`;
  if (remain <= 0) {{ clearExamTimer(); saveProgress(); showResults(); examMode = false; }}
}}
function examNext() {{
  const q = queue[idx], cs = new Set(q.correct);
  const isCorrect = selected.size === cs.size && [...selected].every(k => cs.has(k));
  const rec = {{ id:q.id, userKeys:[...selected], correctKeys:[...cs], isCorrect }};
  const ex = history.findIndex(h => h.id === q.id);
  ex >= 0 ? history[ex] = rec : history.push(rec);
  idx++;
  if (idx < queue.length) {{ renderQ(); }}
  else {{ clearExamTimer(); saveProgress(); showResults(); examMode = false; }}
}}

function startStudyTest(n) {{
  studyPicks = [...ALL].sort(() => Math.random()-.5).slice(0, n);
  studyMode = true;
  queue = [...studyPicks]; idx = 0; history = []; suddenDeath = false;
  document.getElementById('sudden-banner').style.display = 'none';
  showQuiz(); renderQ();
}}

function begin(qs, sd) {{
  queue = qs; idx = 0; history = []; suddenDeath = sd;
  document.getElementById('sudden-banner').style.display = sd ? 'block' : 'none';
  showQuiz(); renderQ();
}}

// ── quiz ──────────────────────────────────────────────────────────────────
function renderQ() {{
  const q = queue[idx]; checked = false; selected = new Set();
  const total = queue.length, correct = history.filter(h=>h.isCorrect).length, answered = history.length;
  document.getElementById('prog-label').textContent  = `Otázka ${{idx+1}} / ${{total}}`;
  if (!examMode) {{
    document.getElementById('score-label').textContent = answered ? `${{Math.round(correct/answered*100)}} %` : '– %';
  }}
  document.getElementById('pbar').style.width = `${{idx/total*100}}%`;
  document.getElementById('q-text').textContent = `Q${{q.id}}: ${{q.question}}`;
  document.getElementById('q-hint').textContent  = q.correct.length > 1 ? '(Více správných odpovědí)' : '';
  document.getElementById('feedback').textContent = '';
  document.getElementById('feedback').className = 'feedback';
  const el = document.getElementById('opts'); el.innerHTML = '';
  for (const [l, t] of Object.entries(q.options)) {{
    const d = document.createElement('div');
    d.className = 'opt'; d.id = 'opt-'+l;
    d.innerHTML = `<span class="letter">${{l}}</span><span>${{t}}</span>`;
    d.addEventListener('click', () => toggleOpt(l));
    el.appendChild(d);
  }}
  document.getElementById('btn-prev').disabled   = idx === 0 || suddenDeath || studyMode || examMode;
  document.getElementById('btn-action').textContent = '✔ Potvrdit';
  document.getElementById('btn-action').disabled = true;

  if (examMode) {{
    document.getElementById('btn-action').textContent = idx < total-1 ? 'Další →' : '📊 Odeslat test';
    document.getElementById('btn-action').disabled = false;
    return;
  }}

  if (studyMode) {{
    document.getElementById('prog-label').textContent = `📖 Studium ${{idx+1}} / ${{total}}`;
    document.getElementById('score-label').textContent = '';
    const cs = new Set(q.correct);
    for (const l of Object.keys(q.options)) {{
      const oel = document.getElementById('opt-'+l);
      if (cs.has(l)) oel.classList.add('correct');
      oel.classList.add('disabled');
    }}
    document.getElementById('feedback').textContent = '📖 Studijní režim — správná odpověď zvýrazněna';
    document.getElementById('feedback').className = 'feedback ok';
    document.getElementById('btn-action').textContent = idx < total-1 ? '📖 Další (studium) →' : '▶ Spustit test bez klíče';
    document.getElementById('btn-action').disabled = false;
    return;
  }}

  const rec = history.find(h => h.id === q.id);
  if (rec) restoreState(rec);
}}

function toggleOpt(l) {{
  if (checked || studyMode) return;
  selected.has(l) ? (selected.delete(l), document.getElementById('opt-'+l).classList.remove('selected'))
                  : (selected.add(l),    document.getElementById('opt-'+l).classList.add('selected'));
  document.getElementById('btn-action').disabled = selected.size === 0;
}}

function handleAction() {{ studyMode ? studyNext() : examMode ? examNext() : (checked ? nextQ() : confirmAnswer()); }}

function studyNext() {{
  idx++;
  if (idx < queue.length) {{ renderQ(); }}
  else {{ studyMode = false; queue = [...studyPicks]; idx = 0; history = []; renderQ(); }}
}}

function confirmAnswer() {{
  if (!selected.size) return;
  checked = true;
  const q = queue[idx], cs = new Set(q.correct);
  const isCorrect = selected.size === cs.size && [...selected].every(k => cs.has(k));
  const rec = {{ id:q.id, userKeys:[...selected], correctKeys:[...cs], isCorrect }};
  const ex = history.findIndex(h => h.id === q.id);
  ex >= 0 ? history[ex] = rec : history.push(rec);
  restoreState(rec); saveProgress();
  if (suddenDeath && !isCorrect)
    setTimeout(() => {{ alert(`☠️ GAME OVER!\\nSprávně: ${{[...cs].join(', ')}}`); showResults(); }}, 600);
}}

function restoreState(rec) {{
  checked = true;
  const cs = new Set(rec.correctKeys), us = new Set(rec.userKeys);
  for (const l of Object.keys(queue[idx].options)) {{
    const el = document.getElementById('opt-'+l); if (!el) continue;
    el.classList.remove('selected','correct','wrong','missed'); el.classList.add('disabled');
    if (us.has(l) && cs.has(l))       el.classList.add('correct');
    else if (us.has(l))                el.classList.add('wrong');
    else if (cs.has(l))                el.classList.add('missed');
  }}
  const fb = document.getElementById('feedback');
  rec.isCorrect ? (fb.textContent='✅  Správně!', fb.className='feedback ok')
                : (fb.textContent=`❌  Špatně! Správně: ${{rec.correctKeys.join(', ')}}`, fb.className='feedback bad');
  const c2 = history.filter(h=>h.isCorrect).length;
  document.getElementById('score-label').textContent = `${{Math.round(c2/history.length*100)}} %`;
  const btn = document.getElementById('btn-action');
  btn.textContent = idx < queue.length-1 ? 'Další →' : '📊 Výsledky';
  btn.disabled = false;
}}

function prevQ() {{ if (studyMode || examMode) return; if (idx>0) {{ idx--; renderQ(); }} }}
function nextQ() {{ idx++; idx < queue.length ? (renderQ(), saveProgress()) : (saveProgress(), showResults()); }}

function finishEarly() {{
  if (!history.length) {{ if (confirm('Zpět do menu?')) {{ clearExamTimer(); examMode = false; showMenu(); }} return; }}
  if (confirm('Ukončit a uložit progress?')) {{ clearExamTimer(); saveProgress(); showResults(); examMode = false; }}
}}

function renderResults() {{
  const c = history.filter(h=>h.isCorrect).length, t = Math.max(history.length,1), pct = Math.round(c/t*100);
  document.getElementById('res-title').textContent = examMode
    ? (pct>=60 ? '✅ MTCNA test SPLNĚN' : '❌ MTCNA test NESPLNĚN')
    : (suddenDeath && pct<100 ? '☠️ GAME OVER ☠️' : 'Výsledky');
  const pe = document.getElementById('res-pct');
  pe.textContent = pct+'%'; pe.className = 'big-pct '+(pct>=60?'good':'bad');
  document.getElementById('res-detail').textContent = `Správně ${{c}} z ${{history.length}}` +
    (examMode ? ' · reálná hranice pro splnění: 60 %' : '');
  const wids = new Set(history.filter(h=>!h.isCorrect).map(h=>h.id));
  const wq   = ALL.filter(q=>wids.has(q.id));
  const wb   = document.getElementById('btn-wrong');
  if (wq.length && !suddenDeath) {{ wb.style.display='block'; wb.textContent=`⚠️ Procvičit chyby (${{wq.length}})`; wb._wq=wq; }}
  else wb.style.display='none';
}}

function restartSame()  {{ begin([...queue], suddenDeath); }}
function practiceWrong(){{ begin([...document.getElementById('btn-wrong')._wq], false); }}

function clearProgress() {{
  if (!confirm(`Smazat progress pro "${{currentSource}}"?`)) return;
  localStorage.removeItem('mtcna_progress_'+currentSource);
  progress={{}}; session=null; updateMenuStats();
}}

// ── keyboard (iPad/desktop) ───────────────────────────────────────────────
document.addEventListener('keydown', e => {{
  if (document.getElementById('quiz').style.display==='none') return;
  if (e.key==='Enter'||e.key==='ArrowRight') {{ const b=document.getElementById('btn-action'); if(!b.disabled) handleAction(); }}
  else if (e.key==='ArrowLeft') {{ if(!document.getElementById('btn-prev').disabled) prevQ(); }}
  else {{ const k=e.key.toUpperCase(); if(/^[A-G]$/.test(k)) toggleOpt(k); }}
}});
document.getElementById('rand-count').addEventListener('keydown', e => {{
  if(e.key==='Enter') startRandom(); if(e.key==='Escape') closeModal();
}});

init();
</script>
</body>
</html>"""

out = BASE / "mtcna_quiz_standalone.html"
out.write_text(HTML, encoding="utf-8")
print(f"Vygenerováno: {out}")
print(f"Velikost: {out.stat().st_size // 1024} KB")
print(f"Zdroje: {', '.join(all_data.keys())}")
print(f"Otázky: {', '.join(str(len(v)) + ' (' + k + ')' for k,v in all_data.items())}")
