import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.unfollow import check_unfollows_and_update


TZ = ZoneInfo("Europe/Berlin")


WEEKDAY_NAME_TO_INT = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def next_weekly_run(now: datetime, *, weekday: int, hour: int = 22, minute: int = 0) -> datetime:
    """
    Compute the next occurrence of weekday@hour:minute in Europe/Berlin.
    weekday: Monday=0 ... Sunday=6 (matches datetime.weekday()).
    """
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    days_ahead = (weekday - now.weekday()) % 7
    target = target + timedelta(days=days_ahead)
    if target <= now:
        target = target + timedelta(days=7)
    return target


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--weekday",
        default="sunday",
        help="Weekday to run at 22:00 Berlin time (e.g. sunday, mon). Default: sunday.",
    )
    args = ap.parse_args()
    weekday_key = str(args.weekday).strip().lower()
    weekday = WEEKDAY_NAME_TO_INT.get(weekday_key, 6)  # default Sunday

    while True:
        now = datetime.now(TZ)
        nxt = next_weekly_run(now, weekday=weekday, hour=22, minute=0)
        sleep_s = max(1.0, (nxt - now).total_seconds())
        print(f"[unfollow_scheduler] Now: {now.isoformat()} | Next run: {nxt.isoformat()} | Sleeping {sleep_s:.0f}s")
        time.sleep(sleep_s)
        try:
            print("[unfollow_scheduler] Checking unfollows...")
            unf = check_unfollows_and_update(notify=True)
            print(f"[unfollow_scheduler] Done. unfollows={len(unf)}")
        except Exception as e:  # noqa: BLE001
            print(f"[unfollow_scheduler] Run failed: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()

