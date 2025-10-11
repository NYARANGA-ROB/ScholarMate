# Testing Guide for Enhanced ScholarMate ITS

## Overview
This guide provides comprehensive testing procedures for all enhanced features of the Intelligent Tutoring System.

## Test Environment Setup

### Prerequisites
```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-flask pytest-mock faker

# Set test environment
export FLASK_ENV=testing

# Create test database
flask db upgrade
```

## Unit Tests

### 1. Model Tests

Create `tests/test_models.py`:

```python
import pytest
from models import User, Quiz, Question, QuizAttempt, Answer, PerformanceMetric
from app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_user_creation(client):
    """Test user model creation"""
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    assert user.id is not None
    assert user.check_password('password123')
    assert not user.check_password('wrongpassword')

def test_quiz_creation(client):
    """Test quiz model creation"""
    quiz = Quiz(
        title='Test Quiz',
        subject='mathematics',
        topic='Algebra',
        difficulty_level='medium'
    )
    db.session.add(quiz)
    db.session.commit()
    
    assert quiz.id is not None
    assert quiz.title == 'Test Quiz'

def test_quiz_attempt_scoring(client):
    """Test quiz attempt score calculation"""
    user = User(username='testuser', email='test@example.com')
    user.set_password('password')
    db.session.add(user)
    
    quiz = Quiz(title='Test', subject='math', topic='Algebra')
    db.session.add(quiz)
    db.session.flush()
    
    question = Question(
        quiz_id=quiz.id,
        question_text='What is 2+2?',
        correct_answer='4',
        points=10
    )
    db.session.add(question)
    db.session.flush()
    
    attempt = QuizAttempt(user_id=user.id, quiz_id=quiz.id)
    db.session.add(attempt)
    db.session.flush()
    
    answer = Answer(
        attempt_id=attempt.id,
        question_id=question.id,
        student_answer='4',
        is_correct=True,
        points_earned=10
    )
    db.session.add(answer)
    db.session.commit()
    
    attempt.calculate_score()
    
    assert attempt.score == 10
    assert attempt.percentage == 100.0
```

### 2. ML Service Tests

Create `tests/test_ml_services.py`:

```python
import pytest
from ml_services import (
    NLPQuestionAnsweringEngine,
    AdaptiveLearningEngine,
    QuizGenerationEngine,
    LearningAnalytics
)

def test_nlp_similarity():
    """Test semantic similarity calculation"""
    engine = NLPQuestionAnsweringEngine()
    
    similarity = engine.calculate_similarity(
        "What is machine learning?",
        "Explain machine learning"
    )
    
    assert 0 <= similarity <= 1
    assert similarity > 0.5  # Should be similar

def test_adaptive_difficulty_adjustment():
    """Test difficulty adjustment based on performance"""
    engine = AdaptiveLearningEngine()
    
    # High performance should increase difficulty
    high_scores = [0.9, 0.85, 0.92, 0.88]
    new_difficulty = engine.adjust_difficulty(high_scores, 'medium')
    assert new_difficulty == 'hard'
    
    # Low performance should decrease difficulty
    low_scores = [0.4, 0.5, 0.45, 0.48]
    new_difficulty = engine.adjust_difficulty(low_scores, 'medium')
    assert new_difficulty == 'easy'

def test_quiz_generation():
    """Test quiz generation"""
    engine = QuizGenerationEngine()
    
    questions = engine.generate_quiz('mathematics', 'Algebra', 'medium', 5)
    
    assert len(questions) == 5
    for q in questions:
        assert 'question_text' in q
        assert 'difficulty_score' in q

def test_mastery_calculation():
    """Test mastery level calculation"""
    analytics = LearningAnalytics()
    
    quiz_scores = [0.7, 0.75, 0.8, 0.85, 0.9]
    mastery = analytics.calculate_mastery_level(quiz_scores, 10, 300)
    
    assert 0 <= mastery <= 1
    assert mastery > 0.7  # Should show good mastery

def test_strengths_weaknesses_identification():
    """Test identification of strengths and weaknesses"""
    analytics = LearningAnalytics()
    
    performance = {
        'Algebra': {'mastery_level': 0.85},
        'Calculus': {'mastery_level': 0.45},
        'Geometry': {'mastery_level': 0.65}
    }
    
    result = analytics.identify_strengths_weaknesses(performance)
    
    assert 'Algebra' in result['strengths']
    assert 'Calculus' in result['weaknesses']
    assert 'Geometry' in result['needs_review']
```

### 3. API Tests

Create `tests/test_api.py`:

```python
import pytest
import json
from app import app, db
from models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create test user
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            yield client
            db.drop_all()

def login(client, username, password):
    """Helper function to login"""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def test_quiz_generation_api(client):
    """Test quiz generation API endpoint"""
    login(client, 'testuser', 'password')
    
    response = client.post('/api/quiz/generate',
        data=json.dumps({
            'subject': 'mathematics',
            'topic': 'Algebra',
            'difficulty': 'medium',
            'num_questions': 10
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'quiz_id' in data

def test_recommendations_api(client):
    """Test recommendations API endpoint"""
    login(client, 'testuser', 'password')
    
    response = client.get('/api/recommendations/topics?subject=mathematics')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'recommendations' in data

def test_analytics_api(client):
    """Test analytics API endpoint"""
    login(client, 'testuser', 'password')
    
    response = client.get('/api/analytics/progress?days=30')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'summary' in data
```

## Integration Tests

### 1. End-to-End Quiz Flow

```python
def test_complete_quiz_flow(client):
    """Test complete quiz taking flow"""
    login(client, 'testuser', 'password')
    
    # 1. Generate quiz
    response = client.post('/api/quiz/generate',
        data=json.dumps({
            'subject': 'mathematics',
            'topic': 'Algebra',
            'difficulty': 'medium',
            'num_questions': 5
        }),
        content_type='application/json'
    )
    quiz_id = json.loads(response.data)['quiz_id']
    
    # 2. Start quiz
    response = client.post(f'/api/quiz/{quiz_id}/start')
    data = json.loads(response.data)
    attempt_id = data['attempt_id']
    questions = data['questions']
    
    # 3. Submit answers
    answers = [
        {'question_id': q['id'], 'answer': 'test answer', 'time_taken': 30}
        for q in questions
    ]
    
    response = client.post(f'/api/quiz/attempt/{attempt_id}/submit',
        data=json.dumps({'answers': answers}),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'score' in data
```

### 2. Learning Path Generation

```python
def test_learning_path_generation(client):
    """Test personalized learning path generation"""
    login(client, 'testuser', 'password')
    
    # Create some performance history
    # ... (create sessions and quiz attempts)
    
    # Get recommendations
    response = client.get('/api/recommendations/topics?subject=mathematics')
    data = json.loads(response.data)
    
    assert len(data['recommendations']) > 0
    assert all('topic' in r for r in data['recommendations'])
    assert all('score' in r for r in data['recommendations'])
```

## Performance Tests

### 1. Load Testing

Create `tests/test_performance.py`:

```python
import time
import concurrent.futures

def test_quiz_generation_performance():
    """Test quiz generation performance"""
    from ml_services import quiz_engine
    
    start_time = time.time()
    questions = quiz_engine.generate_quiz('mathematics', 'Algebra', 'medium', 10)
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 2.0  # Should complete in under 2 seconds
    assert len(questions) == 10

def test_concurrent_requests():
    """Test handling concurrent API requests"""
    from app import app
    
    def make_request():
        with app.test_client() as client:
            response = client.get('/health')
            return response.status_code
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [f.result() for f in futures]
    
    assert all(status == 200 for status in results)
```

### 2. Database Query Performance

```python
def test_analytics_query_performance(client):
    """Test analytics query performance with large dataset"""
    from models import Session, User
    from faker import Faker
    
    fake = Faker()
    
    # Create test data
    user = User(username='perftest', email='perf@test.com')
    user.set_password('password')
    db.session.add(user)
    db.session.flush()
    
    # Create 1000 sessions
    for _ in range(1000):
        session = Session(
            user_id=user.id,
            subject='mathematics',
            topic='Algebra',
            question=fake.sentence(),
            response=fake.text()
        )
        db.session.add(session)
    
    db.session.commit()
    
    # Test query performance
    start_time = time.time()
    sessions = Session.query.filter_by(user_id=user.id).all()
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 0.1  # Should complete in under 100ms
    assert len(sessions) == 1000
```

## Manual Testing Checklist

### User Authentication
- [ ] Register new user
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Logout
- [ ] Password reset (if implemented)

### Tutoring Features
- [ ] Ask question in each subject
- [ ] Receive AI-generated response
- [ ] View response formatting (markdown, LaTeX)
- [ ] Save session to history
- [ ] View session history

### Quiz Features
- [ ] Generate quiz with different difficulties
- [ ] Take quiz and submit answers
- [ ] View quiz results
- [ ] See correct/incorrect answers
- [ ] Receive feedback on answers
- [ ] Retake quiz

### Adaptive Learning
- [ ] Receive topic recommendations
- [ ] Get difficulty suggestions
- [ ] View personalized learning path
- [ ] See recommendations update after quizzes

### Analytics
- [ ] View analytics dashboard
- [ ] See performance trends
- [ ] Check subject distribution
- [ ] View mastery levels
- [ ] Identify strengths/weaknesses
- [ ] Filter by time range

### Settings
- [ ] Update email
- [ ] Change curriculum
- [ ] Change grade level
- [ ] Update learning style
- [ ] Change password
- [ ] Delete account

## Automated Testing Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::test_user_creation

# Run with verbose output
pytest -v

# Run only failed tests
pytest --lf

# Run tests in parallel
pytest -n auto
```

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        python -m spacy download en_core_web_sm
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Test Data Generation

### Seed Database with Test Data

Create `seed_test_data.py`:

```python
from app import app, db
from models import User, Session, Quiz, Question
from faker import Faker
import random

fake = Faker()

def seed_data():
    with app.app_context():
        # Create test users
        users = []
        for i in range(10):
            user = User(
                username=f'user{i}',
                email=f'user{i}@test.com',
                curriculum=random.choice(['General', 'IB', 'AP']),
                grade_level=random.choice(['Grade 9', 'Grade 10', 'Grade 11', 'Grade 12'])
            )
            user.set_password('password')
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        
        # Create sessions
        subjects = ['mathematics', 'physics', 'chemistry', 'computer_science']
        for user in users:
            for _ in range(random.randint(5, 20)):
                subject = random.choice(subjects)
                session = Session(
                    user_id=user.id,
                    subject=subject,
                    topic=fake.word(),
                    question=fake.sentence(),
                    response=fake.text()
                )
                db.session.add(session)
        
        db.session.commit()
        print("Test data seeded successfully!")

if __name__ == '__main__':
    seed_data()
```

## Monitoring and Logging Tests

```python
def test_logging_configuration():
    """Test that logging is properly configured"""
    import logging
    
    logger = logging.getLogger('scholarmate')
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0

def test_error_handling():
    """Test error handling and logging"""
    with app.test_client() as client:
        # Test 404
        response = client.get('/nonexistent')
        assert response.status_code == 404
        
        # Test 500 (simulate error)
        # ... implementation depends on error simulation
```

## Security Tests

```python
def test_password_hashing():
    """Test password security"""
    user = User(username='test', email='test@test.com')
    user.set_password('password123')
    
    # Password should be hashed
    assert user.password_hash != 'password123'
    
    # Should verify correct password
    assert user.check_password('password123')
    
    # Should reject incorrect password
    assert not user.check_password('wrongpassword')

def test_sql_injection_protection(client):
    """Test SQL injection protection"""
    login(client, 'testuser', 'password')
    
    # Attempt SQL injection
    response = client.post('/api/quiz/generate',
        data=json.dumps({
            'subject': "'; DROP TABLE users; --",
            'topic': 'Algebra',
            'difficulty': 'medium',
            'num_questions': 10
        }),
        content_type='application/json'
    )
    
    # Should handle safely
    assert response.status_code in [400, 500]
    
    # Verify users table still exists
    assert User.query.count() > 0
```

## Test Coverage Goals

- **Overall Coverage**: > 80%
- **Critical Paths**: > 95%
- **Models**: > 90%
- **API Endpoints**: > 85%
- **ML Services**: > 75%

## Reporting

Generate test reports:

```bash
# HTML coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=. --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=. --cov-report=xml
```
