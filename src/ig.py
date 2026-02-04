from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from instagrapi import Client

from src.rate_limiter import RateLimits, human_like_delay


@dataclass(frozen=True)
class IgItem:
    kind: str  # "post" | "story"
    unique_id: str
    title: str
    caption: str
    created_ts: float  # unix seconds (best-effort)
    _client: Client
    _media_pk: int
    # Stories only: True if "close friends" story, False if normal, None if unknown.
    story_is_close_friends: Optional[bool] = None

    def download(self, dest_dir: Path) -> list[Path]:
        """Download media with small human-like delay between files."""
        dest_dir.mkdir(exist_ok=True)

        # Small delay to appear more human-like
        human_like_delay(0.5, 1.5)

        if self.kind == "post":
            info = self._client.media_info(self._media_pk)
            media_type = getattr(info, "media_type", None)  # 1=photo,2=video,8=album
            if media_type == 1:
                out = self._client.photo_download(self._media_pk, folder=str(dest_dir))
                return [Path(out)]
            if media_type == 2:
                out = self._client.video_download(self._media_pk, folder=str(dest_dir))
                return [Path(out)]
            if media_type == 8:
                out = self._client.album_download(self._media_pk, folder=str(dest_dir))
                if isinstance(out, (list, tuple)):
                    return [Path(p) for p in out]
                return [Path(out)]
            # Unknown: best-effort try photo then video
            try:
                out = self._client.photo_download(self._media_pk, folder=str(dest_dir))
                return [Path(out)]
            except Exception:
                out = self._client.video_download(self._media_pk, folder=str(dest_dir))
                return [Path(out)]

        if self.kind == "story":
            out = self._client.story_download(self._media_pk, folder=str(dest_dir))
            if isinstance(out, (list, tuple)):
                return [Path(p) for p in out]
            return [Path(out)]
        raise ValueError(f"Unknown kind: {self.kind}")


class IgClient:
    def __init__(
        self, *, session_path: Path, enable_rate_limiting: bool = True
    ) -> None:
        self._cl = Client()
        self._session_path = session_path
        self._enable_rate_limiting = enable_rate_limiting
        self._rate_limiter = RateLimits.MODERATE  # Balanced rate limiting

    def login(self, username: str, password: str) -> None:
        if self._session_path.exists():
            try:
                self._cl.load_settings(str(self._session_path))
                self._cl.login(username, password)
                return
            except Exception:
                # Session might be expired/corrupt; fall back to fresh login.
                pass

        self._cl.login(username, password)
        self._cl.dump_settings(str(self._session_path))

    def get_user_info_by_username(self, username: str):
        """
        Returns instagrapi User info for a username.
        """
        # instagrapi's gql path can break on some versions/builds (we've seen that),
        # so avoid `user_info_by_username()` as much as possible.
        # Prefer v1/mobile endpoints, fall back to id-based lookup.
        try:
            if hasattr(self._cl, "user_info_by_username_v1"):
                return self._cl.user_info_by_username_v1(username)  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            uid = self._cl.user_id_from_username(username)
            if hasattr(self._cl, "user_info_v1"):
                return self._cl.user_info_v1(uid)  # type: ignore[attr-defined]
            return self._cl.user_info(uid)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch user info for @{username}: {e}") from e

    def get_followers_map(self) -> dict[int, str]:
        """
        Returns {user_id: username} for accounts following you.
        """
        user_id = self._cl.user_id
        if not user_id:
            return {}
        try:
            data = self._cl.user_followers_v1(user_id)  # type: ignore[attr-defined]
        except Exception:
            data = self._cl.user_followers(user_id)
        return self._coerce_users_to_map(data)

    def get_following_map(self) -> dict[int, str]:
        """
        Returns {user_id: username} for accounts you follow.
        """
        user_id = self._cl.user_id
        if not user_id:
            return {}
        try:
            data = self._cl.user_following_v1(user_id)  # type: ignore[attr-defined]
        except Exception:
            data = self._cl.user_following(user_id)
        return self._coerce_users_to_map(data)

    @staticmethod
    def _coerce_users_to_map(data) -> dict[int, str]:
        """
        instagrapi may return:
        - dict[id] = UserShort
        - list[UserShort]
        - other (best-effort)
        """
        out: dict[int, str] = {}
        if not data:
            return out

        # dict[id] = user
        if isinstance(data, dict):
            it = data.items()
        # list[user]
        elif isinstance(data, list):
            it = [(getattr(u, "pk", None) or getattr(u, "id", None), u) for u in data]
        else:
            # Unknown shape; try iterating as list
            try:
                it = [
                    (getattr(u, "pk", None) or getattr(u, "id", None), u)
                    for u in list(data)
                ]
            except Exception:
                return out

        for uid, u in it:
            try:
                uid_int = int(uid)
                username = str(getattr(u, "username", "") or "").strip()
                if uid_int and username:
                    out[uid_int] = username
            except Exception:
                continue
        return out

    def get_latest_post_items(self) -> list[IgItem]:
        """Fetch latest post with rate limiting."""
        if self._enable_rate_limiting:
            self._rate_limiter.wait()

        user_id = self._cl.user_id
        if not user_id:
            return []
        # `user_medias` may try public GraphQL and can fail with KeyError('data') on some accounts.
        # Prefer the private/mobile API if available.
        try:
            medias = self._cl.user_medias_v1(user_id, 1)  # type: ignore[attr-defined]
        except Exception:
            medias = self._cl.user_medias(user_id, 1)
        if not medias:
            return []
        m = medias[0]

        caption = (getattr(m, "caption_text", None) or "").strip()
        taken_at = getattr(m, "taken_at", None)
        try:
            taken_ts = float(taken_at.timestamp()) if taken_at is not None else 0.0
        except Exception:
            taken_ts = 0.0

        # Return a single item for the latest post.
        # `IgItem.download()` uses `media_download()`, which can download carousels as multiple files.
        return [
            IgItem(
                kind="post",
                unique_id=f"post:{m.pk}",
                title="Latest post",
                caption=caption,
                created_ts=taken_ts,
                story_is_close_friends=None,
                _client=self._cl,
                _media_pk=int(m.pk),
            )
        ]

    def get_new_post_items_since(
        self, since_ts: float, *, max_posts: int = 10
    ) -> list[IgItem]:
        """
        Returns posts newer than since_ts (unix seconds), newest first.
        Includes rate limiting to prevent account bans.
        """
        if self._enable_rate_limiting:
            self._rate_limiter.wait()

        user_id = self._cl.user_id
        if not user_id:
            return []
        try:
            medias = self._cl.user_medias_v1(user_id, max_posts)  # type: ignore[attr-defined]
        except Exception:
            medias = self._cl.user_medias(user_id, max_posts)
        out: list[IgItem] = []
        for m in medias or []:
            taken_at = getattr(m, "taken_at", None)
            try:
                taken_ts = float(taken_at.timestamp()) if taken_at is not None else 0.0
            except Exception:
                taken_ts = 0.0
            if taken_ts <= since_ts:
                continue
            caption = (getattr(m, "caption_text", None) or "").strip()
            out.append(
                IgItem(
                    kind="post",
                    unique_id=f"post:{m.pk}",
                    title="Post",
                    caption=caption,
                    created_ts=taken_ts,
                    story_is_close_friends=None,
                    _client=self._cl,
                    _media_pk=int(m.pk),
                )
            )
        return out

    def get_active_story_items(self) -> list[IgItem]:
        """Fetch active stories with rate limiting."""
        if self._enable_rate_limiting:
            self._rate_limiter.wait()

        user_id = self._cl.user_id
        if not user_id:
            return []
        stories = self._cl.user_stories(user_id)
        if not stories:
            return []
        # Keep chronological order
        stories_sorted = sorted(stories, key=lambda x: getattr(x, "taken_at", 0))
        items: list[IgItem] = []
        for s in stories_sorted:
            caption = (getattr(s, "caption", None) or "").strip()
            is_cf: Optional[bool] = None
            try:
                v = getattr(s, "is_close_friends", None)
                if isinstance(v, bool):
                    is_cf = v
            except Exception:
                pass
            if is_cf is None:
                # Best-effort: some builds expose audience as string / enum
                try:
                    aud = getattr(s, "audience", None) or getattr(
                        s, "audience_type", None
                    )
                    if isinstance(aud, str):
                        is_cf = "close" in aud.lower()
                except Exception:
                    pass
            taken_at = getattr(s, "taken_at", None)
            try:
                taken_ts = float(taken_at.timestamp()) if taken_at is not None else 0.0
            except Exception:
                taken_ts = 0.0
            items.append(
                IgItem(
                    kind="story",
                    unique_id=f"story:{s.pk}",
                    title="Story",
                    caption=caption,
                    created_ts=taken_ts,
                    story_is_close_friends=is_cf,
                    _client=self._cl,
                    _media_pk=int(s.pk),
                )
            )
        return items

    def get_latest_story(self) -> Optional[IgItem]:
        user_id = self._cl.user_id
        if not user_id:
            return None
        stories = self._cl.user_stories(user_id)
        if not stories:
            return None

        # Pick the most recent story item
        s = max(stories, key=lambda x: getattr(x, "taken_at", 0))
        caption = (getattr(s, "caption", None) or "").strip()
        taken_at = getattr(s, "taken_at", None)
        try:
            taken_ts = float(taken_at.timestamp()) if taken_at is not None else 0.0
        except Exception:
            taken_ts = 0.0
        return IgItem(
            kind="story",
            unique_id=f"story:{s.pk}",
            title="Latest story",
            caption=caption,
            created_ts=taken_ts,
            story_is_close_friends=(
                getattr(s, "is_close_friends", None)
                if isinstance(getattr(s, "is_close_friends", None), bool)
                else None
            ),
            _client=self._cl,
            _media_pk=int(s.pk),
        )
