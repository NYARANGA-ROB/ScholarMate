# ScholarMate Deployment Guide
## Overview
This guide covers deploying the enhanced ScholarMate Intelligent Tutoring System with ML/NLP capabilities, adaptive learning, and production-ready infrastructure.
## Prerequisites
### System Requirements
- Python 3.11+
- PostgreSQL 15+ or MongoDB 6+
- Redis 7+
- Docker & Docker Compose (for containerized deployment)
- 4GB+ RAM (8GB+ recommended for ML models)
- 10GB+ disk space

### API Keys
- **Groq API Key**: Required for DeepSeek-R1 model access
  - Get from: https://console.groq.com/
  - Set as environment variable: `GROQ_API_KEY`
## Local Development Setup
### 1. Clone and Setup Environment

```bash
git clone https://github.com/yourusername/scholarmate.git
cd scholarmate
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download NLP models
python -m spacy download en_core_web_sm
```

### 2. Configure Environment Variables

Create `.env` file in project root:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production

# Database Configuration
DATABASE_URL=postgresql://scholarmate_user:password@localhost:5432/scholarmate
# Or for SQLite (development only):
# DATABASE_URL=sqlite:///scholarmate.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AI/ML Configuration
GROQ_API_KEY=your-groq-api-key-here
USE_LOCAL_MODELS=false  # Set to true to use local transformer models

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Initialize Database

```bash
# Create database tables
flask db upgrade

# Or if migrations don't exist:
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 4. Start Services

```bash
# Terminal 1: Start Flask application
python app.py

# Terminal 2: Start Celery worker (for background tasks)
celery -A celery_worker.celery worker --loglevel=info

# Terminal 3: Start Celery beat (for periodic tasks)
celery -A celery_worker.celery beat --loglevel=info
```

Access application at: http://localhost:5000

## Docker Deployment

### 1. Build and Run with Docker Compose

```bash
# Set environment variables
export GROQ_API_KEY=your-api-key
export DB_PASSWORD=secure-password
export SECRET_KEY=your-secret-key

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Initialize Database in Docker

```bash
# Run migrations
docker-compose exec web flask db upgrade

# Create admin user (optional)
docker-compose exec web python -c "
from models import db, User
from app import app

with app.app_context():
    admin = User(username='admin', email='admin@scholarmate.com')
    admin.set_password('changeme')
    admin.grade_level = 'Professional'
    db.session.add(admin)
    db.session.commit()
    print('Admin user created')
"
```

### 3. Service URLs

- **Web Application**: http://localhost:5000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Nginx** (if enabled): http://localhost:80

## Cloud Deployment (AWS)

### Architecture Overview
```
Internet → ALB → ECS (Flask) → RDS (PostgreSQL)
                    ↓
                ElastiCache (Redis)
                    ↓
                ECS (Celery Workers)
```

### 1. AWS Setup

#### Create RDS PostgreSQL Instance
```bash
aws rds create-db-instance \
    --db-instance-identifier scholarmate-db \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 15.3 \
    --master-username scholarmate_admin \
    --master-user-password YOUR_PASSWORD \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxx \
    --db-subnet-group-name your-subnet-group \
    --backup-retention-period 7 \
    --multi-az
```

#### Create ElastiCache Redis Cluster
```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id scholarmate-redis \
    --cache-node-type cache.t3.medium \
    --engine redis \
    --num-cache-nodes 1 \
    --security-group-ids sg-xxxxx \
    --cache-subnet-group-name your-subnet-group
```

### 2. Build and Push Docker Image

```bash
# Build image
docker build -t scholarmate:latest .

# Tag for ECR
docker tag scholarmate:latest YOUR_AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/scholarmate:latest

# Login to ECR
aws ecr get-login-password --region REGION | docker login --username AWS --password-stdin YOUR_AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com

# Push image
docker push YOUR_AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/scholarmate:latest
```

### 3. Create ECS Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "scholarmate",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "scholarmate-web",
      "image": "YOUR_AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/scholarmate:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:scholarmate/secret-key"
        },
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:scholarmate/database-url"
        },
        {
          "name": "GROQ_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:scholarmate/groq-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/scholarmate",
          "awslogs-region": "REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 4. Deploy to ECS

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create ECS service
aws ecs create-service \
    --cluster scholarmate-cluster \
    --service-name scholarmate-web \
    --task-definition scholarmate \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=scholarmate-web,containerPort=5000"
```

## Google Cloud Platform Deployment

### 1. Setup GCP Project

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
    compute.googleapis.com \
    container.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com
```

### 2. Create Cloud SQL Instance

```bash
gcloud sql instances create scholarmate-db \
    --database-version=POSTGRES_15 \
    --tier=db-g1-small \
    --region=us-central1 \
    --root-password=YOUR_PASSWORD

# Create database
gcloud sql databases create scholarmate --instance=scholarmate-db

# Create user
gcloud sql users create scholarmate_user \
    --instance=scholarmate-db \
    --password=YOUR_PASSWORD
```

### 3. Deploy to Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/scholarmate

# Deploy to Cloud Run
gcloud run deploy scholarmate \
    --image gcr.io/YOUR_PROJECT_ID/scholarmate \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars="FLASK_ENV=production" \
    --set-secrets="SECRET_KEY=scholarmate-secret-key:latest,DATABASE_URL=scholarmate-db-url:latest,GROQ_API_KEY=groq-api-key:latest" \
    --add-cloudsql-instances=YOUR_PROJECT_ID:us-central1:scholarmate-db \
    --memory=2Gi \
    --cpu=2 \
    --max-instances=10
```

## Monitoring and Maintenance

### Health Checks

Add health check endpoint to `app.py`:

```python
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })
```

### Logging

Configure structured logging:

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/scholarmate.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('ScholarMate startup')
```

### Monitoring Tools

- **Application Performance**: New Relic, DataDog, or AWS CloudWatch
- **Error Tracking**: Sentry
- **Uptime Monitoring**: UptimeRobot, Pingdom

### Backup Strategy

```bash
# PostgreSQL backup (daily cron job)
pg_dump -h localhost -U scholarmate_user scholarmate > backup_$(date +%Y%m%d).sql

# Automated backup to S3
aws s3 cp backup_$(date +%Y%m%d).sql s3://scholarmate-backups/
```

## Performance Optimization

### 1. Enable Caching

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL')
})

@app.route('/api/analytics/progress')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_progress():
    # ...
```

### 2. Database Indexing

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_sessions_user_subject ON sessions(user_id, subject);
CREATE INDEX idx_quiz_attempts_user ON quiz_attempts(user_id, completed_at);
CREATE INDEX idx_performance_metrics_user_date ON performance_metrics(user_id, date);
```

### 3. Load Balancing

Use Nginx as reverse proxy (included in docker-compose.yml):

```nginx
upstream scholarmate {
    server web:5000;
}

server {
    listen 80;
    server_name scholarmate.com;

    location / {
        proxy_pass http://scholarmate;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up CORS properly
- [ ] Implement rate limiting
- [ ] Enable CSRF protection
- [ ] Sanitize user inputs
- [ ] Use environment variables for secrets
- [ ] Enable database encryption at rest
- [ ] Set up VPC/firewall rules
- [ ] Regular security updates
- [ ] Implement API authentication
- [ ] Enable audit logging

## Troubleshooting

### Common Issues

**Issue**: Database connection errors
```bash
# Check database status
docker-compose ps db
# View database logs
docker-compose logs db
```

**Issue**: Celery tasks not running
```bash
# Check Celery worker status
docker-compose logs celery_worker
# Restart Celery
docker-compose restart celery_worker
```

**Issue**: Out of memory errors
```bash
# Increase Docker memory limit
# Edit docker-compose.yml and add:
services:
  web:
    mem_limit: 4g
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/scholarmate/issues
- Documentation: https://scholarmate.readthedocs.io
- Email: support@scholarmate.com
