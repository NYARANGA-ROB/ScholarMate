"""
ScholarMate Analytics Dashboard - Streamlit
Companion app for analytics while keeping Flask UI for main app
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="ScholarMate Analytics",
    page_icon="📊",
    layout="wide"
)

# Custom CSS to match Flask theme
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
    }
    h1, h2, h3 {
        color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Connect to Flask database
def get_db_connection():
    conn = sqlite3.connect('scholarmate.db')
    return conn

# Load data
@st.cache_data
def load_sessions():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM session", conn)
    conn.close()
    return df

@st.cache_data
def load_users():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM user", conn)
    conn.close()
    return df

# Main app
st.title("📊 ScholarMate Analytics Dashboard")
st.markdown("---")

try:
    sessions_df = load_sessions()
    users_df = load_users()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", len(users_df))
    
    with col2:
        st.metric("Total Sessions", len(sessions_df))
    
    with col3:
        if len(sessions_df) > 0:
            avg_per_user = len(sessions_df) / len(users_df)
            st.metric("Avg Sessions/User", f"{avg_per_user:.1f}")
    
    with col4:
        if len(sessions_df) > 0:
            subjects = sessions_df['subject'].nunique()
            st.metric("Active Subjects", subjects)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 Sessions by Subject")
        if len(sessions_df) > 0:
            subject_counts = sessions_df['subject'].value_counts()
            fig = px.pie(values=subject_counts.values, names=subject_counts.index,
                        color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Sessions Over Time")
        if len(sessions_df) > 0:
            sessions_df['date'] = pd.to_datetime(sessions_df['timestamp']).dt.date
            daily_sessions = sessions_df.groupby('date').size().reset_index(name='count')
            fig = px.line(daily_sessions, x='date', y='count',
                         labels={'count': 'Sessions', 'date': 'Date'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent sessions
    st.subheader("📝 Recent Sessions")
    if len(sessions_df) > 0:
        recent = sessions_df.sort_values('timestamp', ascending=False).head(10)
        st.dataframe(recent[['subject', 'topic', 'timestamp']], use_container_width=True)

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure the Flask app database exists at 'scholarmate.db'")
