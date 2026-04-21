import pandas as pd
import sqlite3
import os
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gym_log.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

# ---------------------------------------------------------------------------
# Core queries
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def get_days_data():
    query = """
    SELECT
        d.date,
        d.overall_rpe,
        d.gym_minutes,
        b.weight as morning_weight,
        s.total_sleep_minutes,
        a.steps,
        COALESCE(ds.total_calories, 0) as total_calories,
        COALESCE(ds.total_protein, 0) as total_protein,
        COALESCE(ds.total_carbs, 0) as total_carbs,
        COALESCE(ds.total_fat, 0) as total_fat,
        COALESCE(ds.total_fiber, 0) as total_fiber
    FROM days d
    LEFT JOIN body_metrics b ON d.id = b.day_id
    LEFT JOIN sleep_logs s ON d.id = s.day_id
    LEFT JOIN activity_logs a ON d.id = a.day_id
    LEFT JOIN daily_summary ds ON d.id = ds.day_id
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)
    return df

@st.cache_data(ttl=60)
def get_exercise_progression(exercise_name):
    """Max weight per day for a given exercise. 0 on rest/non-exercise days."""
    query = """
    SELECT
        d.date,
        COALESCE(MAX(s.weight), 0) as max_weight
    FROM days d
    LEFT JOIN workouts w ON d.id = w.day_id
    LEFT JOIN exercise_entries e ON w.id = e.workout_id AND e.exercise_name = ?
    LEFT JOIN exercise_sets s ON e.id = s.exercise_entry_id
    GROUP BY d.date
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params=(exercise_name,))
    return df

@st.cache_data(ttl=60)
def get_all_exercise_names():
    query = "SELECT DISTINCT exercise_name FROM exercise_entries ORDER BY exercise_name"
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)
    return df['exercise_name'].tolist()

@st.cache_data(ttl=60)
def get_exercise_summary_timeseries():
    """Max weight per exercise per day. 0-filled on rest days."""
    query = """
    SELECT
        d.date,
        e.exercise_name,
        MAX(s.weight) as max_weight
    FROM days d
    LEFT JOIN workouts w ON d.id = w.day_id
    LEFT JOIN exercise_entries e ON w.id = e.workout_id
    LEFT JOIN exercise_sets s ON e.id = s.exercise_entry_id
    WHERE e.exercise_name IS NOT NULL
    GROUP BY d.date, e.exercise_name
    ORDER BY d.date ASC, e.exercise_name ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)

    if df.empty:
        return df
    all_dates = pd.read_sql_query(
        "SELECT date FROM days ORDER BY date ASC", get_db_connection()
    )['date'].tolist()
    all_exercises = df['exercise_name'].unique().tolist()
    idx = pd.MultiIndex.from_product([all_dates, all_exercises], names=['date', 'exercise_name'])
    out = df.set_index(['date', 'exercise_name']).reindex(idx).reset_index()
    out['max_weight'] = out['max_weight'].fillna(0)
    return out

@st.cache_data(ttl=60)
def get_recent_activity():
    query = """
    SELECT
        d.date,
        COALESCE(a.steps, 0) as steps,
        COALESCE(a.exercise_minutes, 0) as exercise_minutes,
        COALESCE(a.move_calories, 0) as move_calories,
        COALESCE(a.distance_km, 0) as distance_km
    FROM days d
    LEFT JOIN activity_logs a ON d.id = a.day_id
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)
    return df.reset_index(drop=True)

@st.cache_data(ttl=60)
def get_daily_calories():
    query = """
    SELECT d.date, COALESCE(SUM(m.calories), 0) as total_calories
    FROM days d
    LEFT JOIN meals m ON d.id = m.day_id
    GROUP BY d.date
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data(ttl=60)
def get_daily_protein():
    query = """
    SELECT d.date, COALESCE(SUM(m.protein), 0) as total_protein
    FROM days d
    LEFT JOIN meals m ON d.id = m.day_id
    GROUP BY d.date
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data(ttl=60)
def get_weight_with_moving_avg():
    """Single daily weight with 7-day rolling average."""
    query = """
    SELECT d.date, b.weight
    FROM days d
    LEFT JOIN body_metrics b ON d.id = b.day_id
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)
    df = df.dropna(subset=['weight'])
    if df.empty:
        return df
    df['weight_7d_ma'] = df['weight'].rolling(window=7, min_periods=1).mean()
    return df

@st.cache_data(ttl=60)
def get_workout_volume():
    """SUM(weight * reps) per exercise per day. 0-filled on rest days."""
    query = """
    SELECT
        d.date,
        e.exercise_name,
        COALESCE(SUM(s.weight * s.reps), 0) as total_volume
    FROM days d
    LEFT JOIN workouts w ON d.id = w.day_id
    LEFT JOIN exercise_entries e ON w.id = e.workout_id
    LEFT JOIN exercise_sets s ON e.id = s.exercise_entry_id
    WHERE e.exercise_name IS NOT NULL
    GROUP BY d.date, e.exercise_name
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)

    if df.empty:
        return df
    all_dates = pd.read_sql_query(
        "SELECT date FROM days ORDER BY date ASC", get_db_connection()
    )['date'].tolist()
    all_exercises = df['exercise_name'].unique().tolist()
    idx = pd.MultiIndex.from_product([all_dates, all_exercises], names=['date', 'exercise_name'])
    out = df.set_index(['date', 'exercise_name']).reindex(idx).reset_index()
    out['total_volume'] = out['total_volume'].fillna(0)
    return out

# ---------------------------------------------------------------------------
# New queries
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def get_sleep_hr_data():
    """Heart rate min/max per day from sleep logs."""
    query = """
    SELECT
        d.date,
        s.hr_min,
        s.hr_max,
        (s.hr_max - s.hr_min) as hr_range
    FROM days d
    INNER JOIN sleep_logs s ON d.id = s.day_id
    WHERE s.hr_min IS NOT NULL OR s.hr_max IS NOT NULL
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data(ttl=60)
def get_cardio_sessions():
    """Total duration, distance, and avg speed per cardio exercise per day."""
    query = """
    SELECT
        d.date,
        cl.name,
        SUM(cl.duration_min) as total_duration_min,
        SUM(cl.distance_km) as total_distance_km,
        AVG(cl.speed_kmh) as avg_speed_kmh
    FROM days d
    INNER JOIN cardio_logs cl ON d.id = cl.day_id
    GROUP BY d.date, cl.name
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data(ttl=60)
def get_personal_records():
    """Current max weight per exercise and the date it was achieved."""
    query = """
    SELECT
        e.exercise_name,
        MAX(s.weight) as pr_weight_kg,
        d.date as pr_date
    FROM exercise_sets s
    INNER JOIN exercise_entries e ON s.exercise_entry_id = e.id
    INNER JOIN workouts w ON e.workout_id = w.id
    INNER JOIN days d ON w.day_id = d.id
    WHERE s.unit = 'kg' AND s.weight IS NOT NULL
    GROUP BY e.exercise_name
    ORDER BY e.exercise_name ASC
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data(ttl=60)
def get_pr_history(exercise_name):
    """Dates when a new PR was set for a given exercise."""
    query = """
    SELECT d.date, MAX(s.weight) as max_weight_kg
    FROM exercise_sets s
    INNER JOIN exercise_entries e ON s.exercise_entry_id = e.id
    INNER JOIN workouts w ON e.workout_id = w.id
    INNER JOIN days d ON w.day_id = d.id
    WHERE e.exercise_name = ? AND s.unit = 'kg' AND s.weight IS NOT NULL
    GROUP BY d.date
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params=(exercise_name,))
    if df.empty:
        return df
    # Keep only rows where a new PR was actually set
    df['is_pr'] = df['max_weight_kg'].cummax() == df['max_weight_kg']
    df['prev_max'] = df['max_weight_kg'].cummax().shift(1).fillna(0)
    df = df[df['max_weight_kg'] > df['prev_max']].drop(columns=['is_pr', 'prev_max'])
    return df

@st.cache_data(ttl=60)
def get_weekly_summary():
    """Per-week aggregations: gym days, avg weight, avg sleep, total steps, avg protein."""
    query = """
    SELECT
        strftime('%Y-W%W', d.date) as week,
        MIN(date(d.date, '-' || ((strftime('%w', d.date) + 6) % 7) || ' days')) as week_start,
        COUNT(DISTINCT CASE WHEN d.gym_minutes > 0 THEN d.id END) as gym_days,
        SUM(d.gym_minutes) as total_gym_minutes,
        AVG(b.weight) as avg_weight_kg,
        AVG(s.total_sleep_minutes) as avg_sleep_minutes,
        SUM(a.steps) as total_steps,
        AVG(ds.total_protein) as avg_protein_g,
        AVG(ds.total_calories) as avg_calories
    FROM days d
    LEFT JOIN body_metrics b ON d.id = b.day_id
    LEFT JOIN sleep_logs s ON d.id = s.day_id
    LEFT JOIN activity_logs a ON d.id = a.day_id
    LEFT JOIN daily_summary ds ON d.id = ds.day_id
    GROUP BY week
    ORDER BY week ASC
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data(ttl=60)
def get_sleep_workout_correlation():
    """Sleep hours vs next-day RPE and workout volume for scatter analysis."""
    query = """
    SELECT
        d.date,
        ROUND(s.total_sleep_minutes / 60.0, 2) as sleep_hours,
        lead_d.overall_rpe as next_day_rpe,
        COALESCE(vol.total_volume, 0) as next_day_volume
    FROM days d
    INNER JOIN sleep_logs s ON d.id = s.day_id
    INNER JOIN days lead_d ON lead_d.date = date(d.date, '+1 day')
    LEFT JOIN (
        SELECT w.day_id, SUM(es.weight * es.reps) as total_volume
        FROM workouts w
        INNER JOIN exercise_entries ee ON w.id = ee.workout_id
        INNER JOIN exercise_sets es ON ee.id = es.exercise_entry_id
        GROUP BY w.day_id
    ) vol ON lead_d.id = vol.day_id
    WHERE s.total_sleep_minutes IS NOT NULL AND lead_d.overall_rpe IS NOT NULL
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data(ttl=60)
def get_nutrition_trends():
    """Daily macro totals for nutrition trends chart."""
    query = """
    SELECT
        d.date,
        COALESCE(ds.total_calories, 0) as total_calories,
        COALESCE(ds.total_protein, 0) as total_protein,
        COALESCE(ds.total_carbs, 0) as total_carbs,
        COALESCE(ds.total_fat, 0) as total_fat,
        COALESCE(ds.total_fiber, 0) as total_fiber
    FROM days d
    LEFT JOIN daily_summary ds ON d.id = ds.day_id
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)
