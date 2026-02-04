# Detailed Setup Guide

Complete step-by-step instructions for setting up InstaBridge.

**🌉 InstaBridge** - Free, open-source, extensible Instagram automation.

## Prerequisites Checklist

- [ ] Python 3.13 or higher installed
- [ ] Git installed (optional but recommended)
- [ ] Instagram throwaway account created
- [ ] WhatsApp account with active phone number
- [ ] Terminal/command line access

## Step 1: Python Environment

### Verify Python Version

```bash
python3 --version
# Should show 3.13 or higher
```

### Create Virtual Environment

```bash
cd /path/to/your/projects
git clone https://github.com/barisegesevgili/InstaBridge.git
cd InstaBridge

python3 -m venv .venv
```

### Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```cmd
.venv\Scripts\activate
```

You should see `(.venv)` in your terminal prompt.

## Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed instagrapi-2.1.3 playwright-1.50.0 ...
```

### Install Playwright Browsers

```bash
python -m playwright install chromium
```

This downloads Chromium browser (~300MB).

## Step 3: Create Configuration

### Copy Example Config

```bash
cp .env.example .env
```

### Edit Configuration

Open `.env` in your text editor:

```bash
# Instagram credentials (THROWAWAY ACCOUNT ONLY!)
IG_USERNAME=your_test_account
IG_PASSWORD=your_secure_password

# WhatsApp content recipient
WA_CONTENT_CONTACT_NAME=Friend Name
WA_CONTENT_PHONE=491701234567

# WhatsApp report recipient
WA_REPORT_CONTACT_NAME=Notes
WA_REPORT_PHONE=

# Message prefix
MESSAGE_PREFIX=New from Instagram:
```

### Important Notes

**Phone Number Format:**
- Use international format
- Digits only (no + or spaces)
- Examples:
  - USA: 12025551234
  - UK: 447123456789
  - Germany: 491701234567

**Contact Names:**
- Must match exactly in WhatsApp
- Case-sensitive
- Phone number is more reliable

## Step 4: First Test Run

### Run Once

```bash
python -m src.main
```

### Expected Behavior

1. **Instagram Login:**
   ```
   Logging into Instagram...
   Instagram login OK.
   ```

2. **WhatsApp Web:**
   - Browser window opens
   - QR code appears (first time only)
   - Scan with your phone
   
   ```
   Opening WhatsApp Web (scan QR if asked)...
   WhatsApp Web ready.
   ```

3. **Content Check:**
   ```
   Done: nothing new to send.
   # OR
   Downloading post:123...
   Sending to Friend Name (1 item(s))...
   Done: sent new items.
   ```

### Common First-Run Issues

**"Missing required env vars"**
- Check `.env` file exists
- Verify all required fields filled
- No extra spaces around values

**"Instagram login failed"**
- Verify credentials correct
- Complete any Instagram challenges in app
- Wait 15 minutes and try again

**"WhatsApp QR timeout"**
- Scan faster (60 second timeout)
- Keep WhatsApp open during scan
- Try again: `python -m src.main`

## Step 5: Verify Setup

### Check Session Files

```bash
ls -la | grep json
```

You should see:
- `ig_session.json` - Instagram session
- `state.json` - Tracking state

### Check WhatsApp Profile

```bash
ls -la wa_profile/
```

Should contain browser profile files.

### Test Resend

```bash
python -m src.main --resend-last
```

Should resend last batch without re-downloading.

## Step 6: Configure Recipients (Optional)

### Create settings.json

```bash
cat > settings.json << 'EOF'
{
  "schedule": {
    "enabled": true,
    "tz": "Europe/Berlin",
    "time_hhmm": "19:00"
  },
  "recipients": [
    {
      "id": "friend1",
      "display_name": "Best Friend",
      "wa_phone": "491701234567",
      "enabled": true,
      "send_posts": true,
      "send_stories": true,
      "send_close_friends_stories": false
    }
  ]
}
EOF
```

### Or Use Web UI

```bash
python -m src.webapp
# Open http://127.0.0.1:5000/settings
```

## Step 7: Schedule Automation

### Daily Scheduler

Create a new terminal window:

```bash
cd InstaToWhatsapp
source .venv/bin/activate
python -m src.scheduler
```

**Output:**
```
[scheduler] Now: 2026-02-04T14:30:00+01:00 (Europe/Berlin)
[scheduler] Next run: 2026-02-04T19:00:00+01:00
[scheduler] Sleeping 60s
```

Leave this running.

### Weekly Unfollow Checker

Another terminal:

```bash
cd InstaToWhatsapp
source .venv/bin/activate
python -m src.unfollow_scheduler
```

### System Service (Advanced)

**macOS (launchd):**

Create `~/Library/LaunchAgents/com.instatowhatsapp.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.instatowhatsapp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOU/InstaToWhatsapp/.venv/bin/python</string>
        <string>-m</string>
        <string>src.scheduler</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOU/InstaToWhatsapp</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/instatowhatsapp.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/instatowhatsapp.err</string>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.instatowhatsapp.plist
```

**Linux (systemd):**

Create `/etc/systemd/system/instatowhatsapp.service`:

```ini
[Unit]
Description=InstaToWhatsapp Scheduler
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOU/InstaToWhatsapp
ExecStart=/home/YOU/InstaToWhatsapp/.venv/bin/python -m src.scheduler
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable instatowhatsapp
sudo systemctl start instatowhatsapp
```

## Step 8: Verify Everything Works

### Checklist

- [ ] Manual run completes without errors
- [ ] WhatsApp message received
- [ ] Resend test works
- [ ] Web UI accessible at http://127.0.0.1:5000
- [ ] Scheduler shows correct next run time
- [ ] Session files created

### Test Each Component

```bash
# Test Instagram
python -c "from src.ig import IgClient; from pathlib import Path; from src.main import load_config; cfg = load_config(); ig = IgClient(session_path=Path('ig_session.json')); ig.login(cfg.ig_username, cfg.ig_password); print('✓ Instagram OK')"

# Test WhatsApp (opens browser)
python -c "from src.wa import WhatsAppSender; from pathlib import Path; wa = WhatsAppSender(profile_dir=Path('wa_profile')); wa.start(); print('✓ WhatsApp OK'); wa.stop()"

# Test settings
python -c "from src.settings import load_settings; s = load_settings(); print(f'✓ Settings OK: {len(s.recipients)} recipients')"
```

## Troubleshooting Setup Issues

### Python Version Too Old

**Error:** `SyntaxError` or `ModuleNotFoundError`

**Solution:**
```bash
# macOS
brew install python@3.13

# Ubuntu
sudo apt install python3.13

# Windows - download from python.org
```

### Playwright Install Fails

**Error:** `playwright install` fails

**Solution:**
```bash
# Install system dependencies (Linux)
sudo apt install libnss3 libatk1.0-0 libatk-bridge2.0-0

# Or use system browser (not recommended)
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
```

### .env Not Found

**Error:** `Missing required env vars`

**Solution:**
```bash
# Verify file exists
ls -la .env

# Check permissions
chmod 644 .env

# Verify content
cat .env
```

### Instagram Challenge

**Error:** `Challenge required`

**Solution:**
1. Open Instagram app on phone
2. Complete verification
3. Wait 15-30 minutes
4. Try again

### WhatsApp QR Expired

**Error:** `QR code expired`

**Solution:**
1. Delete `wa_profile/` folder
2. Run again: `python -m src.main`
3. Scan QR faster (within 60 seconds)

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand design
- Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Check [ROADMAP.md](ROADMAP.md) for future features
- Contribute via [CONTRIBUTING.md](../CONTRIBUTING.md)

## Getting Help

If setup fails:

1. Check logs for error messages
2. Search GitHub Issues
3. Create new issue with:
   - OS and Python version
   - Full error message
   - Steps to reproduce

Happy automating! 🚀
