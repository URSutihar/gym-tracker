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
    m_weight = input("Morning weight? ")
    pre_weight = input("Pre-workout weight? ")
    post_weight = input("Post-workout weight? ")
    
    if any([m_weight, pre_weight, post_weight]):
        m_weight = float(m_weight) if m_weight else None
        pre_weight = float(pre_weight) if pre_weight else None
        post_weight = float(post_weight) if post_weight else None
        execute_query(
            "INSERT INTO body_metrics (day_id, morning_weight, pre_workout_weight, post_workout_weight) VALUES (?, ?, ?, ?) ON CONFLICT(day_id) DO UPDATE SET morning_weight=excluded.morning_weight, pre_workout_weight=excluded.pre_workout_weight, post_workout_weight=excluded.post_workout_weight",
            (day_id, m_weight, pre_weight, post_weight)
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

    print("\n--- Soreness ---")
    body_part = input("Body part? ")
    if body_part:
        score = input("Soreness score (1-10)? ")
        score = int(score) if score.isdigit() else None
        execute_query(
            "INSERT INTO soreness_logs (day_id, body_part, soreness_score) VALUES (?, ?, ?)",
            (day_id, body_part, score)
        )
    
    print("\nDay logged successfully!")

if __name__ == "__main__":
    main()
