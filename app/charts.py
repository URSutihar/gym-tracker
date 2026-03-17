import plotly.express as px
import plotly.graph_objects as go

TEMPLATE = "plotly_dark"

DATE_ONLY_XAXIS = dict(
    tickformat="%b %d, %Y",
    hoverformat="%b %d, %Y",
    dtick="D1",
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
