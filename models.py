"""
Enhanced database models for Intelligent Tutoring System
Includes models for adaptive learning, assessments, and analytics
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Enhanced User model with learning preferences"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    curriculum = db.Column(db.String(50), default='General')
    grade_level = db.Column(db.String(20), default='High School')
    learning_style = db.Column(db.String(50), default='visual')  # visual, auditory, kinesthetic
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    learning_paths = db.relationship('LearningPath', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    performance_metrics = db.relationship('PerformanceMetric', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'curriculum': self.curriculum,
            'grade_level': self.grade_level,
            'learning_style': self.learning_style
        }


class Session(db.Model):
    """Enhanced Session model with engagement metrics"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    subject = db.Column(db.String(50), nullable=False, index=True)
    topic = db.Column(db.String(100), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    question = db.Column(db.Text)
    response = db.Column(db.Text)
    
    # Engagement metrics
    duration_seconds = db.Column(db.Integer, default=0)
    interaction_count = db.Column(db.Integer, default=1)
    difficulty_level = db.Column(db.String(20), default='medium')  # easy, medium, hard
    satisfaction_rating = db.Column(db.Integer)  # 1-5 stars
    
    # NLP metadata
    question_embedding = db.Column(db.Text)  # JSON serialized vector
    response_quality_score = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'topic': self.topic,
            'timestamp': self.timestamp.isoformat(),
            'question': self.question,
            'response': self.response,
            'duration_seconds': self.duration_seconds,
            'difficulty_level': self.difficulty_level
        }


class Quiz(db.Model):
    """Quiz template with questions"""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(50), nullable=False, index=True)
    topic = db.Column(db.String(100), nullable=False, index=True)
    difficulty_level = db.Column(db.String(20), default='medium')
    grade_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_adaptive = db.Column(db.Boolean, default=True)
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')


class Question(db.Model):
    """Individual quiz questions"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='multiple_choice')  # multiple_choice, true_false, short_answer
    options = db.Column(db.Text)  # JSON serialized list of options
    correct_answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    difficulty_score = db.Column(db.Float, default=0.5)  # 0-1 scale
    bloom_taxonomy_level = db.Column(db.String(20))  # remember, understand, apply, analyze, evaluate, create
    points = db.Column(db.Integer, default=1)
    
    def get_options(self):
        return json.loads(self.options) if self.options else []
    
    def set_options(self, options_list):
        self.options = json.dumps(options_list)


class QuizAttempt(db.Model):
    """Student quiz attempts with detailed analytics"""
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False, index=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    score = db.Column(db.Float)
    max_score = db.Column(db.Float)
    percentage = db.Column(db.Float)
    time_taken_seconds = db.Column(db.Integer)
    
    # Relationships
    answers = db.relationship('Answer', backref='attempt', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_score(self):
        """Calculate total score from answers"""
        total = 0
        max_total = 0
        for answer in self.answers:
            if answer.is_correct:
                total += answer.points_earned
            max_total += answer.question.points
        
        self.score = total
        self.max_score = max_total
        self.percentage = (total / max_total * 100) if max_total > 0 else 0


class Answer(db.Model):
    """Individual answers to quiz questions"""
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    student_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    points_earned = db.Column(db.Float, default=0)
    time_taken_seconds = db.Column(db.Integer)
    
    # Relationships
    question = db.relationship('Question', backref='answers')


class LearningPath(db.Model):
    """Personalized learning paths for students"""
    __tablename__ = 'learning_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    subject = db.Column(db.String(50), nullable=False)
    current_topic = db.Column(db.String(100))
    recommended_topics = db.Column(db.Text)  # JSON serialized list
    completed_topics = db.Column(db.Text)  # JSON serialized list
    difficulty_progression = db.Column(db.Text)  # JSON serialized difficulty map
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_recommended_topics(self):
        return json.loads(self.recommended_topics) if self.recommended_topics else []
    
    def set_recommended_topics(self, topics_list):
        self.recommended_topics = json.dumps(topics_list)
    
    def get_completed_topics(self):
        return json.loads(self.completed_topics) if self.completed_topics else []
    
    def add_completed_topic(self, topic):
        completed = self.get_completed_topics()
        if topic not in completed:
            completed.append(topic)
            self.completed_topics = json.dumps(completed)


class PerformanceMetric(db.Model):
    """Aggregated performance metrics for analytics"""
    __tablename__ = 'performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    subject = db.Column(db.String(50), nullable=False, index=True)
    topic = db.Column(db.String(100), index=True)
    date = db.Column(db.Date, default=datetime.utcnow, index=True)
    
    # Performance indicators
    sessions_count = db.Column(db.Integer, default=0)
    quizzes_attempted = db.Column(db.Integer, default=0)
    average_quiz_score = db.Column(db.Float)
    total_time_spent_minutes = db.Column(db.Integer, default=0)
    mastery_level = db.Column(db.Float, default=0.0)  # 0-1 scale
    
    # Engagement metrics
    questions_asked = db.Column(db.Integer, default=0)
    average_satisfaction = db.Column(db.Float)
    streak_days = db.Column(db.Integer, default=0)


class StudyMaterial(db.Model):
    """Recommended study materials and resources"""
    __tablename__ = 'study_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(50), nullable=False, index=True)
    topic = db.Column(db.String(100), nullable=False, index=True)
    material_type = db.Column(db.String(50))  # video, article, exercise, interactive
    content_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    difficulty_level = db.Column(db.String(20))
    estimated_time_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Feedback(db.Model):
    """User feedback and support tickets"""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    feedback_type = db.Column(db.String(50), nullable=False)  # bug, feature, question, complaint
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
