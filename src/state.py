import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Set

STATE_PATH = Path("state.json")


@dataclass
class State:
    sent_ids: Set[str] = field(default_factory=set)
    # New: per-recipient dedupe (recipient_id -> set[item_id])
    sent_ids_by_recipient: dict[str, Set[str]] = field(default_factory=dict)
    last_run_ts: Optional[float] = None  # unix seconds
    last_run_files: list[str] = field(default_factory=list)
    last_run_caption: str = ""


def load_state() -> State:
    if not STATE_PATH.exists():
        return State()
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    sent = set(data.get("sent_ids", []))
    sent_by_recipient: dict[str, Set[str]] = {}
    raw_map = data.get("sent_ids_by_recipient", {}) or {}
    if isinstance(raw_map, dict):
        for k, v in raw_map.items():
            try:
                rid = str(k)
                if isinstance(v, list):
                    sent_by_recipient[rid] = set(str(x) for x in v)
                elif isinstance(v, set):
                    sent_by_recipient[rid] = set(str(x) for x in list(v))
            except Exception:
                continue
    last_run_ts = data.get("last_run_ts", None)
    try:
        last_run_ts = float(last_run_ts) if last_run_ts is not None else None
    except Exception:
        last_run_ts = None
    last_run_files = data.get("last_run_files", []) or []
    if not isinstance(last_run_files, list):
        last_run_files = []
    last_run_files = [str(x) for x in last_run_files]
    last_run_caption = str(data.get("last_run_caption", "") or "")
    return State(
        sent_ids=sent,
        sent_ids_by_recipient=sent_by_recipient,
        last_run_ts=last_run_ts,
        last_run_files=last_run_files,
        last_run_caption=last_run_caption,
    )


def save_state(state: State) -> None:
    payload = {
        "sent_ids": sorted(state.sent_ids),
        "sent_ids_by_recipient": {
            k: sorted(list(v)) for k, v in (state.sent_ids_by_recipient or {}).items()
        },
        "last_run_ts": state.last_run_ts,
        "last_run_files": list(state.last_run_files),
        "last_run_caption": state.last_run_caption,
    }
    STATE_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
