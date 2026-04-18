"""
Configuration settings for ScholarMate ITS
"""
import os
from datetime import timedelta
class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'ff18e9b506ff42a1922312c08094f705eb20a46d4a306ba523b495d335e26614')
    FLASK_APP = os.getenv('FLASK_APP', 'app.py')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///scholarmate.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
    
    # Session
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    
    # AI/ML Configuration
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    USE_LOCAL_MODELS = os.getenv('USE_LOCAL_MODELS', 'false').lower() == 'true'
    
    # NLP Models
    NLP_MODEL_NAME = os.getenv('NLP_MODEL_NAME', 'deepset/bert-base-cased-squad2')
    SENTENCE_MODEL_NAME = os.getenv('SENTENCE_MODEL_NAME', 'all-MiniLM-L6-v2')
    
    # Feature Flags
    ENABLE_ADAPTIVE_QUIZZES = True
    ENABLE_RECOMMENDATIONS = True
    ENABLE_ANALYTICS = True
    ENABLE_CELERY_TASKS = True
    ENABLE_LOCAL_NLP = USE_LOCAL_MODELS
    
    # Quiz Configuration
    DEFAULT_QUIZ_QUESTIONS = 10
    MIN_QUIZ_QUESTIONS = 5
    MAX_QUIZ_QUESTIONS = 50
    QUIZ_TIME_LIMIT_MINUTES = 30
    
    # Recommendation Settings
    MAX_RECOMMENDATIONS = 5
    RECOMMENDATION_THRESHOLD = 0.6
    
    # Analytics Settings
    DEFAULT_ANALYTICS_DAYS = 30
    MAX_ANALYTICS_DAYS = 365
    
    # Performance Settings
    CACHE_TIMEOUT = 300  # 5 minutes
    RATE_LIMIT = "100 per hour"
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'scholarmate.log')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Require environment variables in production
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Ensure critical settings are configured
        assert os.getenv('SECRET_KEY'), 'SECRET_KEY must be set in production'
        assert os.getenv('DATABASE_URL'), 'DATABASE_URL must be set in production'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    CELERY_TASK_ALWAYS_EAGER = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
