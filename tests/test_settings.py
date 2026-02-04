"""Tests for settings management."""
import pytest
from src.settings import (
    RecipientSettings,
    ScheduleSettings,
    AppSettings,
    load_settings,
    save_settings,
    settings_from_public_dict,
    _normalize_phone,
    _validate_time_hhmm
)


class TestRecipientSettings:
    """Test RecipientSettings dataclass."""

    def test_recipient_defaults(self):
        """Test default values for recipient."""
        r = RecipientSettings(
            id="test1",
            display_name="Test User"
        )
        assert r.id == "test1"
        assert r.display_name == "Test User"
        assert r.wa_contact_name == ""
        assert r.wa_phone == ""
        assert r.enabled is True
        assert r.send_posts is True
        assert r.send_stories is True
        assert r.send_close_friends_stories is False


class TestPhoneNormalization:
    """Test phone number normalization."""

    def test_normalize_phone_basic(self):
        """Test basic phone normalization."""
        assert _normalize_phone("1234567890") == "1234567890"
        assert _normalize_phone("+1234567890") == "1234567890"
        assert _normalize_phone("123-456-7890") == "1234567890"
        assert _normalize_phone("(123) 456-7890") == "1234567890"
        assert _normalize_phone(" 123 456 7890 ") == "1234567890"

    def test_normalize_phone_international(self):
        """Test international formats."""
        assert _normalize_phone("+49 170 1234567") == "491701234567"
        assert _normalize_phone("+1 (555) 123-4567") == "15551234567"
        assert _normalize_phone("+44 20 7123 4567") == "442071234567"

    def test_normalize_phone_empty(self):
        """Test empty input."""
        assert _normalize_phone("") == ""
        assert _normalize_phone(None) == ""


class TestTimeValidation:
    """Test time format validation."""

    def test_validate_time_valid(self):
        """Test valid time formats."""
        assert _validate_time_hhmm("19:00") == "19:00"
        assert _validate_time_hhmm("09:30") == "09:30"
        assert _validate_time_hhmm("23:59") == "23:59"
        assert _validate_time_hhmm("00:00") == "00:00"

    def test_validate_time_padding(self):
        """Test that times are zero-padded."""
        assert _validate_time_hhmm("9:30") == "09:30"
        assert _validate_time_hhmm("9:5") == "09:05"

    def test_validate_time_invalid(self):
        """Test invalid time formats fallback."""
        assert _validate_time_hhmm("25:00") == "19:00"  # Default
        assert _validate_time_hhmm("12:60") == "19:00"  # Default
        assert _validate_time_hhmm("invalid") == "19:00"  # Default
        assert _validate_time_hhmm("") == "19:00"  # Default
        assert _validate_time_hhmm(None) == "19:00"  # Default


class TestSettingsFromDict:
    """Test settings parsing from dictionary."""

    def test_parse_basic_settings(self):
        """Test parsing basic settings structure."""
        data = {
            "schedule": {
                "enabled": True,
                "tz": "Europe/Berlin",
                "time_hhmm": "19:00"
            },
            "recipients": [
                {
                    "id": "friend1",
                    "display_name": "Best Friend",
                    "wa_phone": "491701234567",
                    "enabled": True,
                    "send_posts": True,
                    "send_stories": False,
                    "send_close_friends_stories": False
                }
            ]
        }
        
        settings = settings_from_public_dict(data)
        
        assert settings.schedule.enabled is True
        assert settings.schedule.tz == "Europe/Berlin"
        assert settings.schedule.time_hhmm == "19:00"
        assert len(settings.recipients) == 1
        assert settings.recipients[0].id == "friend1"
        assert settings.recipients[0].send_posts is True
        assert settings.recipients[0].send_stories is False

    def test_parse_with_missing_fields(self):
        """Test parsing with optional fields missing."""
        data = {
            "recipients": [
                {
                    "id": "user1",
                    "display_name": "User"
                }
            ]
        }
        
        settings = settings_from_public_dict(data)
        
        # Should use defaults
        assert settings.schedule.enabled is True
        assert settings.schedule.tz == "Europe/Berlin"
        assert settings.recipients[0].send_posts is True

    def test_parse_filters_invalid_recipients(self):
        """Test that invalid recipients are filtered out."""
        data = {
            "recipients": [
                {"id": "valid", "display_name": "Valid User"},
                {"display_name": "No ID"},  # Missing ID
                {"id": "", "display_name": "Empty ID"},  # Empty ID
                {"id": "valid", "display_name": "Duplicate ID"},  # Duplicate
            ]
        }
        
        settings = settings_from_public_dict(data)
        
        # Should only have 1 valid recipient (first with "valid" ID)
        assert len(settings.recipients) == 1
        assert settings.recipients[0].id == "valid"
        assert settings.recipients[0].display_name == "Valid User"
