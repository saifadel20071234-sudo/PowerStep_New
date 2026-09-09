"""
import_data2.py
================
Second backfill pass, for the two piezo CSV shapes the first script
(import_data.py) doesn't cover. Inserts directly into `piezo_readings`
(bypassing the AI models, since these two files don't carry the raw
Voltage/Power columns the piezo model needs in every row) — good enough
to populate the Analytics page's history/heatmap.

ADAPTED FROM THE ORIGINAL FILE — what changed and why:
  - Original hardcoded the DB path to
    r"C:\\Users\\Adel\\Desktop\\dashboard\\backend\\runtime_data\\powerstep_system.db".
    Replaced with `config.DB_PATH`, so it always writes to the exact same
    database file main_system.py itself uses — no risk of silently
    writing to a DB the running system never reads from.
  - Original df1 read a one-off file named "media_1788728343337.csv" that
    only exists in the teammate's IDE upload cache. Its columns
    (timestamp, piezo_avg_watt, people_count) are an EXACT match for
    your own `university_simulated_week_1st.csv` (the file the whole
    project already treats as the primary reference), so df1 now reads
    that instead.
  - Original df2 read "media_1788728343260.csv" (Timestamp, Power (W),
    SOC (%), Step Status). Those columns are an EXACT match for your own
    `GP.csv`, so df2 now reads that instead.

<<< EDIT HERE if you'd rather import different/additional files — just
change the two `pd.read_csv(...)` paths below. Both currently point at
files already sitting in your "data cleaning and AI models/" folder. >>>
"""

import sqlite3

import pandas as pd

import config


def import_csvs() -> None:
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    count = 0

    # --- Source 1: university_simulated_week_1st.csv ---
    # columns: timestamp, hour, minute, day_of_week, people_count,
    #          csi_variance, piezo_voltage, piezo_avg_watt
    try:
        df1 = pd.read_csv(config.PRIMARY_TRAINING_CSV)
        for _, row in df1.iterrows():
            ts = str(row["timestamp"]).replace(" ", "T")
            gen = float(row["piezo_avg_watt"])
            foot = int(row["people_count"])
            soc = 80.0  # not present in this file — mocked, matches original script's approach

            cursor.execute(
                """
                INSERT INTO piezo_readings (received_at, generation_w, storage_soc_pct, footfall)
                VALUES (?, ?, ?, ?)
                """,
                (ts, gen, soc, foot),
            )
            count += 1
    except Exception as exc:
        print(f"Error importing {config.PRIMARY_TRAINING_CSV.name}: {exc}")

    # --- Source 2: GP.csv ---
    # columns: Timestamp, Sim Time, Uptime, Voltage (V), Current (A),
    #          Power (W), Cumulative Gen (Wh), SOC (%), Power Source, Step Status
    try:
        gp_path = config.MODELS_DIR / "GP.csv"
        df2 = pd.read_csv(gp_path)
        for _, row in df2.iterrows():
            ts = str(row["Timestamp"]).replace(" ", "T")
            gen = float(row["Power (W)"])
            soc = float(row["SOC (%)"])
            foot = 1 if row["Step Status"] == "PRESSED" else 0

            cursor.execute(
                """
                INSERT INTO piezo_readings (received_at, generation_w, storage_soc_pct, footfall)
                VALUES (?, ?, ?, ?)
                """,
                (ts, gen, soc, foot),
            )
            count += 1
    except Exception as exc:
        print(f"Error importing GP.csv: {exc}")

    conn.commit()
    conn.close()
    print(f"Successfully inserted {count} records into piezo_readings.")


if __name__ == "__main__":
    import_csvs()
