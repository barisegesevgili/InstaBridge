"""Tests for state management."""
import json
from pathlib import Path
import tempfile
import pytest

from src.state import State, load_state, save_state


class TestState:
    """Test state persistence and management."""

    def test_state_initialization(self):
        """Test State dataclass initialization."""
        state = State()
        assert isinstance(state.sent_ids, set)
        assert isinstance(state.sent_ids_by_recipient, dict)
        assert state.last_run_ts is None
        assert isinstance(state.last_run_files, list)
        assert state.last_run_caption == ""

    def test_save_and_load_state(self, tmp_path):
        """Test saving and loading state from JSON."""
        # Create a state with data
        state = State(
            sent_ids={"post:123", "story:456"},
            sent_ids_by_recipient={"friend1": {"post:123"}},
            last_run_ts=1234567890.0,
            last_run_files=["file1.jpg", "file2.jpg"],
            last_run_caption="Test caption"
        )

        # Save to temp file
        test_file = tmp_path / "test_state.json"
        original_path = Path("state.json")
        
        # Temporarily replace STATE_PATH
        import src.state
        src.state.STATE_PATH = test_file
        
        save_state(state)
        
        # Load back
        loaded_state = load_state()
        
        # Restore original path
        src.state.STATE_PATH = original_path
        
        # Verify
        assert loaded_state.sent_ids == state.sent_ids
        assert loaded_state.sent_ids_by_recipient == state.sent_ids_by_recipient
        assert loaded_state.last_run_ts == state.last_run_ts
        assert loaded_state.last_run_files == state.last_run_files
        assert loaded_state.last_run_caption == state.last_run_caption

    def test_load_state_nonexistent_file(self, tmp_path):
        """Test loading state when file doesn't exist."""
        import src.state
        original_path = src.state.STATE_PATH
        src.state.STATE_PATH = tmp_path / "nonexistent.json"
        
        state = load_state()
        
        src.state.STATE_PATH = original_path
        
        # Should return default state
        assert isinstance(state.sent_ids, set)
        assert len(state.sent_ids) == 0

    def test_state_json_format(self, tmp_path):
        """Test that saved state has correct JSON structure."""
        state = State(
            sent_ids={"item1", "item2"},
            sent_ids_by_recipient={"user1": {"item1"}},
            last_run_ts=123.45
        )
        
        test_file = tmp_path / "test_state.json"
        import src.state
        original_path = src.state.STATE_PATH
        src.state.STATE_PATH = test_file
        
        save_state(state)
        
        src.state.STATE_PATH = original_path
        
        # Read and parse JSON
        data = json.loads(test_file.read_text())
        
        assert "sent_ids" in data
        assert "sent_ids_by_recipient" in data
        assert "last_run_ts" in data
        assert isinstance(data["sent_ids"], list)
        assert sorted(data["sent_ids"]) == ["item1", "item2"]
