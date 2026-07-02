"""
One-time migration (Jul 2026): collapse exercise names to movement level.

- Clears exercise_aliases and reseeds from seed_aliases.ALIASES
- Renames every exercise_entries row through the alias map
- Fills empty equipment from the old "(Equipment)" name suffix
- Normalizes equipment spellings (e.g. "smith machine" -> "smith_machine")

Idempotent: re-running changes nothing once names are canonical.
"""
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
from db.db_utils import get_connection
import seed_aliases

EQUIPMENT_HINTS = {
    "barbell": "barbell", "fixed bar": "barbell",
    "dumbbell": "dumbbell",
    "ez bar": "ez_bar",
    "smith machine": "smith_machine",
    "machine": "machine",
    "cable crossover": "cable", "cable": "cable",
    "kettlebell": "kettlebell",
    "plate": "other",
    "rod": "cable",
    "bodyweight": "bodyweight",
}

EQUIPMENT_NORMALIZE = {"smith machine": "smith_machine"}

MUSCLE_NORMALIZE = {
    "rear_delts": "rear delts",
    "abs": "core",
    "obliques": "core",
    "brachioradialis": "forearms",
}


def infer_equipment(old_name):
    m = re.search(r"\(([^)]+)\)\s*$", old_name)
    hint = (m.group(1) if m else old_name).lower()
    for key, equip in EQUIPMENT_HINTS.items():
        if key in hint:
            return equip
    return None


def main():
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM exercise_aliases")
        seed_aliases.seed(conn)
        aliases = dict(conn.execute(
            "SELECT alias, canonical_name FROM exercise_aliases").fetchall())

        rows = conn.execute(
            "SELECT id, exercise_name, equipment, muscle_group FROM exercise_entries").fetchall()
        renamed = equipped = 0
        for eid, name, equipment, muscle in rows:
            new_name = aliases.get(name.lower(), name)
            new_equip = EQUIPMENT_NORMALIZE.get((equipment or "").lower(), equipment)
            if not new_equip:
                new_equip = infer_equipment(name)
            new_muscle = MUSCLE_NORMALIZE.get((muscle or "").lower(), muscle)
            if new_name != name or new_equip != equipment or new_muscle != muscle:
                conn.execute(
                    "UPDATE exercise_entries SET exercise_name=?, equipment=?, muscle_group=? WHERE id=?",
                    (new_name, new_equip, new_muscle, eid))
                renamed += new_name != name
                equipped += new_equip != equipment

    distinct = conn.execute(
        "SELECT COUNT(DISTINCT exercise_name) FROM exercise_entries").fetchone()[0]
    print(f"Renamed {renamed} entries, updated equipment on {equipped}.")
    print(f"Distinct exercise names now: {distinct}")
    leftovers = conn.execute("""
        SELECT DISTINCT exercise_name FROM exercise_entries
        WHERE exercise_name LIKE '%(%' ORDER BY 1""").fetchall()
    if leftovers:
        print("Still suffixed (add aliases for these):")
        for (n,) in leftovers:
            print(f"  - {n}")
    conn.close()


if __name__ == "__main__":
    main()
