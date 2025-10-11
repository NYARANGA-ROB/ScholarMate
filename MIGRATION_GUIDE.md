# Migration Guide: Upgrading to Enhanced ScholarMate ITS

## Overview
This guide helps you migrate from the basic ScholarMate application to the enhanced Intelligent Tutoring System with ML/NLP capabilities, adaptive learning, and automated assessment.

## Pre-Migration Checklist

- [ ] Backup existing database
- [ ] Document current environment variables
- [ ] Note any custom modifications
- [ ] Test backup restoration process
- [ ] Review new system requirements
- [ ] Plan downtime window (if applicable)

## System Requirements Changes

### Before (Basic Version)
- Python 3.8+
- SQLite database
- 2GB RAM
- Basic Flask dependencies

### After (Enhanced Version)
- Python 3.11+
- PostgreSQL 15+ (recommended) or SQLite (development only)
- Redis 7+ (required for Celery)
- 4GB+ RAM (8GB+ recommended)
- ML/NLP libraries (transformers, torch, scikit-learn)

## Step-by-Step Migration

### Step 1: Backup Current System

```bash
# Backup database
cp scholarmate.db scholarmate.db.backup

# Backup environment file
cp .env .env.backup

# Create full backup
tar -czf scholarmate_backup_$(date +%Y%m%d).tar.gz \
    scholarmate.db .env app.py templates/ static/
```

### Step 2: Update Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Update pip
pip install --upgrade pip

# Install new dependencies
pip install -r requirements.txt

# Download NLP models
python -m spacy download en_core_web_sm
```

### Step 3: Update Environment Variables

Add new variables to your `.env` file:

```env
# Existing variables (keep these)
SECRET_KEY=your-existing-secret-key
DATABASE_URL=your-existing-database-url
GROQ_API_KEY=your-groq-api-key

# New variables (add these)
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=production
USE_LOCAL_MODELS=false
LOG_LEVEL=INFO

# Celery configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Step 4: Database Migration

#### Option A: SQLite to SQLite (Development)

```bash
# Create new tables
flask db upgrade

# The migration will add new tables without affecting existing data
```

#### Option B: SQLite to PostgreSQL (Recommended for Production)

```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Create PostgreSQL database
createdb scholarmate

# Export data from SQLite
sqlite3 scholarmate.db .dump > scholarmate_dump.sql

# Import to PostgreSQL (requires manual conversion)
# Use a tool like pgloader or manually convert:
pgloader scholarmate.db postgresql://user:pass@localhost/scholarmate

# Or use Python script:
python migrate_db.py
```

Create `migrate_db.py`:

```python
"""
Database migration script from SQLite to PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Old database (SQLite)
old_engine = create_engine('sqlite:///scholarmate.db')
OldSession = sessionmaker(bind=old_engine)

# New database (PostgreSQL)
new_db_url = os.getenv('DATABASE_URL')
new_engine = create_engine(new_db_url)
NewSession = sessionmaker(bind=new_engine)

# Import models
from models import User, Session

def migrate_data():
    old_session = OldSession()
    new_session = NewSession()
    
    try:
        # Migrate users
        users = old_session.query(User).all()
        for user in users:
            new_user = User(
                id=user.id,
                username=user.username,
                email=user.email,
                password_hash=user.password_hash,
                curriculum=user.curriculum,
                grade_level=user.grade_level
            )
            new_session.merge(new_user)
        
        # Migrate sessions
        sessions = old_session.query(Session).all()
        for sess in sessions:
            new_sess = Session(
                id=sess.id,
                user_id=sess.user_id,
                subject=sess.subject,
                topic=sess.topic,
                timestamp=sess.timestamp,
                question=sess.question,
                response=sess.response
            )
            new_session.merge(new_sess)
        
        new_session.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        new_session.rollback()
        print(f"Migration failed: {e}")
    finally:
        old_session.close()
        new_session.close()

if __name__ == '__main__':
    migrate_data()
```

### Step 5: Update Application Files

```bash
# Backup original app.py
mv app.py app_original.py

# Use enhanced version
cp app_enhanced.py app.py

# Or merge changes manually if you have customizations
```

### Step 6: Initialize New Database Tables

```bash
# Create migration
flask db migrate -m "Add ML/ITS features"

# Apply migration
flask db upgrade

# Verify tables were created
flask shell
>>> from models import db
>>> db.engine.table_names()
```

Expected new tables:
- `quizzes`
- `questions`
- `quiz_attempts`
- `answers`
- `learning_paths`
- `performance_metrics`
- `study_materials`
- `feedback`

### Step 7: Install and Configure Redis

#### Linux/Mac:
```bash
# Install Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis  # macOS

# Start Redis
redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

#### Windows:
```bash
# Download Redis from: https://github.com/microsoftarchive/redis/releases
# Or use Docker:
docker run -d -p 6379:6379 redis:7-alpine
```

### Step 8: Start Enhanced Services

```bash
# Terminal 1: Start Flask application
python app.py

# Terminal 2: Start Celery worker
celery -A celery_worker.celery worker --loglevel=info

# Terminal 3: Start Celery beat (for periodic tasks)
celery -A celery_worker.celery beat --loglevel=info
```

### Step 9: Verify Migration

#### Test Checklist:
- [ ] Login with existing account
- [ ] View existing sessions in dashboard
- [ ] Create new tutoring session
- [ ] Generate a quiz
- [ ] Take and submit quiz
- [ ] View analytics dashboard
- [ ] Check recommendations
- [ ] Verify background tasks are running

#### Verification Commands:

```bash
# Check database tables
flask shell
>>> from models import db, Quiz, Question, PerformanceMetric
>>> Quiz.query.count()
>>> Question.query.count()

# Check Redis connection
redis-cli
> PING
> KEYS *

# Check Celery tasks
celery -A celery_worker.celery inspect active
celery -A celery_worker.celery inspect scheduled
```

### Step 10: Data Initialization (Optional)

Generate initial performance metrics for existing users:

```python
# In Flask shell
from celery_worker import update_performance_metrics
from models import User

users = User.query.all()
for user in users:
    update_performance_metrics.delay(user.id)
```

## Docker Migration

### Migrate to Docker Deployment

```bash
# Build Docker image
docker build -t scholarmate:latest .

# Create .env file with production settings
cat > .env << EOF
SECRET_KEY=your-production-secret-key
DB_PASSWORD=secure-database-password
GROQ_API_KEY=your-groq-api-key
EOF

# Start services
docker-compose up -d

# Run migrations in container
docker-compose exec web flask db upgrade

# Import existing data
docker cp scholarmate.db scholarmate_web:/app/
docker-compose exec web python migrate_db.py
```

## Rollback Procedure

If migration fails, rollback to previous version:

```bash
# Stop new services
pkill -f "celery"
pkill -f "flask"

# Restore original files
mv app_original.py app.py

# Restore database
cp scholarmate.db.backup scholarmate.db

# Restore environment
cp .env.backup .env

# Restart original application
python app.py
```

## Common Migration Issues

### Issue 1: Import Errors

**Problem:** `ModuleNotFoundError: No module named 'transformers'`

**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Issue 2: Database Connection Errors

**Problem:** `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

### Issue 3: Redis Connection Errors

**Problem:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution:**
```bash
# Start Redis
redis-server

# Check Redis is accessible
redis-cli ping

# Verify REDIS_URL in .env
echo $REDIS_URL
```

### Issue 4: Celery Tasks Not Running

**Problem:** Background tasks not executing

**Solution:**
```bash
# Check Celery worker is running
celery -A celery_worker.celery inspect active

# Restart Celery worker
pkill -f celery
celery -A celery_worker.celery worker --loglevel=info

# Check Redis queue
redis-cli
> LLEN celery
```

### Issue 5: Migration Conflicts

**Problem:** `alembic.util.exc.CommandError: Target database is not up to date`

**Solution:**
```bash
# Stamp current version
flask db stamp head

# Create new migration
flask db migrate -m "Sync database"

# Apply migration
flask db upgrade
```

## Performance Optimization After Migration

### 1. Database Indexing

```sql
-- Add indexes for better query performance
CREATE INDEX idx_sessions_user_subject ON sessions(user_id, subject);
CREATE INDEX idx_sessions_timestamp ON sessions(timestamp DESC);
CREATE INDEX idx_quiz_attempts_user ON quiz_attempts(user_id, completed_at);
CREATE INDEX idx_performance_metrics_user_date ON performance_metrics(user_id, date);
```

### 2. Enable Caching

```python
# In app.py
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL')
})
```

### 3. Configure Gunicorn

```bash
# Production server
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --threads 2 \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         app:app
```

## Post-Migration Tasks

- [ ] Update documentation
- [ ] Train team on new features
- [ ] Monitor system performance
- [ ] Set up automated backups
- [ ] Configure monitoring/alerting
- [ ] Update user guides
- [ ] Announce new features to users

## Support

For migration assistance:
- GitHub Issues: https://github.com/yourusername/scholarmate/issues
- Email: support@scholarmate.com
- Documentation: https://scholarmate.readthedocs.io/migration

## Changelog

### Enhanced Version (v2.0.0)
- ✅ ML/NLP question answering engine
- ✅ Adaptive learning and recommendations
- ✅ Automated quiz generation and grading
- ✅ Comprehensive analytics dashboard
- ✅ PostgreSQL and Redis support
- ✅ Celery background tasks
- ✅ Docker containerization
- ✅ Production deployment configurations

### Original Version (v1.0.0)
- Basic tutoring with Groq API
- User authentication
- Session history
- Simple progress tracking
