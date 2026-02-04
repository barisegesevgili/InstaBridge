import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.main import load_config, run_once
from src.settings import load_settings


def _parse_hhmm(v: str) -> tuple[int, int]:
    v = (v or "").strip()
    try:
        hh_s, mm_s = v.split(":")
        hh = int(hh_s)
        mm = int(mm_s)
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return hh, mm
    except Exception:
        pass
    return 19, 0


def next_daily_run(now: datetime, *, hhmm: str) -> datetime:
    hh, mm = _parse_hhmm(hhmm)
    today_at = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if now < today_at:
        return today_at
    return today_at + timedelta(days=1)


def main() -> None:
    cfg = load_config()
    while True:
        st = load_settings(
            default_recipient_name=cfg.wa_content_contact_name,
            default_recipient_phone=cfg.wa_content_phone,
        )
        tz_name = (st.schedule.tz or "Europe/Berlin").strip() or "Europe/Berlin"
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("Europe/Berlin")
            tz_name = "Europe/Berlin"

        if not st.schedule.enabled:
            now = datetime.now(tz)
            print(
                f"[scheduler] Schedule disabled in settings.json. Now: {now.isoformat()} ({tz_name}). Sleeping 60s"
            )
            time.sleep(60)
            continue

        now = datetime.now(tz)
        nxt = next_daily_run(now, hhmm=st.schedule.time_hhmm)
        # Sleep in chunks so settings changes take effect quickly.
        while True:
            now2 = datetime.now(tz)
            remaining = (nxt - now2).total_seconds()
            if remaining <= 0:
                break
            chunk = min(60.0, max(1.0, remaining))
            print(
                f"[scheduler] Now: {now2.isoformat()} ({tz_name}) | Next run: {nxt.isoformat()} | Sleeping {chunk:.0f}s"
            )
            time.sleep(chunk)
            # If schedule/timezone changed, recompute.
            st2 = load_settings(
                default_recipient_name=cfg.wa_content_contact_name,
                default_recipient_phone=cfg.wa_content_phone,
            )
            if (
                not st2.schedule.enabled
                or st2.schedule.time_hhmm != st.schedule.time_hhmm
                or (st2.schedule.tz or "") != (st.schedule.tz or "")
            ):
                break
        try:
            print("[scheduler] Running...")
            run_once(cfg=cfg)
        except Exception as e:  # noqa: BLE001
            print(f"[scheduler] Run failed: {e}")
            # backoff to avoid hot loops on repeated failures
            time.sleep(60)


if __name__ == "__main__":
    main()
