# Quick Start Guide

Get InstaBridge running in 5 minutes.

**🌉 InstaBridge** - The free, open-source alternative to $50-500/month commercial tools.

## ⚠️ Important First

**This tool uses unofficial APIs (ToS violation). Risk is lower for personal archival at low frequency; see [Risk by use case](docs/RISK_BY_USE_CASE.md). Prefer throwaway accounts until you're comfortable.**

## Step 1: Setup (2 minutes)

```bash
# Clone the repository
git clone https://github.com/barisegesevgili/InstaBridge.git
cd InstaBridge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
make install
# Or manually: pip install -r requirements.txt && python -m playwright install chromium
```

## Step 2: Configure (1 minute)

```bash
# Copy example config
cp .env.example .env

# Edit .env with your credentials
# (Use throwaway Instagram account!)
nano .env  # or your preferred editor
```

Minimum required:
```env
IG_USERNAME=your_test_account
IG_PASSWORD=your_password
WA_CONTENT_CONTACT_NAME=Friend Name
WA_CONTENT_PHONE=491701234567  # International format, digits only
```

## Step 3: First Run (2 minutes)

```bash
# Run once
make run
# Or: python -m src.main

# What happens:
# 1. Logs into Instagram
# 2. Opens WhatsApp Web (scan QR if first time)
# 3. Checks for new posts/stories
# 4. Sends to WhatsApp if found
```

## Step 4: Verify

Check WhatsApp - you should see a message if there was new Instagram content.

## Next Steps

### Option A: Use Web UI

```bash
make webapp
# Open http://127.0.0.1:5000
```

- Configure multiple recipients
- View analytics
- Manage settings

### Option B: Schedule Automation

```bash
# Daily at 19:00 (keeps running)
make scheduler
```

### Option C: Manual Runs

```bash
# Test resend
python -m src.main --resend-last

# Force resend (ignore deduplication)
python -m src.main --force
```

## Troubleshooting

**Instagram login fails:**
- Verify credentials in `.env`
- Complete any verification in Instagram app
- Wait 15 minutes and retry

**WhatsApp QR expires:**
- Scan faster (within 60 seconds)
- Keep WhatsApp app open
- Delete `wa_profile/` and retry

**Contact not found:**
- Use phone number instead of name
- Format: digits only, international (e.g., 491701234567)

**More help:** See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Development

```bash
# Install dev dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Check code quality
make lint
```

## Full Documentation

- [README.md](README.md) - Complete overview
- [docs/SETUP.md](docs/SETUP.md) - Detailed setup
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - How it works
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute

## Support

- [Issues](https://github.com/yourusername/InstaToWhatsapp/issues) - Report bugs
- [Discussions](https://github.com/yourusername/InstaToWhatsapp/discussions) - Ask questions

Happy automating! 🚀
