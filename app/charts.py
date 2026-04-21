import plotly.express as px
import plotly.graph_objects as go

TEMPLATE = "plotly_dark"

DATE_ONLY_XAXIS = dict(
    tickformat="%b %d",
    hoverformat="%b %d, %Y",
    tickmode="linear",
    dtick=86400000,  # 1 day in ms
)

# ---------------------------------------------------------------------------
# Weight
# ---------------------------------------------------------------------------

def plot_weight_with_ma(df):
    """Dual-line chart: daily weight + 7-day moving average."""
    if df.empty or 'weight' not in df.columns:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['weight'], mode='lines+markers',
        name='Daily Weight', line=dict(color='#636EFA'),
    ))
    if 'weight_7d_ma' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['weight_7d_ma'], mode='lines',
            name='7-Day MA', line=dict(color='#FFA15A', dash='dash', width=2),
        ))
    fig.update_layout(
        title='Weight Over Time', template=TEMPLATE,
        yaxis_title='Weight (kg)', xaxis_title='Date',
        legend=dict(orientation='h', y=-0.15),
    )
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Protein
# ---------------------------------------------------------------------------

def plot_protein_with_target(df, target=120):
    """Bar chart of daily protein with a horizontal target line."""
    if df.empty or 'total_protein' not in df.columns or df['total_protein'].dropna().empty:
        return None
    fig = px.bar(
        df.dropna(subset=['total_protein']), x='date', y='total_protein',
        title='Daily Protein Intake',
        labels={'total_protein': 'Protein (g)', 'date': 'Date'},
        color_discrete_sequence=['#AB63FA'],
    )
    fig.add_hline(
        y=target, line_dash='dash', line_color='#EF553B',
        annotation_text=f'Target {target}g', annotation_position='top left',
    )
    fig.update_layout(template=TEMPLATE)
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Calories
# ---------------------------------------------------------------------------

def plot_daily_calories(df):
    """Bar chart of daily total calories."""
    if df.empty or 'total_calories' not in df.columns:
        return None
    fig = px.bar(
        df, x='date', y='total_calories',
        title='Daily Calories',
        labels={'total_calories': 'Calories (kcal)', 'date': 'Date'},
        color_discrete_sequence=['#00CC96'],
    )
    fig.update_layout(template=TEMPLATE)
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Sleep
# ---------------------------------------------------------------------------

def plot_sleep_over_time(df):
    if df.empty or 'total_sleep_minutes' not in df.columns or df['total_sleep_minutes'].dropna().empty:
        return None
    df_plot = df.dropna(subset=['total_sleep_minutes']).copy()
    df_plot['sleep_hours'] = df_plot['total_sleep_minutes'] / 60
    fig = px.area(
        df_plot, x='date', y='sleep_hours',
        title='Sleep Duration Over Time',
        labels={'sleep_hours': 'Sleep (Hours)', 'date': 'Date'},
    )
    fig.update_layout(template=TEMPLATE)
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def plot_steps_over_time(df):
    if df.empty or 'steps' not in df.columns or df['steps'].dropna().empty:
        return None
    fig = px.bar(
        df.dropna(subset=['steps']), x='date', y='steps',
        title='Steps Over Time',
        labels={'steps': 'Steps', 'date': 'Date'},
    )
    fig.update_layout(template=TEMPLATE)
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Exercise Progression (max weight per session)
# ---------------------------------------------------------------------------

def plot_exercise_progression(df, exercise_name):
    if df.empty:
        return None
    fig = px.line(
        df, x='date', y='max_weight', markers=True,
        title=f'{exercise_name} – Max Weight / Session',
        labels={'max_weight': 'Max Weight (kg)', 'date': 'Date'},
        color_discrete_sequence=['#2ca02c'],
    )
    fig.update_layout(template=TEMPLATE)
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

def plot_exercise_summary(df):
    if df.empty:
        return None
    fig = px.line(
        df, x='date', y='max_weight', color='exercise_name', markers=True,
        title='Exercise Summary (Max Weight per Day)',
        labels={'max_weight': 'Max Weight (kg)', 'date': 'Date', 'exercise_name': 'Exercise'},
    )
    fig.update_layout(template=TEMPLATE, legend_title_text='Exercise')
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Volume Progression
# ---------------------------------------------------------------------------

def plot_volume_progression(df):
    """Multi-line chart of total volume (weight×reps) per exercise."""
    if df.empty:
        return None
    fig = px.line(
        df, x='date', y='total_volume', color='exercise_name', markers=True,
        title='Volume Progression (Weight × Reps)',
        labels={'total_volume': 'Volume (kg·reps)', 'date': 'Date', 'exercise_name': 'Exercise'},
    )
    fig.update_layout(template=TEMPLATE, legend_title_text='Exercise')
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Soreness Heatmap
# ---------------------------------------------------------------------------

def plot_soreness_heatmap(pivot_df):
    """Heatmap: x=body_part, y=date, color=soreness_score 0–10."""
    if pivot_df.empty:
        return None
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns.tolist(),
        y=pivot_df.index.tolist(),
        colorscale='YlOrRd',
        zmin=0, zmax=10,
        colorbar=dict(title='Score'),
    ))
    fig.update_layout(
        title='Soreness Heatmap',
        xaxis_title='Body Part', yaxis_title='Date',
        template=TEMPLATE, yaxis=dict(autorange='reversed'),
    )
    return fig

# ---------------------------------------------------------------------------
# Nutrition Trends
# ---------------------------------------------------------------------------

def plot_nutrition_trends(df):
    """Dual-axis chart: macros (g) on left, calories (kcal) on right."""
    macro_cols = {
        'total_protein': 'Protein (g)',
        'total_carbs': 'Carbs (g)',
        'total_fat': 'Fat (g)',
        'total_fiber': 'Fiber (g)',
    }
    colors = {
        'total_protein': '#AB63FA',
        'total_carbs': '#FFA15A',
        'total_fat': '#19D3F3',
        'total_fiber': '#2CA02C',
        'total_calories': '#EF553B',
    }

    has_macros = any(c in df.columns and df[c].sum() > 0 for c in macro_cols)
    has_cals = 'total_calories' in df.columns and df['total_calories'].sum() > 0
    if not has_macros and not has_cals:
        return None

    fig = go.Figure()

    # Left axis: macros (g)
    for col, label in macro_cols.items():
        if col in df.columns and df[col].sum() > 0:
            fig.add_trace(go.Scatter(
                x=df['date'], y=df[col], mode='lines+markers',
                name=label, line=dict(color=colors[col]),
                yaxis='y1',
            ))

    # Right axis: calories (kcal)
    if has_cals:
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['total_calories'], mode='lines+markers',
            name='Calories (kcal)', line=dict(color=colors['total_calories'], dash='dash', width=2),
            yaxis='y2',
        ))

    # Compute aligned axis ranges so gridlines match exactly
    import math
    macro_max = max(
        (df[c].max() for c in macro_cols if c in df.columns and df[c].sum() > 0),
        default=100
    )
    cal_max = df['total_calories'].max() if has_cals else 1000
    # Round up to clean intervals
    n_ticks = 5
    macro_ceil = math.ceil(macro_max / 50) * 50  # round to nearest 50
    cal_ceil = math.ceil(cal_max / 500) * 500     # round to nearest 500

    fig.update_layout(
        title='Nutrition Over Time',
        template=TEMPLATE,
        yaxis=dict(title='Macros (g)', side='left', range=[0, macro_ceil], dtick=macro_ceil / n_ticks),
        yaxis2=dict(title='Calories (kcal)', side='right', overlaying='y', range=[0, cal_ceil], dtick=cal_ceil / n_ticks, showgrid=False),
        legend=dict(orientation='h', y=-0.15),
    )
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Heart Rate
# ---------------------------------------------------------------------------

def plot_heart_rate_over_time(df):
    """HR band (min to max fill) over time."""
    if df.empty or 'hr_min' not in df.columns:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['hr_max'], mode='lines',
        name='HR Max', line=dict(color='#EF553B', width=1),
        fill=None,
    ))
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['hr_min'], mode='lines',
        name='HR Min', line=dict(color='#636EFA', width=1),
        fill='tonexty', fillcolor='rgba(99,110,250,0.15)',
    ))
    if 'hr_range' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['hr_range'], mode='lines+markers',
            name='HR Range', line=dict(color='#FFA15A', dash='dot', width=1.5),
            yaxis='y2',
        ))
    fig.update_layout(
        title='Sleep Heart Rate',
        template=TEMPLATE,
        yaxis=dict(title='BPM', side='left'),
        yaxis2=dict(title='HR Range (bpm)', side='right', overlaying='y', showgrid=False),
        legend=dict(orientation='h', y=-0.15),
    )
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Cardio
# ---------------------------------------------------------------------------

def plot_cardio_over_time(df):
    """Bars for total duration, line for avg speed per cardio session."""
    if df.empty:
        return None
    fig = go.Figure()
    for name in df['name'].unique():
        sub = df[df['name'] == name]
        fig.add_trace(go.Bar(
            x=sub['date'], y=sub['total_duration_min'],
            name=f'{name} Duration',
        ))
        if sub['avg_speed_kmh'].notna().any():
            fig.add_trace(go.Scatter(
                x=sub['date'], y=sub['avg_speed_kmh'], mode='lines+markers',
                name=f'{name} Avg Speed', yaxis='y2',
                line=dict(dash='dash'),
            ))
    fig.update_layout(
        title='Cardio Sessions',
        template=TEMPLATE,
        barmode='group',
        yaxis=dict(title='Duration (min)', side='left'),
        yaxis2=dict(title='Avg Speed (km/h)', side='right', overlaying='y', showgrid=False),
        legend=dict(orientation='h', y=-0.2),
    )
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Personal Records
# ---------------------------------------------------------------------------

def plot_pr_timeline(df, pr_df, exercise_name):
    """Exercise progression line with star markers at PR dates."""
    if df.empty:
        return None
    fig = px.line(
        df[df['max_weight'] > 0], x='date', y='max_weight', markers=True,
        title=f'{exercise_name} – Progression & PRs',
        labels={'max_weight': 'Max Weight (kg)', 'date': 'Date'},
        color_discrete_sequence=['#2ca02c'],
    )
    if not pr_df.empty:
        fig.add_trace(go.Scatter(
            x=pr_df['date'], y=pr_df['max_weight_kg'], mode='markers',
            marker=dict(symbol='star', size=14, color='#FFD700'),
            name='Personal Record',
        ))
    fig.update_layout(template=TEMPLATE, legend=dict(orientation='h', y=-0.15))
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig

# ---------------------------------------------------------------------------
# Weekly Summary
# ---------------------------------------------------------------------------

def _week_label(week_start):
    """Format 'YYYY-MM-DD' as 'W of Mar 16'."""
    import datetime
    try:
        d = datetime.date.fromisoformat(week_start)
        return d.strftime("%-d %b")
    except Exception:
        return week_start


def plot_weekly_gym_days(df):
    """Bar chart of gym days per week."""
    if df.empty or 'gym_days' not in df.columns:
        return None
    df = df.copy()
    df['week_label'] = df['week_start'].apply(_week_label)
    fig = px.bar(
        df, x='week_label', y='gym_days',
        title='Gym Days per Week',
        labels={'gym_days': 'Gym Days', 'week_label': 'Week Starting'},
        color_discrete_sequence=['#636EFA'],
        text='gym_days',
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(template=TEMPLATE, xaxis=dict(type='category'))
    return fig


def plot_weekly_nutrition(df):
    """Avg protein and avg calories per week."""
    if df.empty:
        return None
    df = df.copy()
    df['week_label'] = df['week_start'].apply(_week_label)
    fig = go.Figure()
    if 'avg_protein_g' in df.columns:
        fig.add_trace(go.Bar(
            x=df['week_label'], y=df['avg_protein_g'].round(1),
            name='Avg Protein (g)', marker_color='#AB63FA',
            text=df['avg_protein_g'].round(1), textposition='outside',
        ))
    if 'avg_calories' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['week_label'], y=df['avg_calories'].round(0), mode='lines+markers',
            name='Avg Calories (kcal)', yaxis='y2',
            line=dict(color='#EF553B', dash='dash'),
        ))
    fig.update_layout(
        title='Weekly Nutrition Averages',
        template=TEMPLATE,
        xaxis=dict(type='category', title='Week Starting'),
        yaxis=dict(title='Protein (g)', side='left'),
        yaxis2=dict(title='Calories (kcal)', side='right', overlaying='y', showgrid=False),
        legend=dict(orientation='h', y=-0.15),
    )
    return fig

# ---------------------------------------------------------------------------
# Insights: Sleep vs RPE
# ---------------------------------------------------------------------------

def plot_sleep_vs_rpe(df):
    """Scatter: sleep hours vs next-day RPE, sized by next-day workout volume."""
    if df.empty or len(df) < 3:
        return None
    fig = px.scatter(
        df, x='sleep_hours', y='next_day_rpe',
        size='next_day_volume' if df['next_day_volume'].sum() > 0 else None,
        hover_data=['date'],
        title='Sleep vs Next-Day Workout RPE',
        labels={
            'sleep_hours': 'Sleep (hours)',
            'next_day_rpe': 'Next-Day RPE',
            'next_day_volume': 'Volume (kg·reps)',
        },
        color_discrete_sequence=['#00CC96'],
        trendline='ols',
    )
    fig.update_layout(template=TEMPLATE)
    return fig

# ---------------------------------------------------------------------------
# Activity Trends (generic)
# ---------------------------------------------------------------------------

def plot_activity_trend(df, metric_col, title, y_label, color="#1f77b4"):
    if df.empty or metric_col not in df.columns:
        return None
    fig = px.line(
        df, x='date', y=metric_col, markers=True,
        title=title,
        labels={metric_col: y_label, 'date': 'Date'},
        color_discrete_sequence=[color],
    )
    fig.update_layout(template=TEMPLATE)
    fig.update_xaxes(**DATE_ONLY_XAXIS)
    return fig
