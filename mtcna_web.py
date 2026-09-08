#!/usr/bin/env python3
import json
import random
import webbrowser
import threading
import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string

BASE = Path(__file__).parent
PROGRESS_FILE = BASE / "progress.json"

app = Flask(__name__)

EXCLUDED_SOURCES = {"progress", "indiatik_questions"}

def list_sources():
    return sorted(p.stem for p in BASE.glob("*.json") if p.stem not in EXCLUDED_SOURCES)

def load_questions(source):
    path = BASE / f"{source}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return [{"id": q["number"], "question": q["text"],
             "options": q["options"], "correct": q["correct"]} for q in data]

def load_progress():
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return {}

def save_progress(data):
    PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

HTML = r"""
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MTCNA Quiz</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #f4f6f9; color: #1f2937; min-height: 100vh; }
  #app { max-width: 900px; margin: 0 auto; padding: 24px 20px; }

  /* menu */
  #menu { display: flex; flex-direction: column; align-items: center; gap: 12px; padding-top: 40px; }
  #menu h1 { font-size: 2.2rem; color: #3b82f6; margin-bottom: 4px; }
  #menu .sub { color: #6b7280; font-size: 1rem; margin-bottom: 8px; }
  .source-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .source-row label { color: #374151; font-weight: 600; }
  .source-row select { padding: 8px 12px; border-radius: 8px; border: 2px solid #d1d5db; font-size: 1rem; cursor: pointer; }
  .progress-summary { background: white; border-radius: 10px; padding: 10px 20px; font-size: .9rem;
    color: #374151; box-shadow: 0 1px 4px rgba(0,0,0,.1); margin-bottom: 4px; text-align: center; }
  .progress-summary .ps-good { color: #16a34a; font-weight: 700; }
  .progress-summary .ps-bad  { color: #dc2626; font-weight: 700; }
  .progress-summary .ps-new  { color: #6b7280; }
  .menu-btn {
    width: 320px; padding: 14px; font-size: 1.05rem; border: none;
    border-radius: 10px; background: white; cursor: pointer;
    box-shadow: 0 1px 4px rgba(0,0,0,.12); transition: transform .1s, box-shadow .1s;
  }
  .menu-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.15); }
  .menu-btn.danger  { background: #111827; color: #ef4444; }
  .menu-btn.quit    { background: #fef2f2; color: #ef4444; }
  .menu-btn.resume  { background: #eff6ff; color: #1d4ed8; border: 2px solid #93c5fd; }
  .menu-btn.unseen  { background: #f0fdf4; color: #166534; }
  .menu-btn.wrongs  { background: #fff7ed; color: #9a3412; }
  .menu-btn:disabled { opacity: .4; cursor: default; transform: none; }
  .menu-sep { width: 320px; border: none; border-top: 1px solid #e5e7eb; margin: 4px 0; }

  /* chunks */
  #chunks { display: none; padding-top: 24px; }
  #chunks h1 { font-size: 1.6rem; color: #3b82f6; text-align: center; margin-bottom: 16px; }
  .chunk-list { display: flex; flex-direction: column; gap: 10px; max-width: 420px; margin: 0 auto; }
  .chunk-btn {
    display: flex; justify-content: space-between; align-items: center;
    background: white; border: none; border-radius: 10px; padding: 14px 18px;
    cursor: pointer; box-shadow: 0 1px 4px rgba(0,0,0,.12); font-size: 1rem; text-align: left;
  }
  .chunk-btn:hover { box-shadow: 0 4px 12px rgba(0,0,0,.15); }
  .chunk-btn .chunk-name { font-weight: 700; }
  .chunk-btn .chunk-stats { font-size: .85rem; }
  .chunk-btn .chunk-stats span { margin-left: 8px; }
  .chunk-back { display: block; margin: 20px auto 0; padding: 10px 20px; border: none; border-radius: 8px; background: #e5e7eb; cursor: pointer; }
  .chunk-size-row { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 16px; font-size: .9rem; }
  .chunk-size-row input { width: 70px; padding: 6px 8px; border-radius: 8px; border: 2px solid #d1d5db; font-size: 1rem; text-align: center; }
  .chunk-size-row button { padding: 7px 14px; border: none; border-radius: 8px; cursor: pointer; background: #3b82f6; color: white; font-weight: 600; }

  /* chunk detail */
  #chunk-detail { display: none; padding-top: 24px; }
  #chunk-detail h1 { font-size: 1.4rem; color: #3b82f6; text-align: center; margin-bottom: 16px; }
  .chunk-detail-wrap { max-width: 480px; margin: 0 auto; }
  .chunk-detail-btns { display: flex; gap: 8px; justify-content: center; margin-bottom: 18px; flex-wrap: wrap; }
  .chunk-detail-btns button { padding: 8px 14px; border: none; border-radius: 8px; cursor: pointer; font-size: .85rem; background: white; box-shadow: 0 1px 4px rgba(0,0,0,.12); }
  .cd-section { margin-bottom: 14px; }
  .cd-section h3 { font-size: .9rem; margin: 0 0 6px; }
  .cd-section.good h3 { color: #16a34a; }
  .cd-section.bad h3 { color: #dc2626; }
  .cd-section.new h3 { color: #6b7280; }
  .cd-qlist { display: flex; flex-wrap: wrap; gap: 6px; }
  .cd-qlist span { background: white; border-radius: 6px; padding: 3px 8px; font-size: .8rem; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
  .cd-qlist .q-pill { border: none; cursor: pointer; font: inherit; background: white; border-radius: 6px; padding: 3px 8px; font-size: .8rem; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
  .cd-qlist .q-pill:hover { background: #dbeafe; box-shadow: 0 1px 4px rgba(0,0,0,.2); }

  /* modal */
  .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 100; align-items: center; justify-content: center; }
  .overlay.show { display: flex; }
  .modal { background: white; padding: 32px; border-radius: 14px; min-width: 320px; text-align: center; }
  .modal h2 { margin-bottom: 20px; }
  .modal input[type=number] { width: 120px; font-size: 1.3rem; text-align: center; padding: 8px; border: 2px solid #d1d5db; border-radius: 8px; }
  .modal-btns { display: flex; gap: 12px; justify-content: center; margin-top: 20px; }
  .modal-btns button { padding: 10px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; }
  .btn-ok { background: #3b82f6; color: white; }
  .btn-cancel { background: #e5e7eb; }

  /* quiz */
  #quiz { display: none; }
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .header .prog  { color: #6b7280; font-size: .95rem; font-weight: 600; }
  .header .score { font-weight: 700; color: #3b82f6; }
  .progress-bar { height: 8px; background: #e5e7eb; border-radius: 99px; margin-bottom: 24px; }
  .progress-bar .fill { height: 100%; background: #3b82f6; border-radius: 99px; transition: width .3s; }
  .sudden-banner { background: #111827; color: #ef4444; text-align: center; padding: 8px; border-radius: 8px; margin-bottom: 16px; font-weight: 700; font-size: 1rem; }
  .question-box { background: white; border-radius: 12px; padding: 24px 28px; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,.1); }
  .question-box .hint { font-size: .85rem; color: #9ca3af; margin-top: 6px; }
  .question-text { font-size: 1.15rem; font-weight: 700; line-height: 1.5; }
  .options { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
  .opt {
    display: flex; align-items: flex-start; gap: 14px;
    background: white; border: 2px solid #e5e7eb; border-radius: 10px;
    padding: 14px 18px; cursor: pointer; transition: border-color .15s, background .15s;
    font-size: 1rem; line-height: 1.4; user-select: none;
  }
  .opt:hover:not(.disabled) { border-color: #93c5fd; background: #eff6ff; }
  .opt.selected { border-color: #3b82f6; background: #dbeafe; }
  .opt.correct  { border-color: #22c55e; background: #dcfce7; }
  .opt.wrong    { border-color: #ef4444; background: #fee2e2; }
  .opt.missed   { border-color: #f59e0b; background: #fef9c3; }
  .opt.disabled { cursor: default; }
  .opt .letter { font-weight: 800; color: #3b82f6; min-width: 20px; }
  .opt.correct .letter { color: #16a34a; }
  .opt.wrong   .letter { color: #dc2626; }
  .opt.missed  .letter { color: #d97706; }
  .feedback { font-size: 1.05rem; font-weight: 700; min-height: 28px; margin-bottom: 16px; }
  .feedback.ok  { color: #22c55e; }
  .feedback.bad { color: #ef4444; }
  .nav { display: flex; justify-content: space-between; align-items: center; }
  .nav button { padding: 12px 24px; border: none; border-radius: 9px; cursor: pointer; font-size: 1rem; font-weight: 600; transition: opacity .15s; }
  .nav button:disabled { opacity: .35; cursor: default; }
  .btn-prev    { background: #e5e7eb; color: #374151; }
  .btn-end     { background: #fff3cd; color: #856404; font-size: .9rem; }
  .btn-next    { background: #3b82f6; color: white; }
  .btn-confirm { background: #3b82f6; color: white; }

  /* results */
  #results { display: none; text-align: center; padding-top: 40px; }
  #results h1 { font-size: 2rem; margin-bottom: 8px; }
  .big-pct { font-size: 5rem; font-weight: 900; margin: 12px 0; }
  .big-pct.good { color: #22c55e; }
  .big-pct.bad  { color: #ef4444; }
  .res-detail { color: #6b7280; font-size: 1rem; margin-bottom: 30px; }
  .res-btns { display: flex; flex-direction: column; align-items: center; gap: 12px; }
  .res-btns button { width: 300px; padding: 13px; border: none; border-radius: 10px; cursor: pointer; font-size: 1rem; font-weight: 600; background: white; box-shadow: 0 1px 4px rgba(0,0,0,.12); }
  .res-btns button:hover { box-shadow: 0 4px 12px rgba(0,0,0,.15); }
  .res-btns .primary     { background: #3b82f6; color: white; }
  .res-btns .warning-btn { background: #ffebee; }

  @media (max-width: 600px) {
    #app { padding: 12px 12px; }

    /* menu */
    #menu { padding-top: 20px; gap: 10px; }
    #menu h1 { font-size: 1.6rem; }
    .menu-btn { width: 100%; }
    .menu-sep { width: 100%; }
    .source-row { flex-wrap: wrap; }
    .source-row select { width: 100%; }

    /* modal */
    .modal { min-width: unset; width: 90vw; padding: 24px 16px; }

    /* quiz */
    .question-box { padding: 16px; }
    .question-text { font-size: 1rem; }
    .opt { padding: 12px 14px; gap: 10px; font-size: .95rem; }
    .nav { flex-wrap: wrap; gap: 8px; }
    .nav button { flex: 1 1 auto; padding: 12px 10px; font-size: .9rem; }
    .btn-end { flex-basis: 100%; order: 3; }

    /* results */
    #results { padding-top: 20px; }
    #results h1 { font-size: 1.5rem; }
    .big-pct { font-size: 3.5rem; }
    .res-btns button { width: 100%; }
  }
</style>
</head>
<body>
<div id="app">

  <!-- MENU -->
  <div id="menu">
    <h1>MTCNA Quiz</h1>
    <p class="sub" id="total-label">Načítám...</p>

    <div class="source-row">
      <label for="source-sel">Zdroj:</label>
      <select id="source-sel" onchange="onSourceChange()"></select>
    </div>

    <div class="progress-summary" id="prog-summary"></div>

    <button class="menu-btn resume" id="btn-resume" onclick="resumeSession()" style="display:none">▶ Pokračovat od Q<span id="resume-label"></span></button>
    <button class="menu-btn" onclick="showChunks()">📦 Po <span id="menu-chunk-size">50</span> (postupně)</button>
    <button class="menu-btn" onclick="startAll()">🚀 Vše popořadě</button>
    <button class="menu-btn unseen" id="btn-unseen" onclick="startUnseen()">🆕 Jen neprokoumané (<span id="unseen-count">?</span>)</button>
    <button class="menu-btn wrongs" id="btn-wrongs" onclick="startWrongs()">⚠️ Jen chybné (<span id="wrongs-count">?</span>)</button>
    <button class="menu-btn" id="btn-correct" onclick="startCorrect()">✅ Zopakovat správné (<span id="correct-count">?</span>)</button>
    <button class="menu-btn" onclick="showRandomModal('random')">🎲 Náhodný výběr</button>
    <button class="menu-btn" onclick="showRandomModal('study')">📖 Studuj pak testuj</button>
    <button class="menu-btn danger" onclick="startExam()">🎯 Ostrý test (25 ot. / 60 min)</button>
    <button class="menu-btn danger" onclick="startSuddenDeath()">💀 Sudden Death (náhodné)</button>
    <hr class="menu-sep">
    <button class="menu-btn" onclick="clearSourceProgress()" style="font-size:.9rem;color:#6b7280">🗑 Smazat progress tohoto zdroje</button>
    <button class="menu-btn quit" onclick="shutdown()">❌ Ukončit server</button>
  </div>

  <!-- CHUNKS -->
  <div id="chunks">
    <h1>📦 Otázky po <span id="chunks-size-label">50</span></h1>
    <div class="chunk-size-row">
      <label for="chunk-size-input">Velikost úseku:</label>
      <input type="number" id="chunk-size-input" min="1" step="1">
      <button onclick="applyChunkSize()">Použít</button>
    </div>
    <div class="chunk-list" id="chunk-list"></div>
    <button class="chunk-back" onclick="showMenu()">← Zpět do menu</button>
  </div>

  <!-- CHUNK DETAIL -->
  <div id="chunk-detail">
    <h1 id="chunk-detail-title"></h1>
    <div class="chunk-detail-wrap">
      <div class="chunk-detail-btns">
        <button onclick="startChunkSubset('all')">🚀 Vše</button>
        <button onclick="startChunkSubset(undefined)">🆕 Neznámé</button>
        <button onclick="startChunkSubset('wrong')">⚠️ Chybné</button>
        <button onclick="startChunkSubset('correct')">✅ Správné</button>
        <button onclick="startChunkStudy()">📖 Studuj pak testuj</button>
      </div>
      <div class="cd-section good">
        <h3>✅ Správné</h3>
        <div class="cd-qlist" id="cd-good"></div>
      </div>
      <div class="cd-section bad">
        <h3>✗ Chybné</h3>
        <div class="cd-qlist" id="cd-bad"></div>
      </div>
      <div class="cd-section new">
        <h3>— Neznámé</h3>
        <div class="cd-qlist" id="cd-new"></div>
      </div>
    </div>
    <button class="chunk-back" onclick="showChunks()">← Zpět na bloky</button>
  </div>

  <!-- RANDOM MODAL -->
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

  <!-- QUIZ -->
  <div id="quiz">
    <div id="sudden-banner" class="sudden-banner" style="display:none">💀 SUDDEN DEATH — jedna chyba = konec!</div>
    <div class="header">
      <span class="prog" id="prog-label"></span>
      <span class="score" id="score-label"></span>
    </div>
    <div class="progress-bar"><div class="fill" id="pbar"></div></div>
    <div class="question-box">
      <div class="question-text" id="q-text"></div>
      <div class="hint" id="q-hint"></div>
    </div>
    <div class="options" id="opts"></div>
    <div class="feedback" id="feedback"></div>
    <div class="nav">
      <button class="btn-prev" id="btn-prev" onclick="prevQ()">← Předchozí</button>
      <button class="btn-end" onclick="finishEarly()">🏳 Ukončit předčasně</button>
      <button class="btn-confirm btn-next" id="btn-action" onclick="handleAction()">✔ Potvrdit (Enter)</button>
    </div>
  </div>

  <!-- RESULTS -->
  <div id="results">
    <h1 id="res-title"></h1>
    <div class="big-pct" id="res-pct"></div>
    <div class="res-detail" id="res-detail"></div>
    <div class="res-btns">
      <button class="primary" onclick="restartSame()">🔄 Restartovat stejný výběr</button>
      <button id="btn-wrong" onclick="practiceWrong()" style="display:none" class="warning-btn"></button>
      <button onclick="backFromResults()">🏠 Hlavní menu</button>
    </div>
  </div>

</div>
<script>
let ALL = [];
let currentSource = '';
let sources = [];
let progress = {};   // {qid: "correct"|"wrong"}
let session = null;  // saved mid-session {queue_ids, idx, history, sudden_death}

let queue = [];
let idx = 0;
let history = [];
let checked = false;
let suddenDeath = false;
let selected = new Set();
let modalMode = 'random';
let studyMode = false;
let studyPicks = [];
let examMode = false;
let examTimer = null;
let examEndTime = 0;

// ── init ──────────────────────────────────────────────────────────────────
async function init() {
  const r = await fetch('/api/sources');
  const data = await r.json();
  sources = data.sources;
  currentSource = data.default;

  const sel = document.getElementById('source-sel');
  sel.innerHTML = sources.map(s =>
    `<option value="${s}" ${s === currentSource ? 'selected' : ''}>${s}</option>`
  ).join('');

  await loadSource(currentSource);
}

async function onSourceChange() {
  currentSource = document.getElementById('source-sel').value;
  await loadSource(currentSource);
}

async function loadSource(source) {
  const [qr, pr] = await Promise.all([
    fetch(`/api/questions?source=${encodeURIComponent(source)}`),
    fetch(`/api/progress?source=${encodeURIComponent(source)}`)
  ]);
  ALL = await qr.json();
  const pd = await pr.json();
  progress = pd.seen || {};
  session  = pd.session || null;

  document.getElementById('rand-count').max = ALL.length;
  document.getElementById('rand-count').value = Math.min(20, ALL.length);
  updateMenuStats();
}

function updateMenuStats() {
  const total = ALL.length;
  const seen  = Object.keys(progress).length;
  const good  = Object.values(progress).filter(v => v === 'correct').length;
  const bad   = seen - good;
  const unseen = total - seen;

  document.getElementById('total-label').textContent = `Databáze: ${total} otázek`;
  document.getElementById('prog-summary').innerHTML =
    `<span class="ps-good">✓ ${good} správně</span> &nbsp;·&nbsp; ` +
    `<span class="ps-bad">✗ ${bad} chybně</span> &nbsp;·&nbsp; ` +
    `<span class="ps-new">— ${unseen} nových</span>`;

  document.getElementById('unseen-count').textContent = unseen;
  document.getElementById('wrongs-count').textContent = bad;
  document.getElementById('correct-count').textContent = good;
  document.getElementById('btn-unseen').disabled = unseen === 0;
  document.getElementById('btn-wrongs').disabled = bad === 0;
  document.getElementById('btn-correct').disabled = good === 0;

  if (session && session.idx < session.queue_ids.length) {
    const resumeQ = session.queue_ids[session.idx];
    document.getElementById('resume-label').textContent = resumeQ;
    document.getElementById('btn-resume').style.display = 'block';
  } else {
    document.getElementById('btn-resume').style.display = 'none';
  }
}

// ── persistence ───────────────────────────────────────────────────────────
async function saveProgress() {
  const histMap = {};
  for (const h of history) histMap[h.id] = h.isCorrect ? 'correct' : 'wrong';
  const newProgress = Object.assign({}, progress, histMap);

  const newSession = (idx < queue.length) ? {
    queue_ids: queue.map(q => q.id),
    idx,
    sudden_death: suddenDeath,
    history
  } : null;

  await fetch(`/api/progress?source=${encodeURIComponent(currentSource)}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({seen: newProgress, session: newSession})
  });

  progress = newProgress;
  session = newSession;
}

// ── navigation ────────────────────────────────────────────────────────────
let fromChunks = false;

function showMenu() {
  updateMenuStats();
  document.getElementById('menu').style.display = 'flex';
  document.getElementById('chunks').style.display = 'none';
  document.getElementById('chunk-detail').style.display = 'none';
  document.getElementById('quiz').style.display = 'none';
  document.getElementById('results').style.display = 'none';
}

function showQuiz() {
  document.getElementById('menu').style.display = 'none';
  document.getElementById('chunks').style.display = 'none';
  document.getElementById('chunk-detail').style.display = 'none';
  document.getElementById('quiz').style.display = 'block';
  document.getElementById('results').style.display = 'none';
}

function showResults() {
  document.getElementById('menu').style.display = 'none';
  document.getElementById('chunks').style.display = 'none';
  document.getElementById('chunk-detail').style.display = 'none';
  document.getElementById('quiz').style.display = 'none';
  document.getElementById('results').style.display = 'block';
  renderResults();
}

// ── chunks (po X) ─────────────────────────────────────────────────────────
let CHUNK_SIZE = parseInt(localStorage.getItem('mtcna_chunk_size'), 10) || 50;

function syncChunkSizeUI() {
  document.getElementById('menu-chunk-size').textContent = CHUNK_SIZE;
  document.getElementById('chunks-size-label').textContent = CHUNK_SIZE;
  document.getElementById('chunk-size-input').value = CHUNK_SIZE;
}

function applyChunkSize() {
  const n = parseInt(document.getElementById('chunk-size-input').value, 10);
  if (!n || n < 1) return;
  CHUNK_SIZE = n;
  localStorage.setItem('mtcna_chunk_size', String(n));
  syncChunkSizeUI();
  renderChunks();
}

function showChunks() {
  fromChunks = false;
  syncChunkSizeUI();
  renderChunks();
  document.getElementById('menu').style.display = 'none';
  document.getElementById('chunks').style.display = 'block';
  document.getElementById('chunk-detail').style.display = 'none';
  document.getElementById('quiz').style.display = 'none';
  document.getElementById('results').style.display = 'none';
}

function getChunks() {
  const out = [];
  for (let i = 0; i < ALL.length; i += CHUNK_SIZE) {
    out.push(ALL.slice(i, i + CHUNK_SIZE));
  }
  return out;
}

function renderChunks() {
  const list = document.getElementById('chunk-list');
  list.innerHTML = '';
  const chunks = getChunks();
  chunks.forEach((qs, i) => {
    const done = qs.filter(q => progress[q.id] === 'correct').length;
    const wrong = qs.filter(q => progress[q.id] === 'wrong').length;
    const unknown = qs.length - done - wrong;
    const from = i * CHUNK_SIZE + 1;
    const to = i * CHUNK_SIZE + qs.length;
    const btn = document.createElement('button');
    btn.className = 'chunk-btn';
    btn.innerHTML = `<span class="chunk-name">Blok ${i + 1} (Q${from}–${to})</span>` +
      `<span class="chunk-stats">` +
      `<span class="ps-new">— ${unknown}</span>` +
      `<span class="ps-bad">✗ ${wrong}</span>` +
      `<span class="ps-good">✓ ${done}</span>` +
      `</span>`;
    btn.onclick = () => showChunkDetail(qs, i);
    list.appendChild(btn);
  });
}

let currentChunk = [];

function showChunkDetail(qs, i) {
  currentChunk = qs;
  document.getElementById('chunk-detail-title').textContent = `Blok ${i + 1} (Q${i * CHUNK_SIZE + 1}–${i * CHUNK_SIZE + qs.length})`;
  const good = qs.filter(q => progress[q.id] === 'correct');
  const bad = qs.filter(q => progress[q.id] === 'wrong');
  const unknown = qs.filter(q => !progress[q.id]);
  const renderList = (elId, list) => {
    document.getElementById(elId).innerHTML =
      list.map(q => `<button class="q-pill" onclick="startChunkQuestion(${q.id})">Q${q.id}</button>`).join('') || '<span>—</span>';
  };
  renderList('cd-good', good);
  renderList('cd-bad', bad);
  renderList('cd-new', unknown);
  document.getElementById('menu').style.display = 'none';
  document.getElementById('chunks').style.display = 'none';
  document.getElementById('chunk-detail').style.display = 'block';
  document.getElementById('quiz').style.display = 'none';
  document.getElementById('results').style.display = 'none';
}

function startChunkQuestion(qid) {
  const q = currentChunk.find(q => q.id === qid);
  if (!q) return;
  fromChunks = true;
  beginSession([q], false);
}

function startChunkSubset(status) {
  let qs;
  if (status === 'all') qs = currentChunk;
  else if (status === undefined) qs = currentChunk.filter(q => !progress[q.id]);
  else qs = currentChunk.filter(q => progress[q.id] === status);
  if (!qs.length) return;
  startChunk(qs);
}

function startChunkStudy() {
  const pool = currentChunk.filter(q => !progress[q.id] || progress[q.id] === 'wrong');
  if (!pool.length) return;
  fromChunks = true;
  showRandomModal('chunk-study', pool);
}

function startChunk(qs) {
  fromChunks = true;
  beginSession([...qs], false);
}

// ── start modes ───────────────────────────────────────────────────────────
function startAll()    { beginSession([...ALL], false); }
function startUnseen() { beginSession(ALL.filter(q => !progress[q.id]), false); }
function startWrongs() { beginSession(ALL.filter(q => progress[q.id] === 'wrong'), false); }
function startCorrect() { beginSession(ALL.filter(q => progress[q.id] === 'correct'), false); }

function resumeSession() {
  if (!session) return;
  const idMap = Object.fromEntries(ALL.map(q => [q.id, q]));
  const qs = session.queue_ids.map(id => idMap[id]).filter(Boolean);
  queue = qs;
  idx = session.idx;
  history = session.history || [];
  suddenDeath = session.sudden_death || false;
  document.getElementById('sudden-banner').style.display = suddenDeath ? 'block' : 'none';
  showQuiz();
  renderQ();
}

let modalPool = null;

function showRandomModal(mode, pool) {
  modalMode = mode || 'random';
  if (modalMode === 'study' && !pool) {
    pool = ALL.filter(q => !progress[q.id] || progress[q.id] === 'wrong');
  }
  modalPool = pool || null;
  document.querySelector('#random-modal h2').textContent =
    (modalMode === 'study' || modalMode === 'chunk-study') ? 'Kolik otázek nastudovat?' : 'Kolik otázek?';
  const maxN = modalPool ? modalPool.length : ALL.length;
  const input = document.getElementById('rand-count');
  input.max = maxN;
  input.value = Math.min(20, maxN);
  document.getElementById('random-modal').classList.add('show');
  setTimeout(() => input.focus(), 50);
}
function closeModal() { document.getElementById('random-modal').classList.remove('show'); }

function startRandom() {
  const maxN = modalPool ? modalPool.length : ALL.length;
  const n = Math.min(Math.max(1, parseInt(document.getElementById('rand-count').value) || 1), maxN);
  closeModal();
  if (modalMode === 'study' || modalMode === 'chunk-study') {
    startStudyTest(n, modalPool);
  } else {
    beginSession([...ALL].sort(() => Math.random() - .5).slice(0, n), false);
  }
}

function startStudy(qs) {
  studyPicks = [...qs];
  studyMode = true;
  queue = [...studyPicks];
  idx = 0;
  history = [];
  suddenDeath = false;
  document.getElementById('sudden-banner').style.display = 'none';
  showQuiz();
  renderQ();
}

function startStudyTest(n, poolOverride) {
  const pool = poolOverride || ALL.filter(q => !progress[q.id] || progress[q.id] === 'wrong');
  startStudy([...pool].sort(() => Math.random() - .5).slice(0, n));
}

function startSuddenDeath() {
  beginSession([...ALL].sort(() => Math.random() - .5), true);
}

// ── ostrý test (simulace reálné MTCNA zkoušky: 25 ot. / 60 min / 60 % k úspěchu) ──
function startExam() {
  const n = Math.min(25, ALL.length);
  examMode = true;
  queue = [...ALL].sort(() => Math.random() - .5).slice(0, n);
  idx = 0;
  history = [];
  suddenDeath = false;
  document.getElementById('sudden-banner').style.display = 'none';
  showQuiz();
  startExamTimer(60 * 60);
  renderQ();
}

function startExamTimer(seconds) {
  clearExamTimer();
  examEndTime = Date.now() + seconds * 1000;
  updateExamTimer();
  examTimer = setInterval(updateExamTimer, 1000);
}

function clearExamTimer() {
  if (examTimer) clearInterval(examTimer);
  examTimer = null;
}

function updateExamTimer() {
  const remain = Math.max(0, Math.round((examEndTime - Date.now()) / 1000));
  const m = String(Math.floor(remain / 60)).padStart(2, '0');
  const s = String(remain % 60).padStart(2, '0');
  document.getElementById('score-label').textContent = `⏱ ${m}:${s}`;
  if (remain <= 0) {
    clearExamTimer();
    saveProgress();
    showResults();
    examMode = false;
  }
}

function examNext() {
  const q = queue[idx];
  const correctSet = new Set(q.correct);
  const isCorrect = selected.size === correctSet.size && [...selected].every(k => correctSet.has(k));
  const rec = { id: q.id, userKeys: [...selected], correctKeys: [...correctSet], isCorrect };
  const existing = history.findIndex(h => h.id === q.id);
  if (existing >= 0) history[existing] = rec; else history.push(rec);

  idx++;
  if (idx < queue.length) {
    renderQ();
  } else {
    clearExamTimer();
    saveProgress();
    showResults();
    examMode = false;
  }
}

function beginSession(qs, sd) {
  queue = qs;
  idx = 0;
  history = [];
  suddenDeath = sd;
  document.getElementById('sudden-banner').style.display = sd ? 'block' : 'none';
  showQuiz();
  renderQ();
}

// ── quiz render ───────────────────────────────────────────────────────────
function renderQ() {
  const q = queue[idx];
  checked = false;
  selected = new Set();

  const total = queue.length;
  const correct = history.filter(h => h.isCorrect).length;
  const answered = history.length;
  const pct = answered ? Math.round(correct / answered * 100) : 0;

  document.getElementById('prog-label').textContent = `Otázka ${idx + 1} / ${total}`;
  if (!examMode) {
    document.getElementById('score-label').textContent = answered ? `Úspěšnost: ${pct} %` : 'Úspěšnost: – %';
  }
  document.getElementById('pbar').style.width = `${(idx / total) * 100}%`;

  const isMulti = q.correct.length > 1;
  document.getElementById('q-text').textContent = `Q${q.id}: ${q.question}`;
  document.getElementById('q-hint').textContent = isMulti ? '(Vyberte více správných odpovědí)' : '';
  document.getElementById('feedback').textContent = '';
  document.getElementById('feedback').className = 'feedback';

  const optsEl = document.getElementById('opts');
  optsEl.innerHTML = '';
  for (const [letter, text] of Object.entries(q.options)) {
    const div = document.createElement('div');
    div.className = 'opt';
    div.id = 'opt-' + letter;
    div.innerHTML = `<span class="letter">${letter}</span><span>${text}</span>`;
    div.addEventListener('click', () => toggleOpt(letter));
    optsEl.appendChild(div);
  }

  document.getElementById('btn-prev').disabled = (idx === 0) || suddenDeath || studyMode || examMode;
  document.getElementById('btn-action').textContent = '✔ Potvrdit (Enter)';
  document.getElementById('btn-action').disabled = true;

  if (examMode) {
    document.getElementById('btn-action').textContent = idx < total - 1 ? 'Další →  (Enter)' : '📊 Odeslat test (Enter)';
    document.getElementById('btn-action').disabled = false;
    return;
  }

  if (studyMode) {
    document.getElementById('prog-label').textContent = `📖 Studium ${idx + 1} / ${total}`;
    document.getElementById('score-label').textContent = '';
    const correctSet = new Set(q.correct);
    for (const letter of Object.keys(q.options)) {
      const el = document.getElementById('opt-' + letter);
      if (correctSet.has(letter)) el.classList.add('correct');
      el.classList.add('disabled');
    }
    document.getElementById('feedback').textContent = '📖 Studijní režim — správná odpověď zvýrazněna';
    document.getElementById('feedback').className = 'feedback ok';
    document.getElementById('btn-action').textContent =
      idx < total - 1 ? '📖 Další (studium) →' : '▶ Spustit test bez klíče';
    document.getElementById('btn-action').disabled = false;
    return;
  }

  const rec = history.find(h => h.id === q.id);
  if (rec) restoreState(rec);
}

function toggleOpt(letter) {
  if (checked || studyMode) return;
  if (selected.has(letter)) {
    selected.delete(letter);
    document.getElementById('opt-' + letter).classList.remove('selected');
  } else {
    selected.add(letter);
    document.getElementById('opt-' + letter).classList.add('selected');
  }
  document.getElementById('btn-action').disabled = selected.size === 0;
}

function handleAction() {
  if (studyMode) { studyNext(); return; }
  if (examMode) { examNext(); return; }
  if (!checked) confirmAnswer();
  else nextQ();
}

function studyNext() {
  idx++;
  if (idx < queue.length) {
    renderQ();
  } else {
    studyMode = false;
    queue = [...studyPicks];
    idx = 0;
    history = [];
    renderQ();
  }
}

function confirmAnswer() {
  if (selected.size === 0) return;
  checked = true;
  const q = queue[idx];
  const correctSet = new Set(q.correct);
  const isCorrect = selected.size === correctSet.size && [...selected].every(k => correctSet.has(k));

  const rec = { id: q.id, userKeys: [...selected], correctKeys: [...correctSet], isCorrect };
  const existing = history.findIndex(h => h.id === q.id);
  if (existing >= 0) history[existing] = rec; else history.push(rec);

  restoreState(rec);
  saveProgress();

  if (suddenDeath && !isCorrect) {
    setTimeout(() => {
      alert(`☠️ GAME OVER!\nSprávně bylo: ${[...correctSet].join(', ')}`);
      showResults();
    }, 600);
  }
}

function restoreState(rec) {
  checked = true;
  const correctSet = new Set(rec.correctKeys);
  const userSet = new Set(rec.userKeys);

  for (const letter of Object.keys(queue[idx].options)) {
    const el = document.getElementById('opt-' + letter);
    if (!el) continue;
    el.classList.remove('selected', 'correct', 'wrong', 'missed');
    el.classList.add('disabled');
    if (userSet.has(letter) && correctSet.has(letter))  el.classList.add('correct');
    else if (userSet.has(letter))                        el.classList.add('wrong');
    else if (correctSet.has(letter))                     el.classList.add('missed');
  }

  const fb = document.getElementById('feedback');
  if (rec.isCorrect) { fb.textContent = '✅  Správně!'; fb.className = 'feedback ok'; }
  else { fb.textContent = `❌  Špatně!   Správně: ${rec.correctKeys.join(', ')}`; fb.className = 'feedback bad'; }

  const correct = history.filter(h => h.isCorrect).length;
  const pct = Math.round(correct / history.length * 100);
  document.getElementById('score-label').textContent = `Úspěšnost: ${pct} %`;

  const btn = document.getElementById('btn-action');
  btn.textContent = idx < queue.length - 1 ? 'Další →  (Enter)' : '📊 Výsledky (Enter)';
  btn.disabled = false;
}

function prevQ() { if (studyMode || examMode) return; if (idx > 0) { idx--; renderQ(); } }

function nextQ() {
  idx++;
  if (idx < queue.length) { renderQ(); saveProgress(); }
  else { saveProgress(); showResults(); }
}

function finishEarly() {
  if (!history.length) { if (confirm('Žádné odpovědi. Zpět do menu?')) { clearExamTimer(); examMode = false; backFromResults(); } return; }
  if (confirm('Ukončit předčasně a uložit progress?')) { clearExamTimer(); saveProgress(); showResults(); examMode = false; }
}

function renderResults() {
  const correct = history.filter(h => h.isCorrect).length;
  const total = Math.max(history.length, 1);
  const pct = Math.round(correct / total * 100);

  if (examMode) {
    document.getElementById('res-title').textContent = pct >= 60 ? '✅ MTCNA test SPLNĚN' : '❌ MTCNA test NESPLNĚN';
  } else {
    document.getElementById('res-title').textContent = suddenDeath && pct < 100 ? '☠️ GAME OVER ☠️' : 'Výsledky testu';
  }
  const pctEl = document.getElementById('res-pct');
  pctEl.textContent = pct + ' %';
  pctEl.className = 'big-pct ' + (pct >= 60 ? 'good' : 'bad');
  document.getElementById('res-detail').textContent = `Správně ${correct} z ${history.length} zodpovězených` +
    (examMode ? ' · reálná hranice pro splnění: 60 %' : '');

  const wrongIds = new Set(history.filter(h => !h.isCorrect).map(h => h.id));
  const wrongQ = ALL.filter(q => wrongIds.has(q.id));
  const wrongBtn = document.getElementById('btn-wrong');
  if (wrongQ.length && !suddenDeath) {
    wrongBtn.style.display = 'block';
    wrongBtn.textContent = `⚠️ Procvičit jen chyby (${wrongQ.length})`;
    wrongBtn._wrongQ = wrongQ;
  } else {
    wrongBtn.style.display = 'none';
  }
}

function backFromResults() { if (fromChunks) showChunks(); else showMenu(); }

function restartSame()  { beginSession([...queue], suddenDeath); }
function practiceWrong(){ beginSession([...document.getElementById('btn-wrong')._wrongQ], false); }

async function clearSourceProgress() {
  if (!confirm(`Smazat veškerý progress pro "${currentSource}"?`)) return;
  await fetch(`/api/progress?source=${encodeURIComponent(currentSource)}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({seen: {}, session: null})
  });
  progress = {};
  session = null;
  updateMenuStats();
}

// ── keyboard ──────────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (document.getElementById('quiz').style.display === 'none') return;
  if (e.key === 'Enter' || e.key === 'ArrowRight') {
    const btn = document.getElementById('btn-action');
    if (!btn.disabled) handleAction();
  } else if (e.key === 'ArrowLeft') {
    if (!document.getElementById('btn-prev').disabled) prevQ();
  } else {
    const k = e.key.toUpperCase();
    if (/^[A-G]$/.test(k)) toggleOpt(k);
  }
});

document.getElementById('rand-count').addEventListener('keydown', e => {
  if (e.key === 'Enter') startRandom();
  if (e.key === 'Escape') closeModal();
});

// ── shutdown ──────────────────────────────────────────────────────────────
async function shutdown() {
  if (!confirm('Ukončit MTCNA Quiz server?')) return;
  document.body.innerHTML = '<div style="text-align:center;padding:80px;font-family:sans-serif"><h2>Server zastaven.</h2><p style="color:#6b7280">Zavři tuto záložku.</p></div>';
  try { await fetch('/shutdown', { method: 'POST' }); } catch {}
}

init();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/sources")
def api_sources():
    srcs = list_sources()
    default = "complete_all" if "complete_all" in srcs else ("mtcna_questions" if "mtcna_questions" in srcs else (srcs[0] if srcs else ""))
    return jsonify({"sources": srcs, "default": default})

@app.route("/api/questions")
def api_questions():
    source = request.args.get("source", "mtcna_questions")
    try:
        return jsonify(load_questions(source))
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route("/api/progress", methods=["GET"])
def api_progress_get():
    source = request.args.get("source", "mtcna_questions")
    data = load_progress()
    return jsonify(data.get(source, {"seen": {}, "session": None}))

@app.route("/api/progress", methods=["POST"])
def api_progress_post():
    source = request.args.get("source", "mtcna_questions")
    payload = request.get_json()
    data = load_progress()
    data[source] = payload
    save_progress(data)
    return jsonify({"ok": True})

@app.route("/shutdown", methods=["POST"])
def shutdown_route():
    def _kill():
        import time; time.sleep(0.2); os._exit(0)
    threading.Thread(target=_kill, daemon=True).start()
    return "bye"

if __name__ == "__main__":
    threading.Timer(0.8, lambda: webbrowser.open("http://127.0.0.1:5050")).start()
    print("MTCNA Quiz → http://127.0.0.1:5050")
    app.run(port=5050, debug=False)
