import sys
import os
from datetime import date

# Add parent directory to path to import db
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from db.db_utils import get_or_create_day, execute_query, fetch_one

def main():
    print("--- Log a Workout ---")
    date_str = input(f"Enter date (YYYY-MM-DD) [default today {date.today()}]: ").strip()
    if not date_str:
        date_str = str(date.today())

    day_id = get_or_create_day(date_str)
    
    duration = input("Workout duration (minutes)? ")
    duration = int(duration) if duration.isdigit() else None
    notes = input("Workout notes? ")
    
    cursor = execute_query(
        "INSERT INTO workouts (day_id, duration_minutes, notes) VALUES (?, ?, ?)",
        (day_id, duration, notes)
    )
    workout_id = cursor.lastrowid
    print(f"Workout logged with ID: {workout_id}")

    while True:
        print("\n-- Add Exercise --")
        ex_name = input("Exercise name (or blank to finish workout): ").strip()
        if not ex_name:
            break
            
        muscle = input("Muscle group? ")
        
        cursor = execute_query(
            "INSERT INTO exercise_entries (workout_id, exercise_name, muscle_group) VALUES (?, ?, ?)",
            (workout_id, ex_name, muscle)
        )
        entry_id = cursor.lastrowid
        
        set_num = 1
        while True:
            print(f"  - Set {set_num} -")
            weight = input("    Weight (or blank to finish exercise): ")
            if not weight:
                break
                
            reps = input("    Reps: ")
            
            weight = float(weight) if weight else 0.0
            reps = int(reps) if reps.isdigit() else 0
            
            execute_query(
                "INSERT INTO exercise_sets (exercise_entry_id, set_number, weight, reps) VALUES (?, ?, ?, ?)",
                (entry_id, set_num, weight, reps)
            )
            set_num += 1

if __name__ == "__main__":
    main()
