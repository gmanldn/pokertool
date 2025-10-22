"""
LangChain API Router for Poker Hand Analysis

FastAPI router providing endpoints for:
- Conversational hand analysis
- Semantic search over hand histories
- Opponent notes storage and retrieval
- AI-powered poker strategy chat

Author: PokerTool Team
Created: 2025-10-21
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Body, Request, status
from pydantic import BaseModel, Field

from pokertool.langchain_memory_service import get_langchain_service, LangChainMemoryService
from pokertool.rbac import Permission, require_permission

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/ai",
    tags=["AI & LangChain"],
    responses={404: {"description": "Not found"}}
)


# Pydantic models for request/response
class HandAnalysisRequest(BaseModel):
    """Request model for hand analysis."""
    hand_text: str = Field(..., description="Poker hand description")
    query: Optional[str] = Field(None, description="Specific question about the hand")
    find_similar: bool = Field(True, description="Whether to find similar hands")


class HandAnalysisResponse(BaseModel):
    """Response model for hand analysis."""
    hand_text: str
    timestamp: str
    similar_hands: List[Dict[str, Any]] = Field(default_factory=list)
    analysis: Optional[str] = None


class StoreHandRequest(BaseModel):
    """Request model for storing a hand."""
    hand_id: str = Field(..., description="Unique identifier for the hand")
    hand_text: str = Field(..., description="Hand description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class OpponentNoteRequest(BaseModel):
    """Request model for storing opponent notes."""
    player_name: str = Field(..., description="Opponent's name")
    note: str = Field(..., description="Note about the opponent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class OpponentNoteResponse(BaseModel):
    """Response model for opponent notes."""
    note_id: str
    player_name: str
    timestamp: str


class ChatRequest(BaseModel):
    """Request model for chat interface."""
    query: str = Field(..., description="User's question")
    context: Optional[str] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    """Response model for chat interface."""
    query: str
    response: str
    similar_hands: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str


class SimilarHandsQuery(BaseModel):
    """Query model for finding similar hands."""
    query: str = Field(..., description="Search query")
    n_results: int = Field(5, description="Number of results", ge=1, le=20)
    filter_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


class ServiceStatsResponse(BaseModel):
    """Response model for service statistics."""
    vector_store: Dict[str, Any]
    conversation_context: str


# Dependency to get LangChain service
def get_service() -> LangChainMemoryService:
    """Get LangChain service instance."""
    return get_langchain_service()


# API Endpoints

@router.post("/analyze_hand", response_model=HandAnalysisResponse, dependencies=[Depends(require_permission(Permission.USE_AI_ANALYSIS))])
async def analyze_hand(
    request: HandAnalysisRequest,
    service: LangChainMemoryService = Depends(get_service)
) -> HandAnalysisResponse:
    """
    Analyze a poker hand and find similar hands from history.

    This endpoint uses semantic search to find similar hands you've played
    and provides context for decision-making.

    Args:
        request: Hand analysis request containing hand text and query

    Returns:
        Analysis results with similar hands

    Example:
        ```json
        {
            "hand_text": "AA in BTN vs tight UTG 3-bet",
            "query": "Should I 4-bet or call?",
            "find_similar": true
        }
        ```
    """
    try:
        result = service.analyze_hand(
            hand_text=request.hand_text,
            query=request.query,
            find_similar=request.find_similar
        )

        return HandAnalysisResponse(
            hand_text=result["hand_text"],
            timestamp=result["timestamp"],
            similar_hands=result["similar_hands"],
            analysis=f"Found {len(result['similar_hands'])} similar situations"
        )
    except Exception as e:
        logger.error(f"Hand analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/store_hand", dependencies=[Depends(require_permission(Permission.USE_AI_ANALYSIS))])
async def store_hand(
    request: StoreHandRequest,
    service: LangChainMemoryService = Depends(get_service)
) -> Dict[str, str]:
    """
    Store a poker hand in the vector database for future analysis.

    The hand will be embedded and indexed for semantic search.

    Args:
        request: Hand storage request

    Returns:
        Success confirmation

    Example:
        ```json
        {
            "hand_id": "hand_20251021_001",
            "hand_text": "AA vs KK all-in preflop",
            "metadata": {
                "position": "BTN",
                "stack_size": 100,
                "result": "won",
                "amount": 200
            }
        }
        ```
    """
    try:
        service.store_hand(
            hand_id=request.hand_id,
            hand_text=request.hand_text,
            metadata=request.metadata
        )

        return {
            "status": "success",
            "hand_id": request.hand_id,
            "message": "Hand stored successfully"
        }
    except Exception as e:
        logger.error(f"Failed to store hand: {e}")
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")


@router.post("/opponent_note", response_model=OpponentNoteResponse, dependencies=[Depends(require_permission(Permission.USE_AI_ANALYSIS))])
async def add_opponent_note(
    request: OpponentNoteRequest,
    service: LangChainMemoryService = Depends(get_service)
) -> OpponentNoteResponse:
    """
    Add a note about an opponent.

    Notes are stored with embeddings for semantic search, allowing you to
    query like "tight aggressive players" and get relevant notes.

    Args:
        request: Opponent note request

    Returns:
        Note confirmation with ID

    Example:
        ```json
        {
            "player_name": "Player123",
            "note": "Very aggressive preflop, tight postflop. 3-bets light from BTN",
            "metadata": {
                "session": "2025-10-21",
                "stakes": "NL100"
            }
        }
        ```
    """
    try:
        note_id = service.vector_store.add_opponent_note(
            player_name=request.player_name,
            note=request.note,
            metadata=request.metadata
        )

        return OpponentNoteResponse(
            note_id=note_id,
            player_name=request.player_name,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to add opponent note: {e}")
        raise HTTPException(status_code=500, detail=f"Note storage failed: {str(e)}")


@router.get("/opponent_notes/{player_name}", dependencies=[Depends(require_permission(Permission.USE_AI_ANALYSIS))])
async def get_opponent_notes(
    player_name: str,
    limit: int = Query(10, description="Maximum number of notes", ge=1, le=100),
    service: LangChainMemoryService = Depends(get_service)
) -> Dict[str, Any]:
    """
    Retrieve all notes for a specific opponent.

    Args:
        player_name: Name of the opponent
        limit: Maximum number of notes to return

    Returns:
        List of notes about the opponent
    """
    try:
        notes = service.vector_store.get_opponent_notes(
            player_name=player_name,
            n_results=limit
        )

        return {
            "player_name": player_name,
            "note_count": len(notes),
            "notes": notes
        }
    except Exception as e:
        logger.error(f"Failed to retrieve opponent notes: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.post("/search_similar", response_model=List[Dict[str, Any]], dependencies=[Depends(require_permission(Permission.USE_AI_ANALYSIS))])
async def search_similar_hands(
    query: SimilarHandsQuery,
    service: LangChainMemoryService = Depends(get_service)
) -> List[Dict[str, Any]]:
    """
    Semantic search for similar poker hands.

    Use natural language to find hands matching your criteria.

    Args:
        query: Search query parameters

    Returns:
        List of similar hands

    Example queries:
        - "hands where I made a hero call"
        - "AA in position against aggressive player"
        - "bluff catches on the river"
        - "thin value bets that got called"
    """
    try:
        results = service.vector_store.query_similar_hands(
            query=query.query,
            n_results=query.n_results,
            filter_metadata=query.filter_metadata
        )

        return results
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_permission(Permission.USE_AI_CHAT))])
async def chat_about_poker(
    request: ChatRequest,
    service: LangChainMemoryService = Depends(get_service)
) -> ChatResponse:
    """
    Conversational interface for poker analysis.

    Ask questions about your hands, strategy, or opponents in natural language.
    The system maintains conversation context and searches your hand history
    for relevant examples.

    Args:
        request: Chat request with user query

    Returns:
        AI response with relevant hands from history

    Example queries:
        - "What's my win rate with pocket pairs?"
        - "Show me hands where I 3-bet AA"
        - "How should I play KK against a tight UTG raise?"
    """
    try:
        response = service.chat_about_poker(
            user_query=request.query,
            context=request.context
        )

        # Get similar hands for context
        similar_hands = service.vector_store.query_similar_hands(
            query=request.query,
            n_results=3
        )

        return ChatResponse(
            query=request.query,
            response=response,
            similar_hands=similar_hands,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/stats", response_model=ServiceStatsResponse, dependencies=[Depends(require_permission(Permission.USE_AI_ANALYSIS))])
async def get_service_stats(
    service: LangChainMemoryService = Depends(get_service)
) -> ServiceStatsResponse:
    """
    Get statistics about the LangChain service.

    Returns information about the vector store size, collections,
    and conversation memory state.

    Returns:
        Service statistics
    """
    try:
        stats = service.get_stats()

        return ServiceStatsResponse(
            vector_store=stats["vector_store"],
            conversation_context=stats["conversation_context"]
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.delete("/hand/{hand_id}", dependencies=[Depends(require_permission(Permission.MANAGE_AI_DATA))])
async def delete_hand(
    hand_id: str,
    service: LangChainMemoryService = Depends(get_service)
) -> Dict[str, str]:
    """
    Delete a hand from the vector store.

    Args:
        hand_id: ID of the hand to delete

    Returns:
        Deletion confirmation
    """
    try:
        success = service.vector_store.delete_hand(hand_id)

        if success:
            return {
                "status": "success",
                "hand_id": hand_id,
                "message": "Hand deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Hand not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete hand: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.post("/memory/clear", dependencies=[Depends(require_permission(Permission.MANAGE_AI_DATA))])
async def clear_memory(
    service: LangChainMemoryService = Depends(get_service)
) -> Dict[str, str]:
    """
    Clear the conversational memory.

    This resets the chat context but does not delete stored hands.

    Returns:
        Confirmation message
    """
    try:
        service.conversational_memory.clear()

        return {
            "status": "success",
            "message": "Conversational memory cleared"
        }
    except Exception as e:
        logger.error(f"Failed to clear memory: {e}")
        raise HTTPException(status_code=500, detail=f"Memory clear failed: {str(e)}")


# Health check for AI services
@router.get("/health")
async def ai_health_check() -> Dict[str, Any]:
    """
    Health check for AI/LangChain services.

    Returns:
        Health status
    """
    try:
        service = get_langchain_service()
        stats = service.get_stats()

        return {
            "status": "healthy",
            "service": "LangChain Memory Service",
            "vector_store_size": stats["vector_store"].get("total_documents", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
