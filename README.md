# 📱 InstaToWhatsapp

> **Automatically forward your Instagram posts and stories to friends on WhatsApp**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

## 🎯 What This Does

InstaToWhatsapp is a **personal automation tool** that:

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
                     ├──│  Core Engine     │
                     │  │  - State Mgmt    │
┌─────────────────┐  │  │  - Scheduling    │
│   WhatsApp Web  │  │  │  - Multi-recipient│
│   (Playwright)  │──┘  │  - Deduplication │
└─────────────────┘     └──────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼─────┐      ┌─────▼─────┐
              │  Web UI   │      │  Insights │
              │  (Flask)  │      │  Engine   │
              └───────────┘      └───────────┘
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design decisions.

---

## ✨ Features

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

### Prerequisites

- Python 3.13+
- macOS, Linux, or Windows
- Instagram account (test/throwaway recommended)
- WhatsApp account

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/InstaToWhatsapp.git
cd InstaToWhatsapp

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

Edit `.env` with your credentials:

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

### Rate Limiting & Delays

The tool includes smart delays to avoid Instagram rate limits:

- **Post fetching**: Respects Instagram API limits
- **User stats**: 0.7-1.0s delay between requests
- **Retry logic**: Exponential backoff on failures

### Platform-Specific Notes

**macOS:**
- Native file picker automation supported via AppleScript
- Requires Accessibility permissions for "System Events"

**Windows/Linux:**
- File picker uses DOM input (fully functional)
- No platform-specific permissions needed

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

## 🤝 Contributing

We welcome contributions! This project is ideal for learning:

- Browser automation (Playwright)
- Unofficial API usage (instagrapi)
- State management patterns
- Flask web apps
- Scheduling systems

**Ways to contribute:**

- 🐛 Report bugs via [Issues](https://github.com/yourusername/InstaToWhatsapp/issues)
- 💡 Suggest features
- 📖 Improve documentation
- 🧪 Add tests
- 🔧 Fix bugs or add features

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
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

This project was built for educational purposes to understand:

- Browser automation techniques
- Unofficial API patterns
- State management in automation
- Multi-platform compatibility

**Inspiration:**
- [instagrapi](https://github.com/adw0rd/instagrapi) - Instagram API
- [Playwright](https://playwright.dev/) - Browser automation
- [SuperClaude Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) - Project structure

---

## ⚖️ License

MIT License with important disclaimers - see [LICENSE](LICENSE) for details.

**Remember:** This is an educational project. Use responsibly and at your own risk.

---

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/InstaToWhatsapp/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/InstaToWhatsapp/discussions)
- 📖 **Documentation**: [docs/](docs/)

---

<div align="center">

**Built with ❤️ for learning browser automation**

[⭐ Star this repo](https://github.com/yourusername/InstaToWhatsapp) | [🐛 Report Bug](https://github.com/yourusername/InstaToWhatsapp/issues) | [💡 Request Feature](https://github.com/yourusername/InstaToWhatsapp/issues)

</div>
