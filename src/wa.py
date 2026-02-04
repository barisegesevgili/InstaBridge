from __future__ import annotations

import re
import platform
import subprocess
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


class WhatsAppSender:
    """
    Very small WhatsApp Web automation:
    - Uses a persistent browser profile, so you scan QR once.
    - Searches the contact by name and sends an image with caption.
    """

    def __init__(self, *, profile_dir: Path) -> None:
        self._profile_dir = profile_dir
        self._pw = None
        self._context = None
        self._page = None

    def start(self) -> None:
        self._pw = sync_playwright().start()
        self._profile_dir.mkdir(parents=True, exist_ok=True)

        def _launch():
            return self._pw.chromium.launch_persistent_context(
                user_data_dir=str(self._profile_dir),
                headless=False,
            )

        try:
            self._context = _launch()
        except Exception as e:  # noqa: BLE001 - retry for common stale-lock issue
            msg = str(e)
            # If the script previously crashed, Chromium can leave stale Singleton* files.
            if "ProcessSingleton" in msg or "SingletonLock" in msg:
                for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
                    p = self._profile_dir / name
                    try:
                        if p.exists():
                            p.unlink()
                    except Exception:
                        # Best-effort cleanup; we'll retry regardless.
                        pass
                self._context = _launch()
            else:
                raise
        self._page = self._context.new_page()
        self._page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded")
        self._wait_until_logged_in()

    def stop(self) -> None:
        try:
            if self._context is not None:
                self._context.close()
        finally:
            if self._pw is not None:
                self._pw.stop()
        self._pw = None
        self._context = None
        self._page = None

    def _wait_until_logged_in(self, timeout_s: int = 120) -> None:
        assert self._page is not None
        # Logged-in UI includes either:
        # - left-pane search box, or
        # - message composer in footer (if a chat is already open)
        deadline = time.time() + timeout_s
        last_error: Exception | None = None
        while time.time() < deadline:
            try:
                # If a chat is open, footer composer exists.
                if self._page.locator(
                    'footer div[role="textbox"][contenteditable="true"]'
                ).first.is_visible():
                    return
                _ = self._get_search_box()
                return
            except Exception as e:  # noqa: BLE001 - best-effort probing
                last_error = e
                time.sleep(1)
        raise TimeoutError("Timed out waiting for WhatsApp Web login") from last_error

    def _click_first(self, selectors: list[str], *, timeout_ms: int = 8_000) -> None:
        assert self._page is not None
        last_err: Exception | None = None
        for sel in selectors:
            try:
                loc = self._page.locator(sel).first
                loc.wait_for(state="visible", timeout=timeout_ms)
                try:
                    loc.scroll_into_view_if_needed(timeout=2_000)
                except Exception:
                    pass
                # Ensure clicks don't hang indefinitely.
                try:
                    loc.click(timeout=timeout_ms)
                except Exception:
                    loc.click(timeout=timeout_ms, force=True)
                return
            except Exception as e:  # noqa: BLE001
                last_err = e
                continue
        raise RuntimeError(f"Could not click any selector: {selectors}") from last_err

    def _click_send_in_preview(self) -> None:
        """
        Click the green bottom-right send button in the media preview screen.
        """
        assert self._page is not None
        self._click_first(
            [
                # Common in current WA builds (matches the screenshot)
                'div[role="button"][aria-label="Send"]',
                'div[role="button"][aria-label="Gönder"]',
                'div[aria-label="Send"]',
                'div[aria-label="Gönder"]',
                'button[aria-label="Send"]',
                'button[aria-label="Gönder"]',
                # Icon variants
                'div[role="button"]:has(span[data-icon="wds-ic-send-filled"])',
                'button:has(span[data-icon="wds-ic-send-filled"])',
                'span[data-icon="wds-ic-send-filled"]',
                'div[role="button"]:has(span[data-icon^="send"])',
                'button:has(span[data-icon^="send"])',
                'span[data-icon^="send"]',
            ],
            timeout_ms=30_000,
        )

    def _pick_media_file_input(self):
        """
        Pick the file input that corresponds to Photos/Videos (not Documents).
        WhatsApp often uses different inputs; we prefer one with an 'accept' that includes image/video.
        """
        assert self._page is not None
        candidates = [
            'input[type="file"][accept*="image"]',
            'input[type="file"][accept*="video"]',
            'input[type="file"][accept*="image"][multiple]',
            'input[type="file"][accept*="video"][multiple]',
            # Fallbacks
            'input[type="file"][multiple]',
            'input[type="file"]',
        ]
        for sel in candidates:
            loc = self._page.locator(sel).first
            try:
                if loc.count() > 0:
                    return loc
            except Exception:
                continue
        return self._page.locator('input[type="file"]').first

    def _upload_via_plus_photos_videos(self, files: list[Path]) -> None:
        """
        Forces the UI flow:
        Click '+' -> click 'Photos & Videos' -> set files.

        This tends to send as normal media (photos/videos) instead of any other attachment type.
        """
        assert self._page is not None
        if not files:
            return

        print(f"[wa] Uploading {len(files)} file(s) via menu...")
        # Click "+" (or attach icon) to open the attachment menu.
        self._click_first(
            [
                'button[aria-label="Attach"]',
                'button[title="Attach"]',
                'span[data-icon="plus"]',
                'span[data-icon="clip"]',
            ]
        )
        print("[wa] Attachment menu opened. Clicking Photos & videos...")

        labels = [
            # English
            "Photos & videos",
            "Photos and videos",
            # Turkish (common)
            "Fotoğraflar ve videolar",
            "Fotoğraflar ve Videolar",
        ]

        # WhatsApp renders the '+' popover with varying DOM. Prefer clicking by visible text
        # inside common menu containers.
        def _click_photos_videos_menu_item(timeout_ms: int = 5_000) -> None:
            assert self._page is not None
            last_err: Exception | None = None
            for lab in labels:
                # Prefer clicking the actual menu-row button (matches your screenshot).
                for sel in (
                    f'div[role="button"]:has-text("{lab}")',
                    f'button:has-text("{lab}")',
                    f'li:has-text("{lab}")',
                ):
                    try:
                        loc = self._page.locator(sel).first
                        loc.wait_for(state="visible", timeout=timeout_ms)
                        loc.click(timeout=timeout_ms)
                        return
                    except Exception as e:  # noqa: BLE001
                        last_err = e
                        continue

                # Fallback: locate the text, then click its closest role=button ancestor via JS.
                try:
                    text_loc = self._page.get_by_text(lab, exact=False).first
                    text_loc.wait_for(state="visible", timeout=timeout_ms)
                    handle = text_loc.evaluate_handle(
                        "el => el.closest('div[role=\"button\"],button,li')"
                    )
                    # elementHandle can be null if closest() fails
                    if handle:
                        self._page.evaluate("(el) => el && el.click()", handle)
                        return
                except Exception as e:  # noqa: BLE001
                    last_err = e
                    continue

            raise RuntimeError(
                "Could not click Photos & videos menu item"
            ) from last_err

        # On your WhatsApp build, "Photos & videos" opens a native macOS picker.
        # Element selectors can be flaky; keyboard navigation is more reliable:
        # menu order is typically: Document (1st), Photos & videos (2nd).
        if platform.system() == "Darwin" and len(files) == 1:
            try:
                # Ensure focus is on the popover menu.
                time.sleep(0.2)
                self._page.keyboard.press("ArrowDown")
                time.sleep(0.1)
                self._page.keyboard.press("Enter")
            except Exception:
                # Fall back to attempting a direct click if key navigation fails.
                try:
                    _click_photos_videos_menu_item(timeout_ms=2_500)
                except Exception:
                    pass

            print("[wa] Trying to select file via macOS picker automation...")
            if self._try_choose_file_in_macos_dialog(files[0]):
                print("[wa] File chosen via macOS picker automation.")
                return
            print(
                "[wa] macOS picker automation did not find a picker window. Falling back to DOM input."
            )
        else:
            # Click the menu row to match the UI (best-effort).
            try:
                _click_photos_videos_menu_item(timeout_ms=2_500)
            except Exception:
                pass

        # Give WhatsApp a moment to attach the correct input after menu click.
        time.sleep(0.6)

        # Pick the best hidden input for "Photos & videos" (and avoid the "New sticker" input).
        print("[wa] Selecting Photos/Videos input (anti-sticker)...")
        want_multiple = len(files) > 1
        best = self._page.eval_on_selector_all(
            'input[type="file"]',
            """
            (els, wantMultiple) => {
              let best = { score: -1e9, idx: 0, accept: "", meta: "" };
              const scored = [];
              els.forEach((el, i) => {
                const accept = (el.getAttribute('accept') || '').toLowerCase();
                const dt = (el.getAttribute('data-testid') || '').toLowerCase();
                const id = (el.id || '').toLowerCase();
                const cls = (el.className || '').toString().toLowerCase();
                const name = (el.getAttribute('name') || '').toLowerCase();
                const meta = [accept, dt, id, cls, name].join(' ');

                let score = 0;
                if (accept.includes('image') || accept.includes('video')) score += 50;
                if (accept.includes('video')) score += 40;  // prefer real media input over sticker-like image-only
                if (accept.includes('jpeg') || accept.includes('png') || accept.includes('mp4')) score += 10;
                if (el.hasAttribute('multiple')) score += 8;
                if (wantMultiple && el.hasAttribute('multiple')) score += 8;
                if (wantMultiple && !el.hasAttribute('multiple')) score -= 3;

                // Strongly avoid sticker-related inputs
                if (meta.includes('sticker')) score -= 200;
                // Avoid "document" style inputs that take anything
                if (accept.includes('*/*') || accept.trim() === '') score -= 20;

                if (score > best.score) best = { score, idx: i, accept, meta };
                scored.push({ i, score, accept, meta });
              });
              scored.sort((a,b) => b.score - a.score);
              return { count: els.length, best, top: scored.slice(0, 8) };
            }
            """,
            want_multiple,
        )
        try:
            idx = int(best.get("best", {}).get("idx", 0))
        except Exception:
            idx = 0
        try:
            top = best.get("top", [])
        except Exception:
            top = []
        print(f"[wa] file inputs found: {best.get('count')}")
        for entry in top:
            try:
                print(
                    f"[wa] input-candidate idx={entry.get('i')} score={entry.get('score')} accept={entry.get('accept')}"
                )
            except Exception:
                pass

        print(
            f"[wa] Chosen file input idx={idx} accept={best.get('best', {}).get('accept','')}"
        )

        file_input = self._page.locator('input[type="file"]').nth(idx)
        file_input.set_input_files(
            [str(p) for p in files] if want_multiple else str(files[0])
        )
        print("[wa] Files set on photos/videos input.")

    def _try_choose_file_in_macos_dialog(self, file_path: Path) -> bool:
        """
        Attempt to select a file in the native macOS file picker.
        Returns True if the AppleScript ran successfully.

        Notes:
        - Requires Accessibility permissions for "System Events" control.
        - Works best when the file picker is the frontmost window.
        """
        try:
            folder = str(file_path.parent.resolve())
            name = file_path.name
        except Exception:
            return False

        # IMPORTANT: We must target the *file picker sheet*; otherwise keystrokes
        # can go to Chrome (e.g. opening Find-in-page, as you saw).
        script = r"""
on run argv
    set folderPath to item 1 of argv
    set fileName to item 2 of argv
    set procNames to {"Google Chrome for Testing", "Chromium", "Google Chrome"}

    tell application "System Events"
        repeat with pName in procNames
            if exists process pName then
                tell process pName
                    set frontmost to true
                    repeat 80 times
                        repeat with w in windows
                            if exists sheet 1 of w then
                                set s to sheet 1 of w
                                try
                                    perform action "AXRaise" of s
                                end try
                                delay 0.1
                                -- Go to folder
                                keystroke "G" using {command down, shift down}
                                delay 0.25
                                keystroke folderPath
                                delay 0.1
                                key code 36
                                delay 0.25
                                -- Type filename and confirm
                                keystroke fileName
                                delay 0.15
                                key code 36
                                delay 0.15
                                -- Press default button (Open)
                                key code 36
                                return "ok"
                            end if

                            -- Some builds show the picker as a dialog window, not a sheet.
                            try
                                set sr to subrole of w
                            on error
                                set sr to ""
                            end try
                            if sr is "AXDialog" or sr is "AXSystemDialog" then
                                try
                                    perform action "AXRaise" of w
                                end try
                                delay 0.1
                                keystroke "G" using {command down, shift down}
                                delay 0.25
                                keystroke folderPath
                                delay 0.1
                                key code 36
                                delay 0.25
                                keystroke fileName
                                delay 0.15
                                key code 36
                                delay 0.15
                                key code 36
                                return "ok"
                            end if
                        end repeat
                        delay 0.1
                    end repeat
                end tell
            end if
        end repeat
    end tell
    return "no_sheet"
end run
"""
        try:
            cp = subprocess.run(
                ["osascript", "-e", script, folder, name],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            out = (cp.stdout or "").strip()
            return out == "ok"
        except Exception:
            return False

    def _get_search_box(self):
        """
        Returns a locator for the left-pane search input.
        WhatsApp changes DOM frequently and labels can be localized.
        """
        assert self._page is not None
        # Try known-ish aria-labels (localized UIs) before generic contenteditable matches.
        candidates = [
            'div[role="textbox"][contenteditable="true"][aria-label*="Search"]',
            'div[role="textbox"][contenteditable="true"][aria-label*="Ara"]',
            'div[role="textbox"][contenteditable="true"][title*="Search"]',
            'div[role="textbox"][contenteditable="true"][title*="Ara"]',
            # Fallbacks (less safe; might match other textboxes)
            'div[role="textbox"][contenteditable="true"][data-tab]',
            'div[role="textbox"][contenteditable="true"]',
        ]
        for sel in candidates:
            loc = self._page.locator(sel).first
            try:
                loc.wait_for(timeout=5_000)
                return loc
            except PlaywrightTimeoutError:
                continue
        raise PlaywrightTimeoutError("Could not locate search box")

    def open_chat(self, *, contact_name: str, phone: str = "") -> None:
        """
        Prefer opening by phone number (most reliable). Falls back to searching by contact_name.
        """
        assert self._page is not None
        phone = re.sub(r"\D+", "", phone or "")
        if phone:
            # Deep link opens the chat directly; avoids search box flakiness.
            self._page.goto(
                f"https://web.whatsapp.com/send?phone={phone}",
                wait_until="domcontentloaded",
            )
            # Wait until message composer exists (footer text box)
            self._page.wait_for_selector(
                'footer div[role="textbox"][contenteditable="true"]', timeout=30_000
            )
            return

        self._open_chat(contact_name)

    def send_text(self, contact_name: str, text: str, *, phone: str = "") -> None:
        assert self._page is not None
        self.open_chat(contact_name=contact_name, phone=phone)
        composer = self._page.locator(
            'footer div[role="textbox"][contenteditable="true"]'
        ).first
        composer.wait_for(state="visible", timeout=30_000)
        composer.click()
        composer.type(text, delay=2)
        self._page.keyboard.press("Enter")
        time.sleep(1)

    def _open_chat(self, contact_name: str) -> None:
        assert self._page is not None
        search = self._get_search_box()
        search.click()
        # Clear by select-all + delete (Mac uses Meta).
        select_all = "Meta+A" if platform.system() == "Darwin" else "Control+A"
        search.press(select_all)
        search.press("Backspace")
        search.type(contact_name, delay=20)
        search.press("Enter")

        # Click first matching chat in results
        # This selector is intentionally broad; WhatsApp DOM changes frequently.
        try:
            result = self._page.locator(f'span[title="{contact_name}"]').first
            result.wait_for(timeout=8_000)
            result.click()
        except PlaywrightTimeoutError:
            # If Enter opened the chat directly, we can continue.
            pass

    def send_media(
        self, contact_name: str, media_path: Path, *, phone: str = "", caption: str = ""
    ) -> None:
        assert self._page is not None
        print(f"[wa] Opening chat (phone={'yes' if phone else 'no'})...")
        self.open_chat(contact_name=contact_name, phone=phone)
        print("[wa] Chat opened. Uploading via + -> Photos & Videos...")
        self._upload_via_plus_photos_videos([media_path])
        print("[wa] File selected. Adding caption (if any)...")

        # Optional caption box before sending
        if caption:
            try:
                # Caption box lives in the media preview dialog; avoid grabbing the left search box.
                dialog = self._page.locator('div[role="dialog"]').first
                caption_box = dialog.locator(
                    'div[role="textbox"][contenteditable="true"]'
                ).last
                caption_box.wait_for(timeout=15_000)
                caption_box.click()
                caption_box.type(caption, delay=5)
            except PlaywrightTimeoutError:
                # Caption selector changes; if we fail, still try sending the media.
                pass
        print("[wa] Clicking send...")

        try:
            self._click_send_in_preview()
        except Exception:
            # Fallback: in some WhatsApp builds the send button is hard to select,
            # but Enter triggers send in the preview.
            try:
                self._page.keyboard.press("Enter")
                time.sleep(1)
            except Exception:
                raise
        print("[wa] Send clicked. Waiting for upload...")

        # Give WhatsApp time to upload before closing context.
        time.sleep(8)
        print("[wa] Done.")

    def send_media_batch(
        self,
        contact_name: str,
        media_paths: list[Path],
        *,
        phone: str = "",
        caption: str = "",
    ) -> None:
        """
        Best-effort "one go" sending:
        - If WhatsApp's file input supports multi-select, uploads all at once.
        - Otherwise, opens the chat once and sends files sequentially (still one run).
        """
        if not media_paths:
            return
        if len(media_paths) == 1:
            self.send_media(contact_name, media_paths[0], phone=phone, caption=caption)
            return

        assert self._page is not None
        print(f"[wa] Opening chat for batch (count={len(media_paths)})...")
        self.open_chat(contact_name=contact_name, phone=phone)
        print("[wa] Chat opened. Checking for multi-select upload...")

        # Try multi-select via '+' -> 'Photos & Videos' and detect a multiple input.
        try:
            multi_input = self._page.locator(
                'input[type="file"][multiple][accept*="image"], input[type="file"][multiple][accept*="video"]'
            ).first
            if multi_input.count() > 0:
                print("[wa] Multi-select input found. Uploading all at once...")
                self._upload_via_plus_photos_videos(media_paths)
                if caption:
                    try:
                        dialog = self._page.locator('div[role="dialog"]').first
                        caption_box = dialog.locator(
                            'div[role="textbox"][contenteditable="true"]'
                        ).last
                        caption_box.wait_for(timeout=15_000)
                        caption_box.click()
                        caption_box.type(caption, delay=5)
                    except PlaywrightTimeoutError:
                        pass
                # Send
                try:
                    self._click_first(
                        [
                            'div[role="dialog"] div[aria-label="Send"]',
                            'div[role="dialog"] div[aria-label="Gönder"]',
                            'div[aria-label="Send"]',
                            'div[aria-label="Gönder"]',
                            'div[role="dialog"] button:has(span[data-icon="wds-ic-send-filled"])',
                            'div[role="dialog"] div[role="button"]:has(span[data-icon="wds-ic-send-filled"])',
                            'button:has(span[data-icon="wds-ic-send-filled"])',
                            'span[data-icon="wds-ic-send-filled"]',
                            'div[role="dialog"] button:has(span[data-icon^="send"])',
                            'div[role="dialog"] div[role="button"]:has(span[data-icon^="send"])',
                            'button:has(span[data-icon^="send"])',
                            'span[data-icon^="send"]',
                        ],
                        timeout_ms=8_000,
                    )
                except Exception:
                    self._page.keyboard.press("Enter")
                    time.sleep(1)
                time.sleep(12)
                print("[wa] Batch send done.")
                return
        except Exception:
            pass

        # Fallback: sequential sends, but keep the same chat open.
        print("[wa] Multi-select not available. Sending sequentially in same chat...")
        for idx, p in enumerate(media_paths, start=1):
            print(f"[wa] Sending {idx}/{len(media_paths)}: {p.name}")
            try:
                self._send_in_open_chat(p, caption=caption if idx == 1 else "")
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                if (
                    "TargetClosedError" in msg
                    or "Target page" in msg
                    or "has been closed" in msg
                ):
                    # Best-effort recovery: restart WhatsApp context once and retry this file.
                    print(
                        "[wa] Page closed unexpectedly. Restarting WhatsApp Web and retrying this file..."
                    )
                    try:
                        self.stop()
                    except Exception:
                        pass
                    self.start()
                    self.open_chat(contact_name=contact_name, phone=phone)
                    self._send_in_open_chat(p, caption=caption if idx == 1 else "")
                else:
                    raise RuntimeError(
                        f"Failed while sending {p.name} ({idx}/{len(media_paths)}): {e}"
                    ) from e
            time.sleep(2)
            print(f"[wa] Sent {idx}/{len(media_paths)}")
        print("[wa] Sequential batch done.")

    def _send_in_open_chat(self, media_path: Path, *, caption: str = "") -> None:
        """
        Assumes a chat is already open.
        """
        assert self._page is not None
        self._upload_via_plus_photos_videos([media_path])

        if caption:
            try:
                dialog = self._page.locator('div[role="dialog"]').first
                caption_box = dialog.locator(
                    'div[role="textbox"][contenteditable="true"]'
                ).last
                caption_box.wait_for(timeout=15_000)
                caption_box.click()
                caption_box.type(caption, delay=5)
            except PlaywrightTimeoutError:
                pass

        # Send using preview-send button (more stable in current UI).
        try:
            self._click_send_in_preview()
        except Exception:
            # If clicking fails, try Enter (only if page is still alive).
            self._page.keyboard.press("Enter")
            time.sleep(1)
        time.sleep(6)
