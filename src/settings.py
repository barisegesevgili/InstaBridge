import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path("settings.json")


def _now_ts() -> float:
    return time.time()


@dataclass
class RecipientSettings:
    """
    WhatsApp recipient + content preferences + per-recipient schedule.
    """

    id: str
    display_name: str
    wa_contact_name: str = ""
    wa_phone: str = ""
    enabled: bool = True

    # Content toggles
    send_posts: bool = True
    send_stories: bool = True
    send_close_friends_stories: bool = False

    # Per-recipient schedule (if None, uses global schedule)
    schedule_enabled: bool | None = None  # None = use global, True/False = override
    schedule_tz: str | None = None  # None = use global
    schedule_time_hhmm: str | None = None  # None = use global


@dataclass
class ScheduleSettings:
    """
    Daily scheduler settings.
    """

    enabled: bool = True
    tz: str = "Europe/Berlin"
    time_hhmm: str = "19:00"


@dataclass
class AppSettings:
    version: int = 1
    updated_ts: float = field(default_factory=_now_ts)
    schedule: ScheduleSettings = field(default_factory=ScheduleSettings)
    recipients: list[RecipientSettings] = field(default_factory=list)


def _coerce_bool(x: Any, default: bool) -> bool:
    if isinstance(x, bool):
        return x
    return default


def _coerce_str(x: Any, default: str = "") -> str:
    if x is None:
        return default
    return str(x)


def _normalize_phone(x: str) -> str:
    # keep digits only; WhatsApp deep-link expects digits
    return "".join(ch for ch in (x or "") if ch.isdigit())


def _validate_time_hhmm(v: str) -> str:
    v = (v or "").strip()
    if not v:
        return "19:00"
    parts = v.split(":")
    if len(parts) != 2:
        return "19:00"
    try:
        hh = int(parts[0])
        mm = int(parts[1])
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return f"{hh:02d}:{mm:02d}"
    except Exception:
        pass
    return "19:00"


def load_settings(
    *, default_recipient_name: str = "", default_recipient_phone: str = ""
) -> AppSettings:
    """
    Loads settings.json if present; otherwise returns a default settings object.
    If there are no recipients configured yet, we create one from the env-based defaults.
    """
    if SETTINGS_PATH.exists():
        try:
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
    else:
        raw = {}

    sched_raw = raw.get("schedule") if isinstance(raw, dict) else {}
    if not isinstance(sched_raw, dict):
        sched_raw = {}
    schedule = ScheduleSettings(
        enabled=_coerce_bool(sched_raw.get("enabled"), True),
        tz=_coerce_str(sched_raw.get("tz") or "Europe/Berlin", "Europe/Berlin"),
        time_hhmm=_validate_time_hhmm(
            _coerce_str(sched_raw.get("time_hhmm") or "19:00", "19:00")
        ),
    )

    recipients: list[RecipientSettings] = []
    rec_raw = raw.get("recipients") if isinstance(raw, dict) else []
    if isinstance(rec_raw, list):
        for r in rec_raw:
            if not isinstance(r, dict):
                continue
            rid = _coerce_str(r.get("id") or "").strip()
            if not rid:
                continue
            # Parse schedule fields (None if not set, to use global)
            sched_enabled = r.get("schedule_enabled")
            sched_enabled = (
                None if sched_enabled is None else _coerce_bool(sched_enabled, True)
            )
            sched_tz = r.get("schedule_tz")
            sched_tz = None if sched_tz is None else _coerce_str(sched_tz, "")
            sched_time = r.get("schedule_time_hhmm")
            sched_time = (
                None
                if sched_time is None
                else _validate_time_hhmm(_coerce_str(sched_time, "19:00"))
            )

            recipients.append(
                RecipientSettings(
                    id=rid,
                    display_name=_coerce_str(
                        r.get("display_name") or r.get("wa_contact_name") or rid, rid
                    ).strip(),
                    wa_contact_name=_coerce_str(
                        r.get("wa_contact_name") or "", ""
                    ).strip(),
                    wa_phone=_normalize_phone(_coerce_str(r.get("wa_phone") or "", "")),
                    enabled=_coerce_bool(r.get("enabled"), True),
                    send_posts=_coerce_bool(r.get("send_posts"), True),
                    send_stories=_coerce_bool(r.get("send_stories"), True),
                    send_close_friends_stories=_coerce_bool(
                        r.get("send_close_friends_stories"), False
                    ),
                    schedule_enabled=sched_enabled,
                    schedule_tz=sched_tz,
                    schedule_time_hhmm=sched_time,
                )
            )

    # If no recipients exist yet, seed one from env-based defaults.
    if not recipients and (default_recipient_name or default_recipient_phone):
        recipients = [
            RecipientSettings(
                id="default",
                display_name=(default_recipient_name or "Friend").strip() or "Friend",
                wa_contact_name=(default_recipient_name or "").strip(),
                wa_phone=_normalize_phone(default_recipient_phone or ""),
                enabled=True,
                send_posts=True,
                send_stories=True,
                send_close_friends_stories=False,
            )
        ]

    st = AppSettings(
        version=int(raw.get("version") or 1) if isinstance(raw, dict) else 1,
        updated_ts=(
            float(raw.get("updated_ts") or _now_ts())
            if isinstance(raw, dict)
            else _now_ts()
        ),
        schedule=schedule,
        recipients=recipients,
    )
    return st


def save_settings(settings: AppSettings) -> None:
    settings.updated_ts = _now_ts()
    payload = asdict(settings)
    SETTINGS_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def settings_to_public_dict(settings: AppSettings) -> dict:
    """
    JSON shape for UI/API.
    """
    return asdict(settings)


def settings_from_public_dict(data: dict) -> AppSettings:
    """
    Parse UI payload into validated settings.
    """
    if not isinstance(data, dict):
        raise ValueError("settings payload must be an object")

    sched = data.get("schedule", {})
    if not isinstance(sched, dict):
        sched = {}

    schedule = ScheduleSettings(
        enabled=_coerce_bool(sched.get("enabled"), True),
        tz=_coerce_str(sched.get("tz") or "Europe/Berlin", "Europe/Berlin"),
        time_hhmm=_validate_time_hhmm(
            _coerce_str(sched.get("time_hhmm") or "19:00", "19:00")
        ),
    )

    recipients_in = data.get("recipients", [])
    if not isinstance(recipients_in, list):
        recipients_in = []

    recipients: list[RecipientSettings] = []
    seen_ids: set[str] = set()
    for r in recipients_in:
        if not isinstance(r, dict):
            continue
        rid = _coerce_str(r.get("id") or "").strip()
        if not rid or rid in seen_ids:
            continue
        seen_ids.add(rid)
        display_name = _coerce_str(
            r.get("display_name") or r.get("wa_contact_name") or rid, rid
        ).strip()
        wa_contact_name = _coerce_str(r.get("wa_contact_name") or "", "").strip()
        wa_phone = _normalize_phone(_coerce_str(r.get("wa_phone") or "", ""))
        # Parse schedule fields
        sched_enabled = r.get("schedule_enabled")
        sched_enabled = (
            None if sched_enabled is None else _coerce_bool(sched_enabled, True)
        )
        sched_tz = r.get("schedule_tz")
        sched_tz = None if sched_tz is None else _coerce_str(sched_tz, "")
        sched_time = r.get("schedule_time_hhmm")
        sched_time = (
            None
            if sched_time is None
            else _validate_time_hhmm(_coerce_str(sched_time, "19:00"))
        )

        recipients.append(
            RecipientSettings(
                id=rid,
                display_name=display_name or rid,
                wa_contact_name=wa_contact_name,
                wa_phone=wa_phone,
                enabled=_coerce_bool(r.get("enabled"), True),
                send_posts=_coerce_bool(r.get("send_posts"), True),
                send_stories=_coerce_bool(r.get("send_stories"), True),
                send_close_friends_stories=_coerce_bool(
                    r.get("send_close_friends_stories"), False
                ),
                schedule_enabled=sched_enabled,
                schedule_tz=sched_tz,
                schedule_time_hhmm=sched_time,
            )
        )

    return AppSettings(version=1, schedule=schedule, recipients=recipients)
