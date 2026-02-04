import argparse
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.main import load_config, resend_last, run_once
from src.state import load_state, save_state


def next_time(now: datetime, *, hour: int, minute: int) -> datetime:
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now < target:
        return target
    return target + timedelta(days=1)


def cleanup_media_dir() -> None:
    media_dir = Path("media")
    if not media_dir.exists():
        return
    for p in list(media_dir.iterdir()):
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
        except Exception:
            pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", default="14:50", help="Target time HH:MM (default 14:50)")
    ap.add_argument(
        "--tz", default="Europe/Berlin", help="IANA timezone (default Europe/Berlin)"
    )
    ap.add_argument(
        "--resend-last", action="store_true", help="Resend last batch (test)"
    )
    ap.add_argument(
        "--cleanup-media",
        action="store_true",
        help="Delete media/ contents after success",
    )
    args = ap.parse_args()

    hour_s, minute_s = args.time.split(":", 1)
    hour = int(hour_s)
    minute = int(minute_s)
    tz = ZoneInfo(args.tz)

    now = datetime.now(tz)
    nxt = next_time(now, hour=hour, minute=minute)
    sleep_s = max(1.0, (nxt - now).total_seconds())
    print(
        f"[run_at] Now: {now.isoformat()} | Scheduled: {nxt.isoformat()} | Sleeping {sleep_s:.0f}s"
    )
    time.sleep(sleep_s)

    cfg = load_config()
    print("[run_at] Running job...")

    if args.resend_last:
        resend_last(cfg=cfg)
    else:
        run_once(cfg=cfg)

    print("[run_at] Job completed successfully.")

    if args.cleanup_media:
        cleanup_media_dir()
        # also clear last_run_files so resend doesn't point to deleted paths
        st = load_state()
        st.last_run_files = []
        save_state(st)
        print("[run_at] Cleaned media/ and cleared last_run_files.")


if __name__ == "__main__":
    main()
