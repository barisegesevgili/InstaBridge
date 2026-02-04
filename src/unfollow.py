import argparse
import json
import time
from pathlib import Path

from src.ig import IgClient
from src.insights import get_not_following_back_usernames
from src.main import load_config
from src.wa import WhatsAppSender


SNAPSHOT_PATH = Path("unfollow_state.json")


def load_snapshot() -> dict:
    if not SNAPSHOT_PATH.exists():
        return {}
    try:
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_snapshot(snapshot: dict) -> None:
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def list_not_following_back() -> list[str]:
    # Fast path with cached followers/following sets.
    return get_not_following_back_usernames()


def check_unfollows_and_update(*, notify: bool) -> list[str]:
    cfg = load_config()
    ig = IgClient(session_path=Path("ig_session.json"))
    ig.login(cfg.ig_username, cfg.ig_password)

    current = ig.get_followers_map()  # {id: username}
    now = time.time()

    snap = load_snapshot()
    prev = snap.get("followers", {}) if isinstance(snap.get("followers", {}), dict) else {}
    prev = {int(k): str(v) for k, v in prev.items() if str(k).isdigit()}

    unfollowed_ids = sorted(set(prev.keys()) - set(current.keys()))
    unfollowed_usernames = [prev[i] for i in unfollowed_ids if i in prev]

    # Update snapshot
    save_snapshot(
        {
            "ts": now,
            "followers": {str(k): v for k, v in current.items()},
        }
    )

    if notify and unfollowed_usernames:
        wa = WhatsAppSender(profile_dir=Path("wa_profile"))
        wa.start()
        msg = "Unfollow alert:\n" + "\n".join(f"- {u}" for u in unfollowed_usernames)
        wa.send_text(cfg.wa_report_contact_name, msg, phone=cfg.wa_report_phone)
        wa.stop()

    return unfollowed_usernames


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--not-following-back", action="store_true", help="List users you follow who don't follow you back.")
    ap.add_argument("--check-unfollows", action="store_true", help="Compare followers with last snapshot and update.")
    ap.add_argument("--notify", action="store_true", help="Send WhatsApp message if unfollows detected (with --check-unfollows).")
    args = ap.parse_args()

    if args.not_following_back or (not args.check_unfollows):
        users = list_not_following_back()
        print(f"Not following you back: {len(users)}")
        for u in users:
            print(u)
        return

    unf = check_unfollows_and_update(notify=bool(args.notify))
    if unf:
        print(f"Unfollowed since last check: {len(unf)}")
        for u in unf:
            print(u)
    else:
        print("No unfollows detected since last check.")


if __name__ == "__main__":
    main()

