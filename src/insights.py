import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Optional

from src.ig import IgClient
from src.main import load_config


CACHE_PATH = Path("user_cache.json")
FOLLOW_CACHE_PATH = Path("follow_cache.json")
WARM_STATE_PATH = Path("warm_state.json")


class RateLimitedError(RuntimeError):
    def __init__(self, message: str, *, retry_after_s: int) -> None:
        super().__init__(message)
        self.retry_after_s = int(retry_after_s)


@dataclass(frozen=True)
class UserStats:
    username: str
    user_id: Optional[int]
    follower_count: Optional[int]
    following_count: Optional[int]
    is_private: Optional[bool]
    is_verified: Optional[bool]
    full_name: str
    fetched_ts: float


def _load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def _load_follow_cache() -> dict:
    if not FOLLOW_CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(FOLLOW_CACHE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_follow_cache(cache: dict) -> None:
    FOLLOW_CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def _load_warm_state() -> dict:
    if not WARM_STATE_PATH.exists():
        return {}
    try:
        data = json.loads(WARM_STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_warm_state(state: dict) -> None:
    WARM_STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def reset_warm_cache_state() -> None:
    try:
        if WARM_STATE_PATH.exists():
            WARM_STATE_PATH.unlink()
    except Exception:
        pass


def _coerce_int(x) -> Optional[int]:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def _coerce_bool(x) -> Optional[bool]:
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    return None


def get_user_stats_by_username(
    ig: IgClient,
    username: str,
    *,
    cache: dict,
    ttl_s: int,
    min_delay_s: float = 0.7,
    jitter_s: float = 0.3,
) -> UserStats:
    now = time.time()
    key = username.strip().lower()
    cached = cache.get(key)
    if isinstance(cached, dict):
        fetched_ts = float(cached.get("fetched_ts") or 0.0)
        if fetched_ts and (now - fetched_ts) < ttl_s:
            try:
                return UserStats(
                    username=str(cached.get("username") or username),
                    user_id=_coerce_int(cached.get("user_id")),
                    follower_count=_coerce_int(cached.get("follower_count")),
                    following_count=_coerce_int(cached.get("following_count")),
                    is_private=_coerce_bool(cached.get("is_private")),
                    is_verified=_coerce_bool(cached.get("is_verified")),
                    full_name=str(cached.get("full_name") or ""),
                    fetched_ts=fetched_ts,
                )
            except Exception:
                pass

    # Be polite to Instagram and spread requests out a bit.
    try:
        d = max(0.0, float(min_delay_s)) + (random.random() * max(0.0, float(jitter_s)))
        if d > 0:
            time.sleep(d)
    except Exception:
        pass

    def _iter_exc_chain(e: BaseException):
        seen: set[int] = set()
        cur: Optional[BaseException] = e
        while cur is not None and id(cur) not in seen:
            seen.add(id(cur))
            yield cur
            nxt = getattr(cur, "__cause__", None) or getattr(cur, "__context__", None)
            cur = nxt if isinstance(nxt, BaseException) else None

    def _is_rate_limited(e: BaseException) -> bool:
        # Prefer type checks, but also fall back to message heuristics.
        try:
            import instagrapi.exceptions as ex  # type: ignore

            rate_types = tuple(
                getattr(ex, n)
                for n in [
                    "RateLimitError",
                    "ClientThrottledError",
                    "PleaseWaitFewMinutes",
                    "FeedbackRequired",
                    "SentryBlock",
                    "ProxyAddressIsBlocked",
                ]
                if hasattr(ex, n)
            )
        except Exception:
            rate_types = tuple()

        for x in _iter_exc_chain(e):
            if rate_types and isinstance(x, rate_types):
                return True
            msg = (str(x) or "").lower()
            if any(
                s in msg
                for s in [
                    "please wait a few minutes",
                    "rate limit",
                    "ratelimit",
                    "too many requests",
                    "feedback_required",
                    "try again later",
                    "throttled",
                    "sentry_block",
                    "429",
                ]
            ):
                return True
        return False

    try:
        info = ig.get_user_info_by_username(username)
    except Exception as e:
        if _is_rate_limited(e):
            raise RateLimitedError(
                f"Instagram rate limited requests while fetching @{username}.",
                retry_after_s=10 * 60,
            ) from e
        raise
    stats = UserStats(
        username=str(getattr(info, "username", "") or username),
        user_id=_coerce_int(getattr(info, "pk", None) or getattr(info, "id", None)),
        follower_count=_coerce_int(getattr(info, "follower_count", None)),
        following_count=_coerce_int(getattr(info, "following_count", None)),
        is_private=_coerce_bool(getattr(info, "is_private", None)),
        is_verified=_coerce_bool(getattr(info, "is_verified", None)),
        full_name=str(getattr(info, "full_name", "") or ""),
        fetched_ts=now,
    )
    cache[key] = asdict(stats)
    return stats


def get_not_following_back_usernames(*, follow_cache_ttl_s: int = 6 * 60 * 60, force_refresh: bool = False) -> list[str]:
    """
    Returns usernames you follow that don't follow you back.
    Uses a local cache for followers/following lists to stay fast.
    """
    now = time.time()
    fc = _load_follow_cache()
    ts = float(fc.get("ts") or 0.0) if isinstance(fc, dict) else 0.0

    followers_ids: set[int] = set()
    following_map: dict[int, str] = {}

    if (not force_refresh) and ts and (now - ts) < follow_cache_ttl_s:
        try:
            followers_ids = {int(x) for x in (fc.get("followers_ids") or [])}
        except Exception:
            followers_ids = set()
        try:
            following_raw = fc.get("following_map") or {}
            if isinstance(following_raw, dict):
                following_map = {int(k): str(v) for k, v in following_raw.items() if str(k).isdigit()}
        except Exception:
            following_map = {}

    if not followers_ids or not following_map:
        cfg = load_config()
        ig = IgClient(session_path=Path("ig_session.json"))
        ig.login(cfg.ig_username, cfg.ig_password)
        followers = ig.get_followers_map()
        following = ig.get_following_map()
        followers_ids = set(followers.keys())
        following_map = following
        _save_follow_cache(
            {
                "ts": now,
                "followers_ids": sorted(followers_ids),
                "following_map": {str(k): v for k, v in following_map.items()},
            }
        )

    not_back_ids = sorted(set(following_map.keys()) - set(followers_ids))
    usernames = [following_map[i] for i in not_back_ids if i in following_map]
    return sorted(set(usernames))


def warm_user_cache_step(
    *,
    chunk_size: int = 25,
    cache_ttl_s: int = 7 * 24 * 60 * 60,
    follow_cache_ttl_s: int = 6 * 60 * 60,
    refresh_follow_cache: bool = False,
    min_delay_s: float = 0.7,
    jitter_s: float = 0.3,
) -> dict:
    """
    Warms `user_cache.json` by fetching stats for the "not following back" usernames in chunks.

    Progress definition:
    - processed: how many usernames have been *processed* (either already cached+fresh OR fetched now)
    - 100% means processed == total (we attempted the whole list)
    """
    now = time.time()
    usernames = get_not_following_back_usernames(
        follow_cache_ttl_s=follow_cache_ttl_s, force_refresh=bool(refresh_follow_cache)
    )

    total = len(usernames)
    if total == 0:
        reset_warm_cache_state()
        return {"total": 0, "processed": 0, "percent": 100.0, "done": True, "newly_fetched": 0}

    # Resume from previous state if it matches the same list size.
    state = _load_warm_state()
    next_index = 0
    if isinstance(state, dict):
        try:
            if int(state.get("total") or 0) == total:
                next_index = int(state.get("next_index") or 0)
        except Exception:
            next_index = 0

    # If we were rate-limited recently, pause.
    try:
        blocked_until_ts = float(state.get("blocked_until_ts") or 0.0) if isinstance(state, dict) else 0.0
    except Exception:
        blocked_until_ts = 0.0
    if blocked_until_ts and now < blocked_until_ts:
        retry_after_s = int(max(1.0, blocked_until_ts - now))
        return {
            "total": total,
            "processed": next_index,
            "percent": round((next_index / total) * 100.0, 1),
            "done": False,
            "newly_fetched": 0,
            "rate_limited": True,
            "retry_after_s": retry_after_s,
        }

    next_index = max(0, min(total, next_index))
    chunk_size = max(1, int(chunk_size or 25))
    end = min(total, next_index + chunk_size)

    cfg = load_config()
    ig = IgClient(session_path=Path("ig_session.json"))
    ig.login(cfg.ig_username, cfg.ig_password)

    cache = _load_cache()
    newly_fetched = 0
    processed = next_index
    for u in usernames[next_index:end]:
        key = u.strip().lower()
        had = key in cache
        try:
            _ = get_user_stats_by_username(
                ig,
                u,
                cache=cache,
                ttl_s=cache_ttl_s,
                min_delay_s=min_delay_s,
                jitter_s=jitter_s,
            )
        except RateLimitedError as rl:
            blocked_until_ts = time.time() + int(getattr(rl, "retry_after_s", 600))
            _save_warm_state(
                {
                    "ts": now,
                    "total": total,
                    "next_index": processed,
                    "done": False,
                    "blocked_until_ts": blocked_until_ts,
                    "blocked_reason": str(rl),
                }
            )
            return {
                "total": total,
                "processed": processed,
                "percent": round((processed / total) * 100.0, 1),
                "done": False,
                "newly_fetched": newly_fetched,
                "rate_limited": True,
                "retry_after_s": int(max(1.0, blocked_until_ts - time.time())),
                "error": str(rl),
            }
        if not had:
            newly_fetched += 1
        processed += 1

    _save_cache(cache)

    done = processed >= total
    percent = round((processed / total) * 100.0, 1)
    _save_warm_state(
        {
            "ts": now,
            "total": total,
            "next_index": 0 if done else processed,
            "done": done,
            "blocked_until_ts": 0,
        }
    )
    return {
        "total": total,
        "processed": processed,
        "percent": percent,
        "done": done,
        "newly_fetched": newly_fetched,
    }

def not_following_back_detailed(
    *,
    min_followers: Optional[int] = None,
    max_followers: Optional[int] = None,
    include_private: bool = True,
    include_verified: bool = True,
    username_contains: str = "",
    sort_by: Literal["followers", "username"] = "followers",
    sort_dir: Literal["asc", "desc"] = "desc",
    max_profiles: int = 200,
    offset: int = 0,
    limit: int = 50,
    cache_ttl_s: int = 7 * 24 * 60 * 60,
    cache_only: bool = False,
    max_fetch_missing: int = 25,
    follow_cache_ttl_s: int = 6 * 60 * 60,
    refresh_follow_cache: bool = False,
) -> list[dict]:
    """
    Returns a list of detailed user objects for:
    accounts you follow who don't follow you back.
    """
    usernames = get_not_following_back_usernames(
        follow_cache_ttl_s=follow_cache_ttl_s, force_refresh=bool(refresh_follow_cache)
    )

    q = (username_contains or "").strip().lower()
    if q:
        usernames = [u for u in usernames if q in u.lower()]

    usernames = sorted(set(usernames))
    if max_profiles and max_profiles > 0:
        usernames = usernames[:max_profiles]

    # pagination
    offset = max(0, int(offset or 0))
    limit = max(1, int(limit or 50))
    usernames = usernames[offset : offset + limit]

    cfg = load_config()
    ig = IgClient(session_path=Path("ig_session.json"))
    ig.login(cfg.ig_username, cfg.ig_password)

    cache = _load_cache()
    out: list[dict] = []
    fetched_missing = 0
    for u in usernames:
        # Cache-only mode: don't fetch missing stats, just use cached values.
        key = u.strip().lower()
        cached = cache.get(key)
        if cache_only and not cached:
            continue

        if (not cache_only) and (not cached) and fetched_missing >= max_fetch_missing:
            continue

        st = get_user_stats_by_username(ig, u, cache=cache, ttl_s=cache_ttl_s)
        if not cached:
            fetched_missing += 1

        if not include_private and st.is_private is True:
            continue
        if not include_verified and st.is_verified is True:
            continue

        fc = st.follower_count
        if min_followers is not None and fc is not None and fc < min_followers:
            continue
        if max_followers is not None and fc is not None and fc > max_followers:
            continue

        out.append(
            {
                "username": st.username,
                "followers": st.follower_count,
                "following": st.following_count,
                "is_private": st.is_private,
                "is_verified": st.is_verified,
                "full_name": st.full_name,
            }
        )

    _save_cache(cache)

    reverse = sort_dir == "desc"
    if sort_by == "username":
        out.sort(key=lambda x: (x.get("username") or "").lower(), reverse=reverse)
    else:
        # followers: unknowns last
        def keyf(x):
            v = x.get("followers")
            if v is None:
                return -1 if reverse else 10**18
            return int(v)

        out.sort(key=keyf, reverse=reverse)

    return out

