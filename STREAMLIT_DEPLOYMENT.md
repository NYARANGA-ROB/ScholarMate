# ScholarMate - Streamlit Deployment Guide

## 🚀 Quick Start (Local)

### 1. Install Dependencies

```bash
pip install -r requirements_streamlit.txt
```

### 2. Set Up API Key

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your-groq-api-key-here"
```

### 3. Run the App

```bash
streamlit run streamlit_app.py
```

The app will open automatically at `http://localhost:8501`

---

## ☁️ Deploy to Streamlit Cloud (Free)

### Step 1: Prepare Your Repository

1. **Push to GitHub**:
   ```bash
   git add streamlit_app.py requirements_streamlit.txt .streamlit/
   git commit -m "Add Streamlit version"
   git push origin main
   ```

2. **Required Files**:
   - ✅ `streamlit_app.py` - Main application
   - ✅ `requirements_streamlit.txt` - Dependencies
   - ✅ `.streamlit/config.toml` - Theme configuration

### Step 2: Deploy on Streamlit Cloud

1. **Go to**: https://share.streamlit.io/

2. **Sign in** with GitHub

3. **Click "New app"**

4. **Configure**:
   - **Repository**: `yourusername/scholarmate`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`

5. **Add Secrets**:
   - Click "Advanced settings"
   - In "Secrets" section, add:
   ```toml
   GROQ_API_KEY = "your-groq-api-key-here"
   ```

6. **Click "Deploy"**

Your app will be live at: `https://yourusername-scholarmate-streamlit-app-xxxxx.streamlit.app`

---

## 🎨 Features

### ✅ Implemented
- **User Authentication** - Login/Register system
- **AI Tutoring** - Powered by Groq DeepSeek-R1
- **4 Subjects** - Mathematics, Physics, Chemistry, Computer Science
- **Session History** - Track all learning sessions
- **Progress Dashboard** - View statistics and history
- **Dark Theme** - Modern, eye-friendly UI
- **SQLite Database** - Persistent data storage

### 📱 User Interface
- Clean, modern design
- Responsive layout
- Easy navigation
- Real-time AI responses
- Session management

---

## 🔧 Configuration

### Environment Variables

For local development, use `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your-groq-api-key-here"
```

For Streamlit Cloud, add secrets in the dashboard under "Advanced settings".

### Theme Customization

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#3b82f6"      # Blue
backgroundColor = "#0f172a"    # Dark blue
secondaryBackgroundColor = "#1e293b"  # Slate
textColor = "#e2e8f0"         # Light gray
```

---

## 📊 Database

The app uses SQLite for data storage:

- **Database file**: `scholarmate_streamlit.db`
- **Tables**:
  - `users` - User accounts
  - `sessions` - Learning sessions

**Note**: On Streamlit Cloud, the database resets on app restart. For production, consider using:
- Streamlit's built-in database (coming soon)
- External database (PostgreSQL, MongoDB)
- Cloud storage (AWS S3, Google Cloud Storage)

---

## 🎯 Usage Guide

### For Students

1. **Register/Login**
   - Create account with username and email
   - Login to access dashboard

2. **Start Learning**
   - Select a subject from dashboard
   - Choose a topic
   - Ask your question
   - Get AI-powered explanation

3. **Track Progress**
   - View total sessions
   - See subjects studied
   - Review past sessions

### For Educators

1. **Monitor Usage**
   - Check session history
   - View subject distribution
   - Track student engagement

2. **Customize**
   - Adjust grade levels
   - Select curriculum
   - Personalize learning experience

---

## 🔐 Security

### Best Practices

1. **API Keys**:
   - Never commit secrets to Git
   - Use Streamlit secrets management
   - Rotate keys regularly

2. **Passwords**:
   - Currently stored as plain text (demo only)
   - For production, implement:
     - Password hashing (bcrypt)
     - Session tokens
     - OAuth integration

3. **Data Protection**:
   - SQLite for local storage
   - Consider encryption for sensitive data
   - Regular backups

---

## 🚀 Performance Tips

### Optimize Loading

1. **Cache Functions**:
   ```python
   @st.cache_data
   def load_data():
       # Your data loading code
       pass
   ```

2. **Session State**:
   - Use `st.session_state` for user data
   - Minimize database queries
   - Cache API responses

3. **Lazy Loading**:
   - Load data only when needed
   - Use pagination for large datasets
   - Implement infinite scroll

---

## 🛠️ Troubleshooting

### Common Issues

**Issue**: App won't start
```bash
# Solution: Check dependencies
pip install --upgrade -r requirements_streamlit.txt
```

**Issue**: API key not found
```bash
# Solution: Create secrets file
echo 'GROQ_API_KEY = "your-key"' > .streamlit/secrets.toml
```

**Issue**: Database errors
```bash
# Solution: Delete and recreate database
rm scholarmate_streamlit.db
streamlit run streamlit_app.py
```

**Issue**: Slow performance
- Check internet connection
- Verify API rate limits
- Clear browser cache
- Restart Streamlit app

---

## 📈 Scaling for Production

### Database Migration

For production deployment, migrate to PostgreSQL:

```python
import psycopg2

# Update connection in streamlit_app.py
conn = psycopg2.connect(
    host=st.secrets["db_host"],
    database=st.secrets["db_name"],
    user=st.secrets["db_user"],
    password=st.secrets["db_password"]
)
```

### Add to `requirements_streamlit.txt`:
```
psycopg2-binary==2.9.9
```

### Update Streamlit secrets:
```toml
GROQ_API_KEY = "your-key"
db_host = "your-db-host"
db_name = "scholarmate"
db_user = "your-user"
db_password = "your-password"
```

---

## 🎓 Advanced Features (Optional)

### Add Quiz System

```python
def quiz_page():
    st.title("📝 Practice Quiz")
    
    questions = [
        {"q": "What is 2+2?", "a": "4"},
        {"q": "What is the capital of France?", "a": "Paris"}
    ]
    
    for i, q in enumerate(questions):
        answer = st.text_input(f"Q{i+1}: {q['q']}")
        if st.button(f"Check Answer {i+1}"):
            if answer.lower() == q['a'].lower():
                st.success("Correct!")
            else:
                st.error(f"Incorrect. Answer: {q['a']}")
```

### Add Analytics Dashboard

```python
def analytics_page():
    st.title("📊 Learning Analytics")
    
    # Get data
    sessions = get_user_sessions(user_id, limit=100)
    
    # Create charts
    import pandas as pd
    df = pd.DataFrame(sessions)
    
    st.line_chart(df['timestamp'])
    st.bar_chart(df['subject'].value_counts())
```

---

## 📝 Comparison: Flask vs Streamlit

| Feature | Flask Version | Streamlit Version |
|---------|--------------|-------------------|
| **Deployment** | Complex (Docker, cloud) | Simple (one-click) |
| **UI Development** | HTML/CSS/JS required | Python only |
| **Database** | PostgreSQL/MongoDB | SQLite (upgradable) |
| **Authentication** | Flask-Login | Custom implementation |
| **Hosting** | AWS, GCP, Heroku | Streamlit Cloud (free) |
| **Best For** | Production apps | Prototypes, demos |

---

## 🌟 Next Steps

### Enhancements

1. **Add More Features**:
   - Quiz generation
   - Progress charts
   - Study materials
   - Collaborative learning

2. **Improve UI**:
   - Add animations
   - Better mobile support
   - Custom components
   - Rich text editor

3. **Scale Up**:
   - PostgreSQL database
   - Redis caching
   - Load balancing
   - CDN integration

4. **Analytics**:
   - User behavior tracking
   - Performance metrics
   - A/B testing
   - Feedback system

---

## 📞 Support

- **Streamlit Docs**: https://docs.streamlit.io
- **Groq API**: https://console.groq.com
- **GitHub Issues**: https://github.com/yourusername/scholarmate/issues

---

## 🎉 You're Ready!

Your ScholarMate Streamlit app is ready to deploy! 

**Local**: `streamlit run streamlit_app.py`  
**Cloud**: Deploy to Streamlit Cloud in 2 minutes

**Happy Teaching! 🎓✨**
