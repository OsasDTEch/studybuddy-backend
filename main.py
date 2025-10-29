"""
StudyBuddy FastAPI Application
Simple endpoint for chat with thread-based memory
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn

from workflow.ini_graph import run_studybuddy_workflow

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="StudyBuddy API",
    description="AI tutoring system with conversation memory",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message", min_length=1)
    thread_id: Optional[str] = Field(
        "", description="Thread ID for conversation continuity (leave empty to start new thread)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Explain quadratic equations to me",
                "thread_id": ""
            }
        }

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response")
    thread_id: str = Field(..., description="Thread ID for this conversation")
    next_action: Optional[str] = Field(None, description="Expected next action (wait_answer, retry, None)")
    metadata: dict = Field(..., description="Additional metadata about the response")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Let me explain quadratic equations...",
                "thread_id": "thread_a1b2c3d4",
                "next_action": "wait_answer",
                "metadata": {
                    "intent": "learn",
                    "subject": "Math",
                    "topic": "Quadratic Equations",
                    "has_active_quiz": False
                }
            }
        }


class HealthResponse(BaseModel):
    status: str
    message: str


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "StudyBuddy API is running"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "message": "All systems operational"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint

    - **message**: User's input message
    - **thread_id**: Optional thread ID to continue a conversation
                     If not provided, a new thread is created

    Returns the AI response and thread_id for conversation continuity
    """
    try:
        result = await run_studybuddy_workflow(
            user_message=request.message,
            thread_id=request.thread_id
        )

        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


# @app.post("/new-conversation", response_model=ChatResponse)
# async def new_conversation(request: ChatRequest):
#     """
#     Start a new conversation (ignores thread_id if provided)
#
#     - **message**: User's first message
#
#     Always creates a new thread
#     """
#     try:
#         result = await run_studybuddy_workflow(
#             user_message=request.message,
#             thread_id=None  # Force new thread
#         )
#
#         return ChatResponse(**result)
#
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error starting conversation: {str(e)}"
#         )


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

