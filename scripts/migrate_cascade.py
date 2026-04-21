"""
One-time migration: recreate tables with ON DELETE CASCADE foreign keys.
Run once against your existing gym_log.db.
Safe to run multiple times (checks if already migrated).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.db_utils import get_connection

MIGRATIONS = [
    # (table_name, create_sql, copy_columns)
    (
        "body_metrics",
        """CREATE TABLE body_metrics_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_id INTEGER UNIQUE REFERENCES days(id) ON DELETE CASCADE,
            weight REAL
        )""",
        # Copy only the weight column; consolidate morning_weight/pre/post into weight
        "SELECT id, day_id, COALESCE(morning_weight, pre_workout_weight, post_workout_weight, weight) FROM body_metrics",
        "INSERT INTO body_metrics_new (id, day_id, weight) VALUES (?, ?, ?)"
    ),
    (
        "sleep_logs",
        """CREATE TABLE sleep_logs_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_id INTEGER UNIQUE REFERENCES days(id) ON DELETE CASCADE,
            total_sleep_minutes INTEGER,
            hr_min INTEGER,
            hr_max INTEGER,
            notes TEXT
        )""",
        "SELECT id, day_id, total_sleep_minutes, hr_min, hr_max, notes FROM sleep_logs",
        "INSERT INTO sleep_logs_new (id, day_id, total_sleep_minutes, hr_min, hr_max, notes) VALUES (?, ?, ?, ?, ?, ?)"
    ),
    (
        "activity_logs",
        """CREATE TABLE activity_logs_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_id INTEGER UNIQUE REFERENCES days(id) ON DELETE CASCADE,
            move_calories REAL,
            exercise_minutes INTEGER,
            stand_hours INTEGER,
            steps INTEGER,
            distance_km REAL
        )""",
        "SELECT id, day_id, move_calories, exercise_minutes, stand_hours, steps, distance_km FROM activity_logs",
        "INSERT INTO activity_logs_new (id, day_id, move_calories, exercise_minutes, stand_hours, steps, distance_km) VALUES (?, ?, ?, ?, ?, ?, ?)"
    ),
    (
        "workouts",
        """CREATE TABLE workouts_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_id INTEGER REFERENCES days(id) ON DELETE CASCADE,
            duration_minutes INTEGER,
            notes TEXT
        )""",
        "SELECT id, day_id, duration_minutes, notes FROM workouts",
        "INSERT INTO workouts_new (id, day_id, duration_minutes, notes) VALUES (?, ?, ?, ?)"
    ),
    (
        "exercise_entries",
        """CREATE TABLE exercise_entries_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER REFERENCES workouts(id) ON DELETE CASCADE,
            exercise_name TEXT NOT NULL,
            muscle_group TEXT,
            equipment TEXT,
            pain_flag BOOLEAN
        )""",
        "SELECT id, workout_id, exercise_name, muscle_group, equipment, pain_flag FROM exercise_entries",
        "INSERT INTO exercise_entries_new (id, workout_id, exercise_name, muscle_group, equipment, pain_flag) VALUES (?, ?, ?, ?, ?, ?)"
    ),
    (
        "exercise_sets",
        """CREATE TABLE exercise_sets_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_entry_id INTEGER REFERENCES exercise_entries(id) ON DELETE CASCADE,
            set_number INTEGER,
            weight REAL,
            reps INTEGER,
            unit TEXT DEFAULT 'kg'
        )""",
        "SELECT id, exercise_entry_id, set_number, weight, reps, unit FROM exercise_sets",
        "INSERT INTO exercise_sets_new (id, exercise_entry_id, set_number, weight, reps, unit) VALUES (?, ?, ?, ?, ?, ?)"
    ),
    (
        "meals",
        """CREATE TABLE meals_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_id INTEGER REFERENCES days(id) ON DELETE CASCADE,
            meal_type TEXT,
            description TEXT,
            calories REAL,
            protein REAL,
            carbs REAL,
            fat REAL,
            fiber REAL,
            is_estimated BOOLEAN DEFAULT FALSE
        )""",
        "SELECT id, day_id, meal_type, description, calories, protein, carbs, fat, fiber, is_estimated FROM meals",
        "INSERT INTO meals_new (id, day_id, meal_type, description, calories, protein, carbs, fat, fiber, is_estimated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    ),
    (
        "foods",
        """CREATE TABLE foods_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_id INTEGER REFERENCES meals(id) ON DELETE CASCADE,
            food_name TEXT,
            quantity REAL,
            unit TEXT,
            calories REAL,
            protein REAL,
            carbs REAL,
            fat REAL,
            fiber REAL
        )""",
        "SELECT id, meal_id, food_name, quantity, unit, calories, protein, carbs, fat, fiber FROM foods",
        "INSERT INTO foods_new (id, meal_id, food_name, quantity, unit, calories, protein, carbs, fat, fiber) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    ),
    (
        "daily_summary",
        """CREATE TABLE daily_summary_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_id INTEGER UNIQUE REFERENCES days(id) ON DELETE CASCADE,
            total_calories REAL,
            total_protein REAL,
            total_carbs REAL,
            total_fat REAL,
            total_fiber REAL
        )""",
        "SELECT id, day_id, total_calories, total_protein, total_carbs, total_fat, total_fiber FROM daily_summary",
        "INSERT INTO daily_summary_new (id, day_id, total_calories, total_protein, total_carbs, total_fat, total_fiber) VALUES (?, ?, ?, ?, ?, ?, ?)"
    ),
]


def already_migrated(conn, table):
    """Check if table already has ON DELETE CASCADE by inspecting schema."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if row and row[0] and 'ON DELETE CASCADE' in row[0]:
        return True
    return False


def migrate():
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = OFF")

    for table, create_sql, select_sql, insert_sql in MIGRATIONS:
        if already_migrated(conn, table):
            print(f"  {table}: already migrated, skipping")
            continue

        print(f"  {table}: migrating...")
        with conn:
            rows = conn.execute(select_sql).fetchall()
            conn.execute(create_sql)
            conn.executemany(insert_sql, rows)
            conn.execute(f"DROP TABLE {table}")
            conn.execute(f"ALTER TABLE {table}_new RENAME TO {table}")
        print(f"  {table}: done ({len(rows)} rows)")

    # Create new tables and indexes from schema if not present
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()
    print("\nMigration complete.")


if __name__ == '__main__':
    print("Running migration...")
    migrate()
