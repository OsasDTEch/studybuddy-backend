"""
StudyBuddy Lite - Pydantic Schemas
Used for validation and LLM agent I/O
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# ENUMS (mirror your SQLAlchemy enums)
# ============================================================

class LearningStyleEnum(str, Enum):
    visual = "visual"
    step_by_step = "step_by_step"
    conceptual = "conceptual"
    balanced = "balanced"


class MasteryLevelEnum(str, Enum):
    struggling = "struggling"
    learning = "learning"
    proficient = "proficient"
    mastered = "mastered"


class IntentEnum(str, Enum):
    learn = "learn"
    practice = "practice"
    review = "review"
    clarify = "clarify"


# ============================================================
# BASE SCHEMAS
# ============================================================

class StudentBase(BaseModel):
    id: str
    name: Optional[str] = None
    learning_style: LearningStyleEnum = LearningStyleEnum.balanced
    total_sessions: int = 0
    wants_challenges: bool = False


class StudentCreate(StudentBase):
    pass


class StudentRead(StudentBase):
    created_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True


# ============================================================
# CONVERSATION SCHEMAS
# ============================================================

class ConversationBase(BaseModel):
    user_message: str
    assistant_response: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    intent: Optional[IntentEnum] = None
    difficulty: Optional[str] = None
    primary_agent: Optional[str] = None
    session_id: Optional[str] = None


class ConversationCreate(ConversationBase):
    student_id: str


class ConversationRead(ConversationBase):
    id: int
    student_id: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ============================================================
# TOPIC PROGRESS SCHEMAS
# ============================================================

class TopicProgressBase(BaseModel):
    subject: str
    topic: str
    mastery_level: MasteryLevelEnum = MasteryLevelEnum.learning
    times_studied: int = 0
    times_correct: int = 0
    times_incorrect: int = 0


class TopicProgressCreate(TopicProgressBase):
    student_id: str


class TopicProgressRead(TopicProgressBase):
    id: int
    student_id: str
    first_studied: datetime
    last_studied: datetime
    next_review_date: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# PRACTICE PROBLEM SCHEMAS
# ============================================================

class PracticeProblemBase(BaseModel):
    subject: str
    topic: str
    difficulty: str
    problem_text: str
    hints: Optional[List[str]] = None
    expected_concepts: Optional[List[str]] = None


class PracticeProblemCreate(PracticeProblemBase):
    pass


class PracticeProblemRead(PracticeProblemBase):
    id: int
    times_used: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# AGENT OUTPUT SCHEMAS
# ============================================================

class RouterOutput(BaseModel):
    subject: str
    topic: str
    intent: IntentEnum
    difficulty: str


class TeacherOutput(BaseModel):
    explanation: str
    examples: Optional[List[str]] = None
    check_question: Optional[str] = None
    covered_concepts: Optional[List[str]] = None


class QuizProblemOutput(BaseModel):
    problem_text: str
    hints: List[str]
    expected_concepts: List[str]
    difficulty: str


class QuizEvaluationOutput(BaseModel):
    correctness: float = Field(..., description="Score between 0 and 1")
    feedback: str
    misconceptions: Optional[List[str]] = None
    next_hint: Optional[str] = None
    overall_comment: Optional[str] = None


class ProgressAnalysisOutput(BaseModel):
    mastery_level: MasteryLevelEnum
    trend: str
    strong_topics: List[str]
    weak_topics: List[str]
    recommendations: List[str]


# ============================================================
# WRAPPERS FOR API RESPONSES (optional)
# ============================================================

class APIResponse(BaseModel):
    status_code:int
    success: bool
    message: str
    data: Optional[Any] = None
