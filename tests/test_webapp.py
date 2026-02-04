"""Tests for web application."""

import json
from unittest.mock import Mock, patch
import pytest

from src.webapp import app


@pytest.fixture
def client():
    """Create test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestRoutes:
    """Test Flask routes."""

    def test_index_page(self, client):
        """Test index page loads."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Not following you back" in response.data

    def test_settings_page(self, client):
        """Test settings page loads."""
        response = client.get("/settings")
        assert response.status_code == 200
        assert b"Content sharing settings" in response.data


class TestSettingsAPI:
    """Test settings API endpoints."""

    @patch("src.webapp.settings_to_public_dict")
    @patch("src.webapp.load_settings")
    @patch("src.webapp.load_config")
    def test_get_settings(
        self, mock_load_config, mock_load_settings, mock_to_dict, client
    ):
        """Test GET /api/settings."""
        # Mock config
        mock_config = Mock()
        mock_config.wa_content_contact_name = "TestContact"
        mock_config.wa_content_phone = "123456789"
        mock_load_config.return_value = mock_config

        # Mock settings
        mock_settings = Mock()
        mock_settings.version = 1
        mock_settings.updated_ts = 1234567890.0
        mock_settings.schedule = Mock()
        mock_settings.schedule.enabled = True
        mock_settings.schedule.tz = "Europe/Berlin"
        mock_settings.schedule.time_hhmm = "19:00"
        mock_settings.recipients = []
        mock_load_settings.return_value = mock_settings

        # Mock serialization
        mock_to_dict.return_value = {"version": 1, "recipients": []}

        response = client.get("/api/settings")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "settings" in data
        assert data["settings"]["version"] == 1

    @patch("src.webapp.load_config")
    @patch("src.webapp.load_settings")
    def test_get_settings_error(self, mock_load_settings, mock_load_config, client):
        """Test GET /api/settings handles errors."""
        mock_load_config.side_effect = Exception("Config error")

        response = client.get("/api/settings")
        assert response.status_code == 500

        data = json.loads(response.data)
        assert "error" in data

    @patch("src.webapp.settings_from_public_dict")
    @patch("src.webapp.save_settings")
    @patch("src.webapp.settings_to_public_dict")
    def test_post_settings(self, mock_to_dict, mock_save, mock_from_dict, client):
        """Test POST /api/settings."""
        mock_settings = Mock()
        mock_from_dict.return_value = mock_settings
        mock_to_dict.return_value = {"version": 1}

        payload = {
            "version": 1,
            "schedule": {"enabled": True, "tz": "Europe/Berlin", "time_hhmm": "19:00"},
            "recipients": [],
        }

        response = client.post(
            "/api/settings", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ok"] is True
        mock_save.assert_called_once_with(mock_settings)

    @patch("src.webapp.settings_from_public_dict")
    def test_post_settings_error(self, mock_from_dict, client):
        """Test POST /api/settings handles errors."""
        mock_from_dict.side_effect = ValueError("Invalid data")

        payload = {"invalid": "data"}
        response = client.post(
            "/api/settings", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data


class TestSchedulerAPI:
    """Test scheduler API endpoint."""

    @patch("src.webapp.datetime")
    @patch("src.webapp.ZoneInfo")
    @patch("src.webapp.load_settings")
    @patch("src.webapp.load_config")
    def test_next_run_enabled(
        self,
        mock_load_config,
        mock_load_settings,
        mock_zone_info,
        mock_datetime,
        client,
    ):
        """Test /api/scheduler/next-run when scheduler is enabled."""
        from datetime import datetime, timedelta, timezone

        mock_config = Mock()
        mock_config.wa_content_contact_name = "Test"
        mock_config.wa_content_phone = ""
        mock_load_config.return_value = mock_config

        mock_schedule = Mock()
        mock_schedule.enabled = True
        mock_schedule.tz = "Europe/Berlin"
        mock_schedule.time_hhmm = "19:00"

        mock_settings = Mock()
        mock_settings.schedule = mock_schedule
        mock_load_settings.return_value = mock_settings

        # Mock timezone
        mock_tz = timezone.utc
        mock_zone_info.return_value = mock_tz

        # Mock datetime.now()
        mock_now = datetime(2026, 2, 4, 15, 30, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        # Mock datetime methods needed by the endpoint
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        response = client.get("/api/scheduler/next-run")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["enabled"] is True
        assert "next_run" in data
        assert data["tz"] == "Europe/Berlin"

    @patch("src.webapp.ZoneInfo")
    @patch("src.webapp.load_settings")
    @patch("src.webapp.load_config")
    def test_next_run_disabled(
        self, mock_load_config, mock_load_settings, mock_zone_info, client
    ):
        """Test /api/scheduler/next-run when scheduler is disabled."""
        from datetime import timezone

        mock_config = Mock()
        mock_config.wa_content_contact_name = "Test"
        mock_config.wa_content_phone = ""
        mock_load_config.return_value = mock_config

        mock_schedule = Mock()
        mock_schedule.enabled = False
        mock_schedule.tz = "Europe/Berlin"
        mock_schedule.time_hhmm = "19:00"

        mock_settings = Mock()
        mock_settings.schedule = mock_schedule
        mock_load_settings.return_value = mock_settings

        # Mock timezone
        mock_zone_info.return_value = timezone.utc

        response = client.get("/api/scheduler/next-run")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["enabled"] is False
        assert data["next_run"] is None


class TestAnalyticsAPI:
    """Test analytics API endpoints."""

    @patch("src.webapp.not_following_back_detailed")
    def test_not_following_back(self, mock_nfb, client):
        """Test /api/not-following-back."""
        mock_nfb.return_value = [
            {
                "username": "user1",
                "followers": 100,
                "is_private": False,
                "is_verified": False,
            },
            {
                "username": "user2",
                "followers": 200,
                "is_private": True,
                "is_verified": False,
            },
        ]

        response = client.get(
            "/api/not-following-back?min_followers=50&max_followers=500"
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["count"] == 2
        assert len(data["users"]) == 2
        assert data["users"][0]["username"] == "user1"

    @patch("src.webapp.not_following_back_detailed")
    def test_not_following_back_rate_limited(self, mock_nfb, client):
        """Test /api/not-following-back handles rate limiting."""
        from src.insights import RateLimitedError

        error = RateLimitedError("Rate limited", retry_after_s=600)
        mock_nfb.side_effect = error

        response = client.get("/api/not-following-back")
        assert response.status_code == 429

        data = json.loads(response.data)
        assert "error" in data
        assert data["retry_after_s"] == 600

    @patch("src.webapp.not_following_back_detailed")
    def test_not_following_back_error(self, mock_nfb, client):
        """Test /api/not-following-back handles general errors."""
        mock_nfb.side_effect = Exception("API error")

        response = client.get("/api/not-following-back")
        assert response.status_code == 500

        data = json.loads(response.data)
        assert "error" in data


class TestWarmCacheAPI:
    """Test cache warming API endpoints."""

    @patch("src.webapp.reset_warm_cache_state")
    def test_warm_cache_reset(self, mock_reset, client):
        """Test POST /api/warm-cache/reset."""
        response = client.post("/api/warm-cache/reset")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["ok"] is True
        mock_reset.assert_called_once()

    @patch("src.webapp.reset_warm_cache_state")
    def test_warm_cache_reset_error(self, mock_reset, client):
        """Test POST /api/warm-cache/reset handles errors."""
        mock_reset.side_effect = Exception("Reset failed")

        response = client.post("/api/warm-cache/reset")
        assert response.status_code == 500

        data = json.loads(response.data)
        assert "error" in data

    @patch("src.webapp.warm_user_cache_step")
    def test_warm_cache_step(self, mock_warm, client):
        """Test GET /api/warm-cache/step."""
        mock_warm.return_value = {
            "done": False,
            "processed": 50,
            "total": 100,
            "percent": 50,
            "newly_fetched": 5,
            "rate_limited": False,
        }

        response = client.get("/api/warm-cache/step?chunk_size=25")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["done"] is False
        assert data["processed"] == 50
        assert data["total"] == 100

    @patch("src.webapp.warm_user_cache_step")
    def test_warm_cache_step_done(self, mock_warm, client):
        """Test GET /api/warm-cache/step when complete."""
        mock_warm.return_value = {
            "done": True,
            "processed": 100,
            "total": 100,
            "percent": 100,
            "newly_fetched": 0,
            "rate_limited": False,
        }

        response = client.get("/api/warm-cache/step")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["done"] is True
        assert data["percent"] == 100
