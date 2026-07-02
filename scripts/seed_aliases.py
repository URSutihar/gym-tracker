"""
Seed exercise_aliases with name variations → canonical MOVEMENT names.

Canonical names are movement-level: no equipment suffix ("Bicep Curl", not
"Bicep Curl (Machine)"). Equipment belongs in exercise_entries.equipment.
Same movement done with different equipment or style logs under ONE name and
shares one PR history (user decision, Jul 3).

Safe to run multiple times (INSERT OR IGNORE). Add new variants here as they
appear in logs, then run: python3 scripts/seed_aliases.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from db.db_utils import get_connection

# (alias, canonical movement name) — aliases matched lowercase.
ALIASES = [
    # --- Chest ---
    ("bench press (barbell)", "Bench Press"),
    ("bench press (smith machine)", "Bench Press"),
    ("flat bench press", "Bench Press"),
    ("bench", "Bench Press"),
    ("incline bench press", "Incline Bench Press"),
    ("incline press (smith machine)", "Incline Bench Press"),
    ("incline press", "Incline Bench Press"),
    ("chest press (modified setup)", "Chest Press"),
    ("close grip flat chest press", "Chest Press"),
    ("pec fly (machine)", "Pec Fly"),
    ("pec deck", "Pec Fly"),
    ("cable crossover (lower chest)", "Cable Crossover"),
    ("cable crossover (middle chest)", "Cable Crossover"),
    ("cable fly", "Cable Crossover"),

    # --- Back ---
    ("lat pulldown (machine)", "Lat Pulldown"),
    ("cable rope lat pulldown", "Lat Pulldown"),
    ("close grip lat pulldown (machine)", "Lat Pulldown"),
    ("seated row (machine)", "Seated Row"),
    ("seated cable row (machine)", "Seated Row"),
    ("seated cable row", "Seated Row"),
    ("long pull 302", "Seated Row"),
    ("long pull", "Seated Row"),
    ("cable bent row", "Bent-Over Row"),
    ("cable bent-over row (cable)", "Bent-Over Row"),
    ("bent over row", "Bent-Over Row"),
    ("chest supported row (dumbbell)", "Chest Supported Row"),
    ("high incline shrug row (dumbbell)", "High Incline Shrug Row"),
    ("straight arm pulldown (cable)", "Straight Arm Pulldown"),
    ("barbell shrug", "Shrug"),
    ("shrugs", "Shrug"),
    ("back extension (machine)", "Back Extension"),
    ("deadlift (barbell)", "Deadlift"),
    ("deadlifts", "Deadlift"),
    ("conventional deadlift", "Deadlift"),
    ("romanian deadlift", "Romanian Deadlift"),
    ("rdl", "Romanian Deadlift"),

    # --- Shoulders ---
    ("shoulder press (dumbbell)", "Shoulder Press"),
    ("shoulder press (machine)", "Shoulder Press"),
    ("overhead press (barbell)", "Shoulder Press"),
    ("overhead press", "Shoulder Press"),
    ("ohp", "Shoulder Press"),
    ("dumbbell lateral raise", "Lateral Raise"),
    ("lateral raise (dumbbell)", "Lateral Raise"),
    ("lateral raises", "Lateral Raise"),
    ("front raise (dumbbell)", "Front Raise"),
    ("dumbbell front raise", "Front Raise"),
    ("front raises", "Front Raise"),
    ("overhead lu raise (dumbbell)", "Lu Raise"),
    ("lu raises", "Lu Raise"),
    ("rear delt machine", "Rear Delt Fly"),
    ("reverse fly", "Rear Delt Fly"),
    ("face pull (cable)", "Face Pull"),
    ("face pulls", "Face Pull"),
    ("upright row (barbell)", "Upright Row"),
    ("upright row (cable)", "Upright Row"),

    # --- Biceps ---
    ("bicep curl (machine)", "Bicep Curl"),
    ("bicep curl (dumbbell)", "Bicep Curl"),
    ("bicep curl (barbell)", "Bicep Curl"),
    ("bicep curl (ez bar)", "Bicep Curl"),
    ("bicep curl (fixed bar)", "Bicep Curl"),
    ("ez bar bicep curl", "Bicep Curl"),
    ("bicep curls", "Bicep Curl"),
    ("curls", "Bicep Curl"),
    ("db curl", "Bicep Curl"),
    ("bb curl", "Bicep Curl"),
    ("preacher curl (machine)", "Preacher Curl"),
    ("preacher curl (cable)", "Preacher Curl"),
    ("preacher curl (ez bar)", "Preacher Curl"),
    ("preacher curls", "Preacher Curl"),
    ("hammer curl (dumbbell)", "Hammer Curl"),
    ("hammer curl (cable)", "Hammer Curl"),
    ("hammer curl (cable crossover)", "Hammer Curl"),
    ("hammer curl (machine)", "Hammer Curl"),
    ("hammer curls", "Hammer Curl"),
    ("preacher hammer curl (dumbbell)", "Preacher Hammer Curl"),
    ("spider curl (dumbbell)", "Spider Curl"),
    ("spider curl (ez bar)", "Spider Curl"),
    ("spider curls", "Spider Curl"),

    # --- Triceps ---
    ("tricep extension (machine)", "Tricep Extension"),
    ("overhead tricep extension (cable)", "Tricep Extension"),
    ("overhead cable extension", "Tricep Extension"),
    ("overhead rope extension", "Tricep Extension"),
    ("cable overhead extension", "Tricep Extension"),
    ("tricep extensions", "Tricep Extension"),
    ("triceps extension", "Tricep Extension"),
    ("triceps pushdown", "Tricep Pushdown"),
    ("tricep rope pushdown (cable)", "Tricep Pushdown"),
    ("tricep bar pushdown (cable)", "Tricep Pushdown"),
    ("cable tricep push down", "Tricep Pushdown"),
    ("cable pulldown (tricep)", "Tricep Pushdown"),
    ("tricep pulldown (rod)", "Tricep Pushdown"),
    ("skull crusher (dumbbell)", "Skull Crusher"),
    ("skull crusher (ez bar)", "Skull Crusher"),
    ("skull crusher (plate)", "Skull Crusher"),
    ("skull crushers", "Skull Crusher"),
    ("skullcrusher", "Skull Crusher"),
    ("lying tricep extension", "Skull Crusher"),

    # --- Legs ---
    ("squat (barbell)", "Squat"),
    ("squats", "Squat"),
    ("kettlebell goblet squat (inner thigh focus)", "Goblet Squat"),
    ("45-degree leg press", "Leg Press"),
    ("horizontal leg press", "Leg Press"),
    ("leg press machine", "Leg Press"),
    ("leg extension (machine)", "Leg Extension"),
    ("leg extension machine", "Leg Extension"),
    ("seated leg extension", "Leg Extension"),
    ("leg extensions", "Leg Extension"),
    ("seated leg curl", "Leg Curl"),
    ("seated leg curl (machine)", "Leg Curl"),
    ("leg curls", "Leg Curl"),
    ("inner thigh (adductor)", "Hip Adduction"),
    ("adductor machine", "Hip Adduction"),
    ("outer thigh (abductor)", "Hip Abduction"),
    ("abductor machine", "Hip Abduction"),
    ("calf raises", "Seated Calf Raise"),

    # --- Core ---
    ("abdominal crunch (machine)", "Abdominal Crunch"),
    ("abdominal crunch machine", "Abdominal Crunch"),
    ("cable abdominal crunch", "Abdominal Crunch"),
    ("cable crunch", "Abdominal Crunch"),
    ("cable crunches", "Abdominal Crunch"),
    ("cable crunch crisscross", "Abdominal Crunch"),
    ("criss cross cable crunches", "Abdominal Crunch"),
    ("cable abdominal crunch criss cross", "Abdominal Crunch"),
    ("cable rope core pulldown (kneeling)", "Abdominal Crunch"),
    ("cable rope pulldown (standing)", "Abdominal Crunch"),
    ("crunches", "Abdominal Crunch"),
    ("reverse cable abdominal crunch", "Reverse Crunch"),
    ("reverse cable crunch", "Reverse Crunch"),
    ("reverse cable crunches", "Reverse Crunch"),
    ("cable anti-rotation hold", "Pallof Press"),
    ("cable anti-rotation pull (pallof variant)", "Pallof Press"),
    ("pallof", "Pallof Press"),
    ("leg raises", "Leg Raise"),

    # --- Forearms ---
    ("wrist curl (dumbbell)", "Wrist Curl"),
    ("wrist curls", "Wrist Curl"),
    ("wrist extension (dumbbell)", "Wrist Extension"),
    ("wrist extensions", "Wrist Extension"),

    # --- Cardio ---
    ("stationary bike", "Stationary Bike"),
    ("bike", "Stationary Bike"),
    ("rowing machine", "Rowing Machine"),
    ("rower", "Rowing Machine"),
]


def seed(conn):
    conn.executemany(
        "INSERT OR IGNORE INTO exercise_aliases (alias, canonical_name) VALUES (?, ?)",
        [(a.lower(), c) for a, c in ALIASES]
    )


if __name__ == '__main__':
    conn = get_connection()
    with conn:
        seed(conn)
    n = conn.execute("SELECT COUNT(*) FROM exercise_aliases").fetchone()[0]
    print(f"Alias table now has {n} entries.")
    conn.close()
