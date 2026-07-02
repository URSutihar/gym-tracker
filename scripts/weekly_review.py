"""
Print a weekly training/nutrition review from gym_log.db.

Usage:
    python3 scripts/weekly_review.py             # 7-day window ending at latest logged day
    python3 scripts/weekly_review.py 2026-06-28  # 7-day window ending at given date

Compares the window against the previous 7 days and all-time history (for PRs).
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
from db.db_utils import get_connection
import tdee as tdee_mod


def daterange(end, days=7):
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def fmt(val, nd=1):
    return "-" if val is None else f"{val:.{nd}f}"


def main():
    conn = get_connection()

    if len(sys.argv) > 1:
        end = date.fromisoformat(sys.argv[1])
    else:
        row = conn.execute("SELECT MAX(date) FROM days").fetchone()
        if not row or not row[0]:
            print("No data in DB.")
            return
        end = date.fromisoformat(row[0])

    cur_start, cur_end = daterange(end)
    prev_start, prev_end = daterange(end - timedelta(days=7))

    print(f"# Weekly review: {cur_start} to {cur_end}")
    print(f"(compared with {prev_start} to {prev_end})\n")

    # --- Body weight ---
    def weight_stats(start, stop):
        return conn.execute(
            "SELECT AVG(bm.weight), MIN(d.date), MAX(d.date), COUNT(bm.weight) "
            "FROM body_metrics bm JOIN days d ON bm.day_id = d.id "
            "WHERE d.date BETWEEN ? AND ? AND bm.weight IS NOT NULL",
            (start, stop)).fetchone()

    w_cur = weight_stats(cur_start, cur_end)
    w_prev = weight_stats(prev_start, prev_end)
    print("## Body weight")
    if w_cur[3]:
        delta = (w_cur[0] - w_prev[0]) if w_prev[0] else None
        print(f"- This week avg: {fmt(w_cur[0], 2)} kg ({w_cur[3]} readings)")
        print(f"- Last week avg: {fmt(w_prev[0], 2)} kg"
              + (f"  (change {delta:+.2f} kg)" if delta is not None else ""))
    else:
        print("- No weight readings this week.")
    print()

    # --- Energy balance (empirical, in logged-calorie units) ---
    eb = tdee_mod.compute(cur_end)
    print("## Energy balance (empirical TDEE, logged-calorie units)")
    if eb and eb.get("tdee"):
        print(f"- TDEE (21d): {eb['tdee']:,.0f} kcal/day")
        if eb["intake_7d"] is not None:
            print(f"- 7d avg intake: {eb['intake_7d']:,.0f} kcal -> avg deficit "
                  f"{eb['tdee'] - eb['intake_7d']:+,.0f} kcal/day (positive = losing)")
        print("- Note: same-unit comparison with logged meals; do NOT mix with Apple Watch numbers.")
    else:
        print("- Not enough history for empirical TDEE.")
    print()

    # --- Sleep ---
    def sleep_avg(start, stop):
        return conn.execute(
            "SELECT AVG(s.total_sleep_minutes), COUNT(*) "
            "FROM sleep_logs s JOIN days d ON s.day_id = d.id "
            "WHERE d.date BETWEEN ? AND ?", (start, stop)).fetchone()

    s_cur, s_prev = sleep_avg(cur_start, cur_end), sleep_avg(prev_start, prev_end)
    print("## Sleep")
    if s_cur[1]:
        print(f"- This week avg: {s_cur[0] / 60:.1f} h/night ({s_cur[1]} nights)")
        if s_prev[1]:
            print(f"- Last week avg: {s_prev[0] / 60:.1f} h/night")
    else:
        print("- No sleep logs this week.")
    print()

    # --- Nutrition ---
    def macro_avgs(start, stop):
        return conn.execute(
            "SELECT COUNT(DISTINCT d.id), SUM(m.calories), SUM(m.protein), "
            "SUM(m.carbs), SUM(m.fat), SUM(m.fiber) "
            "FROM meals m JOIN days d ON m.day_id = d.id "
            "WHERE d.date BETWEEN ? AND ?", (start, stop)).fetchone()

    n_cur, n_prev = macro_avgs(cur_start, cur_end), macro_avgs(prev_start, prev_end)
    print("## Nutrition (daily averages over logged days)")
    if n_cur[0]:
        days_n = n_cur[0]
        print(f"- Days with meals logged: {days_n}")
        labels = ["Calories", "Protein (g)", "Carbs (g)", "Fat (g)", "Fiber (g)"]
        for i, label in enumerate(labels, start=1):
            cur_v = n_cur[i] / days_n if n_cur[i] else None
            prev_v = n_prev[i] / n_prev[0] if n_prev[0] and n_prev[i] else None
            line = f"- {label}: {fmt(cur_v, 0)}"
            if prev_v is not None and cur_v is not None:
                line += f"  (last week {prev_v:.0f}, {cur_v - prev_v:+.0f})"
            print(line)
    else:
        print("- No meals logged this week.")
    print()

    # --- Training volume per muscle group ---
    def volume(start, stop):
        rows = conn.execute(
            "SELECT ee.muscle_group, SUM(es.weight * es.reps), COUNT(es.id) "
            "FROM exercise_sets es "
            "JOIN exercise_entries ee ON es.exercise_entry_id = ee.id "
            "JOIN workouts w ON ee.workout_id = w.id "
            "JOIN days d ON w.day_id = d.id "
            "WHERE d.date BETWEEN ? AND ? AND es.weight IS NOT NULL "
            "GROUP BY ee.muscle_group", (start, stop)).fetchall()
        return {r[0]: (r[1], r[2]) for r in rows}

    v_cur, v_prev = volume(cur_start, cur_end), volume(prev_start, prev_end)
    sessions = conn.execute(
        "SELECT COUNT(*) FROM workouts w JOIN days d ON w.day_id = d.id "
        "WHERE d.date BETWEEN ? AND ?", (cur_start, cur_end)).fetchone()[0]
    print(f"## Training ({sessions} workout(s) this week)")
    if v_cur:
        for mg in sorted(v_cur, key=lambda k: -v_cur[k][0]):
            vol, sets = v_cur[mg]
            prev_vol = v_prev.get(mg, (0, 0))[0]
            change = f", {vol - prev_vol:+.0f} vs last week" if prev_vol else ""
            print(f"- {mg or 'unspecified'}: {vol:.0f} kg·reps across {sets} sets{change}")
    else:
        print("- No lifting sets this week.")
    print()

    # --- PRs: exercises whose top set weight this week beats all-time before the window ---
    prs = conn.execute(
        "WITH this_week AS ("
        "  SELECT ee.exercise_name AS name, MAX(es.weight) AS w "
        "  FROM exercise_sets es "
        "  JOIN exercise_entries ee ON es.exercise_entry_id = ee.id "
        "  JOIN workouts wo ON ee.workout_id = wo.id "
        "  JOIN days d ON wo.day_id = d.id "
        "  WHERE d.date BETWEEN ? AND ? GROUP BY ee.exercise_name), "
        "history AS ("
        "  SELECT ee.exercise_name AS name, MAX(es.weight) AS w "
        "  FROM exercise_sets es "
        "  JOIN exercise_entries ee ON es.exercise_entry_id = ee.id "
        "  JOIN workouts wo ON ee.workout_id = wo.id "
        "  JOIN days d ON wo.day_id = d.id "
        "  WHERE d.date < ? GROUP BY ee.exercise_name) "
        "SELECT t.name, t.w, h.w FROM this_week t "
        "LEFT JOIN history h ON t.name = h.name "
        "WHERE h.w IS NULL OR t.w > h.w ORDER BY t.name",
        (cur_start, cur_end, cur_start)).fetchall()
    print("## PRs (top-set weight)")
    if prs:
        for name, new_w, old_w in prs:
            if old_w is None:
                print(f"- {name}: first time logged, top set {new_w:.1f} kg")
            else:
                print(f"- {name}: {new_w:.1f} kg (previous best {old_w:.1f} kg)")
    else:
        print("- None this week.")
    print()

    # --- Cardio ---
    cardio = conn.execute(
        "SELECT c.name, COUNT(DISTINCT c.day_id), SUM(c.duration_min), SUM(c.distance_km) "
        "FROM cardio_logs c JOIN days d ON c.day_id = d.id "
        "WHERE d.date BETWEEN ? AND ? GROUP BY c.name", (cur_start, cur_end)).fetchall()
    print("## Cardio")
    if cardio:
        for name, n_days, mins, km in cardio:
            dist = f", {km:.1f} km" if km else ""
            print(f"- {name}: {n_days} day(s), {mins:.0f} min{dist}")
    else:
        print("- None this week.")
    print()

    # --- Activity ---
    act = conn.execute(
        "SELECT AVG(a.steps), AVG(a.move_calories), AVG(a.exercise_minutes), COUNT(*) "
        "FROM activity_logs a JOIN days d ON a.day_id = d.id "
        "WHERE d.date BETWEEN ? AND ?", (cur_start, cur_end)).fetchone()
    print("## Activity (daily averages)")
    if act[3]:
        print(f"- Steps: {fmt(act[0], 0)}, Move: {fmt(act[1], 0)} kcal, "
              f"Exercise: {fmt(act[2], 0)} min ({act[3]} days)")
    else:
        print("- No activity logs this week.")

    conn.close()


if __name__ == "__main__":
    main()
