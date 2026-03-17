import streamlit as st
import pandas as pd
from queries import (
    get_days_data,
    get_exercise_progression,
    get_all_exercise_names,
    get_recent_activity,
    get_exercise_summary_timeseries,
    get_daily_calories,
    get_daily_protein,
    get_weight_with_moving_avg,
    get_workout_volume,
)
import charts
import components
import os

st.set_page_config(page_title="Gym Tracker Dashboard", layout="wide", page_icon="🏋️")

def main():
    st.title("URS Progress Tracker")
    st.markdown("Gym & Fitness Tracker .")

    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gym_log.db')
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at {DB_PATH}. Please run `python db/init_db.py` first.")
        return

    # ── Load data ─────────────────────────────────────────────────────────
    try:
        days_df = get_days_data()
        exercises = get_all_exercise_names()
        recent_activity_df = get_recent_activity()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    if days_df.empty:
        st.warning("No data found. Use the CLI scripts in `scripts/` to log some days!")
        return

    # ══════════════════════════════════════════════════════════════════════
    #  OVERVIEW CARDS
    # ══════════════════════════════════════════════════════════════════════
    st.header("Overview")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    weight_data = days_df['morning_weight'].dropna()
    with col1:
        latest_weight = weight_data.iloc[-1] if not weight_data.empty else 0
        components.render_metric_card("Latest Weight", f"{latest_weight} kg")
    with col2:
        if len(weight_data) >= 2:
            delta = round(weight_data.iloc[-1] - weight_data.iloc[0], 1)
            sign = "+" if delta > 0 else ""
            components.render_metric_card("Weight Δ (Total)", f"{sign}{delta} kg")
        else:
            components.render_metric_card("Weight Δ (Total)", "—")
    with col3:
        today = days_df.iloc[-1]
        cal_today = int(today.get('total_calories', 0))
        components.render_metric_card("Calories Today", f"{cal_today} kcal")
    with col4:
        prot_today = int(today.get('total_protein', 0))
        components.render_metric_card("Protein Today", f"{prot_today} / 120g")
    with col5:
        steps_data = days_df['steps'].dropna()
        latest_steps = int(steps_data.iloc[-1]) if not steps_data.empty else 0
        components.render_metric_card("Latest Steps", f"{latest_steps}")
    with col6:
        sleep_data = days_df['total_sleep_minutes'].dropna()
        latest_sleep = sleep_data.iloc[-1] if not sleep_data.empty else 0
        components.render_metric_card("Latest Sleep", f"{latest_sleep / 60:.1f} hrs")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════
    #  TRENDS
    # ══════════════════════════════════════════════════════════════════════
    st.header("Trends")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        # Weight + 7-day MA
        weight_ma_df = get_weight_with_moving_avg()
        fig_weight = charts.plot_weight_with_ma(weight_ma_df) if not weight_ma_df.empty else None
        if fig_weight:
            st.plotly_chart(fig_weight, use_container_width=True)
        else:
            st.info("No weight data available.")

        # Sleep
        fig_sleep = charts.plot_sleep_over_time(days_df)
        if fig_sleep:
            st.plotly_chart(fig_sleep, use_container_width=True)
        else:
            st.info("No sleep data available.")

    with col_chart2:
        # Protein + target line
        fig_protein = charts.plot_protein_with_target(days_df)
        if fig_protein:
            st.plotly_chart(fig_protein, use_container_width=True)
        else:
            st.info("No protein data available.")

        # Daily Calories
        cal_df = get_daily_calories()
        fig_cal = charts.plot_daily_calories(cal_df) if not cal_df.empty else None
        if fig_cal:
            st.plotly_chart(fig_cal, use_container_width=True)
        else:
            st.info("No calorie data available.")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════
    #  EXERCISE PROGRESSION
    # ══════════════════════════════════════════════════════════════════════
    st.header("Exercise Progression")

    # Summary chart (max weight per exercise)
    summary_df = get_exercise_summary_timeseries()
    fig_summary = charts.plot_exercise_summary(summary_df)
    if fig_summary:
        st.plotly_chart(fig_summary, use_container_width=True)
    else:
        st.info("No exercise summary data available.")

    # Volume progression
    vol_df = get_workout_volume()
    fig_vol = charts.plot_volume_progression(vol_df)
    if fig_vol:
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.info("No volume data available.")

    # Per-exercise drill-down
    if exercises:
        selected_exercise = st.selectbox("Select Exercise", exercises)
        prog_df = get_exercise_progression(selected_exercise)
        fig_prog = charts.plot_exercise_progression(prog_df, selected_exercise)
        if fig_prog:
            st.plotly_chart(fig_prog, use_container_width=True)
        else:
            st.info(f"No progression data found for {selected_exercise}.")
    else:
        st.info("No exercises logged yet.")

    st.divider()



    # ══════════════════════════════════════════════════════════════════════
    #  CONSISTENCY PANEL
    # ══════════════════════════════════════════════════════════════════════
    st.header("Consistency")
    total_days = len(days_df)
    c1, c2, c3 = st.columns(3)
    with c1:
        gym_days = int((days_df['gym_minutes'].dropna() > 0).sum())
        st.metric("Gym Days", f"{gym_days} / {total_days}")
    with c2:
        protein_ok = int((days_df['total_protein'] >= 120).sum())
        st.metric("Protein ≥ 120g", f"{protein_ok} / {total_days}")
    with c3:
        sleep_ok = int((days_df['total_sleep_minutes'].fillna(0) >= 360).sum())
        st.metric("Sleep ≥ 6h", f"{sleep_ok} / {total_days}")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════
    #  ACTIVITY TRENDS
    # ══════════════════════════════════════════════════════════════════════
    st.header("Activity Trends")
    activity_metric = st.selectbox(
        "Select Activity Metric",
        ["Steps", "Exercise Minutes", "Move Calories", "Distance (km)"],
    )
    metric_cfg = {
        "Steps": ("steps", "Steps Over Time", "Steps", "#1f77b4"),
        "Exercise Minutes": ("exercise_minutes", "Exercise Minutes Over Time", "Minutes", "#2ca02c"),
        "Move Calories": ("move_calories", "Move Calories Over Time", "Calories", "#d62728"),
        "Distance (km)": ("distance_km", "Distance Over Time", "km", "#9467bd"),
    }
    col, title, y_label, color = metric_cfg[activity_metric]
    fig_activity = charts.plot_activity_trend(recent_activity_df, col, title, y_label, color=color)
    if fig_activity:
        st.plotly_chart(fig_activity, use_container_width=True)
    else:
        st.info("No activity data available.")

if __name__ == "__main__":
    main()
