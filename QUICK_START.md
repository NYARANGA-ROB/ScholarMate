# Quick Start Guide - Enhanced ScholarMate ITS

## 🚀 Get Started in 5 Minutes

### Option 1: Docker (Recommended - Easiest)

```bash
# 1. Clone and navigate
git clone https://github.com/yourusername/scholarmate.git
cd scholarmate

# 2. Set environment variables
export GROQ_API_KEY=your-groq-api-key-here
export DB_PASSWORD=secure-password

# 3. Start everything with one command
docker-compose up -d

# 4. Initialize database
docker-compose exec web flask db upgrade

# 5. Open browser
open http://localhost:5000
```

**That's it! You're ready to go! 🎉**

---

### Option 2: Local Development

```bash
# 1. Clone repository
git clone https://github.com/yourusername/scholarmate.git
cd scholarmate

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4. Create .env file
cat > .env << EOF
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_URL=sqlite:///scholarmate.db
GROQ_API_KEY=your-groq-api-key-here
REDIS_URL=redis://localhost:6379/0
EOF

# 5. Initialize database
flask db upgrade

# 6. Start Redis (in separate terminal)
redis-server

# 7. Start Celery worker (in separate terminal)
celery -A celery_worker.celery worker --loglevel=info

# 8. Start application
python app.py

# 9. Open browser
open http://localhost:5000
```

---

## 📝 First Steps

### 1. Create Account
- Navigate to http://localhost:5000
- Click "Sign up"
- Fill in username, email, password
- Click "Register"

### 2. Set Your Profile
- Login with your credentials
- Click profile dropdown → Settings
- Set your:
  - Grade level (e.g., "Grade 11", "Undergraduate")
  - Curriculum (e.g., "General", "IB", "AP")
  - Learning style (visual, auditory, kinesthetic)

### 3. Start Learning
- Go to Dashboard
- Choose a subject (Mathematics, Physics, Chemistry, Computer Science)
- Select a topic
- Ask a question
- Get AI-powered explanations!

### 4. Take a Quiz
- Navigate to "Quizzes" from menu
- Click "Generate New Quiz"
- Select subject, topic, difficulty
- Take the quiz
- Get instant feedback and scoring

### 5. View Analytics
- Click "Analytics" in menu
- See your:
  - Performance trends
  - Subject distribution
  - Mastery levels
  - Strengths and weaknesses
  - Personalized recommendations

---

## 🎯 Key Features to Try

### ✨ AI Tutoring
```
1. Go to Dashboard → Select Subject
2. Choose a topic (e.g., "Calculus")
3. Ask: "Explain the concept of derivatives"
4. Get step-by-step explanation with examples
```

### 📊 Adaptive Quizzes
```
1. Navigate to Quizzes
2. Generate quiz (10 questions, medium difficulty)
3. Take quiz
4. System adapts difficulty based on your performance
5. View detailed results with explanations
```

### 🎓 Personalized Learning
```
1. Complete a few quizzes
2. Go to Analytics dashboard
3. See recommended topics based on your performance
4. Follow personalized learning path
```

### 📈 Progress Tracking
```
1. View Analytics dashboard
2. See performance over time
3. Identify strengths (mastery > 80%)
4. Focus on weaknesses (mastery < 50%)
5. Track time spent learning
```

---

## 🔧 Configuration

### Minimal Configuration (.env)
```env
SECRET_KEY=your-secret-key
GROQ_API_KEY=your-groq-api-key
```

### Full Configuration (.env)
```env
# Required
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key-here

# Database (choose one)
DATABASE_URL=sqlite:///scholarmate.db                    # Development
# DATABASE_URL=postgresql://user:pass@localhost/db       # Production

# Redis
REDIS_URL=redis://localhost:6379/0

# Optional Features
USE_LOCAL_MODELS=false          # Set true for local NLP models
FLASK_ENV=development           # development or production
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
```

---

## 🧪 Test the System

### Quick Health Check
```bash
# Check if application is running
curl http://localhost:5000/health

# Expected response:
# {"status":"healthy","timestamp":"...","version":"2.0.0"}
```

### Test API Endpoints
```bash
# Login first (get session cookie)
curl -X POST http://localhost:5000/login \
  -d "username=testuser&password=password"

# Generate quiz
curl -X POST http://localhost:5000/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"subject":"mathematics","topic":"Algebra","difficulty":"medium","num_questions":10}'

# Get recommendations
curl http://localhost:5000/api/recommendations/topics?subject=mathematics

# Get analytics
curl http://localhost:5000/api/analytics/progress?days=30
```

---

## 📚 Example Workflows

### Workflow 1: Complete Learning Session
```
1. Login → Dashboard
2. Select "Mathematics" → "Calculus"
3. Ask: "How do I find the derivative of x²?"
4. Read AI explanation
5. Generate practice quiz on derivatives
6. Take quiz (10 questions)
7. Review results and feedback
8. Check analytics to see mastery level
```

### Workflow 2: Adaptive Learning Path
```
1. Take initial assessment quiz (medium difficulty)
2. System analyzes performance
3. View recommendations in dashboard
4. Follow suggested topics
5. Difficulty auto-adjusts based on scores
6. Track progress in analytics
```

### Workflow 3: Exam Preparation
```
1. Set grade level to match exam (e.g., "Grade 12")
2. Set curriculum (e.g., "AP")
3. Generate quizzes for each topic
4. Take quizzes in expert difficulty
5. Review weak areas in analytics
6. Focus on topics with mastery < 70%
7. Retake quizzes until mastery > 80%
```

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors
```bash
# Solution: Reinstall dependencies
pip install --upgrade -r requirements.txt
python -m spacy download en_core_web_sm
```

### Issue: Database errors
```bash
# Solution: Reset database
rm scholarmate.db  # Backup first if needed!
flask db upgrade
```

### Issue: Redis connection errors
```bash
# Solution: Start Redis
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Issue: Celery tasks not running
```bash
# Solution: Restart Celery worker
pkill -f celery
celery -A celery_worker.celery worker --loglevel=info
```

### Issue: Port already in use
```bash
# Solution: Use different port
python app.py --port 5001

# Or find and kill process
lsof -ti:5000 | xargs kill -9  # Unix/Mac
netstat -ano | findstr :5000   # Windows
```

---

## 📖 Next Steps

### Learn More
- Read [ENHANCEMENTS.md](ENHANCEMENTS.md) for detailed feature documentation
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- See [TESTING_GUIDE.md](TESTING_GUIDE.md) for testing procedures
- Review [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) if upgrading

### Customize
- Modify `SUBJECTS` in `app.py` to add more subjects
- Add custom quiz templates in `ml_services.py`
- Customize UI in `templates/` directory
- Adjust ML parameters in `config.py`

### Contribute
- Fork the repository
- Create feature branch
- Make improvements
- Submit pull request

---

## 🎓 Sample Questions to Try

### Mathematics
- "Explain the Pythagorean theorem with examples"
- "How do I solve quadratic equations?"
- "What is the difference between mean, median, and mode?"

### Physics
- "Explain Newton's laws of motion"
- "How does electricity work?"
- "What is the relationship between force, mass, and acceleration?"

### Chemistry
- "What is the periodic table and how is it organized?"
- "Explain chemical bonding"
- "How do acids and bases react?"

### Computer Science
- "What is a binary search algorithm?"
- "Explain object-oriented programming"
- "How do databases work?"

---

## 💡 Tips for Best Results

1. **Be Specific**: Ask detailed questions for better explanations
2. **Set Correct Level**: Match your grade level for appropriate content
3. **Take Quizzes Regularly**: Helps system understand your progress
4. **Review Analytics**: Identify areas needing improvement
5. **Follow Recommendations**: Trust the adaptive learning suggestions
6. **Practice Consistently**: Regular sessions improve mastery levels

---

## 📞 Get Help

- **Documentation**: Full docs in repository
- **Issues**: Report bugs on GitHub Issues
- **Email**: support@scholarmate.com
- **Community**: Join our Discord/Slack (if available)

---

## 🎉 You're All Set!

Start your personalized learning journey with ScholarMate's AI-powered tutoring system!

**Happy Learning! 📚✨**
