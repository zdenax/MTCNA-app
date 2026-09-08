#!/usr/bin/env python3
"""MTCNA Quiz — network server (macOS / LAN).
Run this on Mac, access from iPhone on the same WiFi."""
import json
import socket
import webbrowser
import threading
import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string

BASE = Path(__file__).parent
PROGRESS_FILE = BASE / "progress.json"

app = Flask(__name__)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

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

# reuse same HTML as mtcna_web.py — import it
try:
    import importlib.util, sys as _sys
    _spec = importlib.util.spec_from_file_location("_web", BASE / "mtcna_web.py")
    _mod  = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    HTML = _mod.HTML
except Exception:
    HTML = "<h1>Error: mtcna_web.py not found next to this file.</h1>"

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

PORT = 5050

if __name__ == "__main__":
    ip = get_local_ip()
    url_local  = f"http://127.0.0.1:{PORT}"
    url_lan    = f"http://{ip}:{PORT}"

    print()
    print("=" * 48)
    print("  MTCNA Quiz — LAN server")
    print("=" * 48)
    print(f"  Lokálně (Mac):  {url_local}")
    print(f"  iPhone/jiná:    {url_lan}")
    print()
    print("  Na iPhonu otevři Safari a zadej:")
    print(f"  {url_lan}")
    print()

    # try to show QR in terminal (if qrcode installed)
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url_lan)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        print()
    except ImportError:
        pass

    print("  Ctrl+C pro zastavení")
    print("=" * 48)
    print()

    threading.Timer(0.8, lambda: webbrowser.open(url_local)).start()
    app.run(host="0.0.0.0", port=PORT, debug=False)
