"""
StudyBuddy Lite - Multi-Agent System with PydanticAI
Each agent has a specific role in the student learning journey
"""

from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ============================================================
# AGENT INPUT/OUTPUT MODELS
# ============================================================

# Router Agent I/O
class RouterInput(BaseModel):
    user_message: str
    student_id: str
    conversation_history: Optional[List[dict]] = None

class RouterOutput(BaseModel):
    intent: str = Field(description="learn, practice, review, greeting, clarify, off_topic")
    subject: Optional[str] = Field(default=None, description="Math, Physics, Chemistry, etc.")
    topic: Optional[str] = Field(default=None, description="Specific topic like 'quadratic equations'")
    difficulty: Optional[str] = Field(default=None, description="beginner, intermediate, advanced")
    reasoning: str = Field(description="Why this classification was chosen")
    direct_response: Optional[str] = Field(default=None, description="Direct reply for greetings/off-topic")
    needs_agent: bool = Field(description="True if requires specialized agent, False if handled directly")


# Teacher Agent I/O
class TeacherInput(BaseModel):
    student_id: str
    topic: str
    subject: str
    user_question: str
    difficulty: str
    learning_style: str = "balanced"
    context: Optional[str] = None  # Previous conversation context

class TeacherOutput(BaseModel):
    explanation: str = Field(description="Clear, pedagogical explanation")
    examples: List[str] = Field(description="Concrete examples demonstrating the concept")
    analogies: Optional[List[str]] = Field(default=None, description="Real-world analogies if helpful")
    check_question: str = Field(description="Question to verify understanding")
    key_concepts: List[str] = Field(description="Main concepts covered")
    next_steps: str = Field(description="Suggested next learning steps")


# Quiz Generator I/O
class QuizGeneratorInput(BaseModel):
    student_id: str
    subject: str
    topic: str
    difficulty: str
    num_problems: int = 1
    problem_type: str = "mixed"  # multiple_choice, open_ended, calculation, mixed

class QuizGeneratorOutput(BaseModel):
    problem_text: str = Field(description="The practice problem statement")
    problem_type: str = Field(description="Type of problem")
    hints: List[str] = Field(description="Progressive hints, from subtle to explicit")
    expected_concepts: List[str] = Field(description="Concepts the problem tests")
    difficulty: str
    sample_solution_approach: str = Field(description="How to approach solving this")


# Quiz Evaluator I/O
class QuizEvaluatorInput(BaseModel):
    student_id: str
    problem_text: str
    student_answer: str
    expected_concepts: List[str]
    hints_used: int = 0

class QuizEvaluatorOutput(BaseModel):
    correctness: float = Field(ge=0, le=1, description="Score from 0 to 1")
    is_correct: bool = Field(description="True if answer is substantially correct")
    feedback: str = Field(description="Specific, constructive feedback")
    misconceptions: List[str] = Field(description="Identified misconceptions")
    strengths: List[str] = Field(description="What the student did well")
    next_hint: Optional[str] = Field(default=None, description="Next hint if incorrect")
    should_retry: bool = Field(description="True if student should attempt again")
    mastery_update: str = Field(description="struggling, learning, proficient, mastered")


# Review Agent I/O
class ReviewInput(BaseModel):
    student_id: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    time_period: str = "recent"  # recent, week, month, all

class ReviewOutput(BaseModel):
    summary: str = Field(description="Overview of learning progress")
    topics_covered: List[dict] = Field(description="List of {topic, mastery, times_studied}")
    strengths: List[str] = Field(description="Topics where student excels")
    areas_for_improvement: List[str] = Field(description="Topics needing more work")
    study_recommendations: List[str] = Field(description="Personalized study suggestions")
    next_review_topics: List[str] = Field(description="Topics due for spaced repetition")
    motivational_message: str = Field(description="Encouraging message based on progress")


# Progress Tracker I/O (Background Analysis)
class ProgressTrackerInput(BaseModel):
    student_id: str
    recent_interactions: List[dict]

class ProgressTrackerOutput(BaseModel):
    overall_trajectory: str = Field(description="improving, stable, declining")
    mastery_changes: List[dict] = Field(description="Topics with mastery level changes")
    learning_velocity: str = Field(description="fast, moderate, slow")
    engagement_score: float = Field(ge=0, le=1, description="Student engagement level")
    intervention_needed: bool = Field(description="True if student needs extra support")
    recommendations: List[str] = Field(description="Action items for improvement")