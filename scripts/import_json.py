"""
Import a standardized daily JSON log into gym_log.db.

Usage:
    python scripts/import_json.py day.json
    cat day.json | python scripts/import_json.py -

The script is idempotent: running it twice for the same date produces the same result.
All weights must be in kg in the JSON. Any lbs values are auto-converted if the legacy
'weight_lbs' key is present (backward compatibility).

JSON schema: see .claude/plans/radiant-cooking-puffin.md or the SCHEMA_EXAMPLE below.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from db.db_utils import get_connection

LBS_TO_KG = 0.453592

SCHEMA_EXAMPLE = {
    "date": "2026-03-26",
    "notes": "Felt strong today",
    "overall_rpe": 7.5,
    "gym_minutes": 60,
    "body_metrics": {"weight_kg": 78.2},
    "sleep": {"total_sleep_minutes": 452, "hr_min": 48, "hr_max": 112, "notes": None},
    "activity": {
        "move_calories": 720, "exercise_minutes": 85,
        "stand_hours": 11, "steps": 13450, "distance_km": 9.1
    },
    "workout": {
        "duration_minutes": 60,
        "notes": None,
        "exercises": [
            {
                "type": "lifting",
                "name": "Bicep Curl (Machine)",
                "muscle_group": "biceps",
                "equipment": "machine",
                "pain_flag": False,
                "sets": [{"set": 1, "weight_kg": 9.07, "reps": 10}]
            },
            {
                "type": "cardio",
                "name": "Treadmill",
                "muscle_group": "cardio",
                "equipment": "treadmill",
                "pain_flag": False,
                "intervals": [{"interval": 1, "speed_kmh": 6.0, "duration_min": 2.0, "incline_pct": 0}]
            }
        ]
    },
    "meals": [
        {
            "meal_type": "breakfast",
            "description": "Oats with banana",
            "calories": 420, "protein_g": 35, "carbs_g": 55, "fat_g": 8, "fiber_g": 6,
            "is_estimated": True, "foods": None
        }
    ]
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def lbs_to_kg(val):
    return round(val * LBS_TO_KG, 2) if val is not None else None


def load_aliases(conn):
    rows = conn.execute("SELECT alias, canonical_name FROM exercise_aliases").fetchall()
    return {r[0].lower(): r[1] for r in rows}


def normalize_exercise_name(name, aliases):
    return aliases.get(name.lower(), name)


# ---------------------------------------------------------------------------
# Upsert helpers (all operate inside the caller's transaction)
# ---------------------------------------------------------------------------

def upsert_day(conn, data):
    existing = conn.execute("SELECT id FROM days WHERE date = ?", (data['date'],)).fetchone()
    if existing:
        conn.execute(
            "UPDATE days SET notes=?, overall_rpe=?, gym_minutes=? WHERE id=?",
            (data.get('notes'), data.get('overall_rpe'), data.get('gym_minutes'), existing[0])
        )
        return existing[0]
    else:
        cur = conn.execute(
            "INSERT INTO days (date, notes, overall_rpe, gym_minutes) VALUES (?, ?, ?, ?)",
            (data['date'], data.get('notes'), data.get('overall_rpe'), data.get('gym_minutes'))
        )
        return cur.lastrowid


def upsert_body_metrics(conn, day_id, bm):
    if not bm:
        return
    weight = bm.get('weight_kg')
    # backward compat: accept weight_lbs
    if weight is None and bm.get('weight_lbs') is not None:
        weight = lbs_to_kg(bm['weight_lbs'])
        print("  Warning: weight_lbs found, converting to kg")
    conn.execute(
        "INSERT INTO body_metrics (day_id, weight) VALUES (?, ?) "
        "ON CONFLICT(day_id) DO UPDATE SET weight=excluded.weight",
        (day_id, weight)
    )


def upsert_sleep(conn, day_id, slp):
    if not slp:
        return
    conn.execute(
        "INSERT INTO sleep_logs (day_id, total_sleep_minutes, hr_min, hr_max, notes) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(day_id) DO UPDATE SET "
        "total_sleep_minutes=excluded.total_sleep_minutes, "
        "hr_min=excluded.hr_min, hr_max=excluded.hr_max, notes=excluded.notes",
        (day_id, slp.get('total_sleep_minutes'), slp.get('hr_min'),
         slp.get('hr_max'), slp.get('notes'))
    )


def upsert_activity(conn, day_id, act):
    if not act:
        return
    conn.execute(
        "INSERT INTO activity_logs (day_id, move_calories, exercise_minutes, stand_hours, steps, distance_km) "
        "VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(day_id) DO UPDATE SET "
        "move_calories=excluded.move_calories, exercise_minutes=excluded.exercise_minutes, "
        "stand_hours=excluded.stand_hours, steps=excluded.steps, distance_km=excluded.distance_km",
        (day_id, act.get('move_calories'), act.get('exercise_minutes'),
         act.get('stand_hours'), act.get('steps'), act.get('distance_km'))
    )


def upsert_workout(conn, day_id, wo, aliases):
    if not wo:
        return

    # Delete existing workout(s) for this day — cascades to exercise_entries + exercise_sets
    existing_workout_ids = [
        r[0] for r in conn.execute("SELECT id FROM workouts WHERE day_id=?", (day_id,)).fetchall()
    ]
    for wid in existing_workout_ids:
        entry_ids = [
            r[0] for r in conn.execute(
                "SELECT id FROM exercise_entries WHERE workout_id=?", (wid,)
            ).fetchall()
        ]
        for eid in entry_ids:
            conn.execute("DELETE FROM exercise_sets WHERE exercise_entry_id=?", (eid,))
        conn.execute("DELETE FROM exercise_entries WHERE workout_id=?", (wid,))
    conn.execute("DELETE FROM workouts WHERE day_id=?", (day_id,))

    # Delete existing cardio for this day
    conn.execute("DELETE FROM cardio_logs WHERE day_id=?", (day_id,))

    # Insert new workout
    cur = conn.execute(
        "INSERT INTO workouts (day_id, duration_minutes, notes) VALUES (?, ?, ?)",
        (day_id, wo.get('duration_minutes'), wo.get('notes'))
    )
    workout_id = cur.lastrowid

    for ex in wo.get('exercises', []):
        name = normalize_exercise_name(ex['name'], aliases)
        ex_type = ex.get('type', 'lifting')

        if ex_type == 'cardio':
            for interval in ex.get('intervals', []):
                conn.execute(
                    "INSERT INTO cardio_logs "
                    "(day_id, name, interval_number, duration_min, speed_kmh, distance_km, incline_pct) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        day_id, name,
                        interval.get('interval'),
                        interval.get('duration_min'),
                        interval.get('speed_kmh'),
                        interval.get('distance_km'),
                        interval.get('incline_pct', 0)
                    )
                )
        else:  # lifting
            cur = conn.execute(
                "INSERT INTO exercise_entries (workout_id, exercise_name, muscle_group, equipment, pain_flag) "
                "VALUES (?, ?, ?, ?, ?)",
                (workout_id, name, ex.get('muscle_group'), ex.get('equipment'),
                 1 if ex.get('pain_flag') else 0)
            )
            entry_id = cur.lastrowid

            for s in ex.get('sets', []):
                weight = s.get('weight_kg')
                # backward compat
                if weight is None and s.get('weight_lbs') is not None:
                    weight = lbs_to_kg(s['weight_lbs'])
                conn.execute(
                    "INSERT INTO exercise_sets (exercise_entry_id, set_number, weight, reps, unit) "
                    "VALUES (?, ?, ?, ?, 'kg')",
                    (entry_id, s.get('set'), weight, s.get('reps'))
                )


def upsert_meals(conn, day_id, meals):
    if not meals:
        return

    # Delete existing meals + foods for this day
    existing_meal_ids = [
        r[0] for r in conn.execute("SELECT id FROM meals WHERE day_id=?", (day_id,)).fetchall()
    ]
    for mid in existing_meal_ids:
        conn.execute("DELETE FROM foods WHERE meal_id=?", (mid,))
    conn.execute("DELETE FROM meals WHERE day_id=?", (day_id,))

    for meal in meals:
        cur = conn.execute(
            "INSERT INTO meals (day_id, meal_type, description, calories, protein, carbs, fat, fiber, is_estimated) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                day_id,
                meal.get('meal_type'),
                meal.get('description'),
                meal.get('calories'),
                meal.get('protein_g'),
                meal.get('carbs_g'),
                meal.get('fat_g'),
                meal.get('fiber_g'),
                1 if meal.get('is_estimated') else 0
            )
        )
        meal_id = cur.lastrowid

        for food in (meal.get('foods') or []):
            conn.execute(
                "INSERT INTO foods (meal_id, food_name, quantity, unit, calories, protein, carbs, fat, fiber) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    meal_id,
                    food.get('food_name'),
                    food.get('quantity'),
                    food.get('unit'),
                    food.get('calories'),
                    food.get('protein_g'),
                    food.get('carbs_g'),
                    food.get('fat_g'),
                    food.get('fiber_g')
                )
            )


def populate_daily_summary(conn, day_id):
    row = conn.execute(
        "SELECT SUM(calories), SUM(protein), SUM(carbs), SUM(fat), SUM(fiber) "
        "FROM meals WHERE day_id=?",
        (day_id,)
    ).fetchone()
    total_cal, total_prot, total_carbs, total_fat, total_fiber = row or (None,) * 5
    conn.execute(
        "INSERT INTO daily_summary (day_id, total_calories, total_protein, total_carbs, total_fat, total_fiber) "
        "VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(day_id) DO UPDATE SET "
        "total_calories=excluded.total_calories, total_protein=excluded.total_protein, "
        "total_carbs=excluded.total_carbs, total_fat=excluded.total_fat, total_fiber=excluded.total_fiber",
        (day_id, total_cal, total_prot, total_carbs, total_fat, total_fiber)
    )


# ---------------------------------------------------------------------------
# Main import
# ---------------------------------------------------------------------------

def register_new_exercises(conn, new_exercises):
    """Register new canonical exercises + aliases from the JSON new_exercises field.

    Each entry can be:
      { "canonical": "Deadlift (Barbell)", "aliases": ["deadlift", "barbell deadlift"] }
    or just a string:
      "Deadlift (Barbell)"   — registered as its own alias (lowercased)
    """
    if not new_exercises:
        return
    rows = []
    for entry in new_exercises:
        if isinstance(entry, str):
            rows.append((entry.lower(), entry))
        elif isinstance(entry, dict):
            canonical = entry.get('canonical', '')
            if canonical:
                rows.append((canonical.lower(), canonical))
                for alias in entry.get('aliases', []):
                    rows.append((alias.lower(), canonical))
    if rows:
        conn.executemany(
            "INSERT OR IGNORE INTO exercise_aliases (alias, canonical_name) VALUES (?, ?)",
            rows
        )
        print(f"  Registered {len(rows)} new exercise alias(es)")


def import_day(conn, data):
    # Register any new exercises declared in this log before processing workout
    register_new_exercises(conn, data.get('new_exercises'))
    aliases = load_aliases(conn)
    day_id = upsert_day(conn, data)
    upsert_body_metrics(conn, day_id, data.get('body_metrics'))
    upsert_sleep(conn, day_id, data.get('sleep'))
    upsert_activity(conn, day_id, data.get('activity'))
    upsert_workout(conn, day_id, data.get('workout'), aliases)
    upsert_meals(conn, day_id, data.get('meals'))
    populate_daily_summary(conn, day_id)
    return day_id


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_json.py <file.json | ->")
        print("  Use '-' to read from stdin")
        sys.exit(1)

    path = sys.argv[1]
    if path == '-':
        data = json.load(sys.stdin)
    else:
        with open(path) as f:
            data = json.load(f)

    if 'date' not in data:
        print("Error: JSON must contain a 'date' field (YYYY-MM-DD)")
        sys.exit(1)

    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        with conn:
            day_id = import_day(conn, data)
        print(f"Imported {data['date']} successfully (day_id={day_id})")
    except Exception as e:
        print(f"Import failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
