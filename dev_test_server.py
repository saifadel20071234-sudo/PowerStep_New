"""
dev_test_server.py
===================
Standalone dashboard demo server: replays your own historical CSVs into
the dashboard bridge directly, without needing main_system.py, real
hardware, or the AI models at all. Useful for showing the dashboard UI
off quickly. Do NOT run this at the same time as main_system.py — they
both use port 8000.

ADAPTED FROM THE ORIGINAL FILE — what changed and why:
  1. PATH STRUCTURE: the original computed
     `ROOT = dirname(dirname(__file__))` because the teammate's copy of
     this file lived in `backend/`, two levels below the frontend files.
     Your project is flat — this file and `dashboard_frontend/` are
     siblings — so ROOT now just points at `./dashboard_frontend`
     directly (one level, not two).
  2. DATA FILES: the original pointed at
     `C:\\Users\\Adel\\Desktop\\الداتا\\...`, which only exists on the
     teammate's machine. Replaced with the equivalent files that are
     already in your own "data cleaning and AI models/" folder (see the
     three paths below — <<< EDIT HERE if you'd rather replay different
     files >>>).
  3. PORT: the original ran on port 8001, but `dashboard_frontend/app.js`
     hardcodes port 8000 for both its WebSocket and its fetch() calls
     (see app.js lines 5 and 372). Loading the page from port 8001 while
     this server also listens on 8001 meant the browser's JS would still
     try to reach a *different* port than the one serving it, and never
     connect. Fixed by running this server on port 8000 instead — no
     frontend edits needed. (This is exactly why it must not run
     alongside main_system.py: both now claim port 8000.)
  4. ANALYTICS: the original never called `bridge.set_db(...)`, so the
     Analytics page would stay empty even after running
     import_data.py/import_data2.py. Added that wiring below so Analytics
     reflects whatever's already in runtime_data/powerstep_system.db.
"""

import csv
import json
import os
import sys
import threading
import time
from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS

import config
from database_manager import DatabaseManager

# <<< EDIT HERE if you'd rather replay different historical files. >>>
UNI_CSV = config.MODELS_DIR / "university_simulated_week.csv"
WIFI_CSV = config.MODELS_DIR / "wifi_dataset (3).csv"
PIEZO_JSON_CSV = config.MODELS_DIR / "live_piezo_data_json.csv"

ROOT = Path(__file__).resolve().parent / "dashboard_frontend"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dashboard_bridge import get_bridge


def load_wifi(path: Path) -> list[dict]:
    rows = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    p = json.loads(row["data"])
                    p["ts"] = row.get("ts", "")
                    rows.append(p)
                except Exception:
                    continue
    return rows


def load_uni(path: Path) -> list[dict]:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    return []


def load_piezo(path: Path) -> list[dict]:
    rows = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    p = json.loads(row["JSON_Data"])
                    p["timestamp"] = row.get("Timestamp", "")
                    rows.append(p)
                except Exception:
                    continue
    return rows


app = Flask(__name__, static_folder=str(ROOT), static_url_path="")
CORS(app)
bridge = get_bridge()
bridge.attach(app)
# NOTE: the original file never called set_db(), so the Analytics page
# would stay empty even after running import_data.py/import_data2.py.
# Wiring it up here means Analytics reflects whatever's already in
# runtime_data/powerstep_system.db.
bridge.set_db(DatabaseManager())


@app.route("/")
def index():
    return send_from_directory(str(ROOT), "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(str(ROOT), path)


def feed() -> None:
    wifi, uni, piezo = load_wifi(WIFI_CSV), load_uni(UNI_CSV), load_piezo(PIEZO_JSON_CSV)
    print(f"Loaded {len(wifi)} wifi_dataset rows, {len(uni)} university_simulated_week rows, "
          f"{len(piezo)} live_piezo_data_json rows.")
    wi = fi = pi = 0
    while True:
        if piezo:
            bridge.on_piezo(piezo[pi % len(piezo)])
            pi += 1
        if uni:
            row = uni[fi % len(uni)]
            bridge.on_wifi({
                "people_count": int(float(row.get("people_count", 0))),
                "device_count_raw": int(float(row.get("device_count_raw", 0))),
                "csi_variance": float(row.get("csi_variance", 0)),
            })
            if not piezo:
                bridge.on_piezo({
                    "tile_id": f"Tile_{(fi % 16) + 1}",
                    "voltage": float(row.get("piezo_voltage", 0)),
                    "avg_watt": float(row.get("piezo_avg_watt", 0)),
                    "step_status": "PRESSED" if float(row.get("people_count", 0)) > 0 else "IDLE",
                })
            fi += 1
        if wifi:
            bridge.on_wifi(wifi[wi % len(wifi)])
            wi += 1
        time.sleep(0.5)


if __name__ == "__main__":
    threading.Thread(target=feed, daemon=True).start()
    app.run(host="127.0.0.1", port=8000, threaded=True)
