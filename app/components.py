import streamlit as st

def render_metric_card(title, value, delta=None):
    st.metric(label=title, value=value, delta=delta)

def render_recent_activity_table(df):
    st.subheader("Recent Activity Summary")
    if df.empty:
        st.info("No activity data available.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)
