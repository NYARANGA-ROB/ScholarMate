"""
Celery worker for background tasks
Handles model training, quiz generation, and analytics computation
"""
import os
from celery import Celery
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Initialize Celery
celery = Celery('scholarmate')
celery.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///scholarmate.db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@celery.task(name='generate_quiz_async')
def generate_quiz_async(subject: str, topic: str, difficulty: str, num_questions: int = 10):
    """
    Asynchronously generate quiz questions
    """
    from ml_services import quiz_engine
    from models import Quiz, Question
    
    session = SessionLocal()
    
    try:
        # Generate questions
        questions = quiz_engine.generate_quiz(subject, topic, difficulty, num_questions)
        
        # Create quiz
        quiz = Quiz(
            title=f"{topic} - {difficulty.capitalize()} Quiz",
            subject=subject,
            topic=topic,
            difficulty_level=difficulty,
            is_adaptive=True
        )
        session.add(quiz)
        session.flush()
        
        # Add questions
        for q_data in questions:
            question = Question(
                quiz_id=quiz.id,
                question_text=q_data['question_text'],
                question_type=q_data.get('question_type', 'multiple_choice'),
                difficulty_score=q_data.get('difficulty_score', 0.5),
                bloom_taxonomy_level=q_data.get('bloom_level', 'understand')
            )
            session.add(question)
        
        session.commit()
        
        return {
            'success': True,
            'quiz_id': quiz.id,
            'num_questions': len(questions)
        }
    
    except Exception as e:
        session.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        session.close()


@celery.task(name='update_performance_metrics')
def update_performance_metrics(user_id: int):
    """
    Recalculate and update performance metrics for a user
    """
    from models import PerformanceMetric, Session, QuizAttempt, Quiz
    from ml_services import analytics_engine
    from sqlalchemy import func
    
    session = SessionLocal()
    
    try:
        # Get all subjects the user has studied
        subjects = session.query(Session.subject).filter_by(user_id=user_id).distinct().all()
        
        today = datetime.utcnow().date()
        
        for (subject,) in subjects:
            # Get topics in this subject
            topics = session.query(Session.topic).filter_by(
                user_id=user_id,
                subject=subject
            ).distinct().all()
            
            for (topic,) in topics:
                # Get or create metric
                metric = session.query(PerformanceMetric).filter_by(
                    user_id=user_id,
                    subject=subject,
                    topic=topic,
                    date=today
                ).first()
                
                if not metric:
                    metric = PerformanceMetric(
                        user_id=user_id,
                        subject=subject,
                        topic=topic,
                        date=today
                    )
                    session.add(metric)
                
                # Count sessions
                metric.sessions_count = session.query(Session).filter_by(
                    user_id=user_id,
                    subject=subject,
                    topic=topic
                ).count()
                
                # Count quizzes
                metric.quizzes_attempted = session.query(QuizAttempt).join(Quiz).filter(
                    QuizAttempt.user_id == user_id,
                    Quiz.subject == subject,
                    Quiz.topic == topic
                ).count()
                
                # Calculate average quiz score
                avg_score = session.query(func.avg(QuizAttempt.percentage)).join(Quiz).filter(
                    QuizAttempt.user_id == user_id,
                    Quiz.subject == subject,
                    Quiz.topic == topic,
                    QuizAttempt.completed_at.isnot(None)
                ).scalar()
                
                metric.average_quiz_score = (avg_score / 100) if avg_score else None
                
                # Calculate total time spent
                total_time = session.query(func.sum(Session.duration_seconds)).filter_by(
                    user_id=user_id,
                    subject=subject,
                    topic=topic
                ).scalar() or 0
                
                metric.total_time_spent_minutes = total_time // 60
                
                # Calculate mastery level
                quiz_attempts = session.query(QuizAttempt).join(Quiz).filter(
                    QuizAttempt.user_id == user_id,
                    Quiz.subject == subject,
                    Quiz.topic == topic,
                    QuizAttempt.completed_at.isnot(None)
                ).all()
                
                quiz_scores = [attempt.percentage / 100 for attempt in quiz_attempts]
                
                metric.mastery_level = analytics_engine.calculate_mastery_level(
                    quiz_scores,
                    metric.sessions_count,
                    metric.total_time_spent_minutes
                )
        
        session.commit()
        
        return {
            'success': True,
            'user_id': user_id,
            'subjects_updated': len(subjects)
        }
    
    except Exception as e:
        session.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        session.close()


@celery.task(name='generate_learning_path')
def generate_learning_path(user_id: int, subject: str):
    """
    Generate personalized learning path for a user
    """
    from models import LearningPath, PerformanceMetric
    from ml_services import adaptive_engine
    
    session = SessionLocal()
    
    try:
        # Get user performance
        metrics = session.query(PerformanceMetric).filter_by(
            user_id=user_id,
            subject=subject
        ).all()
        
        user_performance = {}
        for metric in metrics:
            if metric.topic:
                user_performance[metric.topic] = {
                    'mastery_level': metric.mastery_level,
                    'avg_quiz_score': metric.average_quiz_score or 0
                }
        
        # Get available topics (simplified - should come from config)
        available_topics = [
            'Algebra', 'Geometry', 'Calculus', 'Statistics', 
            'Trigonometry', 'Number Theory'
        ]
        
        # Generate recommendations
        recommendations = adaptive_engine.recommend_next_topics(
            user_performance,
            subject,
            available_topics
        )
        
        # Get or create learning path
        learning_path = session.query(LearningPath).filter_by(
            user_id=user_id,
            subject=subject
        ).first()
        
        if not learning_path:
            learning_path = LearningPath(
                user_id=user_id,
                subject=subject
            )
            session.add(learning_path)
        
        # Update recommendations
        recommended_topics = [r['topic'] for r in recommendations]
        learning_path.set_recommended_topics(recommended_topics)
        learning_path.updated_at = datetime.utcnow()
        
        session.commit()
        
        return {
            'success': True,
            'user_id': user_id,
            'subject': subject,
            'recommendations': recommendations
        }
    
    except Exception as e:
        session.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        session.close()


@celery.task(name='train_recommendation_model')
def train_recommendation_model():
    """
    Train or update the recommendation model using student data
    """
    from models import User, QuizAttempt, Session as SessionModel
    from ml_services import adaptive_engine
    import pandas as pd
    
    session = SessionLocal()
    
    try:
        # Fetch student data
        users = session.query(User).all()
        
        student_data = []
        for user in users:
            # Calculate metrics
            total_sessions = session.query(SessionModel).filter_by(user_id=user.id).count()
            
            avg_quiz_score = session.query(func.avg(QuizAttempt.percentage)).filter_by(
                user_id=user.id
            ).scalar() or 0
            
            total_time = session.query(func.sum(SessionModel.duration_seconds)).filter_by(
                user_id=user.id
            ).scalar() or 0
            
            student_data.append({
                'user_id': user.id,
                'sessions_count': total_sessions,
                'avg_quiz_score': avg_quiz_score / 100,
                'time_spent_minutes': total_time // 60
            })
        
        if len(student_data) < 3:
            return {
                'success': False,
                'error': 'Insufficient data for training'
            }
        
        df = pd.DataFrame(student_data)
        
        # Cluster students
        clusters = adaptive_engine.cluster_students(df)
        
        # Store cluster information (simplified - should be stored in database)
        return {
            'success': True,
            'num_students': len(student_data),
            'num_clusters': len(set(clusters))
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        session.close()


@celery.task(name='cleanup_old_data')
def cleanup_old_data(days: int = 90):
    """
    Clean up old session data and metrics
    """
    from models import Session as SessionModel, PerformanceMetric
    
    session = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old sessions
        deleted_sessions = session.query(SessionModel).filter(
            SessionModel.timestamp < cutoff_date
        ).delete()
        
        # Delete old metrics
        deleted_metrics = session.query(PerformanceMetric).filter(
            PerformanceMetric.date < cutoff_date.date()
        ).delete()
        
        session.commit()
        
        return {
            'success': True,
            'deleted_sessions': deleted_sessions,
            'deleted_metrics': deleted_metrics
        }
    
    except Exception as e:
        session.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        session.close()


# Periodic tasks
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Setup periodic background tasks
    """
    # Update metrics daily at midnight
    sender.add_periodic_task(
        86400.0,  # 24 hours
        update_all_metrics.s(),
        name='update_all_metrics_daily'
    )
    
    # Train recommendation model weekly
    sender.add_periodic_task(
        604800.0,  # 7 days
        train_recommendation_model.s(),
        name='train_model_weekly'
    )
    
    # Cleanup old data monthly
    sender.add_periodic_task(
        2592000.0,  # 30 days
        cleanup_old_data.s(),
        name='cleanup_monthly'
    )


@celery.task(name='update_all_metrics')
def update_all_metrics():
    """
    Update metrics for all users
    """
    from models import User
    
    session = SessionLocal()
    
    try:
        users = session.query(User).all()
        
        for user in users:
            update_performance_metrics.delay(user.id)
        
        return {
            'success': True,
            'users_queued': len(users)
        }
    
    finally:
        session.close()


if __name__ == '__main__':
    celery.start()
