# Secure Credential Storage with System Keychain

**InstaBridge v1.0.2+** supports secure credential storage using your operating system's native keychain instead of storing passwords in plain text `.env` files.

---

## 🔐 **Why Use Keychain?**

### **Plain Text .env (Current)**
❌ Passwords stored in readable text file  
❌ Risk if file is accidentally shared/committed  
❌ Visible to anyone with file access  
❌ No encryption at rest  

### **System Keychain (Recommended)**
✅ Passwords encrypted by OS  
✅ Protected by system authentication  
✅ No passwords in text files  
✅ Standard for secure applications  
✅ Easy to use (set once, use forever)  

---

## 🚀 **Quick Setup (5 Minutes)**

### **Step 1: Install Keyring**

```bash
# Install the keyring library
pip install keyring

# Or update requirements
pip install -r requirements.txt
```

### **Step 2: Run Interactive Setup**

```bash
python -m src.credentials
```

### **Step 3: Follow the Wizard**

```
============================================================
🔐 InstaBridge Credential Setup
============================================================

✅ Using system keychain for secure storage
Credentials will be encrypted by your operating system

------------------------------------------------------------
Instagram Credentials (use throwaway account!)
------------------------------------------------------------
Instagram username: my_throwaway_account
Instagram password: ********
Confirm password: ********

------------------------------------------------------------
WhatsApp Contact (who receives forwarded content)
------------------------------------------------------------
WhatsApp contact name: My Friend
WhatsApp phone (international format, e.g., 491701234567): 491701234567

------------------------------------------------------------
Optional: WhatsApp Report Contact (for unfollow alerts)
------------------------------------------------------------
Report contact name (or press Enter to skip): 
Report phone (or press Enter to skip): 

------------------------------------------------------------
Saving credentials...
------------------------------------------------------------
✅ Stored 'IG_USERNAME' in system keychain
✅ Stored 'IG_PASSWORD' in system keychain
✅ Stored 'WA_CONTENT_CONTACT_NAME' in system keychain
✅ Stored 'WA_CONTENT_PHONE' in system keychain

✅ All credentials stored securely in system keychain!

📝 Your .env file can now be empty (or contain only non-sensitive settings)
   Credentials are encrypted and managed by your OS

✅ Setup complete!
```

### **Step 4: Clean Up .env (Optional)**

After credentials are in keychain, you can remove passwords from `.env`:

```bash
# .env can now be minimal or empty:
IG_USERNAME=my_throwaway_account  # Only needed for identification
# IG_PASSWORD is now in keychain, not here!

MESSAGE_PREFIX=New from Instagram:
```

---

## 🖥️ **Platform-Specific Details**

### **macOS**
- **Storage:** Keychain Access app
- **Location:** `~/Library/Keychains/`
- **View:** Open "Keychain Access" app → Search for "InstaBridge"
- **Authentication:** Uses your Mac login password
- **Backup:** Included in Time Machine backups

### **Linux**
- **Storage:** libsecret / gnome-keyring
- **Install:** `sudo apt install python3-secretstorage` (Ubuntu/Debian)
- **Authentication:** Uses your login keyring password
- **View:** Seahorse (GNOME Passwords and Keys app)

### **Windows**
- **Storage:** Windows Credential Manager
- **View:** Control Panel → Credential Manager → Windows Credentials
- **Authentication:** Uses Windows login
- **Location:** Encrypted in Windows registry

---

## 🔄 **Migration from .env to Keychain**

If you're currently using `.env` files:

### **Option 1: Interactive Migration (Easiest)**

```bash
# Run setup wizard
python -m src.credentials

# Enter your current credentials
# They'll be moved to keychain automatically

# Remove passwords from .env
nano .env  # or your preferred editor
# Delete the IG_PASSWORD line
```

### **Option 2: Manual Migration**

```python
# Run Python interactive shell
python

>>> from src.credentials import CredentialManager
>>> cm = CredentialManager()

# Store Instagram password
>>> cm.set_credential("IG_PASSWORD", "your_password", username="your_instagram_username")
✅ Stored 'IG_PASSWORD' in system keychain

# Verify it works
>>> pw = cm.get_credential("IG_PASSWORD", username="your_instagram_username")
>>> print(f"Retrieved: {pw[:3]}***")
Retrieved: abc***

>>> exit()
```

Then remove password from `.env`.

---

## ✅ **Verification**

### **Test Credential Loading**

```bash
# Test that credentials load correctly
python -c "from src.main import load_config; cfg = load_config(); print(f'✅ Loaded user: {cfg.ig_username}')"

# Expected output:
🔐 Loaded credentials from system keychain
✅ Loaded user: your_username
```

### **View Stored Credentials**

**macOS:**
```bash
# Open Keychain Access
open -a "Keychain Access"

# Search for: InstaBridge
# You'll see entries like:
# - InstaBridge (IG_USERNAME)
# - InstaBridge (IG_PASSWORD:your_username)
# - InstaBridge (WA_CONTENT_CONTACT_NAME)
```

**Linux:**
```bash
# Using secret-tool
secret-tool search service InstaBridge

# Or open Seahorse GUI
seahorse
```

**Windows:**
```cmd
# Open Credential Manager
control /name Microsoft.CredentialManager

# Look for: InstaBridge entries
```

---

## 🔧 **Management Commands**

### **Update Password**

```bash
# Run setup again - it will overwrite existing credentials
python -m src.credentials
```

### **Delete Credentials**

```python
python -m src.credentials

# Or manually:
python
>>> from src.credentials import CredentialManager
>>> cm = CredentialManager()
>>> cm.delete_credential("IG_PASSWORD", username="your_username")
✅ Deleted 'IG_PASSWORD' from system keychain
```

### **Switch Back to .env**

If you want to stop using keychain:

```python
# Remove from keychain
python
>>> from src.credentials import CredentialManager
>>> cm = CredentialManager()
>>> cm.delete_credential("IG_PASSWORD", username="your_username")

# Add back to .env
echo "IG_PASSWORD=your_password" >> .env
```

---

## 🔐 **Security Benefits**

### **Encryption**
- Passwords encrypted using OS-level cryptography
- Keys derived from your system password
- Much stronger than plain text files

### **Access Control**
- Protected by system authentication
- Apps need permission to access
- Audit logs (on some systems)

### **Backup Safety**
- Keychain backups are encrypted
- Even if backup is stolen, passwords are safe
- `.env` files in backups are readable

---

## ⚠️ **Important Notes**

### **System Password Required**
The keychain is protected by your system login password. If you:
- Change your system password: Keychain still works
- Lose your system password: Keychain is inaccessible (by design)
- Reset your system: Keychain is lost (use backup)

### **Not Synced by Default**
Keychains are **local** to each machine unless you enable iCloud Keychain (macOS) or similar. This is actually more secure for automation credentials.

### **Backward Compatible**
InstaBridge still supports `.env` files. The tool will:
1. Try keychain first
2. Fall back to `.env` if keychain empty
3. Work perfectly with either method

---

## 🐛 **Troubleshooting**

### **"keyring not installed"**

```bash
pip install keyring

# If still fails:
pip install --upgrade keyring
```

### **"Could not load from keychain"**

Credentials not found. Run setup:
```bash
python -m src.credentials
```

### **Permission Denied (Linux)**

Install secret storage backend:
```bash
# Ubuntu/Debian
sudo apt install python3-secretstorage gnome-keyring

# Fedora
sudo dnf install python3-secretstorage gnome-keyring
```

### **"No keyring backend found" (Linux)**

```bash
# Start gnome-keyring
eval $(gnome-keyring-daemon --start)
export $(gnome-keyring-daemon --start)

# Or install alternative
sudo apt install libsecret-1-0 libsecret-tools
```

### **macOS: "Item not found"**

Keychain Access might be locked:
```bash
# Unlock default keychain
security unlock-keychain login.keychain
```

---

## 📚 **Additional Resources**

- [Python keyring documentation](https://pypi.org/project/keyring/)
- [macOS Keychain Access User Guide](https://support.apple.com/guide/keychain-access/)
- [Linux libsecret documentation](https://wiki.gnome.org/Projects/Libsecret)
- [Windows Credential Manager](https://support.microsoft.com/en-us/windows/accessing-credential-manager-1b5c916a-6a16-889f-8581-fc16e8165ac0)

---

## 🎯 **Best Practices**

1. **Use keychain for passwords** - IG_PASSWORD, etc.
2. **Keep non-sensitive in .env** - Contact names, settings
3. **Never commit .env** - Even without passwords
4. **Backup keychain** - Part of system backups
5. **Test after setup** - Run with `--dry-run`

---

**Ready to switch?** Run `python -m src.credentials` now! 🚀

*Last Updated: 2026-02-04*  
*Version: 1.0.2+keychain*
