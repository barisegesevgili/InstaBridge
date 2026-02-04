"""Custom exception classes for InstaBridge.

This module defines exception hierarchy for better error handling and categorization.
"""


class InstaBridgeError(Exception):
    """Base exception for all InstaBridge errors."""
    
    pass


class ConfigurationError(InstaBridgeError):
    """Configuration or environment setup error."""
    
    pass


class TransientError(InstaBridgeError):
    """Temporary error that may resolve on retry.
    
    Examples: Network timeouts, rate limiting, temporary API unavailability.
    """
    
    def __init__(self, message: str, retry_after_seconds: int = 60):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class PermanentError(InstaBridgeError):
    """Permanent error that won't resolve with retry.
    
    Examples: Invalid credentials, missing permissions, ToS violations.
    """
    
    pass


class InstagramError(InstaBridgeError):
    """Instagram API related errors."""
    
    pass


class InstagramRateLimitError(TransientError):
    """Instagram rate limit exceeded."""
    
    def __init__(self, message: str = "Instagram rate limit exceeded", retry_after_seconds: int = 600):
        super().__init__(message, retry_after_seconds)


class InstagramAuthenticationError(PermanentError):
    """Instagram authentication failed."""
    
    pass


class WhatsAppError(InstaBridgeError):
    """WhatsApp automation related errors."""
    
    pass


class WhatsAppConnectionError(TransientError):
    """WhatsApp Web connection error."""
    
    def __init__(self, message: str = "WhatsApp Web connection failed", retry_after_seconds: int = 30):
        super().__init__(message, retry_after_seconds)


class WhatsAppSendError(TransientError):
    """Failed to send message via WhatsApp."""
    
    pass


class StateError(InstaBridgeError):
    """State persistence or loading error."""
    
    pass


class ValidationError(PermanentError):
    """Data validation error."""
    
    pass
