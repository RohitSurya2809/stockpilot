"""
StockPilot Assistant API Routes

Endpoints for the AI assistant that explains page content
in natural language. Does NOT execute actions - only interprets data.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from models.database import get_db
from assistant.stockpilot_assistant import StockPilotAssistant

router = APIRouter(prefix="/assistant", tags=["Assistant"])


class AssistantRequest(BaseModel):
    page: str  # 'dashboard', 'analysis', 'simulation', 'forecast'
    page_data: Optional[Dict[str, Any]] = None
    question: Optional[str] = None


class AssistantResponse(BaseModel):
    response: str
    page: str
    source: str = "ollama"


@router.post("/explain")
async def explain_page(
    request: AssistantRequest,
    db: Session = Depends(get_db)
):
    """
    Get AI explanation of current page content.
    Sends page data to LLM and returns natural language insight.
    """
    try:
        assistant = StockPilotAssistant(db)

        if request.page == 'dashboard':
            response = assistant.explain_dashboard(request.page_data or {})
        elif request.page == 'analysis':
            response = assistant.explain_analysis(request.page_data or {})
        elif request.page == 'forecast':
            response = assistant.explain_forecast(request.page_data or {})
        elif request.page == 'simulation':
            response = assistant.explain_simulation(request.page_data or {})
        else:
            response = assistant.answer_question(
                question=request.question or f"What am I looking at on the {request.page} page?",
                page_context=request.page_data
            )

        return AssistantResponse(response=response, page=request.page)

    except Exception as e:
        error_msg = str(e)
        if "Cannot connect to Ollama" in error_msg:
            return AssistantResponse(
                response="Assistant is offline - Ollama server is not reachable. Analysis features still work without it.",
                page=request.page,
                source="fallback"
            )
        raise HTTPException(status_code=500, detail=f"Assistant error: {error_msg}")


@router.post("/ask")
async def ask_assistant(
    request: AssistantRequest,
    db: Session = Depends(get_db)
):
    """
    Ask the assistant a free-form question.
    Optionally provide page context for more relevant answers.
    """
    if not request.question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        assistant = StockPilotAssistant(db)
        response = assistant.answer_question(
            question=request.question,
            page_context=request.page_data
        )
        return AssistantResponse(response=response, page=request.page)

    except Exception as e:
        error_msg = str(e)
        if "Cannot connect to Ollama" in error_msg:
            return AssistantResponse(
                response="Assistant is offline - Ollama server is not reachable.",
                page=request.page,
                source="fallback"
            )
        raise HTTPException(status_code=500, detail=f"Assistant error: {error_msg}")


@router.get("/health")
async def assistant_health(db: Session = Depends(get_db)):
    """Check if the assistant (Ollama) is available."""
    try:
        assistant = StockPilotAssistant(db)
        status = assistant.provider.test_connection()
        return {
            "assistant_available": status.get("connected", False),
            "model": status.get("configured_model"),
            "model_loaded": status.get("model_available", False),
            "details": status
        }
    except Exception as e:
        return {
            "assistant_available": False,
            "error": str(e)
        }
