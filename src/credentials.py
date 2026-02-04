"""Secure credential management using system keychain.

This module provides secure storage of Instagram and WhatsApp credentials
using the operating system's native credential manager:
- macOS: Keychain Access
- Linux: libsecret/gnome-keyring
- Windows: Windows Credential Manager

Credentials are encrypted by the OS and never stored in plain text files.
"""

import getpass
import os
from typing import Optional

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    print("⚠️  Warning: keyring not installed. Install with: pip install keyring")

# Service name for keychain entries
SERVICE_NAME = "InstaBridge"


class CredentialManager:
    """Manages credentials securely using system keychain."""
    
    def __init__(self, use_keyring: bool = True):
        """Initialize credential manager.
        
        Args:
            use_keyring: If True, use system keychain. If False, fall back to .env
        """
        self.use_keyring = use_keyring and KEYRING_AVAILABLE
        
        if use_keyring and not KEYRING_AVAILABLE:
            print("⚠️  Keyring not available. Falling back to .env file (less secure).")
            print("   Install keyring for secure storage: pip install keyring")
    
    def get_credential(self, key: str, username: Optional[str] = None) -> Optional[str]:
        """Get credential from keychain or environment.
        
        Args:
            key: Credential key (e.g., 'IG_PASSWORD')
            username: Username for the credential (optional, used for keychain)
        
        Returns:
            Credential value or None if not found
        """
        if self.use_keyring:
            # Try keychain first
            if username:
                value = keyring.get_password(SERVICE_NAME, f"{key}:{username}")
            else:
                value = keyring.get_password(SERVICE_NAME, key)
            
            if value:
                return value
        
        # Fall back to environment variable
        return os.getenv(key)
    
    def set_credential(self, key: str, value: str, username: Optional[str] = None) -> None:
        """Store credential in keychain.
        
        Args:
            key: Credential key (e.g., 'IG_PASSWORD')
            value: Credential value
            username: Username for the credential (optional)
        """
        if self.use_keyring:
            if username:
                keyring.set_password(SERVICE_NAME, f"{key}:{username}", value)
            else:
                keyring.set_password(SERVICE_NAME, key, value)
            print(f"✅ Stored '{key}' in system keychain")
        else:
            print(f"⚠️  Keyring not available. Please set {key} in .env file")
    
    def delete_credential(self, key: str, username: Optional[str] = None) -> None:
        """Delete credential from keychain.
        
        Args:
            key: Credential key
            username: Username for the credential (optional)
        """
        if self.use_keyring:
            try:
                if username:
                    keyring.delete_password(SERVICE_NAME, f"{key}:{username}")
                else:
                    keyring.delete_password(SERVICE_NAME, key)
                print(f"✅ Deleted '{key}' from system keychain")
            except keyring.errors.PasswordDeleteError:
                print(f"⚠️  '{key}' not found in keychain")
        else:
            print(f"⚠️  Keyring not available. Please remove {key} from .env file")
    
    def get_ig_credentials(self) -> tuple[str, str]:
        """Get Instagram credentials.
        
        Returns:
            (username, password) tuple
        
        Raises:
            ValueError: If credentials not found
        """
        username = self.get_credential("IG_USERNAME")
        if not username:
            raise ValueError("IG_USERNAME not found in keychain or .env")
        
        password = self.get_credential("IG_PASSWORD", username)
        if not password:
            raise ValueError(f"IG_PASSWORD not found in keychain or .env for user '{username}'")
        
        return username, password
    
    def interactive_setup(self) -> None:
        """Interactive setup wizard for credentials."""
        print("\n" + "="*60)
        print("🔐 InstaBridge Credential Setup")
        print("="*60)
        
        if not KEYRING_AVAILABLE:
            print("\n⚠️  WARNING: Keyring not available!")
            print("Credentials will be stored in .env file (LESS SECURE)")
            print("\nTo enable secure storage:")
            print("  pip install keyring")
            print("\nPress Ctrl+C to cancel or Enter to continue with .env...")
            try:
                input()
            except KeyboardInterrupt:
                print("\nSetup cancelled.")
                return
        else:
            print("\n✅ Using system keychain for secure storage")
            print("Credentials will be encrypted by your operating system")
        
        print("\n" + "-"*60)
        print("Instagram Credentials (use throwaway account!)")
        print("-"*60)
        
        ig_username = input("Instagram username: ").strip()
        if not ig_username:
            print("❌ Username cannot be empty")
            return
        
        ig_password = getpass.getpass("Instagram password: ")
        if not ig_password:
            print("❌ Password cannot be empty")
            return
        
        # Confirm password
        ig_password_confirm = getpass.getpass("Confirm password: ")
        if ig_password != ig_password_confirm:
            print("❌ Passwords don't match")
            return
        
        print("\n" + "-"*60)
        print("WhatsApp Contact (who receives forwarded content)")
        print("-"*60)
        
        wa_contact = input("WhatsApp contact name: ").strip()
        wa_phone = input("WhatsApp phone (international format, e.g., 491701234567): ").strip()
        
        print("\n" + "-"*60)
        print("Optional: WhatsApp Report Contact (for unfollow alerts)")
        print("-"*60)
        
        wa_report_contact = input("Report contact name (or press Enter to skip): ").strip()
        wa_report_phone = input("Report phone (or press Enter to skip): ").strip()
        
        # Store credentials
        print("\n" + "-"*60)
        print("Saving credentials...")
        print("-"*60)
        
        if self.use_keyring:
            # Store in keychain
            self.set_credential("IG_USERNAME", ig_username)
            self.set_credential("IG_PASSWORD", ig_password, ig_username)
            self.set_credential("WA_CONTENT_CONTACT_NAME", wa_contact)
            self.set_credential("WA_CONTENT_PHONE", wa_phone)
            
            if wa_report_contact:
                self.set_credential("WA_REPORT_CONTACT_NAME", wa_report_contact)
            if wa_report_phone:
                self.set_credential("WA_REPORT_PHONE", wa_report_phone)
            
            print("\n✅ All credentials stored securely in system keychain!")
            print("\n📝 Your .env file can now be empty (or contain only non-sensitive settings)")
            print("   Credentials are encrypted and managed by your OS")
        else:
            # Fall back to .env
            print("\n⚠️  Please add these to your .env file:")
            print("\nIG_USERNAME=" + ig_username)
            print("IG_PASSWORD=<your_password>")
            print("WA_CONTENT_CONTACT_NAME=" + wa_contact)
            print("WA_CONTENT_PHONE=" + wa_phone)
            if wa_report_contact:
                print("WA_REPORT_CONTACT_NAME=" + wa_report_contact)
            if wa_report_phone:
                print("WA_REPORT_PHONE=" + wa_report_phone)
        
        print("\n✅ Setup complete!")
        print("\n🔒 Security Tips:")
        print("   - Never commit .env to git (already in .gitignore)")
        print("   - Use throwaway accounts only")
        print("   - See docs/SECURITY_BEST_PRACTICES.md for more")


def load_credentials_safely() -> dict[str, str]:
    """Load credentials from keychain or .env file.
    
    Returns:
        Dictionary of credential key-value pairs
    
    Raises:
        ValueError: If required credentials not found
    """
    manager = CredentialManager(use_keyring=True)
    
    # Get Instagram credentials
    ig_username, ig_password = manager.get_ig_credentials()
    
    # Get WhatsApp contact info (non-sensitive, can stay in .env)
    wa_content_contact = manager.get_credential("WA_CONTENT_CONTACT_NAME")
    wa_content_phone = manager.get_credential("WA_CONTENT_PHONE")
    
    # Optional report contact
    wa_report_contact = manager.get_credential("WA_REPORT_CONTACT_NAME") or wa_content_contact
    wa_report_phone = manager.get_credential("WA_REPORT_PHONE") or ""
    
    # Optional message prefix
    message_prefix = manager.get_credential("MESSAGE_PREFIX") or "New from Instagram:"
    
    if not wa_content_contact:
        raise ValueError("WA_CONTENT_CONTACT_NAME not found. Run: python -m src.credentials")
    
    return {
        "IG_USERNAME": ig_username,
        "IG_PASSWORD": ig_password,
        "WA_CONTENT_CONTACT_NAME": wa_content_contact,
        "WA_CONTENT_PHONE": wa_content_phone or "",
        "WA_REPORT_CONTACT_NAME": wa_report_contact,
        "WA_REPORT_PHONE": wa_report_phone,
        "MESSAGE_PREFIX": message_prefix,
    }


def main():
    """Run interactive credential setup."""
    manager = CredentialManager(use_keyring=True)
    manager.interactive_setup()


if __name__ == "__main__":
    main()
