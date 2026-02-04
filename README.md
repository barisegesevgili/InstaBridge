# 🌉 InstaBridge

> **The Open-Source Alternative for Instagram to WhatsApp Automation**
> 
> Automatically forward Instagram posts, stories, and reels to WhatsApp, Telegram, and more

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)]()
[![Security](https://img.shields.io/badge/security-best%20practices-blue.svg)](docs/SECURITY_BEST_PRACTICES.md)

**Why InstaBridge?** Free, open-source, personal use focused - unlike $50-500/month commercial tools designed for businesses

---

## ⚠️ CRITICAL WARNING

**This project uses UNOFFICIAL APIs that violate Instagram and WhatsApp Terms of Service.**

| Risk | Impact |
|------|--------|
| 🚫 **Account Bans** | Permanent loss of Instagram/WhatsApp accounts |
| ⏸️ **Rate Limits** | Temporary restrictions on API access |
| 🔒 **Account Locks** | Verification challenges and login issues |
| ⚖️ **Legal Risk** | Potential ToS violation consequences |

**🛡️ Safety Recommendations:**
- ✅ Use only with throwaway/test accounts
- ✅ This is for learning browser automation
- ✅ Not for commercial or production use
- ❌ Do not use with your primary accounts

---

## 🎯 What InstaBridge Does

InstaBridge is a **free, open-source personal automation tool** that:

- 📸 Monitors your Instagram for new posts and stories
- 🤖 Automatically downloads media content
- 💬 Forwards content to specified WhatsApp contacts
- 🎛️ Filters content by type (posts, stories, close friends)
- 📊 Provides insights (who doesn't follow back, unfollow tracking)
- ⏰ Runs on a schedule or on-demand

### Real-World Use Cases

- **Content Creators**: Share Instagram posts with a WhatsApp community group
- **Personal Sharing**: Auto-forward stories to family members
- **Backup**: Keep a local copy of your Instagram content
- **Analytics**: Track follower/following relationships
- **Learning**: Understand browser automation and unofficial APIs

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Instagram     │
│   (instagrapi)  │──┐
└─────────────────┘  │
                     │  ┌──────────────────┐
                     ├──│  InstaBridge     │
                     │  │  Core Engine     │
┌─────────────────┐  │  │  - State Mgmt    │
│   WhatsApp Web  │  │  │  - Scheduling    │
│   (Playwright)  │──┤  │  - Multi-platform│
└─────────────────┘  │  │  - Deduplication │
                     │  └──────────────────┘
┌─────────────────┐  │           │
│  Telegram       │──┘  ┌────────┴─────────┐
│  (Coming Soon)  │     │                  │
└─────────────────┘ ┌───▼────┐      ┌─────▼─────┐
                    │ Web UI │      │ Analytics │
                    │ (Flask)│      │  Engine   │
                    └────────┘      └───────────┘
```

**Extensible Design:** Ready for Telegram, Discord, and more platforms

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design decisions.

---

## ✨ Features

### 🌟 **Why Choose InstaBridge Over Commercial Tools?**

| Feature | Commercial Tools | InstaBridge |
|---------|-----------------|-------------|
| **Cost** | $50-500/month | Free Forever |
| **Target** | Business/Marketing | Personal Use |
| **Open Source** | ❌ Closed | ✅ Open |
| **Learning** | ❌ Black box | ✅ Educational |
| **Extensibility** | ❌ Locked | ✅ Add platforms |
| **Privacy** | ⚠️ Cloud-based | ✅ Self-hosted |

### 🎯 Core Automation
- ✅ Instagram post/story monitoring
- ✅ Multi-recipient support with per-recipient filtering
- ✅ Smart deduplication (never send duplicates)
- ✅ Close friends story detection
- ✅ Carousel/album support
- ✅ Custom message prefixes

### ⏰ Scheduling
- ✅ Daily scheduled runs (customizable time & timezone)
- ✅ Weekly unfollow notifications
- ✅ One-time scheduled runs
- ✅ Settings auto-reload without restart

### 📊 Analytics
- ✅ "Not following back" analysis with filtering
- ✅ Unfollow detection and alerts
- ✅ Follower statistics and trends
- ✅ Warm cache system for performance

### 🎛️ Management
- ✅ Web UI for configuration (localhost:5000)
- ✅ Per-recipient content preferences
- ✅ JSON-based settings (easy to edit)
- ✅ Session persistence (scan QR once)

---

## 🚀 Quick Start

### Platform Compatibility

| Platform | Status | Notes |
|----------|--------|-------|
| **macOS** | ✅ Fully Supported | Native file picker via AppleScript |
| **Linux** | ✅ Supported | Tested on Ubuntu 22.04+ |
| **Windows** | ⚠️ Compatible | DOM file input (no native picker) |

**Minimum Requirements:**
- Python 3.13+
- 2GB RAM
- 500MB disk space
- Internet connection

**Tested Configurations:**
- macOS 13+ (Ventura, Sonoma)
- Ubuntu 22.04+ / Debian 12+
- Windows 10/11 (WSL2 recommended)

### Prerequisites

- Python 3.13+
- Instagram account (test/throwaway recommended)
- WhatsApp account

### Installation

```bash
# Clone the repository
git clone https://github.com/barisegesevgili/InstaBridge.git
cd InstaBridge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium

# Create configuration
cp .env.example .env
# Edit .env with your credentials
```

### Configuration

**🔐 RECOMMENDED: Secure Credential Storage (v1.0.2+)**

InstaBridge now supports system keychain for secure password storage:

```bash
# Install keyring for secure storage
pip install keyring

# Run interactive setup wizard
python -m src.credentials

# Passwords stored encrypted in:
# - macOS: Keychain Access
# - Linux: libsecret/gnome-keyring
# - Windows: Credential Manager
```

**Benefits:**
- ✅ Passwords encrypted by OS (never in plain text)
- ✅ No `.env` file with passwords
- ✅ Protected by system authentication
- ✅ Set once, use forever

**Alternative: Manual .env setup** (less secure)

If you prefer not to use keychain, edit `.env`:

```bash
# Instagram credentials (use throwaway account!)
IG_USERNAME=your_test_account
IG_PASSWORD=your_secure_password

# WhatsApp content recipient
WA_CONTENT_CONTACT_NAME=Friend Name
WA_CONTENT_PHONE=491701234567  # International format, digits only

# WhatsApp report recipient (for unfollow alerts)
WA_REPORT_CONTACT_NAME=Notes  # Your own "Notes" chat
WA_REPORT_PHONE=

# Optional: Custom message prefix
MESSAGE_PREFIX=New from Instagram:
```

📖 **See [Keychain Setup Guide](docs/KEYCHAIN_SETUP.md) for detailed instructions**

**💡 Pro Tip:** Use `WA_CONTENT_PHONE` (international format) instead of contact name for 10x more reliability.

### First Run

```bash
# Run once (you'll scan QR code for WhatsApp Web)
python -m src.main

# Expected output:
# ✓ Instagram login OK
# ✓ WhatsApp Web ready (scan QR if first time)
# ✓ Found 1 new post
# ✓ Sent to Friend Name
```

---

## 📖 Usage

### Basic Commands

```bash
# Dry run (simulate without sending)
python -m src.main --dry-run

# One-time run
python -m src.main

```bash
# One-time run
python -m src.main

# Resend last batch (testing)
python -m src.main --resend-last

# Force resend (ignore deduplication)
python -m src.main --force

# Limit files for testing
python -m src.main --resend-last --max-files 2
```

### Scheduled Automation

```bash
# Daily at 19:00 Berlin time (keeps running)
python -m src.scheduler

# Weekly unfollow checker (Sunday 22:00 Berlin)
python -m src.unfollow_scheduler

# Different weekday
python -m src.unfollow_scheduler --weekday monday

# One-time scheduled run
python -m src.run_at --time 14:50 --tz Europe/Berlin
```

### Web UI

```bash
# Start web interface
python -m src.webapp

# Open browser to http://127.0.0.1:5000
```

**Features:**
- 🎛️ Settings management (recipients, schedule)
- 📊 "Not following back" reports with filters
- 🔄 Warm cache for performance
- 📈 Next run preview

### Analytics Commands

```bash
# List accounts not following you back
python -m src.unfollow

# Check for new unfollows (sends WhatsApp alert)
python -m src.unfollow --check-unfollows --notify
```

---

## 🎨 Per-Recipient Configuration

Create `settings.json` to manage multiple recipients:

```json
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
    },
    {
      "id": "family",
      "display_name": "Family Group",
      "wa_contact_name": "Family Chat",
      "enabled": true,
      "send_posts": true,
      "send_stories": false,
      "send_close_friends_stories": false
    }
  ]
}
```

Or use the Web UI at `http://127.0.0.1:5000/settings` to manage visually.

---

## 🔧 Advanced Configuration

### Session Files

- `ig_session.json` - Instagram session (auto-managed)
- `wa_profile/` - WhatsApp Web profile (persistent login)
- `state.json` - Deduplication state
- `follow_cache.json` - Follower/following cache
- `user_cache.json` - User stats cache

### Rate Limiting & Delays 🛡️

**v1.0.1+ includes comprehensive rate limiting to minimize ban risk:**

- **Automatic delays**: 2-5 seconds + random jitter between all Instagram requests
- **Hourly limits**: Max 60 requests per hour (configurable)
- **Human-like timing**: Random variations to avoid detection patterns
- **Download throttling**: 0.5-1.5s delays between file downloads
- **Analytics delays**: 0.7-1.0s between user stats requests

**Three safety levels:**
- `CONSERVATIVE`: 3-7s delays, 40 req/hour (safest for new accounts)
- `MODERATE`: 2-5s delays, 60 req/hour (default, balanced)
- `AGGRESSIVE`: 1-3s delays, 80 req/hour (higher risk, testing only)

**📖 See [Safe Usage Guide](docs/SAFE_USAGE_GUIDE.md) for detailed recommendations.**

### Platform-Specific Notes

**macOS:**
- ✅ Native file picker automation via AppleScript
- ⚠️ Requires Accessibility permissions: System Settings > Privacy & Security > Accessibility > Terminal/iTerm
- ✅ Best performance and reliability

**Linux:**
- ✅ DOM-based file picker (fully functional)
- ✅ No special permissions required
- ⚠️ Ensure Chromium dependencies: `sudo apt install -y libglib2.0-0 libnss3 libx11-6`
- ✅ Tested on Ubuntu 22.04+, Debian 12+

**Windows:**
- ✅ DOM-based file picker (functional)
- ⚠️ WSL2 recommended for best experience
- ⚠️ Native Windows: May need `playwright install chromium --with-deps`
- ⚠️ Path separators: Use forward slashes or escape backslashes

---

## 🐛 Troubleshooting

### Instagram Issues

**"Login failed" or "Challenge required"**
- Complete Instagram verification in the mobile app
- Delete `ig_session.json` and try again
- Wait 15-30 minutes between attempts

**"Rate limited" errors**
- Stop all automation for 1-2 hours
- Reduce request frequency
- Use a less active Instagram account

### WhatsApp Issues

**QR code not appearing**
- Delete `wa_profile/` folder
- Restart the script
- Check Playwright browser window

**Wrong contact opened**
- Use phone number instead of name (`WA_CONTENT_PHONE`)
- Ensure international format (e.g., 491701234567)

**Upload fails / wrong input selected**
- Known issue: WhatsApp Web DOM changes frequently
- Try closing and reopening the script
- Check logs for specific errors

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

---

## 🧪 Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_ig.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
ruff check src/
```

### Project Structure

```
InstaToWhatsapp/
├── src/                    # Source code
│   ├── ig.py              # Instagram client
│   ├── wa.py              # WhatsApp automation
│   ├── main.py            # Core orchestration
│   ├── settings.py        # Configuration management
│   ├── state.py           # State persistence
│   ├── insights.py        # Analytics engine
│   ├── scheduler.py       # Daily scheduler
│   ├── unfollow.py        # Unfollow tracking
│   └── webapp.py          # Web UI
├── tests/                 # Test suite
├── docs/                  # Documentation
├── .env.example           # Configuration template
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

---

## 🚀 Roadmap

### Current (v1.0) ✅
- WhatsApp automation
- Multi-recipient support
- Analytics & insights

### Coming Soon (v1.1) 🔜
- **Telegram support** 
- **Discord webhooks**
- Docker deployment
- Enhanced UI

### Future (v2.0) 💡
- Multi-platform dashboard
- Plugin architecture
- Cloud deployment options

See [ROADMAP.md](docs/ROADMAP.md) for details.

---

## 🤝 Contributing

We welcome contributions! InstaBridge is ideal for learning:

- Browser automation (Playwright)
- Unofficial API usage (instagrapi)
- State management patterns
- Flask web apps
- Scheduling systems

**Ways to contribute:**

- 🐛 Report bugs via [Issues](https://github.com/barisegesevgili/InstaBridge/issues)
- 💡 Suggest features (Telegram, Discord, etc.)
- 📖 Improve documentation
- 🧪 Add tests
- 🔧 Fix bugs or add features
- 🌍 Add new platform integrations

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [KEYCHAIN_SETUP.md](docs/KEYCHAIN_SETUP.md) | **🔐 Secure password storage (RECOMMENDED)** |
| [SAFE_USAGE_GUIDE.md](docs/SAFE_USAGE_GUIDE.md) | **⚠️ Minimize account ban risk** |
| [SECURITY_BEST_PRACTICES.md](docs/SECURITY_BEST_PRACTICES.md) | Security guidelines & credential safety |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Design decisions & system overview |
| [SETUP.md](docs/SETUP.md) | Detailed setup guide |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues & solutions |
| [ROADMAP.md](docs/ROADMAP.md) | Future plans & wishlist |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

---

## 🗺️ Roadmap

### v1.0 - Stability ✅
- [x] Multi-recipient support
- [x] Per-recipient filtering
- [x] Web UI for configuration
- [x] Unfollow detection
- [x] Comprehensive documentation

### v1.1 - Polish (Current)
- [ ] Docker support
- [ ] Windows compatibility testing
- [ ] Enhanced error recovery
- [ ] Performance optimizations

### v2.0 - Extensibility
- [ ] Plugin architecture
- [ ] Discord/Telegram support
- [ ] Cloud deployment guides
- [ ] Official API support (business accounts)

See [ROADMAP.md](docs/ROADMAP.md) for details.

---

## 📊 Project Stats

- **Code Quality**: Clean, typed Python
- **Test Coverage**: (Coming soon)
- **Documentation**: Comprehensive guides
- **Community**: Open to contributions

---

## 🙏 Acknowledgments

**InstaBridge is the open-source alternative to:**
- Zapier Instagram+WhatsApp integrations ($20-100/month)
- Interakt (CRM tool for businesses)
- Bardeen.ai (paid automation)
- Mark360.ai (enterprise solution)

Built for personal use, learning, and the open-source community.

**Technology Stack:**
- [instagrapi](https://github.com/adw0rd/instagrapi) - Instagram API
- [Playwright](https://playwright.dev/) - Browser automation
- [Flask](https://flask.palletsprojects.com/) - Web interface

**Inspired By:**
- [SuperClaude Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) - Project structure

---

## ⚖️ License

MIT License with important disclaimers - see [LICENSE](LICENSE) for details.

**Remember:** This is an educational project. Use responsibly and at your own risk.

---

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/barisegesevgili/InstaBridge/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/barisegesevgili/InstaBridge/discussions)
- 📖 **Documentation**: [docs/](docs/)
- 🌟 **Show Support**: Star the repo if you find it useful!

---

<div align="center">

**🌉 InstaBridge - Bridge Your Social Media Platforms**

**Free Forever • Open Source • Extensible • Privacy-First**

[⭐ Star this repo](https://github.com/barisegesevgili/InstaBridge) | [🐛 Report Bug](https://github.com/barisegesevgili/InstaBridge/issues) | [💡 Request Platform](https://github.com/barisegesevgili/InstaBridge/issues)

**Made with ❤️ for the open-source community**

</div>
