"""
One-time backfill: populate daily_summary for all existing days.
Safe to run multiple times (uses upsert).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from db.db_utils import get_connection


def backfill():
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON")

    day_ids = [r[0] for r in conn.execute("SELECT id FROM days ORDER BY date").fetchall()]
    count = 0

    with conn:
        for day_id in day_ids:
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
            count += 1

    conn.close()
    print(f"Backfilled daily_summary for {count} days.")


if __name__ == '__main__':
    backfill()
