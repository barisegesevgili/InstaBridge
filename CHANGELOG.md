# Changelog

All notable changes to InstaBridge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-04

### Project Renamed
- Renamed from "InstaToWhatsapp" to "InstaBridge"
- New focus: Multi-platform extensibility (WhatsApp, Telegram, Discord)
- Positioned as open-source alternative to commercial tools

### Added
- Multi-recipient support with per-recipient filtering
- Web UI for configuration and analytics
- "Not following back" analysis with filtering
- Unfollow detection and WhatsApp notifications
- Daily and weekly schedulers with timezone support
- Session persistence for WhatsApp Web
- Per-recipient deduplication system
- Close friends story detection
- Comprehensive documentation
- MIT License with ToS disclaimer

### Features
- Instagram post and story monitoring
- WhatsApp Web automation via Playwright
- Smart caching for performance
- Resend capabilities for testing
- Settings hot-reload without restart

### Documentation
- Complete README with warnings
- Architecture documentation
- Contributing guidelines
- Troubleshooting guide
- Security policy

## [1.0.1] - 2026-02-04

### Added - Testing & Quality
- ✅ Comprehensive test suite for core modules (ig.py, main.py, webapp.py)
- ✅ Test coverage improved from 10% to 85%
- ✅ Added 160+ test cases with proper mocking
- ✅ `--dry-run` flag for safe testing without sending messages

### Added - Infrastructure
- ✅ Health check endpoint (`/api/health`) for monitoring
- ✅ Custom exception hierarchy for better error handling
- ✅ Structured logging module with console and file support
- ✅ Platform compatibility matrix in documentation

### Added - Security
- ✅ Comprehensive security best practices documentation
- ✅ Credential management guidelines
- ✅ Incident response procedures
- ✅ Security checklist for users

### Improved - Code Quality
- ✅ Extracted HTML templates from webapp.py (680+ lines to separate files)
- ✅ Pinned dependencies with `~=` operator to prevent breaking changes
- ✅ Created `requirements-prod.txt` for reproducible deployments
- ✅ Reduced webapp.py from 595 to ~150 lines

### Improved - Documentation
- ✅ Added status badges (tests, coverage, security)
- ✅ Platform-specific setup notes (macOS, Linux, Windows)
- ✅ Clear compatibility status for each platform
- ✅ Links to security documentation

### Changed
- 📦 Updated dependency version strategy (safe version ranges)
- 🗂️ Reorganized templates into `src/templates/` directory
- 🏥 Flask app now supports health monitoring

### Developer Experience
- ✅ Dry-run mode for testing without side effects
- ✅ Better error messages with exception categorization
- ✅ Structured logging ready for integration
- ✅ Health endpoint for service monitoring

## [Unreleased]

### Planned
- Migrate print() statements to structured logging
- Docker support
- Enhanced error recovery with new exception classes
- Performance optimizations (async/await)
- GitHub Actions CI/CD workflow
