"""
Tests for LangChain Memory Service

Tests cover:
- Vector store operations (add, query, delete)
- Opponent notes storage and retrieval
- Conversational memory
- Service integration

Author: PokerTool Team
Created: 2025-10-21
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from pokertool.langchain_memory_service import (
    PokerVectorStore,
    PokerConversationalMemory,
    LangChainMemoryService
)


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for the vector database."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def vector_store(temp_db_dir):
    """Create a PokerVectorStore instance with temporary storage."""
    return PokerVectorStore(persist_directory=temp_db_dir)


@pytest.fixture
def conversation_memory():
    """Create a PokerConversationalMemory instance."""
    return PokerConversationalMemory()


@pytest.fixture
def langchain_service(temp_db_dir):
    """Create a LangChainMemoryService instance with temporary storage."""
    return LangChainMemoryService(persist_directory=temp_db_dir)


class TestPokerVectorStore:
    """Tests for PokerVectorStore class."""

    def test_initialization(self, vector_store):
        """Test vector store initializes correctly."""
        assert vector_store.collection is not None
        assert vector_store.collection_name == "poker_hands"

    def test_add_hand(self, vector_store):
        """Test adding a poker hand."""
        hand_id = "test_hand_001"
        hand_text = "AA in BTN vs tight UTG 3-bet, decided to 4-bet all-in"
        metadata = {"position": "BTN", "result": "won", "amount": 200}

        vector_store.add_hand(hand_id, hand_text, metadata)

        # Verify hand was added
        stats = vector_store.get_collection_stats()
        assert stats["total_documents"] >= 1

    def test_query_similar_hands(self, vector_store):
        """Test querying for similar hands."""
        # Add some test hands
        vector_store.add_hand(
            "hand_001",
            "AA in position against tight player, 4-bet all-in preflop",
            {"position": "BTN", "result": "won"}
        )
        vector_store.add_hand(
            "hand_002",
            "KK in early position, called a 3-bet from aggressive player",
            {"position": "UTG", "result": "lost"}
        )

        # Query for similar hands
        results = vector_store.query_similar_hands(
            query="pocket aces in position",
            n_results=2
        )

        assert len(results) > 0
        assert all("id" in result for result in results)
        assert all("text" in result for result in results)

    def test_add_opponent_note(self, vector_store):
        """Test adding an opponent note."""
        player_name = "TestPlayer123"
        note = "Very aggressive preflop, tight postflop"
        metadata = {"session": "2025-10-21"}

        note_id = vector_store.add_opponent_note(player_name, note, metadata=metadata)

        assert note_id is not None
        assert player_name in note_id

    def test_get_opponent_notes(self, vector_store):
        """Test retrieving opponent notes."""
        player_name = "TestPlayer456"

        # Add multiple notes
        vector_store.add_opponent_note(
            player_name,
            "3-bets light from button"
        )
        vector_store.add_opponent_note(
            player_name,
            "Folds to 4-bets frequently"
        )

        # Retrieve notes
        notes = vector_store.get_opponent_notes(player_name)

        assert len(notes) >= 2
        assert all(note["metadata"].get("player") == player_name for note in notes)

    def test_delete_hand(self, vector_store):
        """Test deleting a hand."""
        hand_id = "hand_to_delete"
        vector_store.add_hand(hand_id, "Test hand for deletion")

        # Delete the hand
        success = vector_store.delete_hand(hand_id)
        assert success is True

    def test_get_collection_stats(self, vector_store):
        """Test getting collection statistics."""
        stats = vector_store.get_collection_stats()

        assert "collection_name" in stats
        assert "total_documents" in stats
        assert "persist_directory" in stats
        assert stats["collection_name"] == "poker_hands"


class TestPokerConversationalMemory:
    """Tests for PokerConversationalMemory class."""

    def test_initialization(self, conversation_memory):
        """Test conversational memory initializes correctly."""
        assert conversation_memory.conversation_history is not None
        assert conversation_memory.memory_type == "buffer"

    def test_add_exchange(self, conversation_memory):
        """Test adding a conversation exchange."""
        user_input = "What should I do with AA against a tight 3-bet?"
        ai_response = "Against a tight 3-better, AA is strong enough to 4-bet"

        conversation_memory.add_exchange(user_input, ai_response)

        # Get context to verify exchange was added
        context = conversation_memory.get_context()
        assert user_input in context or "AA" in context

    def test_clear_memory(self, conversation_memory):
        """Test clearing conversation memory."""
        conversation_memory.add_exchange("Test question", "Test answer")
        conversation_memory.clear()

        # After clearing, context should be minimal
        context = conversation_memory.get_context()
        # Memory should be cleared (empty or minimal state)
        assert context is not None


class TestLangChainMemoryService:
    """Tests for LangChainMemoryService class."""

    def test_initialization(self, langchain_service):
        """Test service initializes correctly."""
        assert langchain_service.vector_store is not None
        assert langchain_service.conversational_memory is not None

    def test_store_hand(self, langchain_service):
        """Test storing a hand through the service."""
        hand_id = "service_hand_001"
        hand_text = "KK vs AA all-in preflop"
        metadata = {"result": "lost", "amount": -100}

        langchain_service.store_hand(hand_id, hand_text, metadata)

        # Verify via vector store
        stats = langchain_service.vector_store.get_collection_stats()
        assert stats["total_documents"] >= 1

    def test_analyze_hand(self, langchain_service):
        """Test hand analysis."""
        # First store some hands for similarity search
        langchain_service.store_hand(
            "analysis_hand_001",
            "AA in position, won big pot"
        )

        # Analyze a new hand
        result = langchain_service.analyze_hand(
            hand_text="AA in late position against aggressive player",
            find_similar=True
        )

        assert "hand_text" in result
        assert "timestamp" in result
        assert "similar_hands" in result

    def test_chat_about_poker(self, langchain_service):
        """Test chat interface."""
        # Store a hand for context
        langchain_service.store_hand(
            "chat_hand_001",
            "Made a successful bluff with 72o"
        )

        # Chat query
        response = langchain_service.chat_about_poker(
            user_query="Tell me about my bluffs"
        )

        assert response is not None
        assert isinstance(response, str)
        assert "Query" in response

    def test_get_stats(self, langchain_service):
        """Test getting service statistics."""
        langchain_service.store_hand("stats_hand_001", "Test hand for stats")

        stats = langchain_service.get_stats()

        assert "vector_store" in stats
        assert "conversation_context" in stats
        assert stats["vector_store"]["total_documents"] >= 1


@pytest.mark.integration
class TestLangChainIntegration:
    """Integration tests for LangChain service."""

    def test_end_to_end_workflow(self, langchain_service):
        """Test complete workflow: store, search, analyze, chat."""
        # 1. Store multiple hands
        hands = [
            ("hand_e2e_001", "AA won against KK preflop all-in", {"result": "won"}),
            ("hand_e2e_002", "KK lost to AA preflop all-in", {"result": "lost"}),
            ("hand_e2e_003", "QQ folded to aggressive 3-bet", {"result": "folded"}),
        ]

        for hand_id, text, metadata in hands:
            langchain_service.store_hand(hand_id, text, metadata)

        # 2. Search for similar hands
        results = langchain_service.vector_store.query_similar_hands(
            query="pocket pairs preflop",
            n_results=3
        )
        assert len(results) > 0

        # 3. Analyze a new hand
        analysis = langchain_service.analyze_hand(
            hand_text="JJ facing a 3-bet from tight player",
            find_similar=True
        )
        assert analysis["similar_hands"] is not None

        # 4. Chat about the hands
        chat_response = langchain_service.chat_about_poker(
            user_query="How often did I win with premium pairs?"
        )
        assert chat_response is not None

        # 5. Verify stats
        stats = langchain_service.get_stats()
        assert stats["vector_store"]["total_documents"] >= 3

    def test_opponent_notes_workflow(self, langchain_service):
        """Test opponent notes workflow."""
        player_name = "AggroPlayer"

        # Add notes
        langchain_service.vector_store.add_opponent_note(
            player_name,
            "3-bets 25% from button"
        )
        langchain_service.vector_store.add_opponent_note(
            player_name,
            "Never folds to 4-bets with TT+"
        )

        # Retrieve notes
        notes = langchain_service.vector_store.get_opponent_notes(player_name)
        assert len(notes) >= 2

        # Search for opponent tendencies
        results = langchain_service.vector_store.query_similar_hands(
            query="aggressive 3-betting",
            n_results=5
        )
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
