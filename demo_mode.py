"""
demo_mode.py
=============
وضع العرض التجريبي (DEMO MODE) - نسخة احتياطية للعرض أمام اللجنة.

✅ يشتغل بشكل مستقل تماماً عن main_system.py
✅ لا يلمس أي ملف في المشروع الأصلي
✅ يفتح نفس الداش بورد بالضبط لكن ببيانات وهمية واقعية
✅ يُغلق ببساطة بالضغط على Ctrl+C

طريقة الاستخدام:
    python demo_mode.py
أو اضغط مرتين على Start_DEMO.bat
"""

import json
import math
import random
import threading
import time
import logging

from flask import Flask, jsonify, request, Response
from flask_sock import Sock
from flask_cors import CORS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DEMO] %(message)s"
)
logger = logging.getLogger("demo_mode")

app = Flask(__name__)
CORS(app)
sock = Sock(app)

# =====================================================
# State المشترك بين كل الـ Threads
# =====================================================
state = {
    "is_pressed": False,
    "press_count": 0,
    "cumulative_wh": 12.5,
    "start_time": time.time(),
    "history": [],
    "soc": 75.0,
    "wifi_people": 3,
}
state_lock = threading.Lock()
ws_clients = set()
ws_lock = threading.Lock()


# =====================================================
# محرك المحاكاة — يعمل في الخلفية
# =====================================================
def simulation_engine():
    """يولد بيانات وهمية واقعية باستمرار."""
    step_active = False
    step_end_time = 0
    wifi_update_counter = 0

    while True:
        now = time.time()

        # --- محاكاة ضغطات عشوائية على البيزو ---
        if not step_active and random.random() < 0.35:
            step_active = True
            step_end_time = now + random.uniform(0.4, 1.8)

        if step_active and now > step_end_time:
            step_active = False

        with state_lock:
            state["is_pressed"] = step_active

            if step_active:
                state["press_count"] += 1
                voltage = random.uniform(2.2, 3.3)
                current = voltage / 950.0
                gen_w = voltage * current * 4.0   # Boost للعرض
                state["cumulative_wh"] += gen_w / 36000.0
                state["soc"] = min(100.0, state["soc"] + 0.003)
            else:
                gen_w = 0.0
                state["soc"] = max(60.0, state["soc"] - 0.001)

            # تحديث عدد الأشخاص كل 5 ثوانٍ
            wifi_update_counter += 1
            if wifi_update_counter >= 25:  # 25 × 0.2s = 5s
                wifi_update_counter = 0
                state["wifi_people"] = random.randint(2, 8)

            # حفظ في الـ History للرسم البياني
            uptime = int(now - state["start_time"])
            t_hours = time.localtime().tm_hour + time.localtime().tm_min / 60.0
            if len(state["history"]) == 0 or t_hours != state["history"][-1]["t"]:
                live_gen = gen_w if step_active else random.uniform(1.5, 3.5)
                live_foot = state["press_count"] % 10 if step_active else random.randint(1, 4)
                state["history"].append({
                    "t": round(t_hours, 2),
                    "gen_wh": round(live_gen, 4),
                    "con_wh": round(random.uniform(4.5, 6.0), 2),
                    "soc_wh": round(state["soc"], 1),
                    "footfall": live_foot,
                })
                if len(state["history"]) > 5000:
                    state["history"].pop(0)

        time.sleep(0.2)


def build_snapshot():
    """يبني الـ JSON payload بنفس شكل الـ API الحقيقي تماماً."""
    with state_lock:
        pressed = state["is_pressed"]
        cumulative = state["cumulative_wh"]
        soc = state["soc"]
        people = state["wifi_people"]
        uptime_sec = int(time.time() - state["start_time"])

    if pressed:
        voltage = random.uniform(2.2, 3.3)
        current = voltage / 950.0
        gen_w = voltage * current * 4.0
    else:
        voltage = 0.0
        current = 0.0
        gen_w = 0.0

    uptime_str = "{:02d}:{:02d}:{:02d}".format(
        uptime_sec // 3600, (uptime_sec % 3600) // 60, uptime_sec % 60
    )

    tiles = []
    for i in range(1, 17):
        tiles.append({
            "id": i,
            "stepped_on": pressed,
            "efficiency_pct": round(random.uniform(95.0, 100.0), 1),
        })

    footfall = random.randint(3, 9) if pressed else 0
    con_w = 5.0
    self_suff = min(100.0, (gen_w / con_w) * 100.0) if gen_w > 0 else 0.0

    return {
        "day": 1,
        "sim_time": time.strftime("%H:%M:%S"),
        "generation_w": round(gen_w, 4),
        "consumption_w": round(con_w, 4),
        "forecast_w": round(gen_w * 1.05, 4),
        "self_sufficiency_pct": round(self_suff, 1) if gen_w > 0 else None,
        "storage_soc_pct": round(soc, 1),
        "power_source": "harvested",
        "footfall": footfall,
        "voltage_v": round(voltage, 4),
        "current_a": round(current, 6),
        "system_uptime": uptime_str,
        "battery_temperature": round(random.uniform(28.0, 35.0), 1),
        "cumulative_gen_wh": round(cumulative, 4),
        "cumulative_con_wh": 0.0,
        "co2_saved_grams": round(cumulative * 0.4, 2),
        "cost_saved": round(cumulative * 0.5, 2),
        "exported_wh": None,
        "ai_status": {"forecast_model": "Online", "anomaly_model": "Online"},
        "loads": {
            "load_1": {"name": "إضاءة A", "state": "ON" if pressed else "OFF"},
            "load_2": {"name": "إضاءة B", "state": "ON" if soc > 70 else "OFF"},
            "load_3": {"name": "مكيف",   "state": "OFF"},
        },
        "alerts": [],
        "tiles": tiles,
    }


# =====================================================
# WebSocket Broadcaster
# =====================================================
def broadcast_loop():
    while True:
        try:
            payload = json.dumps(build_snapshot(), ensure_ascii=False)
            with ws_lock:
                dead = set()
                for ws in ws_clients:
                    try:
                        ws.send(payload)
                    except Exception:
                        dead.add(ws)
                ws_clients.difference_update(dead)
        except Exception:
            pass
        time.sleep(0.2)


@sock.route("/ws/live")
def ws_live(ws):
    with ws_lock:
        ws_clients.add(ws)
    try:
        while True:
            time.sleep(1)
    except Exception:
        pass
    finally:
        with ws_lock:
            ws_clients.discard(ws)


# =====================================================
# REST Endpoints (نفس API الحقيقي)
# =====================================================
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "powerstep-DEMO-mode"})


@app.route("/api/ingest", methods=["POST"])
def ingest():
    return jsonify({"status": "ok"}), 200


@app.route("/api/history", methods=["GET"])
def api_history():
    with state_lock:
        hist = list(state["history"])
    return jsonify({
        "t": [h["t"] for h in hist],
        "gen_wh": [h["gen_wh"] for h in hist],
        "con_wh": [h["con_wh"] for h in hist],
        "footfall": [h["footfall"] for h in hist],
    })


@app.route("/api/analytics/summary", methods=["GET"])
def api_analytics():
    with state_lock:
        hist = list(state["history"])
    if not hist:
        return jsonify({
            "total_records": 0, "peak_generation_wh": 0, "peak_consumption_wh": 0,
            "avg_footfall": 0, "recent_data": [], "total_generation_wh": 0, "heatmap_data": []
        })
    peak_gen = max(h["gen_wh"] for h in hist)
    avg_foot = sum(h["footfall"] for h in hist) / len(hist)
    recent = [
        {"sim_hour": h["t"], "gen_wh": h["gen_wh"], "con_wh": h["con_wh"],
         "soc_wh": h["soc_wh"], "footfall": h["footfall"]}
        for h in hist[-40:]
    ]
    heatmap = [[random.randint(0, 50) for _ in range(24)] for _ in range(7)]
    return jsonify({
        "total_records": len(hist),
        "peak_generation_wh": round(peak_gen, 2),
        "total_generation_wh": round(peak_gen * len(hist), 2),
        "peak_consumption_wh": 6.0,
        "avg_footfall": round(avg_foot, 2),
        "recent_data": recent,
        "heatmap_data": heatmap,
    })


@app.route("/api/analytics/daily", methods=["GET"])
def api_analytics_daily():
    today = time.strftime("%Y-%m-%d")
    hours = [f"{i:02d}:00" for i in range(24)]
    gen = [round(random.uniform(2.0, 5.0) if 8 <= i <= 18 else random.uniform(0.5, 1.5), 2) for i in range(24)]
    foot = [random.randint(5, 20) if 8 <= i <= 18 else random.randint(0, 3) for i in range(24)]
    con = [round(5.0 + f * 1.5, 2) for f in foot]
    soc = [round(70 + math.sin(i / 3.8) * 10, 1) for i in range(24)]
    return jsonify({
        "days": [today],
        "selected_date": today,
        "data": {"hours": hours, "gen_wh": gen, "con_wh": con, "soc_wh": soc, "footfall": foot}
    })


@app.route("/api/export/csv", methods=["GET"])
def api_export():
    import csv, io
    with state_lock:
        hist = list(state["history"])
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["sim_hour", "generation_wh", "consumption_wh", "soc_pct", "footfall"])
    for h in hist:
        w.writerow([h["t"], h["gen_wh"], h["con_wh"], h["soc_wh"], h["footfall"]])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=demo_records.csv"})


@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify({"status": "ok", "mode": "DEMO", "note": "Fake data — for presentation only"})


# =====================================================
# Entry Point
# =====================================================
if __name__ == "__main__":
    logger.info("=" * 55)
    logger.info("  ⚡ PowerStep DEMO MODE — Starting...")
    logger.info("  📊 Dashboard: http://localhost:5500")
    logger.info("  🔌 Backend:   http://localhost:8000")
    logger.info("  ℹ️  Press Ctrl+C to stop")
    logger.info("=" * 55)

    threading.Thread(target=simulation_engine, daemon=True, name="SimEngine").start()
    threading.Thread(target=broadcast_loop,   daemon=True, name="Broadcaster").start()

    app.run(host="0.0.0.0", port=8000, threaded=True)
