import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.main import load_config, run_once
from src.settings import RecipientSettings, ScheduleSettings, load_settings


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


def _get_recipient_schedule(
    recipient, global_schedule: ScheduleSettings
) -> tuple[bool, str, str]:
    """Get effective schedule for a recipient (per-recipient or global fallback)."""
    enabled = (
        recipient.schedule_enabled
        if recipient.schedule_enabled is not None
        else global_schedule.enabled
    )
    tz = (
        recipient.schedule_tz
        if recipient.schedule_tz
        else (global_schedule.tz or "Europe/Berlin")
    )
    time_hhmm = (
        recipient.schedule_time_hhmm
        if recipient.schedule_time_hhmm
        else (global_schedule.time_hhmm or "19:00")
    )
    return enabled, tz, time_hhmm


def main() -> None:
    cfg = load_config()
    while True:
        st = load_settings(
            default_recipient_name=cfg.wa_content_contact_name,
            default_recipient_phone=cfg.wa_content_phone,
        )

        # Get enabled recipients with valid contact info
        enabled_recipients = [
            r
            for r in (st.recipients or [])
            if r.enabled and (r.wa_contact_name or r.wa_phone)
        ]

        if not enabled_recipients:
            print("[scheduler] No enabled recipients. Sleeping 60s")
            time.sleep(60)
            continue

        # Calculate next run time for each recipient
        recipient_schedules: list[tuple[RecipientSettings, datetime, ZoneInfo, str]] = (
            []
        )
        for recipient in enabled_recipients:
            enabled, tz_name, time_hhmm = _get_recipient_schedule(
                recipient, st.schedule
            )
            if not enabled:
                continue
            try:
                tz = ZoneInfo(tz_name)
            except Exception:
                tz = ZoneInfo("Europe/Berlin")
                tz_name = "Europe/Berlin"
            now = datetime.now(tz)
            nxt = next_daily_run(now, hhmm=time_hhmm)
            recipient_schedules.append((recipient, nxt, tz, tz_name))

        if not recipient_schedules:
            print("[scheduler] No recipients with enabled schedules. Sleeping 60s")
            time.sleep(60)
            continue

        # Find the next recipient to run
        recipient_schedules.sort(key=lambda x: x[1])  # Sort by next run time
        next_recipient, next_time, next_tz, next_tz_name = recipient_schedules[0]

        # Sleep until next run, checking for changes
        while True:
            now = datetime.now(next_tz)
            remaining = (next_time - now).total_seconds()
            if remaining <= 0:
                break
            chunk = min(60.0, max(1.0, remaining))
            print(
                f"[scheduler] Next: {next_recipient.display_name} at {next_time.isoformat()} ({next_tz_name}) | Sleeping {chunk:.0f}s"
            )
            time.sleep(chunk)
            # Reload settings to check for changes
            st2 = load_settings(
                default_recipient_name=cfg.wa_content_contact_name,
                default_recipient_phone=cfg.wa_content_phone,
            )
            # If settings changed significantly, recompute
            if len(st2.recipients) != len(st.recipients):
                break

        try:
            print(f"[scheduler] Running for {next_recipient.display_name}...")
            run_once(cfg=cfg, recipient_id=next_recipient.id)
        except Exception as e:  # noqa: BLE001
            print(f"[scheduler] Run failed for {next_recipient.display_name}: {e}")
            # backoff to avoid hot loops on repeated failures
            time.sleep(60)


if __name__ == "__main__":
    main()
