"""
Export days from gym_log.db to per-day JSON files in data/, in the same schema
that scripts/import_json.py consumes. Together they make the JSON files a
lossless, re-importable history of every logged day.

Usage:
    python3 scripts/export_days.py               # export ALL days (skips identical existing files)
    python3 scripts/export_days.py 2026-07-02    # export one day
    python3 scripts/export_days.py --force       # overwrite even if file exists and differs
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from db.db_utils import get_connection

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

BODY_METRIC_COLS = [
    "bmi", "body_fat_pct", "fat_mass_kg", "muscle_mass_kg",
    "skeletal_muscle_mass_kg", "body_water_pct", "bone_mineral_kg",
    "protein_mass_kg", "bmr_kcal", "visceral_fat", "body_age", "waist_hip_ratio",
]


def clean(d):
    """Drop None values so JSON files stay readable."""
    return {k: v for k, v in d.items() if v is not None}


def export_day(conn, day_row):
    day_id, date, notes, rpe, gym_minutes = day_row
    out = {"date": date}
    if notes is not None:
        out["notes"] = notes
    if rpe is not None:
        out["overall_rpe"] = rpe
    if gym_minutes is not None:
        out["gym_minutes"] = gym_minutes

    bm = conn.execute(
        f"SELECT weight, {', '.join(BODY_METRIC_COLS)} FROM body_metrics WHERE day_id=?",
        (day_id,)).fetchone()
    if bm:
        metrics = clean(dict(zip(["weight_kg"] + BODY_METRIC_COLS, bm)))
        if metrics:
            out["body_metrics"] = metrics

    slp = conn.execute(
        "SELECT total_sleep_minutes, hr_min, hr_max, notes FROM sleep_logs WHERE day_id=?",
        (day_id,)).fetchone()
    if slp:
        out["sleep"] = clean(dict(zip(
            ["total_sleep_minutes", "hr_min", "hr_max", "notes"], slp)))

    act = conn.execute(
        "SELECT move_calories, exercise_minutes, stand_hours, steps, distance_km "
        "FROM activity_logs WHERE day_id=?", (day_id,)).fetchone()
    if act:
        out["activity"] = clean(dict(zip(
            ["move_calories", "exercise_minutes", "stand_hours", "steps", "distance_km"], act)))

    # Workout: lifting entries + cardio intervals under one "workout" key
    exercises = []
    workout_row = conn.execute(
        "SELECT id, duration_minutes, notes FROM workouts WHERE day_id=?", (day_id,)).fetchone()
    if workout_row:
        wid, duration, wnotes = workout_row
        entries = conn.execute(
            "SELECT id, exercise_name, muscle_group, equipment, pain_flag "
            "FROM exercise_entries WHERE workout_id=? ORDER BY id", (wid,)).fetchall()
        for eid, name, mg, equip, pain in entries:
            sets = conn.execute(
                "SELECT set_number, weight, reps FROM exercise_sets "
                "WHERE exercise_entry_id=? ORDER BY set_number, id", (eid,)).fetchall()
            exercises.append(clean({
                "type": "lifting",
                "name": name,
                "muscle_group": mg,
                "equipment": equip,
                "pain_flag": bool(pain) if pain is not None else None,
                "sets": [clean({"set": s[0], "weight_kg": s[1], "reps": s[2]}) for s in sets],
            }))

    cardio_rows = conn.execute(
        "SELECT name, interval_number, duration_min, speed_kmh, distance_km, incline_pct, avg_hr "
        "FROM cardio_logs WHERE day_id=? ORDER BY name, interval_number, id", (day_id,)).fetchall()
    cardio_by_name = {}
    for name, interval, dur, speed, dist, incline, hr in cardio_rows:
        cardio_by_name.setdefault(name, []).append(clean({
            "interval": interval, "duration_min": dur, "speed_kmh": speed,
            "distance_km": dist, "incline_pct": incline, "avg_hr": hr,
        }))
    for name, intervals in cardio_by_name.items():
        exercises.append({
            "type": "cardio", "name": name,
            "muscle_group": "cardio", "intervals": intervals,
        })

    if workout_row or exercises:
        wo = {}
        if workout_row:
            if workout_row[1] is not None:
                wo["duration_minutes"] = workout_row[1]
            if workout_row[2] is not None:
                wo["notes"] = workout_row[2]
        wo["exercises"] = exercises
        out["workout"] = wo

    meal_rows = conn.execute(
        "SELECT id, meal_type, description, calories, protein, carbs, fat, fiber, is_estimated "
        "FROM meals WHERE day_id=? ORDER BY id", (day_id,)).fetchall()
    if meal_rows:
        meals = []
        for mid, mtype, desc, cal, prot, carbs, fat, fiber, est in meal_rows:
            meal = clean({
                "meal_type": mtype, "description": desc, "calories": cal,
                "protein_g": prot, "carbs_g": carbs, "fat_g": fat, "fiber_g": fiber,
                "is_estimated": bool(est),
            })
            food_rows = conn.execute(
                "SELECT food_name, quantity, unit, calories, protein, carbs, fat, fiber "
                "FROM foods WHERE meal_id=? ORDER BY id", (mid,)).fetchall()
            if food_rows:
                meal["foods"] = [clean(dict(zip(
                    ["food_name", "quantity", "unit", "calories",
                     "protein_g", "carbs_g", "fat_g", "fiber_g"], f))) for f in food_rows]
            meals.append(meal)
        out["meals"] = meals

    micro_cols = ["calcium_mg", "iron_mg", "zinc_mg", "b12_ug", "potassium_mg",
                  "sodium_mg", "vitamin_c_mg", "vitamin_d_ug", "omega3_g", "magnesium_mg"]
    micros = conn.execute(
        f"SELECT {', '.join(micro_cols)} FROM micros WHERE day_id=?", (day_id,)).fetchone()
    if micros:
        m = clean(dict(zip(micro_cols, micros)))
        if m:
            out["micros"] = m

    return out


def main():
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    conn = get_connection()
    if args:
        rows = conn.execute(
            "SELECT id, date, notes, overall_rpe, gym_minutes FROM days WHERE date=?",
            (args[0],)).fetchall()
        if not rows:
            print(f"No day found for {args[0]}")
            sys.exit(1)
    else:
        rows = conn.execute(
            "SELECT id, date, notes, overall_rpe, gym_minutes FROM days ORDER BY date").fetchall()

    written = skipped = 0
    for row in rows:
        out = export_day(conn, row)
        path = os.path.join(DATA_DIR, f"{row[1]}.json")
        new_content = json.dumps(out, indent=2, ensure_ascii=False) + "\n"
        if os.path.exists(path) and not force:
            with open(path) as f:
                if f.read() == new_content:
                    skipped += 1
                    continue
        with open(path, "w") as f:
            f.write(new_content)
        written += 1

    print(f"Exported {written} day(s), {skipped} unchanged, to {os.path.abspath(DATA_DIR)}")
    conn.close()


if __name__ == "__main__":
    main()
