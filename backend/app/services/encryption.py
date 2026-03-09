import base64
import hashlib

from cryptography.fernet import Fernet


def _derive_key(secret: str) -> bytes:
    """Derive a 32-byte Fernet key from an arbitrary secret string."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_value(plaintext: str, secret: str) -> str:
    """Encrypt a plaintext string using Fernet symmetric encryption."""
    fernet = Fernet(_derive_key(secret))
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(encrypted: str, secret: str) -> str:
    """Decrypt an encrypted string using Fernet symmetric encryption."""
    fernet = Fernet(_derive_key(secret))
    return fernet.decrypt(encrypted.encode("utf-8")).decode("utf-8")
