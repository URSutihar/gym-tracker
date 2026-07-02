import sys
import os
from datetime import date

# Add parent directory to path to import db
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from db.db_utils import get_or_create_day, execute_query

def main():
    print("--- Log Daily Metrics ---")
    date_str = input(f"Enter date (YYYY-MM-DD) [default today {date.today()}]: ").strip()
    if not date_str:
        date_str = str(date.today())

    day_id = get_or_create_day(date_str)

    notes = input("Any notes for the day? ")
    rpe = input("Overall RPE (1-10)? ")
    rpe = int(rpe) if rpe.isdigit() else None
    
    gym_minutes = input("Gym minutes? ")
    gym_minutes = int(gym_minutes) if gym_minutes.isdigit() else None
    
    execute_query(
        "UPDATE days SET notes = ?, overall_rpe = ?, gym_minutes = ? WHERE id = ?",
        (notes, rpe, gym_minutes, day_id)
    )

    print("\n--- Body Metrics ---")
    weight = input("Weight (kg)? ")
    if weight:
        execute_query(
            "INSERT INTO body_metrics (day_id, weight) VALUES (?, ?) "
            "ON CONFLICT(day_id) DO UPDATE SET weight=excluded.weight",
            (day_id, float(weight))
        )

    print("\n--- Sleep ---")
    sleep_minutes = input("Total sleep minutes? ")
    if sleep_minutes:
        sleep_minutes = int(sleep_minutes)
        notes = input("Sleep notes? ")
        execute_query(
            "INSERT INTO sleep_logs (day_id, total_sleep_minutes, notes) VALUES (?, ?, ?) ON CONFLICT(day_id) DO UPDATE SET total_sleep_minutes=excluded.total_sleep_minutes, notes=excluded.notes",
            (day_id, sleep_minutes, notes)
        )

    print("\n--- Activity ---")
    steps = input("Steps? ")
    if steps:
        steps = int(steps)
        execute_query(
            "INSERT INTO activity_logs (day_id, steps) VALUES (?, ?) ON CONFLICT(day_id) DO UPDATE SET steps=excluded.steps",
            (day_id, steps)
        )

    print("\nDay logged successfully!")

if __name__ == "__main__":
    main()
