"""
Seed exercise_aliases table with common name variations → canonical names.
Safe to run multiple times (uses INSERT OR IGNORE).
Add your own aliases to ALIASES below as you discover inconsistencies.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from db.db_utils import get_connection

# (alias, canonical_name)
# All aliases are stored lowercase for case-insensitive matching.
ALIASES = [
    # Bicep Curl
    ("bicep curl", "Bicep Curl (Machine)"),
    ("bicep curls", "Bicep Curl (Machine)"),
    ("curl machine", "Bicep Curl (Machine)"),
    ("machine curl", "Bicep Curl (Machine)"),
    ("curls", "Bicep Curl (Machine)"),
    ("dumbbell curl", "Bicep Curl (Dumbbell)"),
    ("db curl", "Bicep Curl (Dumbbell)"),
    ("barbell curl", "Bicep Curl (Barbell)"),
    ("bb curl", "Bicep Curl (Barbell)"),

    # Tricep
    ("tricep extension", "Tricep Extension (Machine)"),
    ("tricep extensions", "Tricep Extension (Machine)"),
    ("triceps extension", "Tricep Extension (Machine)"),
    ("tricep pushdown", "Tricep Pushdown (Cable)"),
    ("triceps pushdown", "Tricep Pushdown (Cable)"),
    ("cable pushdown", "Tricep Pushdown (Cable)"),

    # Chest / Pec
    ("pec fly", "Pec Fly (Machine)"),
    ("pec deck", "Pec Fly (Machine)"),
    ("chest fly", "Pec Fly (Machine)"),
    ("chest fly machine", "Pec Fly (Machine)"),
    ("fly machine", "Pec Fly (Machine)"),
    ("bench press", "Bench Press (Barbell)"),
    ("barbell bench press", "Bench Press (Barbell)"),
    ("bb bench press", "Bench Press (Barbell)"),
    ("dumbbell bench press", "Bench Press (Dumbbell)"),
    ("db bench press", "Bench Press (Dumbbell)"),

    # Back
    ("lat pulldown", "Lat Pulldown (Machine)"),
    ("lat pull down", "Lat Pulldown (Machine)"),
    ("pulldown", "Lat Pulldown (Machine)"),
    ("seated row", "Seated Row (Machine)"),
    ("cable row", "Seated Row (Machine)"),
    ("row machine", "Seated Row (Machine)"),

    # Legs
    ("leg press", "Leg Press"),
    ("squat", "Squat (Barbell)"),
    ("barbell squat", "Squat (Barbell)"),
    ("leg extension", "Leg Extension (Machine)"),
    ("leg extensions", "Leg Extension (Machine)"),
    ("leg curl", "Leg Curl (Machine)"),
    ("leg curls", "Leg Curl (Machine)"),
    ("hamstring curl", "Leg Curl (Machine)"),

    # Shoulders
    ("shoulder press", "Shoulder Press (Machine)"),
    ("shoulder press machine", "Shoulder Press (Machine)"),
    ("dumbbell shoulder press", "Shoulder Press (Dumbbell)"),
    ("db shoulder press", "Shoulder Press (Dumbbell)"),
    ("lateral raise", "Lateral Raise (Dumbbell)"),
    ("lateral raises", "Lateral Raise (Dumbbell)"),
    ("side raise", "Lateral Raise (Dumbbell)"),
    ("rear delt", "Rear Delt Machine"),
    ("rear delt fly", "Rear Delt Machine"),
    ("reverse fly", "Rear Delt Machine"),
    ("face pull", "Face Pull (Cable)"),

    # Abs
    ("ab crunch", "Abdominal Crunch (Machine)"),
    ("abs crunch", "Abdominal Crunch (Machine)"),
    ("abdominal crunch", "Abdominal Crunch (Machine)"),
    ("crunch machine", "Abdominal Crunch (Machine)"),

    # Tricep Pushdown variants (distinguish rope vs bar)
    ("tricep rope pushdown", "Tricep Rope Pushdown (Cable)"),
    ("rope pushdown", "Tricep Rope Pushdown (Cable)"),
    ("v bar pushdown", "Tricep Bar Pushdown (Cable)"),
    ("straight bar pushdown", "Tricep Bar Pushdown (Cable)"),
    ("tricep bar pushdown", "Tricep Bar Pushdown (Cable)"),
    ("cable pushdown", "Tricep Rope Pushdown (Cable)"),
    ("a/v rope pulldown", "Tricep Rope Pushdown (Cable)"),
    ("rope pulldown", "Tricep Rope Pushdown (Cable)"),

    # Cable Crossover
    ("cable crossover", "Cable Crossover"),
    ("cable fly", "Cable Crossover"),
    ("cable flyes", "Cable Crossover"),
    ("cable cross", "Cable Crossover"),

    # Overhead Tricep Extension
    ("overhead tricep extension", "Overhead Tricep Extension (Cable)"),
    ("overhead cable extension", "Overhead Tricep Extension (Cable)"),
    ("overhead rope extension", "Overhead Tricep Extension (Cable)"),
    ("cable overhead extension", "Overhead Tricep Extension (Cable)"),

    # Skull Crusher
    ("skull crusher", "Skull Crusher (Dumbbell)"),
    ("skull crushers", "Skull Crusher (Dumbbell)"),
    ("skullcrusher", "Skull Crusher (Dumbbell)"),
    ("lying tricep extension", "Skull Crusher (Dumbbell)"),

    # Deadlift
    ("deadlift", "Deadlift (Barbell)"),
    ("deadlifts", "Deadlift (Barbell)"),
    ("conventional deadlift", "Deadlift (Barbell)"),
    ("romanian deadlift", "Romanian Deadlift (Barbell)"),
    ("rdl", "Romanian Deadlift (Barbell)"),

    # Cardio
    ("treadmill", "Treadmill"),
    ("stationary bike", "Stationary Bike"),
    ("bike", "Stationary Bike"),
    ("rowing machine", "Rowing Machine"),
    ("rower", "Rowing Machine"),
]


def seed():
    conn = get_connection()
    with conn:
        conn.executemany(
            "INSERT OR IGNORE INTO exercise_aliases (alias, canonical_name) VALUES (?, ?)",
            ALIASES
        )
    print(f"Seeded {len(ALIASES)} exercise aliases.")
    conn.close()


if __name__ == '__main__':
    seed()
