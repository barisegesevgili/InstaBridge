"""Tests for main orchestration."""

import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.main import (
    Config,
    load_config,
    _format_run_caption,
    _recipient_wants_item,
    resend_last,
    run_once,
)
from src.ig import IgItem
from src.settings import RecipientSettings


class TestLoadConfig:
    """Test configuration loading."""

    def test_load_config_all_vars_set(self, monkeypatch):
        """Test loading config when all environment variables are set."""
        monkeypatch.setenv("IG_USERNAME", "testuser")
        monkeypatch.setenv("IG_PASSWORD", "testpass")
        monkeypatch.setenv("WA_CONTENT_CONTACT_NAME", "Friend")
        monkeypatch.setenv("WA_CONTENT_PHONE", "123456789")
        monkeypatch.setenv("WA_REPORT_CONTACT_NAME", "Notes")
        monkeypatch.setenv("WA_REPORT_PHONE", "987654321")
        monkeypatch.setenv("MESSAGE_PREFIX", "Instagram:")

        config = load_config()

        assert config.ig_username == "testuser"
        assert config.ig_password == "testpass"
        assert config.wa_content_contact_name == "Friend"
        assert config.wa_content_phone == "123456789"
        assert config.wa_report_contact_name == "Notes"
        assert config.wa_report_phone == "987654321"
        assert config.message_prefix == "Instagram:"

    def test_load_config_legacy_vars(self, monkeypatch):
        """Test backward compatibility with legacy environment variables."""
        monkeypatch.setenv("IG_USERNAME", "testuser")
        monkeypatch.setenv("IG_PASSWORD", "testpass")
        monkeypatch.setenv("WA_CONTACT_NAME", "LegacyContact")
        monkeypatch.setenv("WA_PHONE", "111111111")

        config = load_config()

        assert config.wa_content_contact_name == "LegacyContact"
        assert config.wa_content_phone == "111111111"
        assert config.wa_report_contact_name == "LegacyContact"

    def test_load_config_missing_required(self, monkeypatch):
        """Test that missing required vars raises SystemExit."""
        monkeypatch.delenv("IG_USERNAME", raising=False)
        monkeypatch.delenv("IG_PASSWORD", raising=False)
        monkeypatch.delenv("WA_CONTENT_CONTACT_NAME", raising=False)
        monkeypatch.delenv("WA_CONTACT_NAME", raising=False)

        with pytest.raises(SystemExit):
            load_config()

    def test_load_config_default_message_prefix(self, monkeypatch):
        """Test default message prefix when not set."""
        monkeypatch.setenv("IG_USERNAME", "testuser")
        monkeypatch.setenv("IG_PASSWORD", "testpass")
        monkeypatch.setenv("WA_CONTENT_CONTACT_NAME", "Friend")
        monkeypatch.delenv("MESSAGE_PREFIX", raising=False)

        config = load_config()

        assert config.message_prefix == "New from Instagram:"


class TestFormatRunCaption:
    """Test caption formatting."""

    def test_format_run_caption_single_post(self):
        """Test formatting caption for a single post."""
        mock_client = Mock()
        items = [
            IgItem(
                kind="post",
                unique_id="post:123",
                title="Post",
                caption="Test post caption",
                created_ts=1000.0,
                _client=mock_client,
                _media_pk=123,
            )
        ]

        caption = _format_run_caption("New from Instagram:", items)

        assert "New from Instagram:" in caption
        assert "post: latest" in caption
        assert "Test post caption" in caption

    def test_format_run_caption_story(self):
        """Test formatting caption for a story."""
        mock_client = Mock()
        items = [
            IgItem(
                kind="story",
                unique_id="story:456",
                title="Story",
                caption="Story text",
                created_ts=2000.0,
                story_is_close_friends=False,
                _client=mock_client,
                _media_pk=456,
            )
        ]

        caption = _format_run_caption("Prefix:", items)

        assert "Prefix:" in caption
        assert "story" in caption
        assert "Story text" in caption

    def test_format_run_caption_close_friends_story(self):
        """Test formatting caption for close friends story."""
        mock_client = Mock()
        items = [
            IgItem(
                kind="story",
                unique_id="story:789",
                title="CF Story",
                caption="",
                created_ts=3000.0,
                story_is_close_friends=True,
                _client=mock_client,
                _media_pk=789,
            )
        ]

        caption = _format_run_caption("Test:", items)

        assert "close friends" in caption

    def test_format_run_caption_multiple_items(self):
        """Test formatting caption for multiple items."""
        mock_client = Mock()
        items = [
            IgItem(
                kind="post",
                unique_id="post:1",
                title="Post 1",
                caption="Caption 1",
                created_ts=1000.0,
                _client=mock_client,
                _media_pk=1,
            ),
            IgItem(
                kind="story",
                unique_id="story:2",
                title="Story 1",
                caption="Caption 2",
                created_ts=2000.0,
                story_is_close_friends=False,
                _client=mock_client,
                _media_pk=2,
            ),
        ]

        caption = _format_run_caption("Multi:", items)

        assert "Multi:" in caption
        assert "Caption 1" in caption
        assert "Caption 2" in caption


class TestRecipientWantsItem:
    """Test recipient filtering logic."""

    def test_recipient_wants_post_enabled(self):
        """Test recipient wants posts when enabled."""
        mock_client = Mock()
        recipient = RecipientSettings(
            id="r1",
            display_name="Friend",
            enabled=True,
            send_posts=True,
            send_stories=False,
            send_close_friends_stories=False,
        )
        item = IgItem(
            kind="post",
            unique_id="post:123",
            title="Post",
            caption="",
            created_ts=1000.0,
            _client=mock_client,
            _media_pk=123,
        )

        assert _recipient_wants_item(recipient, item) is True

    def test_recipient_doesnt_want_post(self):
        """Test recipient doesn't want posts when disabled."""
        mock_client = Mock()
        recipient = RecipientSettings(
            id="r1",
            display_name="Friend",
            enabled=True,
            send_posts=False,
            send_stories=True,
            send_close_friends_stories=False,
        )
        item = IgItem(
            kind="post",
            unique_id="post:123",
            title="Post",
            caption="",
            created_ts=1000.0,
            _client=mock_client,
            _media_pk=123,
        )

        assert _recipient_wants_item(recipient, item) is False

    def test_recipient_disabled(self):
        """Test disabled recipient doesn't want anything."""
        mock_client = Mock()
        recipient = RecipientSettings(
            id="r1",
            display_name="Friend",
            enabled=False,
            send_posts=True,
            send_stories=True,
            send_close_friends_stories=True,
        )
        item = IgItem(
            kind="post",
            unique_id="post:123",
            title="Post",
            caption="",
            created_ts=1000.0,
            _client=mock_client,
            _media_pk=123,
        )

        assert _recipient_wants_item(recipient, item) is False

    def test_recipient_wants_regular_story(self):
        """Test recipient wants regular stories."""
        mock_client = Mock()
        recipient = RecipientSettings(
            id="r1",
            display_name="Friend",
            enabled=True,
            send_posts=False,
            send_stories=True,
            send_close_friends_stories=False,
        )
        item = IgItem(
            kind="story",
            unique_id="story:456",
            title="Story",
            caption="",
            created_ts=2000.0,
            story_is_close_friends=False,
            _client=mock_client,
            _media_pk=456,
        )

        assert _recipient_wants_item(recipient, item) is True

    def test_recipient_wants_close_friends_story(self):
        """Test recipient wants close friends stories when enabled."""
        mock_client = Mock()
        recipient = RecipientSettings(
            id="r1",
            display_name="BestFriend",
            enabled=True,
            send_posts=False,
            send_stories=False,
            send_close_friends_stories=True,
        )
        item = IgItem(
            kind="story",
            unique_id="story:789",
            title="CF Story",
            caption="",
            created_ts=3000.0,
            story_is_close_friends=True,
            _client=mock_client,
            _media_pk=789,
        )

        assert _recipient_wants_item(recipient, item) is True

    def test_recipient_doesnt_want_close_friends_story(self):
        """Test recipient doesn't get close friends stories when disabled."""
        mock_client = Mock()
        recipient = RecipientSettings(
            id="r1",
            display_name="Friend",
            enabled=True,
            send_posts=False,
            send_stories=True,
            send_close_friends_stories=False,
        )
        item = IgItem(
            kind="story",
            unique_id="story:789",
            title="CF Story",
            caption="",
            created_ts=3000.0,
            story_is_close_friends=True,
            _client=mock_client,
            _media_pk=789,
        )

        assert _recipient_wants_item(recipient, item) is False


class TestResendLast:
    """Test resend functionality."""

    @patch("src.main.load_state")
    @patch("src.main.WhatsAppSender")
    def test_resend_last_with_files(
        self, mock_wa_class, mock_load_state, tmp_path, monkeypatch
    ):
        """Test resending last batch when files exist."""
        # Set up environment
        monkeypatch.setenv("IG_USERNAME", "test")
        monkeypatch.setenv("IG_PASSWORD", "test")
        monkeypatch.setenv("WA_CONTENT_CONTACT_NAME", "Friend")

        # Create test files
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test")

        # Mock state
        mock_state = Mock()
        mock_state.last_run_files = [str(test_file)]
        mock_state.last_run_caption = "Test caption"
        mock_load_state.return_value = mock_state

        # Mock WhatsApp sender
        mock_wa = Mock()
        mock_wa_class.return_value = mock_wa

        config = load_config()
        resend_last(cfg=config, max_files=0)

        mock_wa.start.assert_called_once()
        mock_wa.open_chat.assert_called_once()
        mock_wa.send_media_batch.assert_called_once()
        mock_wa.stop.assert_called_once()

    @patch("src.main.load_state")
    @patch("src.main.WhatsAppSender")
    def test_resend_last_no_files(
        self, mock_wa_class, mock_load_state, monkeypatch, capsys
    ):
        """Test resending when no files available."""
        monkeypatch.setenv("IG_USERNAME", "test")
        monkeypatch.setenv("IG_PASSWORD", "test")
        monkeypatch.setenv("WA_CONTENT_CONTACT_NAME", "Friend")

        # Mock state with no files
        mock_state = Mock()
        mock_state.last_run_files = []
        mock_load_state.return_value = mock_state

        config = load_config()
        resend_last(cfg=config, max_files=0)

        captured = capsys.readouterr()
        assert "Nothing to resend" in captured.out


class TestRunOnce:
    """Test main run_once orchestration."""

    @patch("src.main.load_state")
    @patch("src.main.load_settings")
    @patch("src.main.save_state")
    @patch("src.main.IgClient")
    @patch("src.main.WhatsAppSender")
    def test_run_once_no_recipients(
        self,
        mock_wa_class,
        mock_ig_class,
        mock_save_state,
        mock_load_settings,
        mock_load_state,
        monkeypatch,
    ):
        """Test run_once exits early when no enabled recipients."""
        monkeypatch.setenv("IG_USERNAME", "test")
        monkeypatch.setenv("IG_PASSWORD", "test")
        monkeypatch.setenv("WA_CONTENT_CONTACT_NAME", "Friend")

        # Mock state
        mock_state = Mock()
        mock_state.last_run_ts = None
        mock_state.sent_ids = set()
        mock_state.sent_ids_by_recipient = {}
        mock_load_state.return_value = mock_state

        # Mock settings with no recipients
        mock_settings = Mock()
        mock_settings.recipients = []
        mock_load_settings.return_value = mock_settings

        # Mock IG client
        mock_ig = Mock()
        mock_ig_class.return_value = mock_ig

        # Mock WA sender
        mock_wa = Mock()
        mock_wa_class.return_value = mock_wa

        config = load_config()
        run_once(cfg=config, force_resend_current=False)

        # Should login and start WA, but not send anything
        mock_ig.login.assert_called_once()
        mock_wa.start.assert_called_once()
        mock_wa.stop.assert_called_once()
        mock_wa.send_media_batch.assert_not_called()

    @patch("src.main.load_state")
    @patch("src.main.load_settings")
    @patch("src.main.save_state")
    @patch("src.main.IgClient")
    @patch("src.main.WhatsAppSender")
    def test_run_once_no_new_items(
        self,
        mock_wa_class,
        mock_ig_class,
        mock_save_state,
        mock_load_settings,
        mock_load_state,
        monkeypatch,
    ):
        """Test run_once when no new content available."""
        monkeypatch.setenv("IG_USERNAME", "test")
        monkeypatch.setenv("IG_PASSWORD", "test")
        monkeypatch.setenv("WA_CONTENT_CONTACT_NAME", "Friend")

        # Mock state
        mock_state = Mock()
        mock_state.last_run_ts = time.time()
        mock_state.sent_ids = set()
        mock_state.sent_ids_by_recipient = {}
        mock_load_state.return_value = mock_state

        # Mock settings with enabled recipient
        mock_recipient = RecipientSettings(
            id="r1",
            display_name="Friend",
            wa_contact_name="Friend",
            enabled=True,
            send_posts=True,
            send_stories=True,
        )
        mock_settings = Mock()
        mock_settings.recipients = [mock_recipient]
        mock_load_settings.return_value = mock_settings

        # Mock IG client - no new content
        mock_ig = Mock()
        mock_ig.get_new_post_items_since.return_value = []
        mock_ig.get_active_story_items.return_value = []
        mock_ig_class.return_value = mock_ig

        # Mock WA sender
        mock_wa = Mock()
        mock_wa_class.return_value = mock_wa

        config = load_config()
        run_once(cfg=config, force_resend_current=False)

        # Should check for content but not send
        mock_ig.get_new_post_items_since.assert_called_once()
        mock_ig.get_active_story_items.assert_called_once()
        mock_wa.send_media_batch.assert_not_called()
