"""
import_data.py
===============
Backfills piezo_readings / wifi_readings from historical CSVs that are
already sitting in your "data cleaning and AI models/" folder, so the
dashboard (especially the Analytics page) has something to show before
real hardware has streamed enough live data.

ADAPTED FROM THE ORIGINAL FILE — what changed and why:
  - Original hardcoded: glob.glob(r"C:\\Users\\Adel\\.gemini\\antigravity-ide\\...")
    That path only exists on the teammate's machine. Replaced with
    `config.MODELS_DIR` (i.e. your own "data cleaning and AI models/"
    folder) so it works on any machine that has this project.
  - Narrowed the glob to `wifi_dataset*.csv` specifically, because those
    are the only files in this project using the generic
    {"source": ..., "data": "<json>", "ts": ...} shape this script parses.
    (GP.csv / live_piezo_data_json.csv use a different shape — see
    import_data2.py for those.)
  - Uses `import config` (like every other file in this project) instead
    of a manual sys.path hack, for consistency.

If you ever get another CSV in the same {source, data, ts} shape
(including one with source == "piezo"), just drop it into
"data cleaning and AI models/" — the glob below will pick it up
automatically, no code change needed.
"""

import glob
import json

import pandas as pd

import config
from database_manager import DatabaseManager
from realtime_inference import InferenceEngine


def import_all() -> None:
    db = DatabaseManager()
    engine = InferenceEngine()

    # <<< EDIT HERE if your historical CSVs live somewhere else or under a
    # different naming pattern. Defaults to every wifi_dataset*.csv already
    # in your "data cleaning and AI models/" folder. >>>
    csv_files = glob.glob(str(config.MODELS_DIR / "wifi_dataset*.csv"))

    if not csv_files:
        print(f"No matching CSVs found under {config.MODELS_DIR}")
        return

    total_piezo = 0
    total_wifi = 0

    for file in csv_files:
        print(f"Processing {file} ...")
        try:
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                source = row["source"]
                try:
                    raw = json.loads(row["data"])
                    ts = row.get("ts")

                    if source == "piezo":
                        record = engine.process_piezo_reading(raw)
                        if ts:
                            record["received_at"] = str(ts).replace(" ", "T")
                        db.insert_piezo_reading(record)
                        total_piezo += 1
                    elif source in ("wifi_occupancy", "wifi"):
                        record = engine.process_wifi_reading(raw)
                        if ts:
                            record["received_at"] = str(ts).replace(" ", "T")
                        db.insert_wifi_reading(record)
                        total_wifi += 1
                except Exception:
                    # skip malformed rows rather than aborting the whole import
                    pass
        except Exception as exc:
            print(f"Failed to read {file}: {exc}")

    print(f"Done! Imported {total_piezo} piezo readings and {total_wifi} wifi readings.")


if __name__ == "__main__":
    import_all()
