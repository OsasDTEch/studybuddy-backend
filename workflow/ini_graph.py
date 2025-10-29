"""
StudyBuddy - Simplified LangGraph Workflow with Memory
Ready for FastAPI integration
"""

from typing import TypedDict, Literal, Annotated, Optional
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
import operator
import uuid

# Import your agents
from agents.router_agent import router_agent
from agents.teacher_agent import teacher_agent
from agents.quiz_generator_agent import quiz_generator_agent
from agents.quiz_evaluator_agent import quiz_evaluator_agent
from agents.schemas import RouterOutput, TeacherOutput, QuizGeneratorOutput, QuizEvaluatorOutput


# ============================================================
# STATE DEFINITION
# ============================================================

class StudyBuddyState(TypedDict):
    """Minimal state for the workflow"""
    # Input
    user_message: str

    # Messages history (accumulates)
    messages: Annotated[list[dict], operator.add]

    # Router output
    intent: Optional[str]
    subject: Optional[str]
    topic: Optional[str]
    difficulty: Optional[str]
    needs_agent: bool

    # Active quiz tracking
    active_quiz: Optional[dict]

    # Final response
    response: str
    next_action: Optional[str]  # "wait_answer", "retry", None


# ============================================================
# NODE FUNCTIONS
# ============================================================

def router_node(state: StudyBuddyState) -> StudyBuddyState:
    """Route user intent"""
    print(f"🔀 ROUTER: {state['user_message'][:50]}")

    # Call router agent
    result = router_agent.run_sync(state["user_message"])
    output: RouterOutput = result.output

    # Update state
    state["intent"] = output.intent
    state["subject"] = output.subject
    state["topic"] = output.topic
    state["difficulty"] = output.difficulty or "intermediate"
    state["needs_agent"] = output.needs_agent

    # Add to messages
    state["messages"] = [{
        "role": "user",
        "content": state["user_message"]
    }]

    # Handle direct responses (greetings, off-topic)
    if not output.needs_agent:
        state["response"] = output.direct_response
        state["next_action"] = None
        state["messages"].append({
            "role": "assistant",
            "content": output.direct_response
        })
        print(f"✅ ROUTER: Direct response - {output.intent}")
        return state

    print(f"✅ ROUTER: {output.intent} → {output.subject}/{output.topic}")
    return state


def teacher_node(state: StudyBuddyState) -> StudyBuddyState:
    """Teach concepts"""
    print(f"👨‍🏫 TEACHER: {state['topic']}")

    # Build prompt with context
    prompt = f"""
Student Question: {state['user_message']}
Subject: {state['subject']}
Topic: {state['topic']}
Difficulty: {state['difficulty']}

Provide a clear explanation with examples.
"""

    # Call teacher agent
    result = teacher_agent.run_sync(prompt)
    output: TeacherOutput = result.output

    # Format response
    response = f"{output.explanation}\n\n"

    if output.examples:
        response += "**Examples:**\n"
        for i, ex in enumerate(output.examples, 1):
            response += f"{i}. {ex}\n"
        response += "\n"

    if output.analogies:
        response += f"💡 {output.analogies[0]}\n\n"

    response += f"**Check:** {output.check_question}\n\n"
    response += f"*{output.next_steps}*"

    state["response"] = response
    state["next_action"] = "wait_answer"

    state["messages"].append({
        "role": "assistant",
        "content": response
    })

    print(f"✅ TEACHER: Explanation provided")
    return state


def quiz_generator_node(state: StudyBuddyState) -> StudyBuddyState:
    """Generate quiz"""
    print(f"📝 QUIZ: {state['topic']}")

    prompt = f"""
Generate a practice problem:
Subject: {state['subject']}
Topic: {state['topic']}
Difficulty: {state['difficulty']}

Create an engaging problem with hints.
"""

    # Call quiz generator
    result = quiz_generator_agent.run_sync(prompt)
    output: QuizGeneratorOutput = result.output

    # Save quiz to state
    state["active_quiz"] = {
        "problem_text": output.problem_text,
        "hints": output.hints,
        "expected_concepts": output.expected_concepts,
        "difficulty": output.difficulty
    }

    # Format response
    difficulty_emoji = {"beginner": "🌱", "intermediate": "🌿", "advanced": "🌳"}
    emoji = difficulty_emoji.get(output.difficulty, "📝")

    response = f"{emoji} **Practice Problem** ({output.difficulty})\n\n"
    response += f"{output.problem_text}\n\n"
    response += "Type your answer when ready! 💡 Need a hint? Just ask!"

    state["response"] = response
    state["next_action"] = "wait_answer"

    state["messages"].append({
        "role": "assistant",
        "content": response
    })

    print(f"✅ QUIZ: Problem created")
    return state


def quiz_evaluator_node(state: StudyBuddyState) -> StudyBuddyState:
    """Evaluate answer"""
    print(f"🔍 EVALUATOR: Checking answer")

    quiz = state["active_quiz"]

    prompt = f"""
Evaluate this answer:

Problem: {quiz["problem_text"]}
Student Answer: {state["user_message"]}
Expected Concepts: {', '.join(quiz["expected_concepts"])}

Provide feedback.
"""

    # Call evaluator
    result = quiz_evaluator_agent.run_sync(prompt)
    output: QuizEvaluatorOutput = result.output

    # Format response
    if output.is_correct:
        response = "🎉 **Excellent!** "
    elif output.correctness > 0.6:
        response = "👍 **Good effort!** "
    else:
        response = "💭 **Let's work through this.** "

    response += f"{output.feedback}\n\n"

    if output.strengths:
        response += "**What you did well:**\n"
        for s in output.strengths:
            response += f"✓ {s}\n"
        response += "\n"

    if output.misconceptions:
        response += "**Let's clarify:**\n"
        for m in output.misconceptions:
            response += f"• {m}\n"
        response += "\n"

    # Determine next action
    if output.should_retry and output.next_hint:
        response += f"💡 **Hint:** {output.next_hint}\n\nTry again!"
        state["next_action"] = "retry"
    elif not output.is_correct and not output.should_retry:
        response += "Let me explain this again..."
        state["next_action"] = "reteach"
    else:
        response += "🎯 Ready for another problem?"
        state["next_action"] = None
        state["active_quiz"] = None  # Clear quiz

    state["response"] = response

    state["messages"].append({
        "role": "assistant",
        "content": response
    })

    print(f"✅ EVALUATOR: Score={output.correctness:.2f}")
    return state


# ============================================================
# ROUTING LOGIC
# ============================================================

def route_after_router(state: StudyBuddyState) -> Literal["teacher", "quiz_generator", "end"]:
    """Route based on intent"""
    if not state["needs_agent"]:
        return "end"

    # If there's an active quiz, evaluate it
    if state.get("active_quiz"):
        return "quiz_evaluator"

    intent = state["intent"]

    if intent in ["learn", "clarify"]:
        return "teacher"
    elif intent == "practice":
        return "quiz_generator"
    else:
        return "end"


def route_after_evaluation(state: StudyBuddyState) -> Literal["teacher", "end"]:
    """Route after quiz evaluation"""
    next_action = state.get("next_action")

    if next_action == "reteach":
        return "teacher"
    else:
        return "end"


def should_evaluate(state: StudyBuddyState) -> Literal["quiz_evaluator", "router"]:
    """Check if message is an answer to active quiz"""
    if state.get("active_quiz") and state.get("next_action") in ["wait_answer", "retry"]:
        # Simple check: not a new question
        msg = state["user_message"].lower()
        is_new_request = any(kw in msg for kw in ["explain", "teach", "new problem", "different"])

        if not is_new_request:
            return "quiz_evaluator"

    return "router"


# ============================================================
# BUILD GRAPH
# ============================================================

def build_graph() -> CompiledStateGraph:
    """Build the workflow graph with memory"""

    workflow = StateGraph(StudyBuddyState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("teacher", teacher_node)
    workflow.add_node("quiz_generator", quiz_generator_node)
    workflow.add_node("quiz_evaluator", quiz_evaluator_node)

    # Entry point with quiz detection
    workflow.add_conditional_edges(
        START,
        should_evaluate,
        {
            "quiz_evaluator": "quiz_evaluator",
            "router": "router"
        }
    )

    # Router routes to specialized agents
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "teacher": "teacher",
            "quiz_generator": "quiz_generator",
            "quiz_evaluator": "quiz_evaluator",
            "end": END
        }
    )

    # Teacher → END
    workflow.add_edge("teacher", END)

    # Quiz generator → END (waits for answer)
    workflow.add_edge("quiz_generator", END)

    # Quiz evaluator → conditional
    workflow.add_conditional_edges(
        "quiz_evaluator",
        route_after_evaluation,
        {
            "teacher": "teacher",
            "end": END
        }
    )

    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ============================================================
# MAIN FUNCTION FOR FASTAPI
# ============================================================

# Global graph instance
_graph = None

def get_graph() -> CompiledStateGraph:
    """Get or create graph instance"""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_studybuddy_workflow(
    user_message: str,
    thread_id: Optional[str] = None
) -> dict:
    """
    Main function to run the workflow with proper state preservation
    """
    # Generate thread_id if not provided
    if thread_id is None:
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        print(f"🆕 New conversation: {thread_id}")
    else:
        print(f"📝 Continuing: {thread_id}")

    # Get graph
    graph = get_graph()

    # Config for memory persistence
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    # Get current state from memory
    try:
        current_state = graph.get_state(config)
        if current_state.values:
            # Preserve existing state and only update user_message
            initial_state = dict(current_state.values)
            initial_state["user_message"] = user_message
            print(f"📚 Loaded existing state - Active quiz: {initial_state.get('active_quiz') is not None}")
        else:
            # No existing state - create new
            initial_state = {
                "user_message": user_message,
                "messages": [],
                "intent": None,
                "subject": None,
                "topic": None,
                "difficulty": None,
                "needs_agent": True,
                "active_quiz": None,
                "response": "",
                "next_action": None
            }
            print(f"🆕 No existing state - starting fresh")
    except Exception as e:
        # Error loading state - start fresh
        print(f"⚠️ Error loading state: {e}")
        initial_state = {
            "user_message": user_message,
            "messages": [],
            "intent": None,
            "subject": None,
            "topic": None,
            "difficulty": None,
            "needs_agent": True,
            "active_quiz": None,
            "response": "",
            "next_action": None
        }

    # Run graph
    print(f"\n{'='*60}")
    print(f"🚀 Processing: {user_message[:50]}")
    print(f"{'='*60}\n")

    result = await graph.ainvoke(initial_state, config)

    print(f"\n{'='*60}")
    print(f"✅ Complete")
    print(f"{'='*60}\n")

    # Return response
    return {
        "response": result["response"],
        "thread_id": thread_id,
        "next_action": result.get("next_action"),
        "metadata": {
            "intent": result.get("intent"),
            "subject": result.get("subject"),
            "topic": result.get("topic"),
            "has_active_quiz": result.get("active_quiz") is not None
        }
    }

# Sync version
def run_studybuddy_workflow_sync(
    user_message: str,
    thread_id: Optional[str] = None
) -> dict:
    """Synchronous wrapper"""
    import asyncio
    return asyncio.run(run_studybuddy_workflow(user_message, thread_id))