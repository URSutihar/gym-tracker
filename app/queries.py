import pandas as pd
import sqlite3
import os
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gym_log.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

# ---------------------------------------------------------------------------
# Existing queries (unchanged logic, added Streamlit caching)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def get_days_data():
    query = """
    SELECT 
        d.date, 
        d.overall_rpe, 
        d.gym_minutes,
        MAX(b.morning_weight) as morning_weight,
        MAX(s.total_sleep_minutes) as total_sleep_minutes,
        MAX(a.steps) as steps,
        COALESCE((SELECT SUM(calories) FROM meals WHERE day_id = d.id), 0) as total_calories,
        COALESCE((SELECT SUM(protein) FROM meals WHERE day_id = d.id), 0) as total_protein,
        COALESCE((SELECT SUM(carbs) FROM meals WHERE day_id = d.id), 0) as total_carbs,
        COALESCE((SELECT SUM(fat) FROM meals WHERE day_id = d.id), 0) as total_fat,
        COALESCE((SELECT SUM(fiber) FROM meals WHERE day_id = d.id), 0) as total_fiber
    FROM days d
    LEFT JOIN body_metrics b ON d.id = b.day_id
    LEFT JOIN sleep_logs s ON d.id = s.day_id
    LEFT JOIN activity_logs a ON d.id = a.day_id
    GROUP BY d.id
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
    query = "SELECT DISTINCT exercise_name FROM exercise_entries WHERE exercise_name != 'Treadmill' ORDER BY exercise_name"
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
      AND e.exercise_name != 'Treadmill'
    GROUP BY d.date, e.exercise_name
    ORDER BY d.date ASC, e.exercise_name ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)

    # Ensure every (date, exercise) combo exists; fill missing with 0
    if df.empty:
        return df
    all_dates = pd.read_sql_query("SELECT date FROM days ORDER BY date ASC", get_db_connection())['date'].tolist()
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

# ---------------------------------------------------------------------------
# New aggregation queries
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def get_daily_calories():
    """Sum of meal calories per day."""
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
    """Sum of meal protein per day."""
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
    """Morning weight with 7-day rolling average (pandas)."""
    query = """
    SELECT d.date, b.morning_weight as weight
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
      AND e.exercise_name != 'Treadmill'
    GROUP BY d.date, e.exercise_name
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)

    # 0-fill rest days
    if df.empty:
        return df
    all_dates = pd.read_sql_query("SELECT date FROM days ORDER BY date ASC", get_db_connection())['date'].tolist()
    all_exercises = df['exercise_name'].unique().tolist()
    idx = pd.MultiIndex.from_product([all_dates, all_exercises], names=['date', 'exercise_name'])
    out = df.set_index(['date', 'exercise_name']).reindex(idx).reset_index()
    out['total_volume'] = out['total_volume'].fillna(0)
    return out

@st.cache_data(ttl=60)
def get_soreness_matrix():
    """Pivot table: rows=date, columns=body_part, values=soreness_score."""
    query = """
    SELECT d.date, sl.body_part, sl.soreness_score
    FROM days d
    INNER JOIN soreness_logs sl ON d.id = sl.day_id
    ORDER BY d.date ASC
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)
    if df.empty:
        return df
    pivot = df.pivot_table(index='date', columns='body_part', values='soreness_score', aggfunc='max')
    return pivot
