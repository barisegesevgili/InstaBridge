"""Tests for Instagram client."""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import tempfile
import pytest

from src.ig import IgClient, IgItem


class TestIgClient:
    """Test Instagram client wrapper."""

    def test_initialization(self, tmp_path):
        """Test IgClient initialization."""
        session_path = tmp_path / "test_session.json"
        client = IgClient(session_path=session_path)
        assert client._session_path == session_path

    @patch("src.ig.Client")
    def test_login_new_session(self, mock_client_class, tmp_path):
        """Test login creates new session when file doesn't exist."""
        session_path = tmp_path / "test_session.json"
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        client = IgClient(session_path=session_path)
        client.login("testuser", "testpass")

        mock_client.login.assert_called_once_with("testuser", "testpass")
        mock_client.dump_settings.assert_called_once_with(str(session_path))

    @patch("src.ig.Client")
    def test_login_existing_session(self, mock_client_class, tmp_path):
        """Test login reuses existing session."""
        session_path = tmp_path / "test_session.json"
        session_path.write_text('{"device_settings": {}}')

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        client = IgClient(session_path=session_path)
        client.login("testuser", "testpass")

        mock_client.load_settings.assert_called_once_with(str(session_path))
        mock_client.login.assert_called_once_with("testuser", "testpass")

    @patch("src.ig.Client")
    def test_login_expired_session_fallback(self, mock_client_class, tmp_path):
        """Test login falls back to fresh login if session is expired."""
        session_path = tmp_path / "test_session.json"
        session_path.write_text('{"device_settings": {}}')

        mock_client = Mock()
        mock_client.load_settings.side_effect = Exception("Session expired")
        mock_client_class.return_value = mock_client

        client = IgClient(session_path=session_path)
        client.login("testuser", "testpass")

        # Should try load (fail), then do fresh login
        mock_client.load_settings.assert_called_once()
        mock_client.login.assert_called_once_with("testuser", "testpass")

    @patch("src.ig.Client")
    def test_get_latest_post_items_success(self, mock_client_class):
        """Test fetching latest post."""
        mock_client = Mock()
        mock_client.user_id = 123456
        mock_client_class.return_value = mock_client

        # Mock media object
        mock_media = Mock()
        mock_media.pk = 987654
        mock_media.caption_text = "Test caption"
        mock_media.taken_at = Mock()
        mock_media.taken_at.timestamp.return_value = 1234567890.0

        mock_client.user_medias_v1.return_value = [mock_media]

        client = IgClient(session_path=Path("test.json"))
        items = client.get_latest_post_items()

        assert len(items) == 1
        assert items[0].kind == "post"
        assert items[0].caption == "Test caption"
        assert items[0].unique_id == "post:987654"
        assert items[0].created_ts == 1234567890.0

    @patch("src.ig.Client")
    def test_get_latest_post_items_empty(self, mock_client_class):
        """Test fetching latest post when no posts exist."""
        mock_client = Mock()
        mock_client.user_id = 123456
        mock_client.user_medias_v1.return_value = []
        mock_client_class.return_value = mock_client

        client = IgClient(session_path=Path("test.json"))
        items = client.get_latest_post_items()

        assert len(items) == 0

    @patch("src.ig.Client")
    def test_get_latest_post_items_no_user_id(self, mock_client_class):
        """Test fetching latest post when not logged in."""
        mock_client = Mock()
        mock_client.user_id = None
        mock_client_class.return_value = mock_client

        client = IgClient(session_path=Path("test.json"))
        items = client.get_latest_post_items()

        assert len(items) == 0

    @patch("src.ig.Client")
    def test_get_new_post_items_since(self, mock_client_class):
        """Test fetching new posts since timestamp."""
        mock_client = Mock()
        mock_client.user_id = 123456
        mock_client_class.return_value = mock_client

        # Create 3 mock posts: 2 new, 1 old
        new_media1 = Mock()
        new_media1.pk = 1
        new_media1.caption_text = "New post 1"
        new_media1.taken_at = Mock()
        new_media1.taken_at.timestamp.return_value = 2000.0

        new_media2 = Mock()
        new_media2.pk = 2
        new_media2.caption_text = "New post 2"
        new_media2.taken_at = Mock()
        new_media2.taken_at.timestamp.return_value = 3000.0

        old_media = Mock()
        old_media.pk = 3
        old_media.caption_text = "Old post"
        old_media.taken_at = Mock()
        old_media.taken_at.timestamp.return_value = 500.0

        mock_client.user_medias_v1.return_value = [new_media2, new_media1, old_media]

        client = IgClient(session_path=Path("test.json"))
        items = client.get_new_post_items_since(since_ts=1000.0, max_posts=10)

        assert len(items) == 2
        assert items[0].unique_id == "post:2"
        assert items[1].unique_id == "post:1"

    @patch("src.ig.Client")
    def test_get_active_story_items(self, mock_client_class):
        """Test fetching active stories."""
        mock_client = Mock()
        mock_client.user_id = 123456
        mock_client_class.return_value = mock_client

        # Mock regular story
        story1 = Mock()
        story1.pk = 111
        story1.caption = "Story 1"
        story1.taken_at = 1000  # Use int for sorting, not Mock
        story1.is_close_friends = False

        # Mock close friends story
        story2 = Mock()
        story2.pk = 222
        story2.caption = "CF Story"
        story2.taken_at = 2000  # Use int for sorting, not Mock
        story2.is_close_friends = True

        mock_client.user_stories.return_value = [story2, story1]  # Unordered

        client = IgClient(session_path=Path("test.json"))
        items = client.get_active_story_items()

        assert len(items) == 2
        # Should be sorted by timestamp
        assert items[0].unique_id == "story:111"
        assert items[0].story_is_close_friends is False
        assert items[1].unique_id == "story:222"
        assert items[1].story_is_close_friends is True

    @patch("src.ig.Client")
    def test_get_followers_map(self, mock_client_class):
        """Test fetching followers map."""
        mock_client = Mock()
        mock_client.user_id = 123456
        mock_client_class.return_value = mock_client

        # Mock followers as dict
        mock_follower1 = Mock()
        mock_follower1.pk = 111
        mock_follower1.username = "follower1"

        mock_follower2 = Mock()
        mock_follower2.pk = 222
        mock_follower2.username = "follower2"

        mock_client.user_followers_v1.return_value = {
            111: mock_follower1,
            222: mock_follower2,
        }

        client = IgClient(session_path=Path("test.json"))
        followers = client.get_followers_map()

        assert len(followers) == 2
        assert followers[111] == "follower1"
        assert followers[222] == "follower2"

    @patch("src.ig.Client")
    def test_get_following_map(self, mock_client_class):
        """Test fetching following map."""
        mock_client = Mock()
        mock_client.user_id = 123456
        mock_client_class.return_value = mock_client

        # Mock following as list
        mock_user1 = Mock()
        mock_user1.pk = 333
        mock_user1.username = "following1"

        mock_client.user_following_v1.return_value = [mock_user1]

        client = IgClient(session_path=Path("test.json"))
        following = client.get_following_map()

        assert len(following) == 1
        assert following[333] == "following1"

    @patch("src.ig.Client")
    def test_coerce_users_to_map_dict_format(self, mock_client_class):
        """Test _coerce_users_to_map with dict input."""
        mock_client_class.return_value = Mock()
        client = IgClient(session_path=Path("test.json"))

        user1 = Mock()
        user1.pk = 1
        user1.username = "user1"

        data = {1: user1}
        result = client._coerce_users_to_map(data)

        assert result == {1: "user1"}

    @patch("src.ig.Client")
    def test_coerce_users_to_map_list_format(self, mock_client_class):
        """Test _coerce_users_to_map with list input."""
        mock_client_class.return_value = Mock()
        client = IgClient(session_path=Path("test.json"))

        user1 = Mock()
        user1.pk = 1
        user1.username = "user1"

        user2 = Mock()
        user2.pk = 2
        user2.username = "user2"

        data = [user1, user2]
        result = client._coerce_users_to_map(data)

        assert result == {1: "user1", 2: "user2"}


class TestIgItem:
    """Test IgItem dataclass and methods."""

    @patch("src.ig.Client")
    def test_download_photo(self, mock_client_class, tmp_path):
        """Test downloading a photo post."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock media info
        mock_info = Mock()
        mock_info.media_type = 1  # Photo

        mock_client.media_info.return_value = mock_info
        mock_client.photo_download.return_value = str(tmp_path / "photo.jpg")

        item = IgItem(
            kind="post",
            unique_id="post:123",
            title="Test",
            caption="Caption",
            created_ts=1000.0,
            _client=mock_client,
            _media_pk=123,
        )

        paths = item.download(tmp_path)

        assert len(paths) == 1
        assert paths[0].name == "photo.jpg"
        mock_client.photo_download.assert_called_once()

    @patch("src.ig.Client")
    def test_download_video(self, mock_client_class, tmp_path):
        """Test downloading a video post."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_info = Mock()
        mock_info.media_type = 2  # Video

        mock_client.media_info.return_value = mock_info
        mock_client.video_download.return_value = str(tmp_path / "video.mp4")

        item = IgItem(
            kind="post",
            unique_id="post:456",
            title="Video",
            caption="",
            created_ts=2000.0,
            _client=mock_client,
            _media_pk=456,
        )

        paths = item.download(tmp_path)

        assert len(paths) == 1
        assert paths[0].name == "video.mp4"
        mock_client.video_download.assert_called_once()

    @patch("src.ig.Client")
    def test_download_album(self, mock_client_class, tmp_path):
        """Test downloading an album/carousel."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_info = Mock()
        mock_info.media_type = 8  # Album

        mock_client.media_info.return_value = mock_info
        mock_client.album_download.return_value = [
            str(tmp_path / "img1.jpg"),
            str(tmp_path / "img2.jpg"),
        ]

        item = IgItem(
            kind="post",
            unique_id="post:789",
            title="Album",
            caption="",
            created_ts=3000.0,
            _client=mock_client,
            _media_pk=789,
        )

        paths = item.download(tmp_path)

        assert len(paths) == 2
        mock_client.album_download.assert_called_once()

    @patch("src.ig.Client")
    def test_download_story(self, mock_client_class, tmp_path):
        """Test downloading a story."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.story_download.return_value = str(tmp_path / "story.jpg")

        item = IgItem(
            kind="story",
            unique_id="story:999",
            title="Story",
            caption="",
            created_ts=4000.0,
            story_is_close_friends=False,
            _client=mock_client,
            _media_pk=999,
        )

        paths = item.download(tmp_path)

        assert len(paths) == 1
        assert paths[0].name == "story.jpg"
        mock_client.story_download.assert_called_once()

    def test_igitem_immutable(self):
        """Test that IgItem is frozen/immutable."""
        mock_client = Mock()
        item = IgItem(
            kind="post",
            unique_id="test",
            title="Test",
            caption="",
            created_ts=0.0,
            _client=mock_client,
            _media_pk=123,
        )

        with pytest.raises(Exception):  # FrozenInstanceError in Python 3.10+
            item.kind = "story"
