"""
Machine Learning and NLP Services for Intelligent Tutoring System
Includes question answering, recommendation engine, and adaptive learning
"""
import os
import numpy as np
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# ML/NLP imports
try:
    from transformers import (
        AutoTokenizer, 
        AutoModelForQuestionAnswering,
        AutoModelForSequenceClassification,
        pipeline
    )
    from sentence_transformers import SentenceTransformer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: Transformers not available. Install with: pip install transformers torch sentence-transformers")
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd

class NLPQuestionAnsweringEngine:
    """
    NLP-powered question answering using Transformer models
    Supports both local models (BERT, T5) and API-based models (Groq)
    """
    def __init__(self, model_name: str = "deepset/bert-base-cased-squad2", use_local: bool = False):
        self.use_local = use_local and TRANSFORMERS_AVAILABLE
        self.model_name = model_name
        
        if self.use_local:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForQuestionAnswering.from_pretrained(model_name)
                self.qa_pipeline = pipeline("question-answering", model=self.model, tokenizer=self.tokenizer)
                print(f"Loaded local QA model: {model_name}")
            except Exception as e:
                print(f"Error loading local model: {e}")
                self.use_local = False
        
        # Sentence embeddings for semantic similarity
        if TRANSFORMERS_AVAILABLE:
            try:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            except:
                self.sentence_model = None
        else:
            self.sentence_model = None
    
    def answer_question(self, question: str, context: str) -> Dict:
        """
        Answer a question given context using local model
        """
        if not self.use_local:
            return {"error": "Local model not available"}
        try:
            result = self.qa_pipeline(question=question, context=context)
            return {
                "answer": result['answer'],
                "confidence": result['score'],
                "start": result['start'],
                "end": result['end']
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_question_embedding(self, question: str) -> Optional[np.ndarray]:
        """
        Generate semantic embedding for a question
        """
        if self.sentence_model is None:
            return None
        
        try:
            embedding = self.sentence_model.encode(question)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts
        """
        if self.sentence_model is None:
            return 0.0
        
        try:
            embeddings = self.sentence_model.encode([text1, text2])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
        except:
            return 0.0
    
    def extract_key_concepts(self, text: str) -> List[str]:
        """
        Extract key concepts from text using NLP
        """
        # Simplified concept extraction - can be enhanced with spaCy NER
        words = text.lower().split()
        # Filter out common words (simplified stopwords)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        concepts = [w for w in words if w not in stopwords and len(w) > 3]
        return concepts[:10]  # Return top 10 concepts


class AdaptiveLearningEngine:
    """
    Adaptive learning and recommendation system
    Uses collaborative filtering and student performance modeling
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def recommend_next_topics(self, user_performance: Dict, subject: str, 
                             available_topics: List[str]) -> List[Dict]:
        """
        Recommend next topics based on user performance and learning path
        
        Args:
            user_performance: Dict with topic -> performance metrics
            subject: Current subject
            available_topics: List of available topics
        
        Returns:
            List of recommended topics with scores
        """
        recommendations = []
        
        for topic in available_topics:
            score = self._calculate_topic_score(topic, user_performance)
            recommendations.append({
                'topic': topic,
                'score': score,
                'reason': self._get_recommendation_reason(topic, user_performance)
            })
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:5]  # Return top 5
    
    def _calculate_topic_score(self, topic: str, user_performance: Dict) -> float:
        """
        Calculate recommendation score for a topic
        """
        # Check if topic already mastered
        if topic in user_performance:
            mastery = user_performance[topic].get('mastery_level', 0)
            if mastery > 0.8:
                return 0.2  # Low score for mastered topics
            else:
                return 0.5 + (1 - mastery) * 0.3  # Medium score for in-progress
        
        # New topic - check prerequisites
        # Simplified: assume topics are ordered by difficulty
        return 0.8  # High score for new topics
    
    def _get_recommendation_reason(self, topic: str, user_performance: Dict) -> str:
        """
        Generate explanation for recommendation
        """
        if topic in user_performance:
            mastery = user_performance[topic].get('mastery_level', 0)
            if mastery < 0.5:
                return "Continue practicing to improve mastery"
            else:
                return "Review to maintain proficiency"
        return "New topic recommended based on your progress"
    
    def adjust_difficulty(self, recent_performance: List[float], 
                         current_difficulty: str) -> str:
        """
        Dynamically adjust difficulty based on recent performance
        
        Args:
            recent_performance: List of recent quiz scores (0-1)
            current_difficulty: Current difficulty level
        
        Returns:
            Recommended difficulty level
        """
        if not recent_performance:
            return current_difficulty
        
        avg_performance = np.mean(recent_performance)
        
        difficulty_levels = ['easy', 'medium', 'hard', 'expert']
        current_idx = difficulty_levels.index(current_difficulty) if current_difficulty in difficulty_levels else 1
        
        # Adjust based on performance
        if avg_performance > 0.85 and current_idx < len(difficulty_levels) - 1:
            return difficulty_levels[current_idx + 1]  # Increase difficulty
        elif avg_performance < 0.6 and current_idx > 0:
            return difficulty_levels[current_idx - 1]  # Decrease difficulty
        else:
            return current_difficulty  # Maintain current level
    
    def predict_performance(self, user_features: np.ndarray) -> float:
        """
        Predict student performance using ML model
        
        Args:
            user_features: Feature vector [time_spent, sessions_count, avg_score, etc.]
        
        Returns:
            Predicted performance score (0-1)
        """
        # Simplified prediction - can be replaced with trained model
        # Features: [total_sessions, avg_quiz_score, time_spent_hours, streak_days]
        
        if len(user_features) < 4:
            return 0.5
        
        # Weighted combination of features
        weights = np.array([0.2, 0.4, 0.2, 0.2])
        normalized_features = np.clip(user_features / np.array([100, 1, 100, 30]), 0, 1)
        prediction = np.dot(normalized_features, weights)
        
        return float(np.clip(prediction, 0, 1))
    
    def cluster_students(self, student_data: pd.DataFrame) -> np.ndarray:
        """
        Cluster students by learning patterns for collaborative filtering
        
        Args:
            student_data: DataFrame with student performance metrics
        
        Returns:
            Cluster labels for each student
        """
        if len(student_data) < 3:
            return np.zeros(len(student_data))
        
        try:
            # Select features for clustering
            features = student_data[['avg_quiz_score', 'sessions_count', 'time_spent_minutes']].values
            
            # Normalize features
            features_scaled = self.scaler.fit_transform(features)
            
            # K-means clustering
            n_clusters = min(3, len(student_data))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(features_scaled)
            
            return clusters
        except Exception as e:
            print(f"Clustering error: {e}")
            return np.zeros(len(student_data))


class QuizGenerationEngine:
    """
    Automated quiz generation with adaptive difficulty
    """
    
    def __init__(self):
        self.question_templates = self._load_question_templates()
    
    def _load_question_templates(self) -> Dict:
        """
        Load question templates for different subjects and topics
        """
        return {
            'mathematics': {
                'algebra': [
                    "Solve for x: {equation}",
                    "Simplify the expression: {expression}",
                    "Factor the polynomial: {polynomial}"
                ],
                'calculus': [
                    "Find the derivative of: {function}",
                    "Calculate the integral: {integral}",
                    "Determine the limit: {limit}"
                ]
            },
            'physics': {
                'mechanics': [
                    "Calculate the force given mass {mass}kg and acceleration {acceleration}m/s²",
                    "Find the velocity after {time}s with initial velocity {v0}m/s and acceleration {a}m/s²"
                ]
            }
        }
    
    def generate_quiz(self, subject: str, topic: str, difficulty: str, 
                     num_questions: int = 10) -> List[Dict]:
        """
        Generate adaptive quiz questions
        
        Args:
            subject: Subject area
            topic: Specific topic
            difficulty: Difficulty level (easy, medium, hard)
            num_questions: Number of questions to generate
        
        Returns:
            List of question dictionaries
        """
        questions = []
        
        # Difficulty score mapping
        difficulty_scores = {'easy': 0.3, 'medium': 0.5, 'hard': 0.7, 'expert': 0.9}
        base_score = difficulty_scores.get(difficulty, 0.5)
        
        for i in range(num_questions):
            question = self._generate_single_question(subject, topic, base_score)
            questions.append(question)
        
        return questions
    
    def _generate_single_question(self, subject: str, topic: str, 
                                  difficulty_score: float) -> Dict:
        """
        Generate a single question
        """
        # Simplified question generation - in production, use question banks or GPT
        templates = self.question_templates.get(subject, {}).get(topic, [])
        
        if not templates:
            return {
                'question_text': f"Explain a key concept in {topic}",
                'question_type': 'short_answer',
                'difficulty_score': difficulty_score,
                'bloom_level': 'understand'
            }
        
        import random
        template = random.choice(templates)
        
        return {
            'question_text': template,
            'question_type': 'multiple_choice',
            'difficulty_score': difficulty_score,
            'bloom_level': self._assign_bloom_level(difficulty_score)
        }
    
    def _assign_bloom_level(self, difficulty_score: float) -> str:
        """
        Assign Bloom's taxonomy level based on difficulty
        """
        if difficulty_score < 0.3:
            return 'remember'
        elif difficulty_score < 0.5:
            return 'understand'
        elif difficulty_score < 0.7:
            return 'apply'
        elif difficulty_score < 0.85:
            return 'analyze'
        else:
            return 'evaluate'
    
    def evaluate_answer(self, student_answer: str, correct_answer: str, 
                       question_type: str) -> Tuple[bool, float, str]:
        """
        Evaluate student answer and provide feedback
        
        Returns:
            (is_correct, partial_credit, feedback)
        """
        if question_type == 'multiple_choice':
            is_correct = student_answer.strip().lower() == correct_answer.strip().lower()
            return is_correct, 1.0 if is_correct else 0.0, self._generate_feedback(is_correct)
        
        elif question_type == 'short_answer':
            # Use semantic similarity for short answers
            similarity = self._calculate_text_similarity(student_answer, correct_answer)
            is_correct = similarity > 0.7
            partial_credit = similarity
            return is_correct, partial_credit, self._generate_feedback(is_correct, similarity)
        
        return False, 0.0, "Unable to evaluate answer"
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text answers
        """
        # Simplified similarity - can use sentence transformers
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _generate_feedback(self, is_correct: bool, score: float = None) -> str:
        """
        Generate formative feedback
        """
        if is_correct:
            return "Excellent! Your answer is correct."
        elif score and score > 0.5:
            return f"Partially correct ({score*100:.0f}%). Review the key concepts and try again."
        else:
            return "Incorrect. Let's review this concept together."


class LearningAnalytics:
    """
    Analytics engine for tracking and visualizing student progress
    """
    
    def calculate_mastery_level(self, quiz_scores: List[float], 
                               session_count: int, time_spent: int) -> float:
        """
        Calculate mastery level for a topic
        
        Args:
            quiz_scores: List of quiz scores (0-1)
            session_count: Number of learning sessions
            time_spent: Total time spent in minutes
        
        Returns:
            Mastery level (0-1)
        """
        if not quiz_scores:
            return 0.0
        
        # Weighted components
        avg_score = np.mean(quiz_scores)
        recent_trend = self._calculate_trend(quiz_scores)
        engagement = min(session_count / 10, 1.0)  # Normalize to 10 sessions
        
        mastery = (avg_score * 0.5) + (recent_trend * 0.3) + (engagement * 0.2)
        return float(np.clip(mastery, 0, 1))
    
    def _calculate_trend(self, scores: List[float]) -> float:
        """
        Calculate performance trend (improving, stable, declining)
        """
        if len(scores) < 2:
            return scores[0] if scores else 0.5
        
        # Simple linear trend
        recent = scores[-3:] if len(scores) >= 3 else scores
        trend = (recent[-1] - recent[0]) / len(recent)
        
        # Normalize to 0-1
        return float(np.clip(0.5 + trend, 0, 1))
    
    def identify_strengths_weaknesses(self, performance_by_topic: Dict) -> Dict:
        """
        Identify student's strengths and weaknesses
        
        Args:
            performance_by_topic: Dict of topic -> performance metrics
        
        Returns:
            Dict with strengths and weaknesses
        """
        if not performance_by_topic:
            return {'strengths': [], 'weaknesses': [], 'needs_review': []}
        
        strengths = []
        weaknesses = []
        needs_review = []
        
        for topic, metrics in performance_by_topic.items():
            mastery = metrics.get('mastery_level', 0)
            
            if mastery >= 0.8:
                strengths.append(topic)
            elif mastery < 0.5:
                weaknesses.append(topic)
            else:
                needs_review.append(topic)
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'needs_review': needs_review
        }
    
    def generate_progress_report(self, user_id: int, subject: str = None) -> Dict:
        """
        Generate comprehensive progress report
        """
        # This would query the database for actual metrics
        # Placeholder structure
        return {
            'user_id': user_id,
            'subject': subject,
            'overall_progress': 0.0,
            'topics_completed': 0,
            'total_time_spent': 0,
            'average_score': 0.0,
            'mastery_by_topic': {},
            'recommendations': []
        }


# Singleton instances
nlp_engine = NLPQuestionAnsweringEngine()
adaptive_engine = AdaptiveLearningEngine()
quiz_engine = QuizGenerationEngine()
analytics_engine = LearningAnalytics()
