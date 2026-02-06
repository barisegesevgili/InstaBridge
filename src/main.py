import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from src.ig import IgClient, IgItem
from src.state import load_state, save_state
from src.settings import RecipientSettings, load_settings
from src.wa import WhatsAppSender

# Try to load credentials from keychain first, fall back to .env
try:
    from src.credentials import load_credentials_safely

    USE_KEYCHAIN = True
except ImportError:
    USE_KEYCHAIN = False


@dataclass(frozen=True)
class Config:
    ig_username: str
    ig_password: str
    wa_content_contact_name: str
    wa_content_phone: str
    wa_report_contact_name: str
    wa_report_phone: str
    message_prefix: str


def load_config() -> Config:
    """Load configuration from keychain (preferred) or .env file (fallback).

    Priority:
    1. System keychain (if keyring installed and credentials stored)
    2. Environment variables / .env file

    For setup, run: python -m src.credentials
    """
    # Try keychain first
    if USE_KEYCHAIN:
        try:
            creds = load_credentials_safely()
            print("🔐 Loaded credentials from system keychain")
            return Config(
                ig_username=creds["IG_USERNAME"],
                ig_password=creds["IG_PASSWORD"],
                wa_content_contact_name=creds["WA_CONTENT_CONTACT_NAME"],
                wa_content_phone=creds["WA_CONTENT_PHONE"],
                wa_report_contact_name=creds["WA_REPORT_CONTACT_NAME"],
                wa_report_phone=creds["WA_REPORT_PHONE"],
                message_prefix=creds["MESSAGE_PREFIX"],
            )
        except Exception as e:
            print(f"⚠️  Could not load from keychain: {e}")
            print("   Falling back to .env file...")

    # Fall back to .env
    load_dotenv()
    ig_username = os.getenv("IG_USERNAME", "").strip()
    ig_password = os.getenv("IG_PASSWORD", "").strip()
    # New vars
    wa_content_contact_name = os.getenv("WA_CONTENT_CONTACT_NAME", "").strip()
    wa_content_phone = os.getenv("WA_CONTENT_PHONE", "").strip()
    wa_report_contact_name = os.getenv("WA_REPORT_CONTACT_NAME", "").strip()
    wa_report_phone = os.getenv("WA_REPORT_PHONE", "").strip()

    # Legacy vars (backward compatible)
    legacy_name = os.getenv("WA_CONTACT_NAME", "").strip()
    legacy_phone = os.getenv("WA_PHONE", "").strip()

    if not wa_content_contact_name:
        wa_content_contact_name = legacy_name
    if not wa_content_phone:
        wa_content_phone = legacy_phone
    if not wa_report_contact_name:
        wa_report_contact_name = legacy_name or "Notes"
    if not wa_report_phone:
        wa_report_phone = ""  # optional

    message_prefix = os.getenv("MESSAGE_PREFIX", "New from Instagram:").strip()

    missing = []
    if not ig_username:
        missing.append("IG_USERNAME")
    if not ig_password:
        missing.append("IG_PASSWORD")
    if not wa_content_contact_name:
        missing.append("WA_CONTENT_CONTACT_NAME (or legacy WA_CONTACT_NAME)")
    if missing:
        raise SystemExit(
            "Missing required credentials.\n\n"
            "Option 1 (Secure): Use system keychain\n"
            "  python -m src.credentials\n\n"
            "Option 2 (Less secure): Use .env file\n"
            "  Copy .env.example to .env and fill values.\n\n"
            f"Missing: {', '.join(missing)}"
        )

    return Config(
        ig_username=ig_username,
        ig_password=ig_password,
        wa_content_contact_name=wa_content_contact_name,
        wa_content_phone=wa_content_phone,
        wa_report_contact_name=wa_report_contact_name,
        wa_report_phone=wa_report_phone,
        message_prefix=message_prefix or "New from Instagram:",
    )


def _format_run_caption(prefix: str, items: list[IgItem]) -> str:
    lines: list[str] = [prefix]
    for it in items:
        if it.kind == "post":
            lines.append("post: latest")
        else:
            if it.story_is_close_friends is True:
                lines.append("story (close friends)")
            else:
                lines.append("story")
        if it.caption:
            lines.append(it.caption)
        lines.append("")  # spacer
    return "\n".join(lines).strip()


def _recipient_wants_item(r: RecipientSettings, it: IgItem) -> bool:
    if not r.enabled:
        return False
    if it.kind == "post":
        return bool(r.send_posts)
    # story
    if it.story_is_close_friends is True:
        return bool(r.send_close_friends_stories)
    return bool(r.send_stories)


def resend_last(*, cfg: Config, max_files: int = 0) -> None:
    state = load_state()
    files = [Path(p) for p in state.last_run_files]
    files = [p for p in files if p.exists()]
    caption = state.last_run_caption or "Resend test"

    if not files:
        # Fallback: resend most-recent cached media files.
        media_dir = Path("media")
        if media_dir.exists():
            candidates = [p for p in media_dir.iterdir() if p.is_file()]
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            files = candidates[:12]
        caption = "Resend test (from media cache)"

    if not files:
        print("Nothing to resend (no last batch recorded, and media/ is empty).")
        return

    if max_files and max_files > 0:
        files = files[:max_files]

    wa = WhatsAppSender(profile_dir=Path("wa_profile"))
    print("Opening WhatsApp Web (scan QR if asked)...")
    wa.start()
    print("WhatsApp Web ready.")
    wa.open_chat(contact_name=cfg.wa_content_contact_name, phone=cfg.wa_content_phone)
    print(f"Re-sending last batch ({len(files)} file(s))...")
    wa.send_media_batch(
        cfg.wa_content_contact_name, files, phone=cfg.wa_content_phone, caption=caption
    )
    wa.stop()
    print("Done: re-sent last batch (state unchanged).")


def run_once(
    *,
    cfg: Config,
    force_resend_current: bool = False,
    dry_run: bool = False,
    recipient_id: str | None = None,
) -> None:
    media_dir = Path("media")
    media_dir.mkdir(exist_ok=True)

    if dry_run:
        print("🔍 DRY RUN MODE: No actual messages will be sent")

    state = load_state()
    settings = load_settings(
        default_recipient_name=cfg.wa_content_contact_name,
        default_recipient_phone=cfg.wa_content_phone,
    )

    ig = IgClient(session_path=Path("ig_session.json"))
    print("Logging into Instagram...")
    ig.login(cfg.ig_username, cfg.ig_password)
    print("Instagram login OK.")

    wa = None
    if not dry_run:
        wa = WhatsAppSender(profile_dir=Path("wa_profile"))
        print("Opening WhatsApp Web (scan QR if asked)...")
        wa.start()
        print("WhatsApp Web ready.")
    else:
        print("📵 Dry run: Skipping WhatsApp Web connection")

    # Filter recipients: if recipient_id specified, only that one; otherwise all enabled
    all_recipients = [
        r
        for r in (settings.recipients or [])
        if r.enabled and (r.wa_contact_name or r.wa_phone)
    ]
    if recipient_id:
        recipients = [r for r in all_recipients if r.id == recipient_id]
        if not recipients:
            if wa:
                wa.stop()
            print(f"Done: recipient '{recipient_id}' not found or not enabled.")
            return
    else:
        recipients = all_recipients
    if not recipients:
        if wa:
            wa.stop()
        print("Done: no enabled recipients configured in settings.json.")
        state.last_run_ts = time.time()
        save_state(state)
        return

    # Collect items for this run:
    # - posts since last run (or just latest post on first run)
    # - all active stories
    items: list[IgItem] = []
    if state.last_run_ts is None:
        items.extend(ig.get_latest_post_items())
    else:
        items.extend(ig.get_new_post_items_since(state.last_run_ts, max_posts=12))
    items.extend(ig.get_active_story_items())

    cutoff_ts = time.time() - 24 * 60 * 60
    items = [it for it in items if (it.created_ts or 0.0) >= cutoff_ts]

    if not items:
        if wa:
            wa.stop()
        print("Done: nothing new to send.")
        state.last_run_ts = time.time()
        save_state(state)
        return

    # Decide which items each recipient should receive (content-type filtering + per-recipient dedupe).
    items_by_recipient: dict[str, list[IgItem]] = {}
    for r in recipients:
        rid = r.id
        already = state.sent_ids_by_recipient.get(rid, set())
        selected: list[IgItem] = []
        for it in items:
            if not _recipient_wants_item(r, it):
                continue
            if not force_resend_current and it.unique_id in already:
                continue
            selected.append(it)
        if selected:
            items_by_recipient[rid] = selected

    if not items_by_recipient:
        if wa:
            wa.stop()
        print("Done: nothing new to send (after filtering/dedupe).")
        state.last_run_ts = time.time()
        save_state(state)
        return

    # Download each needed item once (then send to multiple recipients).
    unique_needed = {
        it.unique_id: it for lst in items_by_recipient.values() for it in lst
    }
    downloaded: dict[str, list[Path]] = {}
    run_files: list[Path] = []
    for uid, it in unique_needed.items():
        print(f"Downloading {uid}...")
        paths = it.download(media_dir)
        downloaded[uid] = paths
        run_files.extend(paths)

    # Send per-recipient, and persist state after each item to avoid duplicates on crashes.
    for r in recipients:
        rid = r.id
        to_send = items_by_recipient.get(rid, [])
        if not to_send:
            continue
        print(
            f"{'[DRY RUN] Would send' if dry_run else 'Sending'} to {r.display_name} ({len(to_send)} item(s))..."
        )

        if dry_run:
            # Simulate sending without actual WhatsApp interaction
            for it in to_send:
                paths = downloaded.get(it.unique_id) or []
                if not paths:
                    continue
                caption = _format_run_caption(cfg.message_prefix, [it])
                print(f"  📋 Would send {len(paths)} file(s) for {it.unique_id}")
                print(
                    f"     Caption: {caption[:100]}..."
                    if len(caption) > 100
                    else f"     Caption: {caption}"
                )
            # Don't update state in dry-run mode
            continue

        # Real sending (non-dry-run)
        if wa:
            wa.open_chat(
                contact_name=r.wa_contact_name or r.display_name, phone=r.wa_phone
            )
        sent_set = state.sent_ids_by_recipient.setdefault(rid, set())
        for it in to_send:
            paths = downloaded.get(it.unique_id) or []
            if not paths:
                continue
            caption = _format_run_caption(cfg.message_prefix, [it])
            print(f"Sending {len(paths)} file(s) for {it.unique_id}...")
            if wa:
                wa.send_media_batch(
                    r.wa_contact_name or r.display_name,
                    paths,
                    phone=r.wa_phone,
                    caption=caption,
                )
            sent_set.add(it.unique_id)
            state.sent_ids.add(it.unique_id)  # legacy/global dedupe
            save_state(state)

    if wa:
        wa.stop()

    if not dry_run:
        state.last_run_ts = time.time()
        state.last_run_files = [str(p) for p in run_files]
        # Save a generic caption for the run (using the union of items).
        union_items = list(unique_needed.values())
        state.last_run_caption = _format_run_caption(cfg.message_prefix, union_items)
        save_state(state)
        print("Done: sent new items (no duplicates).")
    else:
        print("✅ Dry run complete: No messages sent, no state updated")


def main() -> None:
    cfg = load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--resend-last",
        action="store_true",
        help="Resend last run's files from state.json (test mode).",
    )
    ap.add_argument(
        "--max-files",
        type=int,
        default=0,
        help="Limit number of files sent (test mode).",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Ignore dedupe for current IG items (test mode).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate run without sending messages or updating state.",
    )
    args = ap.parse_args()

    if args.resend_last:
        resend_last(cfg=cfg, max_files=int(args.max_files or 0))
        return

    run_once(cfg=cfg, force_resend_current=bool(args.force), dry_run=bool(args.dry_run))


if __name__ == "__main__":
    main()
