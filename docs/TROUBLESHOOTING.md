# Troubleshooting Guide

Common issues and solutions for InstaToWhatsapp.

## Instagram Issues

### Login Failures

#### "Challenge Required"

**Symptoms:**
```
Exception: Challenge required
```

**Causes:**
- Instagram detected unusual activity
- New device/location
- Multiple login attempts

**Solutions:**
1. Open Instagram mobile app
2. Complete verification (email/SMS)
3. Wait 15-30 minutes
4. Delete `ig_session.json`
5. Try again with longer delays

#### "Bad Password"

**Symptoms:**
```
Exception: Bad password
```

**Solutions:**
- Verify credentials in `.env`
- Check for trailing spaces
- Try logging in via browser first
- Reset password if needed

#### "Rate Limited"

**Symptoms:**
```
Exception: Rate limit exceeded
Please wait a few minutes
```

**Solutions:**
1. Stop all automation immediately
2. Wait 1-2 hours minimum
3. Reduce frequency of requests
4. Use less active account

### Content Fetching Issues

#### "No New Items Found"

**Possible Causes:**
- No new posts/stories since last run
- `state.json` already tracking latest
- 24-hour cutoff filtering out content

**Debug:**
```bash
# Check state
cat state.json | jq .last_run_ts

# Force resend to test
python -m src.main --force
```

#### "Download Failed"

**Symptoms:**
```
Exception during download
```

**Solutions:**
- Check internet connection
- Verify `media/` folder writable
- Try different media format
- Clear `media/` folder if full

## WhatsApp Issues

### QR Code Problems

#### "QR Code Not Appearing"

**Solutions:**
1. Check browser window opened
2. Verify Playwright installed: `playwright --version`
3. Delete `wa_profile/` and retry
4. Check firewall/antivirus not blocking

#### "QR Code Expired"

**Symptoms:**
```
Timeout waiting for login
```

**Solutions:**
- Scan faster (< 60 seconds)
- Keep WhatsApp app open during scan
- Ensure phone has internet
- Try again immediately

### Contact/Chat Issues

#### "Contact Not Found"

**Symptoms:**
```
Could not locate search box
Could not click any selector
```

**Solutions:**

1. **Use phone number instead of name:**
```env
WA_CONTENT_PHONE=491701234567  # ✓ Recommended
WA_CONTENT_CONTACT_NAME=       # Leave empty
```

2. **Verify contact name exact match:**
```env
WA_CONTENT_CONTACT_NAME=John Doe  # Must match WhatsApp exactly
```

3. **Check contact exists in WhatsApp Web**

#### "Wrong Chat Opened"

**Causes:**
- Multiple contacts with similar names
- Contact name fuzzy match

**Solution:**
Use phone number for 100% accuracy.

### Upload/Send Issues

#### "File Upload Failed"

**Symptoms:**
```
Could not click Photos & videos
File input not found
```

**Solutions:**

**macOS:**
1. Grant Accessibility permissions:
   - System Settings → Privacy & Security
   - Accessibility → Add Terminal/Cursor

2. If persists, disable AppleScript:
   Edit `src/wa.py`, set platform check to skip macOS path

**Windows/Linux:**
- Usually works via DOM input
- Check browser console for errors

#### "Send Button Not Found"

**Causes:**
- WhatsApp Web UI changed
- Preview dialog not loaded
- Localization mismatch

**Solutions:**
1. Check browser for manual errors
2. Update selectors in `wa.py`:
```python
# Add your language's label
'div[aria-label="Send"]',
'div[aria-label="Your Language Send Text"]',
```

3. Use Enter key fallback (already implemented)

### Session Issues

#### "Profile Lock Error"

**Symptoms:**
```
ProcessSingleton
SingletonLock
```

**Cause:**
Previous crash left lock file

**Solution:**
Automatic cleanup in code. If persists:
```bash
rm -rf wa_profile/SingletonLock
rm -rf wa_profile/SingletonCookie
rm -rf wa_profile/SingletonSocket
```

## Configuration Issues

### Missing Variables

**Symptoms:**
```
Missing required env vars: IG_USERNAME
```

**Solutions:**
1. Verify `.env` exists
2. Check file encoding (UTF-8)
3. No spaces around `=`:
```env
IG_USERNAME=test123     # ✓ Correct
IG_USERNAME = test123   # ✗ Wrong
```

### Invalid Settings JSON

**Symptoms:**
```
JSONDecodeError
```

**Solutions:**
1. Validate JSON: https://jsonlint.com
2. Check trailing commas
3. Regenerate via Web UI

## Performance Issues

### Slow Execution

**Possible Causes:**
- Rate limiting delays (intentional)
- Network latency
- Large media files

**Normal Timings:**
- Instagram login: 2-5 seconds
- WhatsApp start: 5-10 seconds
- Media download: 1-3 seconds per item
- Send: 5-10 seconds per item

**Optimization:**
```bash
# Reduce max files for testing
python -m src.main --max-files 2
```

### High Memory Usage

**Cause:**
Playwright browser process

**Solutions:**
- Increase system RAM
- Close other browsers
- Use headless mode (future feature)

## Platform-Specific Issues

### macOS

#### "Accessibility Permission Denied"

**Solution:**
System Settings → Privacy & Security → Accessibility → Add Terminal

#### "File Picker Automation Fails"

**Fallback:**
DOM input automatically used if AppleScript fails

### Windows

#### "Playwright Not Found"

**Solution:**
```cmd
python -m playwright install chromium
```

#### "Path Issues"

Use forward slashes even on Windows:
```python
Path("wa_profile")  # ✓ Works everywhere
```

### Linux

#### "Browser Dependencies Missing"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install libnss3 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
  libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

# Fedora
sudo dnf install nss atk at-spi2-atk cups-libs libdrm \
  libxkbcommon libXcomposite libXdamage libXrandr \
  mesa-libgbm alsa-lib
```

## Scheduler Issues

### "Scheduler Not Running"

**Debug:**
```bash
# Check if process running
ps aux | grep scheduler

# Check logs
tail -f logs/scheduler.out.log
```

### "Wrong Timezone"

**Solutions:**
1. Verify timezone name: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
2. Update in `settings.json` or Web UI
3. Restart scheduler

### "Schedule Not Updating"

**Cause:**
Settings cached in running process

**Solution:**
Scheduler auto-reloads every 60s. Just wait.

## Debugging Tips

### Enable Verbose Logging

```python
# Add to src/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check State Files

```bash
# View current state
cat state.json | jq .

# View settings
cat settings.json | jq .

# View cache stats
cat user_cache.json | jq 'to_entries | length'
```

### Manual Testing

```bash
# Test Instagram only
python -c "from src.ig import IgClient; from pathlib import Path; ig = IgClient(session_path=Path('ig_session.json')); ig.login('user', 'pass'); print(ig.get_latest_post_items())"

# Test WhatsApp only
python -c "from src.wa import WhatsAppSender; from pathlib import Path; wa = WhatsAppSender(profile_dir=Path('wa_profile')); wa.start(); input('Check browser...'); wa.stop()"
```

### Reset Everything

```bash
# Nuclear option - start fresh
rm -rf .venv/
rm -f ig_session.json state.json
rm -rf wa_profile/
rm -f user_cache.json follow_cache.json

# Reinstall
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Getting Help

### Before Opening Issue

1. Search existing issues
2. Check logs for errors
3. Test with minimal config
4. Try on different account

### What to Include

```markdown
**Environment:**
- OS: macOS 14.2
- Python: 3.13.0
- Dependencies: (from `pip list`)

**Config:**
- Recipients: 1
- Scheduler: enabled
- Custom settings: (if any)

**Error:**
(Full error message)

**Steps to Reproduce:**
1. Run `python -m src.main`
2. See error

**Expected:**
Should send to WhatsApp

**Actual:**
Error occurred
```

### Emergency Contacts

- GitHub Issues: https://github.com/yourusername/InstaToWhatsapp/issues
- Discussions: https://github.com/yourusername/InstaToWhatsapp/discussions

## Known Limitations

### Cannot Be Fixed

- Instagram rate limits (platform limitation)
- WhatsApp Web DOM changes (monitor and update)
- Account ban risk (use throwaway accounts)
- macOS file picker quirks (fallback implemented)

### Workarounds Available

- Contact not found → use phone number
- QR timeout → rescan faster
- Rate limited → wait longer between runs
- Profile lock → automatic cleanup

## FAQ

**Q: Can I use my main Instagram account?**
A: Not recommended. High ban risk.

**Q: How often can I run this?**
A: Max 1-2 times per hour. Daily recommended.

**Q: Why does it take so long?**
A: Intentional delays to avoid rate limits.

**Q: Can I run multiple instances?**
A: No. Profile conflicts and increased ban risk.

**Q: Is there a way to avoid QR scan?**
A: Yes - session persists in `wa_profile/`

**Q: Can I send to groups?**
A: Yes - use group name or phone in config
