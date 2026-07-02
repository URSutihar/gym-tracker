"""
Print the current empirical TDEE and recent deficit, computed from the
weight trend + logged intake.

Method (same as the dashboard's app/energy.py): meal calorie estimates carry
a systematic bias (restaurant oil, portion guesses), so TDEE is computed
empirically IN LOGGED-CALORIE UNITS:

    TDEE = mean logged intake over window - (trend_kg_change * 7700) / window_days

The bias cancels: eating N logged-kcal below this TDEE gives a real ~N kcal
deficit. Never compare these numbers with Apple Watch burn estimates.

Usage:
    python3 scripts/tdee.py              # as of latest logged day
    python3 scripts/tdee.py 2026-07-02   # as of a given date
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from db.db_utils import get_connection

KCAL_PER_KG = 7700
TREND_ALPHA = 0.10  # exponential smoothing of scale weight


def compute(cutoff="9999-12-31"):
    """Return dict with trend weight and TDEE windows as of cutoff (or None)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT d.date, bm.weight, ds.total_calories
        FROM days d
        LEFT JOIN body_metrics bm ON bm.day_id = d.id
        LEFT JOIN daily_summary ds ON ds.day_id = d.id
        WHERE d.date <= ? ORDER BY d.date
    """, (cutoff,)).fetchall()
    conn.close()
    if not rows:
        return None

    by_date = {date.fromisoformat(r[0]): (r[1], r[2]) for r in rows}
    start, end = min(by_date), max(by_date)
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    # trend weight: EMA carried across missing days
    trend, intake = {}, {}
    current = None
    for d in days:
        w, cal = by_date.get(d, (None, None))
        if w is not None:
            current = w if current is None else current + TREND_ALPHA * (w - current)
        trend[d] = current
        intake[d] = cal

    def tdee_at(t, window):
        t0 = t - timedelta(days=window)
        if trend.get(t) is None or trend.get(t0) is None:
            return None
        cals = [intake[t0 + timedelta(days=i + 1)] for i in range(window)
                if intake.get(t0 + timedelta(days=i + 1)) is not None]
        if len(cals) < max(5, int(window * 0.7)):
            return None
        return sum(cals) / len(cals) - (trend[t] - trend[t0]) * KCAL_PER_KG / window

    week = [intake[end - timedelta(days=i)] for i in range(7)
            if intake.get(end - timedelta(days=i)) is not None]
    headline = tdee_at(end, 21) or tdee_at(end, 14)
    return {
        "as_of": end,
        "trend_weight": trend[end],
        "tdee_14": tdee_at(end, 14),
        "tdee_21": tdee_at(end, 21),
        "tdee_28": tdee_at(end, 28),
        "tdee": headline,
        "intake_day": intake.get(end),
        "intake_7d": sum(week) / len(week) if week else None,
    }


def main():
    cutoff = sys.argv[1] if len(sys.argv) > 1 else "9999-12-31"
    r = compute(cutoff)
    if r is None:
        print("No data.")
        return
    print(f"As of {r['as_of']}:")
    if r["trend_weight"] is None:
        print("  No weight data yet.")
        return
    print(f"  Trend weight:    {r['trend_weight']:.2f} kg")
    for w in (14, 21, 28):
        v = r[f"tdee_{w}"]
        if v is not None:
            print(f"  TDEE ({w}d):      {v:,.0f} kcal/day (logged-calorie units)")
    if r["tdee"] is None:
        print("  Not enough history for empirical TDEE yet.")
        return
    if r["intake_day"] is not None:
        print(f"  Intake that day: {r['intake_day']:,.0f} kcal -> deficit {r['tdee'] - r['intake_day']:+,.0f} kcal vs 21d TDEE")
    if r["intake_7d"] is not None:
        print(f"  7d avg intake:   {r['intake_7d']:,.0f} kcal -> avg deficit {r['tdee'] - r['intake_7d']:+,.0f} kcal/day")
    print("  (Positive deficit = losing. Logged-unit numbers; do not compare with Apple Watch.)")


if __name__ == "__main__":
    main()
