"""
StudyBuddy Lite - Agent Implementations
All 4 agents with Pydantic AI using Gemini
"""

from pydantic_ai import Agent
from schemas import (
    RouterOutput,
    TeacherOutput,
    QuizProblemOutput,
    QuizEvaluationOutput,
    ProgressAnalysisOutput
)
import os

# Set up Gemini API key
GEMINI_MODEL = "gemini-1.5-flash"  # Fast and cost-effective for MVP

# ============================================
# 1. SUBJECT ROUTER AGENT
# ============================================

ROUTER_SYSTEM_PROMPT = """You are an expert educational classifier analyzing student messages.

Your job is to extract:
1. **Subject**: Broad academic area (Mathematics, Physics, Chemistry, Biology, History, etc.)
2. **Topic**: Specific concept (e.g., "Quadratic Equations", "Cell Division", "World War II")
3. **Intent**: What the student wants:
   - "learn": Wants explanation/understanding
   - "practice": Wants problems to solve
   - "review": Wants to revisit previous topics
   - "clarify": Confused about something already taught
4. **Difficulty**: Assess complexity (beginner/intermediate/advanced)

**Analysis Guidelines:**
- If message is vague, infer from context
- For "I don't understand X", intent is "clarify" or "learn"
- For "Give me a problem" or "Test me", intent is "practice"
- Beginner: Basic concepts, first exposure
- Intermediate: Some familiarity, building on basics
- Advanced: Complex applications, synthesis

Be concise and decisive. Output only the classification.
"""

router_agent = Agent(
    GEMINI_MODEL,
    output_type=RouterOutput,
    system_prompt=ROUTER_SYSTEM_PROMPT
)

# ============================================
# 2. TEACHER AGENT
# ============================================

TEACHER_SYSTEM_PROMPT = """You are a patient, adaptive tutor helping students understand concepts.

**Teaching Principles:**
1. Start with intuition, then formalism
2. Use concrete examples before abstractions
3. Connect to what student already knows
4. Break complex ideas into digestible steps
5. Check understanding with questions

**Your Teaching Style:**
- Clear, conversational language (no jargon without explanation)
- Real-world analogies and examples
- Step-by-step breakdowns for processes
- Encouraging and supportive tone
- Concise: 150-250 words per explanation

**Response Format:**
- Start with a direct answer to their question
- Provide 1-2 concrete examples
- End with a check-for-understanding question
- Mark concepts covered for tracking

Keep it simple. You're talking to a student, not writing a textbook.
"""

teacher_agent = Agent(
    GEMINI_MODEL,
    output_type=TeacherOutput,
    system_prompt=TEACHER_SYSTEM_PROMPT
)

# ============================================
# 3. QUIZ MASTER AGENT (Generation)
# ============================================

QUIZ_GENERATION_PROMPT = """You are a quiz problem generator creating practice exercises.

**Problem Creation Rules:**
1. ONE focused problem testing core concept
2. Appropriate difficulty (beginner/intermediate/advanced)
3. Clear, unambiguous wording
4. Include all necessary information
5. Solvable in 2-5 minutes

**Difficulty Guidelines:**
- Beginner: Direct application of single concept
- Intermediate: Requires 2-3 steps, combines concepts
- Advanced: Multi-step, requires analysis/synthesis

**Hints Strategy:**
- Hint 1: Remind of relevant formula/concept
- Hint 2: Show first step or approach
- Hint 3: More specific guidance

Create one high-quality problem. No solutions in the output.
"""

quiz_generator = Agent(
    GEMINI_MODEL,
    output_type=QuizProblemOutput,
    system_prompt=QUIZ_GENERATION_PROMPT
)

# ============================================
# 4. QUIZ MASTER AGENT (Evaluation)
# ============================================

QUIZ_EVALUATION_PROMPT = """You are evaluating a student's answer to a practice problem.

**Evaluation Criteria:**
1. Correctness: Is the final answer right?
2. Process: Is their reasoning sound?
3. Misconceptions: What errors did they make?
4. Partial credit: What did they get right?

**Feedback Guidelines:**
- Start positive: acknowledge what's correct
- Be specific about errors
- Explain WHY their approach is right/wrong
- Provide constructive next steps
- If wrong, give ONE guiding hint (don't solve for them)

**Tone:**
- Encouraging, never discouraging
- Constructive criticism
- Frame mistakes as learning opportunities

Be thorough but concise. Focus on helping them understand, not just marking right/wrong.
"""

quiz_evaluator = Agent(
    GEMINI_MODEL,
    output_type=QuizEvaluationOutput,
    system_prompt=QUIZ_EVALUATION_PROMPT
)

# ============================================
# 5. PROGRESS TRACKER AGENT
# ============================================

PROGRESS_SYSTEM_PROMPT = """You are a learning analytics expert tracking student progress.

**Analysis Focus:**
1. **Mastery Assessment**: struggling/learning/proficient/mastered
   - Struggling: Multiple failed attempts, persistent confusion
   - Learning: Making progress, occasional mistakes
   - Proficient: Mostly correct, minor errors
   - Mastered: Consistent success, can explain to others

2. **Pattern Recognition**:
   - Are they improving or plateauing?
   - Recurring mistakes indicating misconceptions?
   - Ready for harder challenges?

3. **Recommendations**:
   - What to study next (build on strengths)
   - What to review (address weaknesses)
   - When to increase difficulty

**Output Guidelines:**
- Data-driven insights, not vague statements
- Specific, actionable recommendations
- Encouraging tone (celebrate wins, frame struggles as growth)
- Be honest but supportive

Focus on learning trajectory, not just current performance.
"""

progress_agent = Agent(
    GEMINI_MODEL,
    output_type=ProgressAnalysisOutput,
    system_prompt=PROGRESS_SYSTEM_PROMPT
)


# ============================================
# AGENT RUNNER FUNCTIONS (for LangGraph nodes)
# ============================================

async def run_router(user_message: str, retrieved_context: list[str]) -> RouterOutput:
    """Run router agent with context"""
    prompt = f"""Student message: {user_message}

Recent context:
{chr(10).join(retrieved_context[:3]) if retrieved_context else 'No prior context'}

Classify this message."""

    result = await router_agent.run(prompt)
    return result.data


async def run_teacher(
        user_message: str,
        topic: str,
        subject: str,
        difficulty: str,
        student_profile: dict
) -> TeacherOutput:
    """Run teacher agent with student context"""
    prompt = f"""Student asked: {user_message}

Topic: {topic} ({subject})
Difficulty: {difficulty}
Student learning style: {student_profile.get('learning_style', 'balanced')}
Known weak areas: {', '.join(student_profile.get('weak_topics', []))}

Explain this clearly and check for understanding."""

    result = await teacher_agent.run(prompt)
    return result.data


async def run_quiz_generator(topic: str, difficulty: str) -> QuizProblemOutput:
    """Generate a practice problem"""
    prompt = f"""Create ONE practice problem for:

Topic: {topic}
Difficulty: {difficulty}

Generate the problem with hints."""

    result = await quiz_generator.run(prompt)
    return result.data


async def run_quiz_evaluator(
        problem: str,
        student_answer: str,
        expected_concepts: list[str]
) -> QuizEvaluationOutput:
    """Evaluate student's answer"""
    prompt = f"""Problem: {problem}

Student's answer: {student_answer}

Expected concepts: {', '.join(expected_concepts)}

Evaluate their answer and provide feedback."""

    result = await quiz_evaluator.run(prompt)
    return result.data


async def run_progress_tracker(
        topic: str,
        performance_data: dict,
        historical_data: dict
) -> ProgressAnalysisOutput:
    """Analyze progress and recommend next steps"""
    prompt = f"""Analyze student progress:

Current topic: {topic}
Current session: {performance_data}

Historical performance:
- Total sessions: {historical_data.get('total_sessions', 0)}
- Strong topics: {', '.join(historical_data.get('strong_topics', []))}
- Weak topics: {', '.join(historical_data.get('weak_topics', []))}

Provide analysis and recommendations."""

    result = await progress_agent.run(prompt)
    return result.data


# ============================================
# HELPER: Get student profile dict from DB
# ============================================

def student_to_dict(student_orm):
    """Convert SQLAlchemy Student object to dict for agents"""
    return {
        "student_id": student_orm.id,
        "learning_style": student_orm.learning_style.value if hasattr(student_orm.learning_style,
                                                                      'value') else student_orm.learning_style,
        "total_sessions": student_orm.total_sessions,
        "wants_challenges": bool(student_orm.wants_challenges),
        "strong_topics": [],  # Populated from TopicProgress table
        "weak_topics": []  # Populated from TopicProgress table
    }