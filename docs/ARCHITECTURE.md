# Architecture Documentation

## System Overview

**InstaBridge** is an open-source personal automation platform that bridges Instagram with messaging platforms (WhatsApp, Telegram, Discord) using unofficial APIs and browser automation.

**Design Philosophy:** Extensible, multi-platform, self-hosted alternative to commercial tools.

## Design Principles

### 1. Unofficial API Usage
**Decision:** Use `instagrapi` for Instagram, Playwright for WhatsApp Web

**Rationale:**
- Instagram personal accounts lack official API access for stories/posts
- WhatsApp Web has no official automation API
- Alternative: Manual sharing (defeats purpose of automation)

**Trade-offs:**
- ✅ Access to personal account features
- ❌ Risk of account restrictions
- ❌ Breaking changes from platform updates

### 2. Browser Automation vs Native
**Decision:** Use Playwright to drive actual browser

**Rationale:**
- WhatsApp Web is the only automation path
- Real browser = better compatibility
- Session persistence (scan QR once)

**Trade-offs:**
- ✅ Works with current WhatsApp Web
- ✅ Human-like behavior
- ❌ Heavier resource usage
- ❌ Platform-specific quirks (macOS file picker)

### 3. State Management
**Decision:** JSON files for state, not database

**Rationale:**
- Simple setup (no DB required)
- Human-readable
- Easy to debug and modify
- Small data volumes

**Files:**
- `state.json` - Deduplication tracking
- `ig_session.json` - Instagram session
- `wa_profile/` - WhatsApp browser profile
- `user_cache.json` - Analytics cache
- `settings.json` - Configuration

### 4. Per-Recipient Filtering
**Decision:** Each recipient has content preferences

**Rationale:**
- Different audiences want different content
- Family vs friends vs close friends
- Avoid spam

**Implementation:**
```python
sent_ids_by_recipient: dict[str, Set[str]]
```

## Component Architecture

```
┌─────────────────────────────────────────────────┐
│                  Entry Points                   │
├─────────────┬───────────┬──────────┬────────────┤
│   main.py   │ scheduler │ webapp.py│ unfollow.py│
└──────┬──────┴─────┬─────┴─────┬────┴──────┬─────┘
       │            │           │           │
       └────────────┴───────────┴───────────┘
                    │
       ┌────────────▼───────────────┐
       │      Core Orchestration     │
       │   - load_config()           │
       │   - run_once()              │
       │   - resend_last()           │
       └────────┬──────────┬─────────┘
                │          │
     ┌──────────▼──┐   ┌──▼─────────────┐
     │  IgClient   │   │ WhatsAppSender │
     │  (ig.py)    │   │   (wa.py)      │
     └─────────────┘   └────────────────┘
           │                   │
     ┌─────▼──────┐     ┌──────▼────────┐
     │ instagrapi │     │  Playwright   │
     │  library   │     │   browser     │
     └────────────┘     └───────────────┘
```

## Key Components

### 1. Instagram Client (`ig.py`)

**Responsibilities:**
- Login with session caching
- Fetch posts and stories
- Download media files
- Handle rate limiting

**Key Methods:**
```python
login(username, password)              # Session-aware
get_latest_post_items() -> list[IgItem]
get_active_story_items() -> list[IgItem]
download(dest_dir) -> list[Path]
```

**Design Notes:**
- Uses mobile API endpoints when available (more stable)
- Graceful fallback to GraphQL
- Retry logic for transient errors

### 2. WhatsApp Sender (`wa.py`)

**Responsibilities:**
- Launch persistent browser context
- Navigate WhatsApp Web
- Search and open chats
- Upload and send media

**Key Methods:**
```python
start()                                  # Launch browser
open_chat(contact_name, phone)          # Prefer phone
send_media_batch(paths, caption)        # Multi-file
stop()                                  # Cleanup
```

**Design Notes:**
- Persistent profile → scan QR once
- Phone number prioritization (10x more reliable)
- Fallback selectors for UI changes
- Platform-specific file picker handling

### 3. Core Orchestration (`main.py`)

**Responsibilities:**
- Configuration loading
- Item collection logic
- Per-recipient filtering
- Deduplication
- Batch sending

**Flow:**
```python
1. Load config from .env
2. Load settings (recipients)
3. Load state (dedupe tracking)
4. Login to Instagram
5. Start WhatsApp Web
6. Collect new items (posts + stories)
7. Filter by age (24h cutoff)
8. For each recipient:
   a. Filter by preferences
   b. Check dedupe state
   c. Download media
   d. Send to WhatsApp
   e. Update state
9. Cleanup
```

### 4. Settings Management (`settings.py`)

**Responsibilities:**
- Load/save JSON configuration
- Validate recipient data
- Default values
- Schema evolution

**Design:**
```python
@dataclass
class RecipientSettings:
    id: str
    wa_phone: str
    send_posts: bool
    send_stories: bool
    send_close_friends_stories: bool
```

### 5. Web UI (`webapp.py`)

**Responsibilities:**
- Configuration interface
- Analytics display
- Cache warming
- Scheduler preview

**Tech Stack:**
- Flask (lightweight)
- Embedded HTML templates
- REST API endpoints
- No external JS dependencies

## Data Flow

### Content Forwarding Flow

```
Instagram → Download → Filter → Send → Update State
    ↓           ↓         ↓        ↓         ↓
instagrapi   media/   dedupe   WhatsApp  state.json
```

### Analytics Flow

```
Instagram → Cache → Filter → Display
    ↓         ↓       ↓        ↓
followers  user_   UI logic  Web UI
following  cache.
           json
```

## Performance Optimizations

### 1. Caching Strategy

**Follower/Following Lists:**
- TTL: 6 hours (configurable)
- Avoids repeated API calls
- Stored in `follow_cache.json`

**User Stats:**
- TTL: 7 days (configurable)
- Delayed fetching (0.7-1.0s)
- Stored in `user_cache.json`

### 2. Deduplication

**Global Level:**
```python
sent_ids: Set[str]  # All ever sent
```

**Per-Recipient Level:**
```python
sent_ids_by_recipient: dict[str, Set[str]]
```

**Why both?** Backward compatibility + flexibility

### 3. Rate Limiting

**Instagram:**
- Session caching
- Exponential backoff
- Mobile API preference

**WhatsApp:**
- Natural delays in automation
- Retry on transient failures

## Security Considerations

### 1. Credential Storage

**Current:** Plain text in `.env`

**Future Options:**
- System keychain integration
- Encrypted .env files
- Environment variables only

### 2. Session Files

**Risk:** Session tokens in plain JSON

**Mitigation:**
- File permissions (600)
- .gitignore coverage
- Documentation warnings

### 3. Browser Profile

**Risk:** WhatsApp session accessible

**Mitigation:**
- Local storage only
- No cloud sync
- Throw away accounts

## Platform-Specific Behavior

### macOS
- AppleScript for native file picker
- Requires Accessibility permissions
- Better UX for single file uploads

### Windows/Linux
- DOM input file selection
- No special permissions
- Fully functional

## Error Handling Philosophy

### 1. Fail Fast on Config
Missing credentials → immediate exit with clear message

### 2. Retry on Transient
Network errors → exponential backoff

### 3. Skip on Partial
One item fails → log and continue with others

### 4. Preserve State
Crash mid-run → already-sent items still tracked

## Extension Points

### 1. New Platforms
Interface pattern:
```python
class PlatformSender:
    def start() -> None: ...
    def send_media(path, caption) -> None: ...
    def stop() -> None: ...
```

### 2. New Content Types
Add to `IgItem`:
```python
kind: Literal["post", "story", "reel", "igtv"]
```

### 3. New Filters
Extend `RecipientSettings`:
```python
send_reels: bool
send_igtv: bool
filter_by_hashtag: list[str]
```

## Testing Strategy

### Unit Tests
- State management
- Configuration validation
- Deduplication logic

### Integration Tests
- Instagram mock API
- WhatsApp selector testing

### Manual Tests
- Full end-to-end flow
- Platform-specific quirks
- Error recovery

## Known Limitations

### Technical
- Single Instagram account
- WhatsApp Web only (no mobile API)
- Single-threaded execution
- No distributed setup

### Platform
- Instagram rate limits
- WhatsApp Web DOM changes
- macOS-specific file picker
- No official API support

## Future Improvements

### Short Term
- Docker containerization
- Enhanced error recovery
- More granular logging

### Long Term
- Plugin architecture
- Telegram/Discord support
- Cloud deployment
- Official API when available
