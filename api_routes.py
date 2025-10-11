"""
API Routes for ML/AI features
Includes quiz generation, recommendations, and analytics endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
import json

from models import (
    db, User, Session, Quiz, Question, QuizAttempt, Answer,
    LearningPath, PerformanceMetric, StudyMaterial
)
from ml_services import (
    nlp_engine, adaptive_engine, quiz_engine, analytics_engine
)

api_bp = Blueprint('api', __name__, url_prefix='/api')


# ==================== Quiz API ====================

@api_bp.route('/quiz/generate', methods=['POST'])
@login_required
def generate_quiz():
    """
    Generate adaptive quiz based on student performance
    """
    data = request.json
    subject = data.get('subject')
    topic = data.get('topic')
    difficulty = data.get('difficulty', 'medium')
    num_questions = data.get('num_questions', 10)
    
    if not subject or not topic:
        return jsonify({'error': 'Subject and topic required'}), 400
    
    try:
        # Generate quiz questions
        questions = quiz_engine.generate_quiz(subject, topic, difficulty, num_questions)
        
        # Create quiz in database
        quiz = Quiz(
            title=f"{topic} - {difficulty.capitalize()} Quiz",
            subject=subject,
            topic=topic,
            difficulty_level=difficulty,
            grade_level=current_user.grade_level,
            is_adaptive=True
        )
        db.session.add(quiz)
        db.session.flush()
        
        # Add questions to quiz
        for q_data in questions:
            question = Question(
                quiz_id=quiz.id,
                question_text=q_data['question_text'],
                question_type=q_data.get('question_type', 'multiple_choice'),
                difficulty_score=q_data.get('difficulty_score', 0.5),
                bloom_taxonomy_level=q_data.get('bloom_level', 'understand')
            )
            db.session.add(question)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'quiz_id': quiz.id,
            'num_questions': len(questions),
            'message': 'Quiz generated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/quiz/<int:quiz_id>/start', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    """
    Start a quiz attempt
    """
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Create quiz attempt
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        started_at=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.commit()
    
    # Get questions
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    questions_data = [{
        'id': q.id,
        'question_text': q.question_text,
        'question_type': q.question_type,
        'options': q.get_options(),
        'points': q.points
    } for q in questions]
    
    return jsonify({
        'success': True,
        'attempt_id': attempt.id,
        'quiz_title': quiz.title,
        'questions': questions_data
    })


@api_bp.route('/quiz/attempt/<int:attempt_id>/submit', methods=['POST'])
@login_required
def submit_quiz(attempt_id):
    """
    Submit quiz answers and calculate score
    """
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if attempt.completed_at:
        return jsonify({'error': 'Quiz already submitted'}), 400
    
    data = request.json
    answers = data.get('answers', [])
    
    try:
        # Process each answer
        for answer_data in answers:
            question_id = answer_data.get('question_id')
            student_answer = answer_data.get('answer')
            time_taken = answer_data.get('time_taken', 0)
            
            question = Question.query.get(question_id)
            if not question:
                continue
            
            # Evaluate answer
            is_correct, partial_credit, feedback = quiz_engine.evaluate_answer(
                student_answer,
                question.correct_answer,
                question.question_type
            )
            
            # Save answer
            answer = Answer(
                attempt_id=attempt_id,
                question_id=question_id,
                student_answer=student_answer,
                is_correct=is_correct,
                points_earned=partial_credit * question.points,
                time_taken_seconds=time_taken
            )
            db.session.add(answer)
        
        # Calculate final score
        attempt.completed_at = datetime.utcnow()
        attempt.time_taken_seconds = (attempt.completed_at - attempt.started_at).total_seconds()
        attempt.calculate_score()
        
        # Update performance metrics
        _update_performance_metrics(
            current_user.id,
            attempt.quiz.subject,
            attempt.quiz.topic,
            attempt.percentage / 100
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'score': attempt.score,
            'max_score': attempt.max_score,
            'percentage': attempt.percentage,
            'time_taken': attempt.time_taken_seconds
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Recommendation API ====================

@api_bp.route('/recommendations/topics', methods=['GET'])
@login_required
def get_topic_recommendations():
    """
    Get personalized topic recommendations
    """
    subject = request.args.get('subject')
    
    if not subject:
        return jsonify({'error': 'Subject required'}), 400
    
    try:
        # Get user performance data
        performance_metrics = PerformanceMetric.query.filter_by(
            user_id=current_user.id,
            subject=subject
        ).all()
        
        user_performance = {}
        for metric in performance_metrics:
            user_performance[metric.topic] = {
                'mastery_level': metric.mastery_level,
                'avg_quiz_score': metric.average_quiz_score or 0,
                'sessions_count': metric.sessions_count
            }
        
        # Get available topics (from SUBJECTS config)
        from app import SUBJECTS
        available_topics = SUBJECTS.get(subject, {}).get('topics', [])
        
        # Generate recommendations
        recommendations = adaptive_engine.recommend_next_topics(
            user_performance,
            subject,
            available_topics
        )
        
        return jsonify({
            'success': True,
            'subject': subject,
            'recommendations': recommendations
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/recommendations/difficulty', methods=['POST'])
@login_required
def adjust_difficulty():
    """
    Get recommended difficulty level based on recent performance
    """
    data = request.json
    subject = data.get('subject')
    topic = data.get('topic')
    current_difficulty = data.get('current_difficulty', 'medium')
    
    try:
        # Get recent quiz attempts
        recent_attempts = QuizAttempt.query.join(Quiz).filter(
            QuizAttempt.user_id == current_user.id,
            Quiz.subject == subject,
            Quiz.topic == topic,
            QuizAttempt.completed_at.isnot(None)
        ).order_by(QuizAttempt.completed_at.desc()).limit(5).all()
        
        recent_scores = [attempt.percentage / 100 for attempt in recent_attempts]
        
        # Get recommended difficulty
        recommended_difficulty = adaptive_engine.adjust_difficulty(
            recent_scores,
            current_difficulty
        )
        
        return jsonify({
            'success': True,
            'current_difficulty': current_difficulty,
            'recommended_difficulty': recommended_difficulty,
            'recent_performance': recent_scores
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Analytics API ====================

@api_bp.route('/analytics/progress', methods=['GET'])
@login_required
def get_progress_analytics():
    """
    Get comprehensive progress analytics
    """
    subject = request.args.get('subject')
    days = int(request.args.get('days', 30))
    
    try:
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Query performance metrics
        query = PerformanceMetric.query.filter(
            PerformanceMetric.user_id == current_user.id,
            PerformanceMetric.date >= start_date
        )
        
        if subject:
            query = query.filter(PerformanceMetric.subject == subject)
        
        metrics = query.all()
        
        # Aggregate data
        total_sessions = sum(m.sessions_count for m in metrics)
        total_quizzes = sum(m.quizzes_attempted for m in metrics)
        total_time = sum(m.total_time_spent_minutes for m in metrics)
        
        # Calculate average scores by subject
        subject_performance = {}
        for metric in metrics:
            if metric.subject not in subject_performance:
                subject_performance[metric.subject] = {
                    'scores': [],
                    'mastery': [],
                    'sessions': 0
                }
            
            if metric.average_quiz_score:
                subject_performance[metric.subject]['scores'].append(metric.average_quiz_score)
            subject_performance[metric.subject]['mastery'].append(metric.mastery_level)
            subject_performance[metric.subject]['sessions'] += metric.sessions_count
        
        # Calculate averages
        for subject_key in subject_performance:
            scores = subject_performance[subject_key]['scores']
            mastery = subject_performance[subject_key]['mastery']
            
            subject_performance[subject_key]['avg_score'] = sum(scores) / len(scores) if scores else 0
            subject_performance[subject_key]['avg_mastery'] = sum(mastery) / len(mastery) if mastery else 0
        
        # Get strengths and weaknesses
        topic_performance = {}
        for metric in metrics:
            if metric.topic:
                topic_performance[metric.topic] = {
                    'mastery_level': metric.mastery_level,
                    'avg_quiz_score': metric.average_quiz_score or 0
                }
        
        strengths_weaknesses = analytics_engine.identify_strengths_weaknesses(topic_performance)
        
        return jsonify({
            'success': True,
            'period_days': days,
            'summary': {
                'total_sessions': total_sessions,
                'total_quizzes': total_quizzes,
                'total_time_minutes': total_time,
                'total_time_hours': round(total_time / 60, 1)
            },
            'by_subject': subject_performance,
            'strengths': strengths_weaknesses['strengths'],
            'weaknesses': strengths_weaknesses['weaknesses'],
            'needs_review': strengths_weaknesses['needs_review']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/analytics/mastery/<subject>/<topic>', methods=['GET'])
@login_required
def get_topic_mastery(subject, topic):
    """
    Get detailed mastery level for a specific topic
    """
    try:
        # Get quiz attempts for this topic
        quiz_attempts = QuizAttempt.query.join(Quiz).filter(
            QuizAttempt.user_id == current_user.id,
            Quiz.subject == subject,
            Quiz.topic == topic,
            QuizAttempt.completed_at.isnot(None)
        ).all()
        
        quiz_scores = [attempt.percentage / 100 for attempt in quiz_attempts]
        
        # Get session count
        session_count = Session.query.filter_by(
            user_id=current_user.id,
            subject=subject,
            topic=topic
        ).count()
        
        # Get total time spent
        total_time = db.session.query(func.sum(Session.duration_seconds)).filter_by(
            user_id=current_user.id,
            subject=subject,
            topic=topic
        ).scalar() or 0
        
        # Calculate mastery level
        mastery_level = analytics_engine.calculate_mastery_level(
            quiz_scores,
            session_count,
            total_time // 60
        )
        
        return jsonify({
            'success': True,
            'subject': subject,
            'topic': topic,
            'mastery_level': mastery_level,
            'quiz_attempts': len(quiz_attempts),
            'avg_quiz_score': sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0,
            'session_count': session_count,
            'time_spent_minutes': total_time // 60
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== NLP API ====================

@api_bp.route('/nlp/similarity', methods=['POST'])
@login_required
def calculate_similarity():
    """
    Calculate semantic similarity between two texts
    """
    data = request.json
    text1 = data.get('text1')
    text2 = data.get('text2')
    
    if not text1 or not text2:
        return jsonify({'error': 'Both texts required'}), 400
    
    try:
        similarity = nlp_engine.calculate_similarity(text1, text2)
        
        return jsonify({
            'success': True,
            'similarity': similarity,
            'interpretation': _interpret_similarity(similarity)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/nlp/concepts', methods=['POST'])
@login_required
def extract_concepts():
    """
    Extract key concepts from text
    """
    data = request.json
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'Text required'}), 400
    
    try:
        concepts = nlp_engine.extract_key_concepts(text)
        
        return jsonify({
            'success': True,
            'concepts': concepts
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Helper Functions ====================

def _update_performance_metrics(user_id: int, subject: str, topic: str, score: float):
    """
    Update or create performance metrics for a user
    """
    today = datetime.utcnow().date()
    
    metric = PerformanceMetric.query.filter_by(
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
        db.session.add(metric)
    
    # Update metrics
    metric.quizzes_attempted = (metric.quizzes_attempted or 0) + 1
    
    # Update average quiz score
    if metric.average_quiz_score:
        metric.average_quiz_score = (metric.average_quiz_score + score) / 2
    else:
        metric.average_quiz_score = score
    
    # Recalculate mastery level
    quiz_attempts = QuizAttempt.query.join(Quiz).filter(
        QuizAttempt.user_id == user_id,
        Quiz.subject == subject,
        Quiz.topic == topic
    ).all()
    
    quiz_scores = [attempt.percentage / 100 for attempt in quiz_attempts if attempt.percentage]
    session_count = Session.query.filter_by(user_id=user_id, subject=subject, topic=topic).count()
    total_time = db.session.query(func.sum(Session.duration_seconds)).filter_by(
        user_id=user_id, subject=subject, topic=topic
    ).scalar() or 0
    
    metric.mastery_level = analytics_engine.calculate_mastery_level(
        quiz_scores,
        session_count,
        total_time // 60
    )


def _interpret_similarity(score: float) -> str:
    """
    Interpret similarity score
    """
    if score >= 0.9:
        return "Very similar"
    elif score >= 0.7:
        return "Similar"
    elif score >= 0.5:
        return "Somewhat similar"
    elif score >= 0.3:
        return "Slightly similar"
    else:
        return "Not similar"
