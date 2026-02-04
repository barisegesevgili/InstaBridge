# Security Best Practices

**InstaBridge** handles sensitive credentials and session data. Follow these best practices to minimize risks.

## ⚠️ Critical Warnings

### Account Safety
- ✅ **ONLY use throwaway accounts** - Never use your primary Instagram or WhatsApp accounts
- ✅ **Expect bans** - This tool violates Terms of Service
- ✅ **Educational purpose only** - Not for production or commercial use
- ❌ **No warranties** - Use at your own risk

### Legal & Ethical
- This tool uses unofficial APIs that violate platform ToS
- Automated access may trigger security responses
- Check local laws regarding automation and data access
- Respect privacy and consent when forwarding content

---

## 🔐 Credential Management

### Environment Variables (`.env` file)

**Current State:** Credentials stored in plain text

```bash
# .env
IG_USERNAME=throwaway_account
IG_PASSWORD=secure_password_here
WA_CONTENT_PHONE=491701234567
```

**Best Practices:**

1. **File Permissions**
   ```bash
   chmod 600 .env  # Only owner can read/write
   ```

2. **Never Commit `.env`**
   - Already in `.gitignore`
   - Double-check before git commits
   - Use `.env.example` for templates only

3. **Use Strong Passwords**
   - Unique passwords for throwaway accounts
   - Consider password manager
   - Rotate regularly (every 30-90 days)

4. **Environment-Specific Files**
   ```bash
   .env.development  # Local testing
   .env.production   # If deploying (not recommended)
   ```

### Session Files

**Sensitive Files:**
- `ig_session.json` - Instagram session tokens
- `wa_profile/` - WhatsApp Web browser profile
- `state.json` - Tracking data (includes item IDs)

**Protection Measures:**

```bash
# Secure file permissions
chmod 600 ig_session.json
chmod 700 wa_profile/
chmod 600 state.json
```

**Recommendations:**
- ✅ These files are in `.gitignore` by default
- ✅ Exclude from cloud backups (Dropbox, iCloud, etc.)
- ✅ Delete when switching accounts
- ⚠️ Consider encryption at rest (see Advanced section)

---

## 🌐 Network Security

### Local Development

```bash
# Web UI binds to localhost only
python -m src.webapp  # Accessible at 127.0.0.1:5000
```

**This is good:** Only accessible from your machine.

### Production Deployment (NOT RECOMMENDED)

If you deploy despite warnings:

1. **Use HTTPS** - Never expose over plain HTTP
2. **Add Authentication** - Basic auth minimum
3. **Firewall Rules** - Restrict access by IP
4. **VPN Only** - Deploy behind VPN
5. **Monitor Access Logs** - Watch for suspicious activity

**Better:** Don't deploy to public internet.

---

## 🔒 Advanced: Encryption at Rest

### Option 1: Encrypted Home Directory

**macOS:**
```bash
# FileVault (System Settings > Privacy & Security)
# Encrypts entire disk
```

**Linux:**
```bash
# LUKS full disk encryption
# Set up during OS installation
```

**Windows:**
```bash
# BitLocker (Windows Pro)
```

### Option 2: Encrypted Container

Use VeraCrypt to create encrypted volume:

```bash
# 1. Create encrypted container (e.g., 500MB)
# 2. Mount as drive
# 3. Store InstaBridge project inside
# 4. Unmount when not in use
```

### Option 3: System Keychain (Future Enhancement)

**Planned for v1.2:**
```python
# Store credentials in system keychain
# macOS: Keychain Access
# Linux: libsecret
# Windows: Credential Manager
```

---

## 🚨 Incident Response

### If Accounts Are Banned

1. **Don't panic** - Expected outcome
2. **Don't appeal** - May draw more attention
3. **Create new throwaway accounts**
4. **Delete old session files**
   ```bash
   rm ig_session.json
   rm -rf wa_profile/
   ```
5. **Wait 24-48 hours** before retry

### If Credentials Are Exposed

1. **Change passwords immediately**
2. **Revoke Instagram access tokens**
3. **Check for unauthorized access**
4. **Review git history** for accidental commits
   ```bash
   git log -p | grep -i password
   ```
5. **Use `git-filter-repo` to remove from history** if found

### If State Data Is Compromised

**Risk Level:** Low-Medium

`state.json` contains:
- Item IDs (post/story identifiers)
- Recipient IDs (not real names/phones)
- Timestamps

**No direct PII, but:**
- Can correlate with public Instagram posts
- Shows automation patterns

**Response:**
- Delete `state.json` (regenerates on next run)
- Review who had access
- Change patterns (timing, frequency)

---

## 📋 Security Checklist

### Initial Setup
- [ ] Use throwaway Instagram account
- [ ] Use throwaway WhatsApp account (or separate device)
- [ ] Create strong, unique passwords
- [ ] Secure `.env` file permissions (`chmod 600`)
- [ ] Verify `.gitignore` includes sensitive files
- [ ] Enable disk encryption (FileVault/BitLocker/LUKS)

### Ongoing
- [ ] Rotate passwords every 30-90 days
- [ ] Monitor for account restrictions
- [ ] Review git commits before pushing
- [ ] Check web UI only binds to localhost
- [ ] Keep dependencies updated (`pip list --outdated`)
- [ ] Audit session files quarterly

### Deployment (If Ignoring Warnings)
- [ ] HTTPS with valid certificate
- [ ] Strong authentication (not just .env passwords)
- [ ] Firewall rules (IP whitelist)
- [ ] VPN-only access
- [ ] Logging and monitoring
- [ ] Incident response plan

### Decommissioning
- [ ] Delete `.env` file
- [ ] Securely wipe `ig_session.json`
- [ ] Delete `wa_profile/` directory
- [ ] Delete `state.json` and cache files
- [ ] Remove from cron/scheduler
- [ ] Uninstall dependencies (`pip uninstall -r requirements.txt`)

---

## 🛡️ Defense in Depth

**Layers of Protection:**

1. **Physical Security**
   - Lock your computer when away
   - Full disk encryption
   - Secure workspace

2. **System Security**
   - Keep OS updated
   - Firewall enabled
   - Antivirus/antimalware
   - Secure boot

3. **Application Security**
   - File permissions (600/700)
   - Localhost binding
   - No hardcoded secrets

4. **Network Security**
   - VPN for remote access
   - HTTPS only
   - No public exposure

5. **Operational Security**
   - Throwaway accounts
   - Regular credential rotation
   - Monitoring and alerting
   - Incident response plan

---

## 📚 Additional Resources

- [OWASP Credential Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Instagram Security Tips](https://help.instagram.com/369001149843369)
- [WhatsApp Security Features](https://www.whatsapp.com/security)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

## 🔔 Reporting Security Issues

**Found a security vulnerability in InstaBridge?**

- **Email:** [Your contact email - if you want reports]
- **GitHub Security Advisories:** (Private disclosure)
- **Response Time:** Best effort (hobby project)

**Please provide:**
- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if any)

**We do NOT offer:**
- Bug bounties
- SLAs
- Warranties

---

## ⚖️ Disclaimer

This tool is provided "as is" without warranty. Users are responsible for:
- Compliance with platform Terms of Service
- Legal compliance in their jurisdiction
- Security of their own credentials and data
- Consequences of account bans or restrictions

**Use responsibly and at your own risk.**

---

*Last Updated: 2026-02-04*  
*Version: 1.0.0*
