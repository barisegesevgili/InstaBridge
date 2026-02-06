from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, render_template, request

from src.insights import (
    RateLimitedError,
    not_following_back_detailed,
    reset_warm_cache_state,
    warm_user_cache_step,
)
from src.main import load_config
from src.settings import (
    load_settings,
    save_settings,
    settings_from_public_dict,
    settings_to_public_dict,
)

app = Flask(__name__, template_folder="templates")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/settings")
def settings_page():
    return render_template("settings.html")


# Legacy HTML strings removed - now using template files
# Templates are in src/templates/
_LEGACY_INDEX_HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>InstaToWhatsapp — Reports</title>
    <style>
      body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; margin: 24px; }
      .card { max-width: 720px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; }
      button { padding: 10px 12px; border-radius: 10px; border: 1px solid #111827; background: #111827; color: white; cursor: pointer; }
      button:disabled { opacity: 0.6; cursor: not-allowed; }
      .muted { color: #6b7280; font-size: 14px; }
      .row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px; }
      label { font-size: 13px; color: #374151; display: flex; flex-direction: column; gap: 6px; }
      input, select { padding: 8px 10px; border-radius: 10px; border: 1px solid #d1d5db; min-width: 140px; }
      .chk { flex-direction: row; align-items: center; }
      ul { margin-top: 12px; }
      li { padding: 4px 0; }
      code { background: #f3f4f6; padding: 2px 6px; border-radius: 6px; }
      .err { color: #b91c1c; white-space: pre-wrap; }
    </style>
  </head>
  <body>
    <div class="card">
      <div class="row" style="justify-content: space-between; align-items: center; margin-top: 0;">
        <div class="muted"><b>Reports</b></div>
        <div class="muted"><a href="/settings">Settings</a></div>
      </div>
      <h2>Not following you back</h2>
      <p class="muted">Filters require fetching account stats; first run can take a bit. Results are cached in <code>user_cache.json</code>.</p>

      <div class="row">
        <label>Min followers
          <input id="minFollowers" type="number" placeholder="e.g. 0" />
        </label>
        <label>Max followers
          <input id="maxFollowers" type="number" placeholder="e.g. 5000" />
        </label>
        <label>Username contains
          <input id="q" type="text" placeholder="e.g. music" />
        </label>
        <label>Sort by
          <select id="sortBy">
            <option value="followers" selected>followers</option>
            <option value="username">username</option>
          </select>
        </label>
        <label>Sort dir
          <select id="sortDir">
            <option value="desc" selected>desc</option>
            <option value="asc">asc</option>
          </select>
        </label>
        <label>Max profiles to inspect
          <input id="maxProfiles" type="number" value="200" />
        </label>
        <label>Offset
          <input id="offset" type="number" value="0" />
        </label>
        <label>Limit
          <input id="limit" type="number" value="50" />
        </label>
        <label>Max new stats to fetch
          <input id="maxFetch" type="number" value="25" />
        </label>
        <label class="chk">
          <input id="cacheOnly" type="checkbox" checked />
          cache-only (fast)
        </label>
        <label class="chk">
          <input id="refreshFollow" type="checkbox" />
          refresh follow lists (slow)
        </label>
        <label class="chk">
          <input id="includePrivate" type="checkbox" checked />
          include private
        </label>
        <label class="chk">
          <input id="includeVerified" type="checkbox" checked />
          include verified
        </label>
      </div>

      <button id="btn" onclick="run()" style="margin-top: 12px;">Fetch list</button>
      <div class="row" style="align-items: center;">
        <button id="warmBtn" onclick="warm()" style="margin-top: 12px; background: #0f766e; border-color: #0f766e;">Warm cache (show progress)</button>
        <button id="warmResetBtn" onclick="warmReset()" style="margin-top: 12px; background: white; color: #111827;">Reset progress</button>
      </div>
      <div style="margin-top: 10px;">
        <div class="muted">Warm progress (100% = stats fetched/checked for all not-following-back users)</div>
        <progress id="warmProg" value="0" max="100" style="width: 100%; height: 16px;"></progress>
        <div id="warmText" class="muted" style="margin-top: 6px;"></div>
      </div>
      <div id="status" class="muted" style="margin-top: 12px;"></div>
      <div id="error" class="err" style="margin-top: 12px;"></div>
      <ul id="list"></ul>
    </div>

    <script>
      async function run() {
        const btn = document.getElementById('btn');
        const status = document.getElementById('status');
        const error = document.getElementById('error');
        const list = document.getElementById('list');
        const minFollowers = document.getElementById('minFollowers').value;
        const maxFollowers = document.getElementById('maxFollowers').value;
        const q = document.getElementById('q').value;
        const sortBy = document.getElementById('sortBy').value;
        const sortDir = document.getElementById('sortDir').value;
        const maxProfiles = document.getElementById('maxProfiles').value;
        const offset = document.getElementById('offset').value;
        const limit = document.getElementById('limit').value;
        const maxFetch = document.getElementById('maxFetch').value;
        const cacheOnly = document.getElementById('cacheOnly').checked;
        const refreshFollow = document.getElementById('refreshFollow').checked;
        const includePrivate = document.getElementById('includePrivate').checked;
        const includeVerified = document.getElementById('includeVerified').checked;

        error.textContent = "";
        list.innerHTML = "";
        btn.disabled = true;
        status.textContent = "Fetching…";
        try {
          const params = new URLSearchParams();
          if (minFollowers) params.set('min_followers', minFollowers);
          if (maxFollowers) params.set('max_followers', maxFollowers);
          if (q) params.set('q', q);
          params.set('sort_by', sortBy);
          params.set('sort_dir', sortDir);
          if (maxProfiles) params.set('max_profiles', maxProfiles);
          if (offset) params.set('offset', offset);
          if (limit) params.set('limit', limit);
          if (maxFetch) params.set('max_fetch_missing', maxFetch);
          params.set('cache_only', cacheOnly ? '1' : '0');
          params.set('refresh_follow_cache', refreshFollow ? '1' : '0');
          params.set('include_private', includePrivate ? '1' : '0');
          params.set('include_verified', includeVerified ? '1' : '0');

          const res = await fetch('/api/not-following-back?' + params.toString());
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Request failed');
          status.textContent = `Found ${data.count} (this page).`;
          for (const u of data.users) {
            const li = document.createElement('li');
            const followers = (u.followers === null || u.followers === undefined) ? '?' : u.followers;
            const priv = u.is_private ? 'private' : 'public';
            const ver = u.is_verified ? ', verified' : '';
            li.textContent = `${u.username} — followers: ${followers} (${priv}${ver})`;
            list.appendChild(li);
          }
        } catch (e) {
          status.textContent = "";
          error.textContent = String(e);
        } finally {
          btn.disabled = false;
        }
      }

      async function warmReset() {
        const warmText = document.getElementById('warmText');
        const warmProg = document.getElementById('warmProg');
        warmText.textContent = "Resetting…";
        try {
          const res = await fetch('/api/warm-cache/reset', { method: 'POST' });
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Reset failed');
          warmProg.value = 0;
          warmText.textContent = "Reset done.";
        } catch (e) {
          warmText.textContent = String(e);
        }
      }

      async function warm() {
        const warmBtn = document.getElementById('warmBtn');
        const warmResetBtn = document.getElementById('warmResetBtn');
        const warmText = document.getElementById('warmText');
        const warmProg = document.getElementById('warmProg');
        const refreshFollow = document.getElementById('refreshFollow').checked;

        warmBtn.disabled = true;
        warmResetBtn.disabled = true;
        warmText.textContent = "Warming…";
        try {
          while (true) {
            const params = new URLSearchParams();
            params.set('chunk_size', '25');
            if (refreshFollow) params.set('refresh_follow_cache', '1');
            const res = await fetch('/api/warm-cache/step?' + params.toString());
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Warm step failed');

            if (data.rate_limited) {
              const s = data.retry_after_s || 600;
              warmText.textContent = `Instagram rate limited. Please wait ~${s}s, then click “Warm cache” again.`;
              break;
            }

            warmProg.value = data.percent || 0;
            warmText.textContent = `Progress: ${data.processed}/${data.total} (${data.percent}%). Newly fetched this step: ${data.newly_fetched}.`;

            if (data.done) break;
            // Let the UI repaint between steps.
            await new Promise(r => setTimeout(r, 50));
          }
          warmText.textContent += " Done.";
        } catch (e) {
          warmText.textContent = String(e);
        } finally {
          warmBtn.disabled = false;
          warmResetBtn.disabled = false;
        }
      }
    </script>
  </body>
</html>
"""

SETTINGS_HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>InstaToWhatsapp — Settings</title>
    <style>
      body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; margin: 24px; }
      .card { max-width: 920px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; }
      button { padding: 10px 12px; border-radius: 10px; border: 1px solid #111827; background: #111827; color: white; cursor: pointer; }
      button.secondary { background: white; color: #111827; }
      button:disabled { opacity: 0.6; cursor: not-allowed; }
      .muted { color: #6b7280; font-size: 14px; }
      .row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px; align-items: center; }
      label { font-size: 13px; color: #374151; display: flex; flex-direction: column; gap: 6px; }
      input, select { padding: 8px 10px; border-radius: 10px; border: 1px solid #d1d5db; min-width: 160px; }
      table { width: 100%; border-collapse: collapse; margin-top: 12px; }
      th, td { border-bottom: 1px solid #e5e7eb; padding: 8px; font-size: 13px; vertical-align: top; }
      th { text-align: left; color: #374151; }
      .chk { display: inline-flex; gap: 8px; align-items: center; }
      .err { color: #b91c1c; white-space: pre-wrap; }
      code { background: #f3f4f6; padding: 2px 6px; border-radius: 6px; }
      a { color: #0f766e; text-decoration: none; }
      a:hover { text-decoration: underline; }
    </style>
  </head>
  <body>
    <div class="card">
      <div class="row" style="justify-content: space-between; align-items: center; margin-top: 0;">
        <div class="muted"><a href="/">Reports</a></div>
        <div class="muted"><b>Settings</b></div>
      </div>

      <h2>Content sharing settings</h2>
      <p class="muted">
        This page edits <code>settings.json</code>. Your scheduler reads it automatically.
      </p>

      <h3>Schedule</h3>
      <div class="row">
        <label class="chk"><input id="schedEnabled" type="checkbox" /> enable scheduler</label>
        <label>Timezone
          <input id="schedTz" type="text" value="Europe/Berlin" />
        </label>
        <label>Daily time
          <input id="schedTime" type="time" value="19:00" />
        </label>
        <div class="muted" id="nextRun"></div>
      </div>

      <h3>Friends (WhatsApp recipients)</h3>
      <p class="muted">
        Tip: <b>Phone</b> is most reliable (WhatsApp Web deep link). Use international format digits only.
      </p>

      <div class="row">
        <button class="secondary" onclick="addRecipient()">Add friend</button>
        <button onclick="save()">Save</button>
        <div id="status" class="muted"></div>
        <div id="error" class="err"></div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Enabled</th>
            <th>Display name</th>
            <th>WhatsApp contact name (optional)</th>
            <th>Phone (recommended)</th>
            <th>Share posts</th>
            <th>Share stories</th>
            <th>Close friends stories</th>
            <th></th>
          </tr>
        </thead>
        <tbody id="recTable"></tbody>
      </table>
    </div>

    <script>
      let settings = null;

      function uid() {
        if (crypto && crypto.randomUUID) return crypto.randomUUID();
        return 'id_' + Math.random().toString(16).slice(2);
      }

      function render() {
        document.getElementById('error').textContent = '';
        document.getElementById('status').textContent = '';
        document.getElementById('schedEnabled').checked = !!(settings.schedule && settings.schedule.enabled);
        document.getElementById('schedTz').value = (settings.schedule && settings.schedule.tz) || 'Europe/Berlin';
        document.getElementById('schedTime').value = (settings.schedule && settings.schedule.time_hhmm) || '19:00';

        const tbody = document.getElementById('recTable');
        tbody.innerHTML = '';
        for (const r of (settings.recipients || [])) {
          const tr = document.createElement('tr');
          tr.dataset.id = r.id;
          tr.innerHTML = `
            <td><input type="checkbox" class="r_enabled" ${r.enabled ? 'checked' : ''} /></td>
            <td><input type="text" class="r_display_name" value="${(r.display_name||'').replaceAll('"','&quot;')}" /></td>
            <td><input type="text" class="r_wa_contact_name" value="${(r.wa_contact_name||'').replaceAll('"','&quot;')}" /></td>
            <td><input type="text" class="r_wa_phone" value="${(r.wa_phone||'').replaceAll('"','&quot;')}" placeholder="e.g. 491701234567" /></td>
            <td><input type="checkbox" class="r_send_posts" ${r.send_posts ? 'checked' : ''} /></td>
            <td><input type="checkbox" class="r_send_stories" ${r.send_stories ? 'checked' : ''} /></td>
            <td><input type="checkbox" class="r_send_close" ${r.send_close_friends_stories ? 'checked' : ''} /></td>
            <td><button class="secondary" onclick="removeRecipient('${r.id}')">Remove</button></td>
          `;
          tbody.appendChild(tr);
        }
      }

      function addRecipient() {
        settings.recipients = settings.recipients || [];
        settings.recipients.push({
          id: uid(),
          display_name: 'Friend',
          wa_contact_name: '',
          wa_phone: '',
          enabled: true,
          send_posts: true,
          send_stories: true,
          send_close_friends_stories: false
        });
        render();
      }

      function removeRecipient(id) {
        settings.recipients = (settings.recipients || []).filter(r => r.id !== id);
        render();
      }

      function collectFromUI() {
        settings.schedule = settings.schedule || {};
        settings.schedule.enabled = document.getElementById('schedEnabled').checked;
        settings.schedule.tz = document.getElementById('schedTz').value;
        settings.schedule.time_hhmm = document.getElementById('schedTime').value;

        const rows = document.querySelectorAll('#recTable tr');
        const out = [];
        for (const tr of rows) {
          const id = tr.dataset.id;
          out.push({
            id,
            display_name: tr.querySelector('.r_display_name').value,
            wa_contact_name: tr.querySelector('.r_wa_contact_name').value,
            wa_phone: tr.querySelector('.r_wa_phone').value,
            enabled: tr.querySelector('.r_enabled').checked,
            send_posts: tr.querySelector('.r_send_posts').checked,
            send_stories: tr.querySelector('.r_send_stories').checked,
            send_close_friends_stories: tr.querySelector('.r_send_close').checked
          });
        }
        settings.recipients = out;
      }

      async function refreshNextRun() {
        const el = document.getElementById('nextRun');
        try {
          const res = await fetch('/api/scheduler/next-run');
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'failed');
          el.textContent = data.enabled ? (`Next run: ${data.next_run}`) : 'Scheduler disabled';
        } catch (e) {
          el.textContent = '';
        }
      }

      async function save() {
        const status = document.getElementById('status');
        const error = document.getElementById('error');
        error.textContent = '';
        status.textContent = 'Saving…';
        try {
          collectFromUI();
          const res = await fetch('/api/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(settings)
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Save failed');
          settings = data.settings;
          status.textContent = 'Saved.';
          render();
          await refreshNextRun();
        } catch (e) {
          status.textContent = '';
          error.textContent = String(e);
        }
      }

      async function init() {
        const status = document.getElementById('status');
        status.textContent = 'Loading…';
        const res = await fetch('/api/settings');
        const data = await res.json();
        if (!res.ok) {
          status.textContent = '';
          document.getElementById('error').textContent = data.error || 'Failed to load settings';
          return;
        }
        settings = data.settings;
        status.textContent = '';
        render();
        await refreshNextRun();
      }

      init();
    </script>
  </body>
</html>
"""

# Routes are defined above (using render_template instead of render_template_string)


@app.get("/api/health")
def api_health():
    """
    Health check endpoint for monitoring and diagnostics.
    Returns system status and basic configuration info.
    """
    import os
    from pathlib import Path

    try:
        # Check required files exist
        checks = {
            "ig_session_writable": os.access(".", os.W_OK),
            "settings_file_exists": Path("settings.json").exists(),
            "state_file_exists": Path("state.json").exists(),
        }

        # Check environment variables
        env_vars = {
            "ig_username_set": bool(os.getenv("IG_USERNAME")),
            "ig_password_set": bool(os.getenv("IG_PASSWORD")),
            "wa_contact_set": bool(
                os.getenv("WA_CONTENT_CONTACT_NAME") or os.getenv("WA_CONTACT_NAME")
            ),
        }

        # Overall health
        all_checks_pass = all(checks.values()) and all(env_vars.values())

        return jsonify(
            {
                "status": "healthy" if all_checks_pass else "degraded",
                "checks": checks,
                "environment": env_vars,
                "version": "1.0.0",
            }
        ), (200 if all_checks_pass else 503)

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "version": "1.0.0",
                }
            ),
            500,
        )


@app.get("/api/settings")
def api_get_settings():
    try:
        cfg = load_config()
        st = load_settings(
            default_recipient_name=cfg.wa_content_contact_name,
            default_recipient_phone=cfg.wa_content_phone,
        )
        return jsonify({"settings": settings_to_public_dict(st)})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


@app.post("/api/settings")
def api_save_settings():
    try:
        data = request.get_json(force=True, silent=False)
        st = settings_from_public_dict(data if isinstance(data, dict) else {})
        save_settings(st)
        return jsonify({"ok": True, "settings": settings_to_public_dict(st)})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


@app.get("/api/scheduler/next-run")
def api_scheduler_next_run():
    """
    Computes next run time for each recipient based on settings.json.
    Returns per-recipient schedules.
    """
    try:
        from src.scheduler import next_daily_run

        cfg = load_config()
        st = load_settings(
            default_recipient_name=cfg.wa_content_contact_name,
            default_recipient_phone=cfg.wa_content_phone,
        )

        # Get enabled recipients
        enabled_recipients = [
            r
            for r in (st.recipients or [])
            if r.enabled and (r.wa_contact_name or r.wa_phone)
        ]

        def get_recipient_schedule(recipient, global_schedule):
            """Get effective schedule for a recipient."""
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

        recipient_schedules = []
        for recipient in enabled_recipients:
            enabled, tz_name, time_hhmm = get_recipient_schedule(recipient, st.schedule)
            try:
                tz = ZoneInfo(tz_name)
            except Exception:
                tz = ZoneInfo("Europe/Berlin")
                tz_name = "Europe/Berlin"

            if enabled:
                now = datetime.now(tz)
                nxt = next_daily_run(now, hhmm=time_hhmm)
                recipient_schedules.append(
                    {
                        "recipient_id": recipient.id,
                        "recipient_name": recipient.display_name,
                        "enabled": True,
                        "next_run": nxt.isoformat(),
                        "tz": tz_name,
                        "time": time_hhmm,
                    }
                )
            else:
                recipient_schedules.append(
                    {
                        "recipient_id": recipient.id,
                        "recipient_name": recipient.display_name,
                        "enabled": False,
                        "next_run": None,
                        "tz": tz_name,
                        "time": time_hhmm,
                    }
                )

        # Sort by next_run time
        recipient_schedules.sort(
            key=lambda x: (x["next_run"] or "9999-12-31", x["recipient_name"])
        )

        return jsonify(
            {
                "global_schedule": {
                    "enabled": st.schedule.enabled,
                    "tz": st.schedule.tz or "Europe/Berlin",
                    "time_hhmm": st.schedule.time_hhmm or "19:00",
                },
                "recipients": recipient_schedules,
            }
        )
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


@app.get("/api/not-following-back")
def api_not_following_back():
    try:

        def as_int(name: str):
            v = request.args.get(name, "").strip()
            return int(v) if v else None

        users = not_following_back_detailed(
            min_followers=as_int("min_followers"),
            max_followers=as_int("max_followers"),
            include_private=request.args.get("include_private", "1") != "0",
            include_verified=request.args.get("include_verified", "1") != "0",
            username_contains=request.args.get("q", ""),
            sort_by=request.args.get("sort_by", "followers"),
            sort_dir=request.args.get("sort_dir", "desc"),
            max_profiles=int(request.args.get("max_profiles", "200") or 200),
            offset=int(request.args.get("offset", "0") or 0),
            limit=int(request.args.get("limit", "50") or 50),
            cache_only=request.args.get("cache_only", "1") != "0",
            max_fetch_missing=int(request.args.get("max_fetch_missing", "25") or 25),
            refresh_follow_cache=request.args.get("refresh_follow_cache", "0") != "0",
        )
        return jsonify({"count": len(users), "users": users})
    except RateLimitedError as rl:
        return (
            jsonify(
                {
                    "error": str(rl),
                    "retry_after_s": int(getattr(rl, "retry_after_s", 600)),
                }
            ),
            429,
        )
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


@app.post("/api/warm-cache/reset")
def api_warm_cache_reset():
    try:
        reset_warm_cache_state()
        return jsonify({"ok": True})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


@app.get("/api/warm-cache/step")
def api_warm_cache_step():
    try:
        chunk_size = int(request.args.get("chunk_size", "25") or 25)
        refresh_follow_cache = request.args.get("refresh_follow_cache", "0") != "0"
        data = warm_user_cache_step(
            chunk_size=chunk_size, refresh_follow_cache=refresh_follow_cache
        )
        return jsonify(data)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500


def main() -> None:
    # Default Flask dev server
    app.run(host="127.0.0.1", port=5000, debug=True)


if __name__ == "__main__":
    main()
