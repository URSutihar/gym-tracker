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
    get_sleep_hr_data,
    get_cardio_sessions,
    get_personal_records,
    get_pr_history,
    get_weekly_summary,
    get_sleep_workout_correlation,
    get_nutrition_trends,
)
import charts
import components
import os

st.set_page_config(page_title="Gym Tracker Dashboard", layout="wide", page_icon="🏋️")

def main():
    st.title("URS Progress Tracker 💪")

    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gym_log.db')
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at {DB_PATH}. Please run `python db/init_db.py` first.")
        return

    # ── Load core data ─────────────────────────────────────────────────────
    try:
        days_df = get_days_data()
        exercises = get_all_exercise_names()
        recent_activity_df = get_recent_activity()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    if days_df.empty:
        st.warning("No data found. Use `python scripts/import_json.py day.json` to log your first day!")
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
        weight_ma_df = get_weight_with_moving_avg()
        fig_weight = charts.plot_weight_with_ma(weight_ma_df) if not weight_ma_df.empty else None
        if fig_weight:
            st.plotly_chart(fig_weight, use_container_width=True)
        else:
            st.info("No weight data available.")

        fig_sleep = charts.plot_sleep_over_time(days_df)
        if fig_sleep:
            st.plotly_chart(fig_sleep, use_container_width=True)
        else:
            st.info("No sleep data available.")

        # Heart Rate
        hr_df = get_sleep_hr_data()
        if not hr_df.empty:
            fig_hr = charts.plot_heart_rate_over_time(hr_df)
            if fig_hr:
                st.plotly_chart(fig_hr, use_container_width=True)

    with col_chart2:
        fig_protein = charts.plot_protein_with_target(days_df)
        if fig_protein:
            st.plotly_chart(fig_protein, use_container_width=True)
        else:
            st.info("No protein data available.")

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

    summary_df = get_exercise_summary_timeseries()
    fig_summary = charts.plot_exercise_summary(summary_df)
    if fig_summary:
        st.plotly_chart(fig_summary, use_container_width=True)
    else:
        st.info("No exercise summary data available.")

    vol_df = get_workout_volume()
    fig_vol = charts.plot_volume_progression(vol_df)
    if fig_vol:
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.info("No volume data available.")

    if exercises:
        selected_exercise = st.selectbox("Select Exercise", exercises)
        prog_df = get_exercise_progression(selected_exercise)
        pr_df = get_pr_history(selected_exercise)
        fig_prog = charts.plot_pr_timeline(prog_df, pr_df, selected_exercise)
        if fig_prog:
            st.plotly_chart(fig_prog, use_container_width=True)
        else:
            st.info(f"No progression data found for {selected_exercise}.")
    else:
        st.info("No exercises logged yet.")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════
    #  PERSONAL RECORDS
    # ══════════════════════════════════════════════════════════════════════
    st.header("Personal Records")
    pr_all_df = get_personal_records()
    if not pr_all_df.empty:
        st.dataframe(
            pr_all_df.rename(columns={
                'exercise_name': 'Exercise',
                'pr_weight_kg': 'PR (kg)',
                'pr_date': 'Date Achieved'
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No PR data available yet.")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════
    #  CARDIO
    # ══════════════════════════════════════════════════════════════════════
    cardio_df = get_cardio_sessions()
    if not cardio_df.empty:
        st.header("Cardio")
        fig_cardio = charts.plot_cardio_over_time(cardio_df)
        if fig_cardio:
            st.plotly_chart(fig_cardio, use_container_width=True)
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

    st.divider()

    # ══════════════════════════════════════════════════════════════════════
    #  NUTRITION TRENDS
    # ══════════════════════════════════════════════════════════════════════
    st.header("Nutrition Trends")
    nutrition_df = get_nutrition_trends()
    fig_nutrition = charts.plot_nutrition_trends(nutrition_df)
    if fig_nutrition:
        st.plotly_chart(fig_nutrition, use_container_width=True)
    else:
        st.info("No nutrition data available.")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════
    #  WEEKLY SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    with st.expander("Weekly Summary"):
        weekly_df = get_weekly_summary()
        if not weekly_df.empty:
            col_w1, col_w2 = st.columns(2)
            with col_w1:
                fig_wk_gym = charts.plot_weekly_gym_days(weekly_df)
                if fig_wk_gym:
                    st.plotly_chart(fig_wk_gym, use_container_width=True)
            with col_w2:
                fig_wk_nut = charts.plot_weekly_nutrition(weekly_df)
                if fig_wk_nut:
                    st.plotly_chart(fig_wk_nut, use_container_width=True)
            st.dataframe(
                weekly_df[['week_start', 'gym_days', 'total_gym_minutes',
                            'avg_weight_kg', 'avg_sleep_minutes', 'total_steps',
                            'avg_protein_g', 'avg_calories']].rename(columns={
                    'week_start': 'Week', 'gym_days': 'Gym Days',
                    'total_gym_minutes': 'Gym Min', 'avg_weight_kg': 'Avg Weight (kg)',
                    'avg_sleep_minutes': 'Avg Sleep (min)', 'total_steps': 'Total Steps',
                    'avg_protein_g': 'Avg Protein (g)', 'avg_calories': 'Avg Calories',
                }),
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("Not enough data for weekly summary.")

    # ══════════════════════════════════════════════════════════════════════
    #  INSIGHTS: Sleep vs RPE
    # ══════════════════════════════════════════════════════════════════════
    corr_df = get_sleep_workout_correlation()
    if not corr_df.empty and len(corr_df) >= 5:
        with st.expander("Insight: Sleep vs Workout Performance"):
            fig_corr = charts.plot_sleep_vs_rpe(corr_df)
            if fig_corr:
                st.plotly_chart(fig_corr, use_container_width=True)


if __name__ == "__main__":
    main()
