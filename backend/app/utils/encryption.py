import base64
import hashlib
import os
from cryptography.fernet import Fernet

def _get_fernet():
    # Derive a 32-byte URL-safe base64 key from SECURITY_PASSWORD_SALT
    salt = os.getenv("SECURITY_PASSWORD_SALT", "default-salt-key-do-not-use-in-prod")
    key = base64.urlsafe_b64encode(hashlib.sha256(salt.encode()).digest())
    return Fernet(key)

def encrypt_token(token: str) -> str:
    """Encrypt a token using Fernet symmetric encryption."""
    if not token:
        return ""
    try:
        fernet = _get_fernet()
        return fernet.encrypt(token.encode()).decode()
    except Exception as e:
        print(f"Token encryption failed: {e}")
        return ""

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token using Fernet symmetric encryption."""
    if not encrypted_token:
        return ""
    try:
        fernet = _get_fernet()
        return fernet.decrypt(encrypted_token.encode()).decode()
    except Exception as e:
        print(f"Token decryption failed: {e}")
        return ""
