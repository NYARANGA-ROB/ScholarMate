"""
Enhanced ScholarMate - Intelligent Tutoring System
Integrates ML/NLP, adaptive learning, automated assessment, and analytics
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()
# Import configuration
from config import get_config

# Import models
from models import db, User, Session, Quiz, Question, QuizAttempt, Answer, LearningPath, PerformanceMetric

# Import API routes
from api_routes import api_bp

# Import ML services
from ml_services import nlp_engine, adaptive_engine, quiz_engine, analytics_engine

# Initialize Flask app
app = Flask(__name__, static_url_path='')
app.config.from_object(get_config())

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)

# Initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'
# Register API blueprint
app.register_blueprint(api_bp)

# Subject configurations (enhanced)
SUBJECTS = {
    'mathematics': {
        'topics': ['Algebra', 'Geometry', 'Calculus', 'Statistics', 'Trigonometry', 'Number Theory'],
        'description': 'Master mathematical concepts from basic arithmetic to advanced calculus',
        'icon': 'fa-calculator'
    },
    'physics': {
        'topics': ['Mechanics', 'Thermodynamics', 'Electromagnetism', 'Quantum Physics', 'Optics', 'Waves'],
        'description': 'Understand the fundamental laws that govern our universe',
        'icon': 'fa-atom'
    },
    'chemistry': {
        'topics': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry', 'Biochemistry', 'Analytical Chemistry'],
        'description': 'Explore the composition, structure, and properties of matter',
        'icon': 'fa-flask'
    },
    'computer_science': {
        'topics': ['Programming', 'Data Structures', 'Algorithms', 'Web Development', 'Database Systems', 'Computer Architecture'],
        'description': 'Learn the principles of computing and software development',
        'icon': 'fa-laptop-code'
    }
}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

# Context processor
@app.context_processor
def inject_subjects():
    return dict(subjects=SUBJECTS)

# ==================== Health Check ====================

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0'
    })

# ==================== Authentication Routes ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        
        flash('Invalid username or password.', 'error')
        return render_template('login.html')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([username, email, password, confirm_password]):
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ==================== Main Application Routes ====================

@app.route('/dashboard')
@login_required
def dashboard():
    sessions = Session.query.filter_by(user_id=current_user.id).order_by(Session.timestamp.desc()).limit(10).all()
    
    # Get recent quiz attempts
    recent_quizzes = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.started_at.desc()).limit(5).all()
    
    # Get recommendations
    recommendations = []
    if app.config['ENABLE_RECOMMENDATIONS']:
        try:
            # Get performance data
            performance_metrics = PerformanceMetric.query.filter_by(user_id=current_user.id).all()
            user_performance = {}
            for metric in performance_metrics:
                if metric.topic:
                    user_performance[metric.topic] = {
                        'mastery_level': metric.mastery_level,
                        'avg_quiz_score': metric.average_quiz_score or 0
                    }
            
            # Get recommendations for first subject with data
            if user_performance:
                first_subject = list(SUBJECTS.keys())[0]
                recommendations = adaptive_engine.recommend_next_topics(
                    user_performance,
                    first_subject,
                    SUBJECTS[first_subject]['topics']
                )[:3]  # Top 3 recommendations
        except Exception as e:
            app.logger.error(f"Error getting recommendations: {e}")
    
    return render_template('dashboard.html', 
                         sessions=sessions, 
                         subjects=SUBJECTS,
                         recent_quizzes=recent_quizzes,
                         recommendations=recommendations)

# ==================== Tutoring Routes ====================

@app.route('/tutor/<subject>', methods=['GET'])
@app.route('/tutor', methods=['GET', 'POST'])
@login_required
def tutor(subject=None):
    if request.method == 'GET' and subject:
        return render_template('tutor.html', 
                            subjects=SUBJECTS,
                            subject=subject,
                            topics=SUBJECTS[subject]['topics'] if subject in SUBJECTS else [])
    
    if request.method == 'POST':
        subject = request.form.get('subject', '')
        topic = request.form.get('topic', '')
        question = request.form.get('question', '')
        
        if not subject or not topic or not question:
            flash('Please select a subject, topic, and provide a question.', 'error')
            return render_template('tutor.html', subjects=SUBJECTS)
        
        try:
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                flash('AI Tutor is not properly configured. Please contact support.', 'error')
                return render_template('tutor.html', subjects=SUBJECTS)

            client = Groq(api_key=groq_api_key)
            
            chat_prompt = f"""You are an expert {subject} tutor specializing in {topic} for {current_user.grade_level} students following {current_user.curriculum} curriculum.
            Please explain the following concept/question in a clear, step-by-step manner:

            {question}

            Structure your response with:
            1. Basic concept explanation in simple terms
            2. Key formulas, rules, or principles (if applicable)
            3. Step-by-step solution or explanation
            4. Real-world applications and examples
            5. A practice problem for the student to try
            6. Additional resources or related topics to explore
            
            Format your response in markdown for better readability.
            Use LaTeX notation for mathematical formulas where appropriate."""

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert {subject} tutor. You excel at explaining complex concepts in simple terms while maintaining academic rigor."
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
                frequency_penalty=0.3,
                presence_penalty=0.3,
            )

            response = chat_completion.choices[0].message.content

            # Generate question embedding if NLP is enabled
            question_embedding = None
            if app.config['ENABLE_LOCAL_NLP']:
                try:
                    embedding = nlp_engine.get_question_embedding(question)
                    if embedding is not None:
                        question_embedding = embedding.tolist()
                except Exception as e:
                    app.logger.error(f"Error generating embedding: {e}")

            # Save the tutoring session
            new_session = Session(
                user_id=current_user.id,
                subject=subject,
                topic=topic,
                question=question,
                response=response,
                question_embedding=str(question_embedding) if question_embedding else None
            )
            db.session.add(new_session)
            db.session.commit()

            # Queue background task to update metrics
            if app.config['ENABLE_CELERY_TASKS']:
                try:
                    from celery_worker import update_performance_metrics
                    update_performance_metrics.delay(current_user.id)
                except Exception as e:
                    app.logger.error(f"Error queuing Celery task: {e}")

            return render_template('tutor.html', 
                                subjects=SUBJECTS,
                                response=response, 
                                subject=subject, 
                                topic=topic,
                                question=question)
        except Exception as e:
            app.logger.error(f"Error in tutor route: {e}")
            flash(f'Error: {str(e)}', 'error')
            return render_template('tutor.html', subjects=SUBJECTS)

    return render_template('tutor.html', subjects=SUBJECTS)

# ==================== Quiz Routes ====================

@app.route('/quiz')
@login_required
def quiz_home():
    """Quiz home page"""
    return render_template('quiz_home.html', subjects=SUBJECTS)

@app.route('/quiz/take/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    """Take a specific quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    return render_template('take_quiz.html', quiz=quiz, questions=questions)

@app.route('/quiz/results/<int:attempt_id>')
@login_required
def quiz_results(attempt_id):
    """View quiz results"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('dashboard'))
    
    answers = Answer.query.filter_by(attempt_id=attempt_id).all()
    
    return render_template('quiz_results.html', attempt=attempt, answers=answers)

# ==================== Analytics Routes ====================

@app.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard"""
    if not app.config['ENABLE_ANALYTICS']:
        flash('Analytics feature is not enabled.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('analytics_dashboard.html')

@app.route('/analytics/topic/<subject>/<topic>')
@login_required
def topic_analytics(subject, topic):
    """Detailed analytics for a specific topic"""
    # Get mastery level
    try:
        from sqlalchemy import func
        
        quiz_attempts = QuizAttempt.query.join(Quiz).filter(
            QuizAttempt.user_id == current_user.id,
            Quiz.subject == subject,
            Quiz.topic == topic,
            QuizAttempt.completed_at.isnot(None)
        ).all()
        
        quiz_scores = [attempt.percentage / 100 for attempt in quiz_attempts]
        
        session_count = Session.query.filter_by(
            user_id=current_user.id,
            subject=subject,
            topic=topic
        ).count()
        
        total_time = db.session.query(func.sum(Session.duration_seconds)).filter_by(
            user_id=current_user.id,
            subject=subject,
            topic=topic
        ).scalar() or 0
        
        mastery_level = analytics_engine.calculate_mastery_level(
            quiz_scores,
            session_count,
            total_time // 60
        )
        
        return render_template('topic_analytics.html',
                             subject=subject,
                             topic=topic,
                             mastery_level=mastery_level,
                             quiz_attempts=quiz_attempts,
                             session_count=session_count,
                             total_time=total_time)
    
    except Exception as e:
        app.logger.error(f"Error in topic analytics: {e}")
        flash('Error loading analytics.', 'error')
        return redirect(url_for('analytics'))

# ==================== Profile and Settings Routes ====================

@app.route('/profile')
@login_required
def profile():
    sessions = Session.query.filter_by(user_id=current_user.id).order_by(Session.timestamp.desc()).all()
    return render_template('profile.html', sessions=sessions, subjects=SUBJECTS)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        try:
            new_email = request.form.get('email')
            if new_email and new_email != current_user.email:
                if User.query.filter_by(email=new_email).first():
                    flash('Email already exists.', 'error')
                    return redirect(url_for('settings'))
                current_user.email = new_email

            if 'curriculum' in request.form:
                current_user.curriculum = request.form['curriculum']
            
            if 'grade_level' in request.form:
                current_user.grade_level = request.form['grade_level']
            
            if 'learning_style' in request.form:
                current_user.learning_style = request.form['learning_style']
            
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if current_password and new_password:
                if not current_user.check_password(current_password):
                    flash('Current password is incorrect.', 'error')
                    return redirect(url_for('settings'))
                
                if new_password != confirm_password:
                    flash('New passwords do not match.', 'error')
                    return redirect(url_for('settings'))
                
                current_user.set_password(new_password)
            
            db.session.commit()
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('settings'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating settings: {e}")
            flash(f'Error updating settings: {str(e)}', 'error')
            
    return render_template('settings.html')

# ==================== Additional Routes ====================

@app.route('/progress')
@login_required
def progress():
    from sqlalchemy import func
    
    total_sessions = Session.query.filter_by(user_id=current_user.id).count()
    
    subject_stats = db.session.query(
        Session.subject,
        func.count(Session.id).label('count')
    ).filter_by(user_id=current_user.id)\
     .group_by(Session.subject)\
     .order_by(func.count(Session.id).desc())\
     .all()
    
    recent_sessions = Session.query.filter_by(user_id=current_user.id)\
        .order_by(Session.timestamp.desc())\
        .limit(5).all()
    
    subject_percentages = []
    if total_sessions > 0:
        for subject, count in subject_stats:
            percentage = (count / total_sessions) * 100
            subject_percentages.append((subject, count, percentage))
    
    return render_template('progress.html', 
                         total_sessions=total_sessions,
                         subject_stats=subject_stats,
                         sessions=recent_sessions,
                         subject_percentages=subject_percentages)

@app.route('/history')
@login_required
def history():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        sessions = Session.query.filter_by(user_id=current_user.id)\
            .order_by(Session.timestamp.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        if not sessions.items and page > 1:
            return redirect(url_for('history', page=1))
            
        return render_template('history.html', 
                             sessions=sessions,
                             current_page=page,
                             total_pages=sessions.pages)
    except Exception as e:
        app.logger.error(f"Error loading history: {e}")
        flash(f'Error loading session history: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Keep other existing routes (curriculum, grade_level, help, feedback, about, privacy, terms, contact, delete_account)
# ... (copy from original app.py)

# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ==================== Logging Configuration ====================

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('ScholarMate ITS startup')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
