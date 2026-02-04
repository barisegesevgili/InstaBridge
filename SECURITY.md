# Security Policy

## Important Security Considerations

### Credential Storage

This project stores credentials in plain text files:

- `.env` - Instagram and WhatsApp credentials
- `ig_session.json` - Instagram session tokens
- `wa_profile/` - WhatsApp Web session data

**Recommendations:**

- Never commit these files to version control
- Use throwaway/test accounts only
- Restrict file permissions: `chmod 600 .env ig_session.json`
- Do not share these files publicly

### Platform Risk

This tool uses unofficial APIs that may:

- Trigger account restrictions
- Expose your credentials to third-party libraries
- Change without notice, breaking functionality

**Use at your own risk with test accounts only.**

## Reporting Vulnerabilities

If you discover a security vulnerability:

1. **Do NOT** open a public issue
2. Email the maintainers privately
3. Provide detailed information about the vulnerability
4. Allow time for a fix before public disclosure

We will acknowledge your report within 48 hours.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Best Practices

- Use virtual environments
- Keep dependencies updated
- Review code before running
- Monitor account activity
- Use separate test accounts
