"""
ScholarMate - AI-Powered Intelligent Tutoring System
Streamlit Version
"""
import streamlit as st
import os
from datetime import datetime
import json
from groq import Groq
import sqlite3
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="ScholarMate - AI Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        border: none;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #2563eb;
    }
    .stTextInput>div>div>input {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    .stTextArea>div>div>textarea {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    .stSelectbox>div>div>select {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    .response-box {
        background-color: #1e293b;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #1e293b;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    h1, h2, h3 {
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Subject configurations
SUBJECTS = {
    'Mathematics': {
        'topics': ['Algebra', 'Geometry', 'Calculus', 'Statistics', 'Trigonometry', 'Number Theory'],
        'icon': '🔢'
    },
    'Physics': {
        'topics': ['Mechanics', 'Thermodynamics', 'Electromagnetism', 'Quantum Physics', 'Optics', 'Waves'],
        'icon': '⚛️'
    },
    'Chemistry': {
        'topics': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry', 'Biochemistry', 'Analytical Chemistry'],
        'icon': '🧪'
    },
    'Computer Science': {
        'topics': ['Programming', 'Data Structures', 'Algorithms', 'Web Development', 'Database Systems', 'AI/ML'],
        'icon': '💻'
    }
}

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'sessions' not in st.session_state:
    st.session_state.sessions = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'

# Database functions
def init_db():
    """Initialize SQLite database"""
    db_path = Path('scholarmate_streamlit.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  grade_level TEXT DEFAULT 'High School',
                  curriculum TEXT DEFAULT 'General',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  subject TEXT NOT NULL,
                  topic TEXT NOT NULL,
                  question TEXT NOT NULL,
                  response TEXT NOT NULL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

def create_user(username, email, password):
    """Create a new user"""
    try:
        conn = sqlite3.connect('scholarmate_streamlit.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    """Authenticate user"""
    conn = sqlite3.connect('scholarmate_streamlit.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def save_session(user_id, subject, topic, question, response):
    """Save tutoring session"""
    conn = sqlite3.connect('scholarmate_streamlit.db')
    c = conn.cursor()
    c.execute("INSERT INTO sessions (user_id, subject, topic, question, response) VALUES (?, ?, ?, ?, ?)",
              (user_id, subject, topic, question, response))
    conn.commit()
    conn.close()

def get_user_sessions(user_id, limit=10):
    """Get user's recent sessions"""
    conn = sqlite3.connect('scholarmate_streamlit.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE user_id=? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
    sessions = c.fetchall()
    conn.close()
    return sessions

def get_user_stats(user_id):
    """Get user statistics"""
    conn = sqlite3.connect('scholarmate_streamlit.db')
    c = conn.cursor()
    
    # Total sessions
    c.execute("SELECT COUNT(*) FROM sessions WHERE user_id=?", (user_id,))
    total_sessions = c.fetchone()[0]
    
    # Sessions by subject
    c.execute("SELECT subject, COUNT(*) FROM sessions WHERE user_id=? GROUP BY subject", (user_id,))
    subject_stats = c.fetchall()
    
    conn.close()
    return total_sessions, subject_stats

# AI Tutor function
def get_ai_response(subject, topic, question, grade_level, curriculum):
    """Get AI response from Groq"""
    groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv('GROQ_API_KEY')
    
    if not groq_api_key:
        return "⚠️ AI Tutor is not configured. Please set your GROQ_API_KEY in Streamlit secrets."
    
    try:
        client = Groq(api_key=groq_api_key)
        
        chat_prompt = f"""You are an expert {subject} tutor specializing in {topic} for {grade_level} students following {curriculum} curriculum.
        Please explain the following concept/question in a clear, step-by-step manner:

        {question}

        Structure your response with:
        1. Basic concept explanation in simple terms
        2. Key formulas, rules, or principles (if applicable)
        3. Step-by-step solution or explanation
        4. Real-world applications and examples
        5. A practice problem for the student to try
        
        Format your response in markdown for better readability."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert {subject} tutor. You excel at explaining complex concepts in simple terms."
                },
                {
                    "role": "user",
                    "content": chat_prompt
                }
            ],
            model="deepseek-r1-distill-llama-70b",
            temperature=0.5,
            max_tokens=1536,
            top_p=0.9,
        )

        return chat_completion.choices[0].message.content
    
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Pages
def login_page():
    """Login/Register page"""
    st.title("🎓 ScholarMate - AI-Powered Tutoring")
    st.markdown("### Your Personal AI Learning Companion")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_btn"):
            if username and password:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.user = {
                        'id': user[0],
                        'username': user[1],
                        'email': user[2],
                        'grade_level': user[4],
                        'curriculum': user[5]
                    }
                    st.session_state.current_page = 'dashboard'
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    
    with tab2:
        st.subheader("Create New Account")
        new_username = st.text_input("Username", key="reg_username")
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register", key="register_btn"):
            if new_username and new_email and new_password and confirm_password:
                if new_password == confirm_password:
                    if create_user(new_username, new_email, new_password):
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username or email already exists")
                else:
                    st.error("Passwords do not match")
            else:
                st.warning("Please fill in all fields")

def dashboard_page():
    """Main dashboard"""
    st.title(f"Welcome back, {st.session_state.user['username']}! 👋")
    
    # Get user stats
    total_sessions, subject_stats = get_user_stats(st.session_state.user['id'])
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Sessions", total_sessions)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Subjects Studied", len(subject_stats))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Grade Level", st.session_state.user['grade_level'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Subject cards
    st.subheader("📚 Choose Your Subject")
    cols = st.columns(4)
    
    for idx, (subject, data) in enumerate(SUBJECTS.items()):
        with cols[idx % 4]:
            if st.button(f"{data['icon']} {subject}", key=f"subject_{subject}", use_container_width=True):
                st.session_state.selected_subject = subject
                st.session_state.current_page = 'tutor'
                st.rerun()
    
    st.markdown("---")
    
    # Recent sessions
    st.subheader("📝 Recent Learning Sessions")
    sessions = get_user_sessions(st.session_state.user['id'], limit=5)
    
    if sessions:
        for session in sessions:
            with st.expander(f"{session[2]} - {session[3]} ({session[6]})"):
                st.markdown(f"**Question:** {session[4]}")
                st.markdown(f"**Response:** {session[5][:200]}...")
    else:
        st.info("No sessions yet. Start learning by selecting a subject above!")

def tutor_page():
    """AI Tutor page"""
    subject = st.session_state.get('selected_subject', 'Mathematics')
    
    st.title(f"{SUBJECTS[subject]['icon']} {subject} Tutor")
    
    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()
    
    st.markdown("---")
    
    # Topic selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        topic = st.selectbox("Select Topic", SUBJECTS[subject]['topics'])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("View Progress", use_container_width=True):
            st.session_state.current_page = 'progress'
            st.rerun()
    
    # Question input
    st.markdown("### 💭 Ask Your Question")
    question = st.text_area(
        "What would you like to learn?",
        height=100,
        placeholder="e.g., Explain the Pythagorean theorem with examples..."
    )
    
    if st.button("🚀 Get AI Explanation", type="primary", use_container_width=True):
        if question:
            with st.spinner("🤔 AI Tutor is thinking..."):
                response = get_ai_response(
                    subject,
                    topic,
                    question,
                    st.session_state.user['grade_level'],
                    st.session_state.user['curriculum']
                )
                
                # Save session
                save_session(
                    st.session_state.user['id'],
                    subject,
                    topic,
                    question,
                    response
                )
                
                # Display response
                st.markdown("### 📖 AI Tutor's Explanation")
                st.markdown(f'<div class="response-box">{response}</div>', unsafe_allow_html=True)
                
                st.success("✅ Session saved to your history!")
        else:
            st.warning("Please enter a question")

def progress_page():
    """Progress tracking page"""
    st.title("📊 Your Learning Progress")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()
    
    st.markdown("---")
    
    # Get stats
    total_sessions, subject_stats = get_user_stats(st.session_state.user['id'])
    
    # Display stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Overall Statistics")
        st.metric("Total Learning Sessions", total_sessions)
        st.metric("Active Subjects", len(subject_stats))
    
    with col2:
        st.subheader("📚 Sessions by Subject")
        if subject_stats:
            for subject, count in subject_stats:
                st.write(f"**{subject}:** {count} sessions")
        else:
            st.info("No sessions yet")
    
    st.markdown("---")
    
    # Recent sessions
    st.subheader("📝 All Sessions")
    sessions = get_user_sessions(st.session_state.user['id'], limit=20)
    
    if sessions:
        for session in sessions:
            with st.expander(f"{session[2]} - {session[3]} | {session[6]}"):
                st.markdown(f"**Question:** {session[4]}")
                st.markdown("**Response:**")
                st.markdown(session[5])
    else:
        st.info("No sessions yet. Start learning!")

def settings_page():
    """Settings page"""
    st.title("⚙️ Settings")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()
    
    st.markdown("---")
    
    st.subheader("👤 Profile Settings")
    
    grade_level = st.selectbox(
        "Grade Level",
        ["Elementary", "Middle School", "High School", "Undergraduate", "Graduate", "Professional"],
        index=2
    )
    
    curriculum = st.selectbox(
        "Curriculum",
        ["General", "IB", "AP", "GCSE", "A-Level", "Common Core"],
        index=0
    )
    
    if st.button("Save Settings"):
        # Update session state
        st.session_state.user['grade_level'] = grade_level
        st.session_state.user['curriculum'] = curriculum
        st.success("Settings saved successfully!")

# Main app
def main():
    # Initialize database
    init_db()
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/3b82f6/ffffff?text=ScholarMate", use_container_width=True)
        st.markdown("---")
        
        if st.session_state.user:
            st.markdown(f"### 👤 {st.session_state.user['username']}")
            st.markdown(f"📧 {st.session_state.user['email']}")
            st.markdown("---")
            
            # Navigation
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            
            if st.button("📊 Progress", use_container_width=True):
                st.session_state.current_page = 'progress'
                st.rerun()
            
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.current_page = 'settings'
                st.rerun()
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.current_page = 'login'
                st.rerun()
        else:
            st.info("Please login to continue")
    
    # Main content
    if not st.session_state.user:
        login_page()
    else:
        if st.session_state.current_page == 'dashboard':
            dashboard_page()
        elif st.session_state.current_page == 'tutor':
            tutor_page()
        elif st.session_state.current_page == 'progress':
            progress_page()
        elif st.session_state.current_page == 'settings':
            settings_page()

if __name__ == "__main__":
    main()
