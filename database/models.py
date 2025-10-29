"""
StudyBuddy Lite - SQLAlchemy Database Models
PostgreSQL schema for student profiles, conversations, and progress tracking
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database.db import Base


class LearningStyleEnum(enum.Enum):
    """Student learning preferences"""
    VISUAL = "visual"
    STEP_BY_STEP = "step_by_step"
    CONCEPTUAL = "conceptual"
    BALANCED = "balanced"


class MasteryLevelEnum(enum.Enum):
    """Topic mastery levels"""
    STRUGGLING = "struggling"
    LEARNING = "learning"
    PROFICIENT = "proficient"
    MASTERED = "mastered"


class IntentEnum(enum.Enum):
    """User intent classification"""
    LEARN = "learn"
    PRACTICE = "practice"
    REVIEW = "review"
    CLARIFY = "clarify"


class Student(Base):
    """Student profile and preferences"""
    __tablename__ = "students"

    id = Column(String(50), primary_key=True)  # e.g., "student_001"
    name = Column(String(100), nullable=True)
    learning_style = Column(Enum(LearningStyleEnum), default=LearningStyleEnum.BALANCED)
    total_sessions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Preferences
    wants_challenges = Column(Integer, default=0)  # 0=false, 1=true (SQLite compatible)

    # Relationships
    conversations = relationship("Conversation", back_populates="student", cascade="all, delete-orphan")
    topic_progress = relationship("TopicProgress", back_populates="student", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation history for context and analytics"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey("students.id"), nullable=False)

    # Message content
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)

    # Classification
    subject = Column(String(100), nullable=True)
    topic = Column(String(200), nullable=True)
    intent = Column(Enum(IntentEnum), nullable=True)
    difficulty = Column(String(20), nullable=True)  # beginner, intermediate, advanced

    # Agent that handled it
    primary_agent = Column(String(50), nullable=True)  # teacher, quiz_master, etc.

    # Session tracking
    session_id = Column(String(100), nullable=True)  # group related messages
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="conversations")


class TopicProgress(Base):
    """Track student mastery of specific topics"""
    __tablename__ = "topic_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey("students.id"), nullable=False)

    subject = Column(String(100), nullable=False)
    topic = Column(String(200), nullable=False)

    # Progress metrics
    mastery_level = Column(Enum(MasteryLevelEnum), default=MasteryLevelEnum.LEARNING)
    times_studied = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)  # for practice problems
    times_incorrect = Column(Integer, default=0)

    # Timestamps
    first_studied = Column(DateTime, default=datetime.utcnow)
    last_studied = Column(DateTime, default=datetime.utcnow)

    # Next review (for spaced repetition)
    next_review_date = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="topic_progress")


class PracticeProblem(Base):
    """Store generated practice problems for reuse"""
    __tablename__ = "practice_problems"

    id = Column(Integer, primary_key=True, autoincrement=True)

    subject = Column(String(100), nullable=False)
    topic = Column(String(200), nullable=False)
    difficulty = Column(String(20), nullable=False)

    # Problem content
    problem_text = Column(Text, nullable=False)
    hints = Column(JSON, nullable=True)  # ["hint1", "hint2"]
    expected_concepts = Column(JSON, nullable=True)  # ["concept1", "concept2"]

    # Usage tracking
    times_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# Database initialization
def init_db(engine):
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


# Helper function to create sample student
def create_sample_student(session, student_id: str = "demo_student"):
    """Create a demo student for testing"""
    student = Student(
        id=student_id,
        name="Demo Student",
        learning_style=LearningStyleEnum.BALANCED,
        wants_challenges=0
    )
    session.add(student)
    session.commit()
    return student