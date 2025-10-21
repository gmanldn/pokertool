"""
LangChain Memory Service for Poker Hand Analysis

This module provides vector-backed memory and conversational AI capabilities
for analyzing poker hands, tracking opponent patterns, and providing strategic advice.

Features:
- ChromaDB vector store for semantic search over poker hands
- Conversational memory for contextual hand analysis
- Opponent notes and pattern storage
- Hand history embedding and retrieval

Author: PokerTool Team
Created: 2025-10-21
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.config import Settings
try:
    from langchain.memory import ConversationBufferMemory
except ImportError:
    # LangChain 0.3+ moved memory to langchain-community
    from langchain_community.chat_message_histories import ChatMessageHistory
    # Create a simple in-memory buffer for compatibility
    ConversationBufferMemory = None

logger = logging.getLogger(__name__)


class PokerVectorStore:
    """
    Vector store for poker hands using ChromaDB.

    Provides semantic search capabilities for:
    - Hand histories
    - Opponent notes
    - Strategy patterns
    - Playing situations
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "poker_hands"
    ):
        """
        Initialize the poker vector store.

        Args:
            persist_directory: Directory to persist the vector database
            collection_name: Name of the collection for poker data
        """
        if persist_directory is None:
            # Default to pokertool data directory
            persist_directory = os.path.join(
                os.path.expanduser("~"),
                ".pokertool",
                "vector_db"
            )

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Poker hand histories and analysis"}
            )
            logger.info(f"Created new collection: {collection_name}")

    def add_hand(
        self,
        hand_id: str,
        hand_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a poker hand to the vector store.

        Args:
            hand_id: Unique identifier for the hand
            hand_text: Text description of the hand
            metadata: Additional metadata (position, stack size, result, etc.)
        """
        if metadata is None:
            metadata = {}

        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "type": "hand_history"
        })

        try:
            self.collection.add(
                documents=[hand_text],
                metadatas=[metadata],
                ids=[hand_id]
            )
            logger.info(f"Added hand {hand_id} to vector store")
        except Exception as e:
            logger.error(f"Failed to add hand {hand_id}: {e}")
            raise

    def add_opponent_note(
        self,
        player_name: str,
        note: str,
        note_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add an opponent note to the vector store.

        Args:
            player_name: Name of the opponent
            note: Text note about the opponent
            note_id: Optional unique ID (auto-generated if not provided)
            metadata: Additional metadata

        Returns:
            The note ID
        """
        if note_id is None:
            note_id = f"opponent_{player_name}_{datetime.now().timestamp()}"

        if metadata is None:
            metadata = {}

        metadata.update({
            "player": player_name,
            "timestamp": datetime.now().isoformat(),
            "type": "opponent_note"
        })

        try:
            self.collection.add(
                documents=[note],
                metadatas=[metadata],
                ids=[note_id]
            )
            logger.info(f"Added opponent note for {player_name}")
            return note_id
        except Exception as e:
            logger.error(f"Failed to add opponent note: {e}")
            raise

    def query_similar_hands(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for similar poker hands using semantic search.

        Args:
            query: Natural language query (e.g., "AA vs tight player in position")
            n_results: Number of results to return
            filter_metadata: Optional filters (e.g., {"position": "BTN"})

        Returns:
            List of similar hands with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )

            formatted_results = []
            if results and results['ids']:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        "id": doc_id,
                        "text": results['documents'][0][i] if results['documents'] else "",
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results.get('distances') else None
                    })

            logger.info(f"Found {len(formatted_results)} similar hands for query: {query}")
            return formatted_results
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def get_opponent_notes(
        self,
        player_name: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all notes for a specific opponent.

        Args:
            player_name: Name of the opponent
            n_results: Maximum number of notes to return

        Returns:
            List of notes about the opponent
        """
        try:
            # ChromaDB requires an operator like $and for multiple conditions
            results = self.collection.get(
                where={"$and": [{"player": player_name}, {"type": "opponent_note"}]},
                limit=n_results
            )

            formatted_results = []
            if results and results['ids']:
                for i, doc_id in enumerate(results['ids']):
                    formatted_results.append({
                        "id": doc_id,
                        "text": results['documents'][i] if results['documents'] else "",
                        "metadata": results['metadatas'][i] if results['metadatas'] else {}
                    })

            return formatted_results
        except Exception as e:
            logger.error(f"Failed to get opponent notes: {e}")
            return []

    def delete_hand(self, hand_id: str) -> bool:
        """
        Delete a hand from the vector store.

        Args:
            hand_id: ID of the hand to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[hand_id])
            logger.info(f"Deleted hand {hand_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete hand {hand_id}: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "persist_directory": str(self.persist_directory)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


class PokerConversationalMemory:
    """
    Conversational memory for poker hand analysis chat.

    Maintains context across multiple questions about poker hands,
    strategies, and opponent analysis.

    Simple in-memory implementation compatible with LangChain 0.3+
    """

    def __init__(
        self,
        memory_type: str = "buffer",
        max_token_limit: int = 2000
    ):
        """
        Initialize conversational memory.

        Args:
            memory_type: Type of memory ("buffer" or "summary")
            max_token_limit: Maximum tokens to keep in memory
        """
        self.memory_type = memory_type
        self.max_token_limit = max_token_limit
        self.conversation_history: List[Dict[str, str]] = []

        logger.info(f"Initialized {memory_type} memory")

    def add_exchange(self, user_input: str, ai_response: str) -> None:
        """
        Add a conversation exchange to memory.

        Args:
            user_input: User's question or input
            ai_response: AI's response
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only last N exchanges to respect token limit
        # Simple heuristic: ~4 chars per token
        max_exchanges = self.max_token_limit // 100  # Roughly 25 chars per exchange avg
        if len(self.conversation_history) > max_exchanges * 2:
            self.conversation_history = self.conversation_history[-(max_exchanges * 2):]

    def get_context(self) -> str:
        """
        Get the conversation context as a string.

        Returns:
            Formatted conversation history
        """
        if not self.conversation_history:
            return "No conversation history"

        context_lines = []
        for msg in self.conversation_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            context_lines.append(f"{role}: {msg['content']}")

        return "\n".join(context_lines)

    def clear(self) -> None:
        """Clear the conversation memory."""
        self.conversation_history.clear()
        logger.info("Cleared conversation memory")


class LangChainMemoryService:
    """
    Main service for LangChain-powered poker hand analysis.

    Combines vector store and conversational memory for comprehensive
    poker analysis capabilities.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        enable_logging: bool = True
    ):
        """
        Initialize the LangChain memory service.

        Args:
            persist_directory: Directory for vector database persistence
            enable_logging: Whether to enable detailed logging
        """
        if enable_logging:
            logging.basicConfig(level=logging.INFO)

        self.vector_store = PokerVectorStore(persist_directory=persist_directory)
        self.conversational_memory = PokerConversationalMemory()

        logger.info("LangChain Memory Service initialized")

    def analyze_hand(
        self,
        hand_text: str,
        query: Optional[str] = None,
        find_similar: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a poker hand, optionally finding similar hands.

        Args:
            hand_text: Description of the poker hand
            query: Optional specific question about the hand
            find_similar: Whether to find similar hands from history

        Returns:
            Analysis results with similar hands if requested
        """
        result = {
            "hand_text": hand_text,
            "timestamp": datetime.now().isoformat(),
            "similar_hands": []
        }

        if find_similar:
            search_query = query if query else hand_text
            similar = self.vector_store.query_similar_hands(search_query, n_results=3)
            result["similar_hands"] = similar

        return result

    def store_hand(
        self,
        hand_id: str,
        hand_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store a poker hand in the vector database.

        Args:
            hand_id: Unique identifier
            hand_text: Hand description
            metadata: Additional metadata
        """
        self.vector_store.add_hand(hand_id, hand_text, metadata)

    def chat_about_poker(
        self,
        user_query: str,
        context: Optional[str] = None
    ) -> str:
        """
        Chat interface for poker questions.

        Args:
            user_query: User's question
            context: Optional additional context

        Returns:
            Response (placeholder for now, will integrate with LLM)
        """
        # Find relevant hands
        similar_hands = self.vector_store.query_similar_hands(user_query, n_results=3)

        # Build response with context
        response = f"Query: {user_query}\n\n"
        if similar_hands:
            response += "Relevant hands from your history:\n"
            for hand in similar_hands:
                response += f"- {hand['text'][:100]}...\n"

        # Store in conversational memory
        self.conversational_memory.add_exchange(user_query, response)

        return response

    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "vector_store": self.vector_store.get_collection_stats(),
            "conversation_context": self.conversational_memory.get_context()
        }


# Global instance (lazy-loaded)
_service_instance: Optional[LangChainMemoryService] = None


def get_langchain_service() -> LangChainMemoryService:
    """
    Get or create the global LangChain memory service instance.

    Returns:
        LangChain memory service singleton
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = LangChainMemoryService()
    return _service_instance
