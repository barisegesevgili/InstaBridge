# Contributing to InstaBridge

Thank you for considering contributing to InstaBridge! This document provides guidelines for contributing to the project.

## 🌉 About InstaBridge

InstaBridge is the open-source alternative to commercial Instagram automation tools. We focus on personal use, extensibility, and education.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected vs actual behavior**
- **Environment details** (OS, Python version)
- **Log output** if available

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Provide:

- **Clear title** for the enhancement
- **Detailed description** of the proposed functionality
- **Use cases** explaining why this would be useful
- **Possible implementation** if you have ideas

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black src/ tests/`)
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/InstaBridge.git
cd InstaBridge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black mypy ruff

# Install Playwright
python -m playwright install chromium
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Format with `black`
- Maximum line length: 120 characters
- Use descriptive variable names

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
ruff check src/
```

### Testing

- Write tests for new features
- Maintain or improve test coverage
- Run tests before submitting PR

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Project Structure

```
src/
├── ig.py           # Instagram client wrapper
├── wa.py           # WhatsApp automation
├── main.py         # Core orchestration
├── settings.py     # Configuration management
├── state.py        # State persistence
├── insights.py     # Analytics features
├── scheduler.py    # Daily scheduler
├── unfollow.py     # Unfollow tracking
└── webapp.py       # Web interface
```

## Commit Messages

Use clear, descriptive commit messages:

```
feat: add multi-recipient filtering
fix: handle WhatsApp Web DOM changes
docs: update installation guide
test: add tests for state management
refactor: simplify Instagram client
```

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for design changes
- Add docstrings to new functions
- Update CHANGELOG.md for releases

## Getting Help

- Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Search existing issues
- Ask in GitHub Discussions

## Recognition

Contributors will be acknowledged in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing! 🎉
