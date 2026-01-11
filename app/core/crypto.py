# app/core/crypto.py
import logging
from cryptography.fernet import Fernet, InvalidToken
import base64
import os

logger = logging.getLogger(__name__)


class CryptoError(Exception):
    """Base exception for cryptography errors"""
    pass


class EncryptionError(CryptoError):
    """Raised when encryption fails"""
    pass


class DecryptionError(CryptoError):
    """Raised when decryption fails (e.g., invalid token or key mismatch)"""
    pass


class KeyConfigurationError(CryptoError):
    """Raised when encryption key is missing or invalid"""
    pass


class TokenEncryptor:
    def __init__(self, key_b64: str):
        try:
            self._fernet = Fernet(key_b64.encode())
        except Exception as e:
            logger.error(f"Failed to initialize Fernet with provided key: {e}")
            raise KeyConfigurationError(f"Invalid encryption key format: {str(e)}")

    def enc(self, s: str) -> str:
        """
        Encrypt a string.

        Args:
            s: Plain text string to encrypt

        Returns:
            Encrypted string

        Raises:
            EncryptionError: If encryption fails
        """
        if s is None:
            raise EncryptionError("Cannot encrypt None value")
        try:
            return self._fernet.encrypt(s.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {str(e)}")

    def dec(self, s: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            s: Encrypted string to decrypt

        Returns:
            Decrypted plain text string

        Raises:
            DecryptionError: If decryption fails (invalid token, key mismatch, etc.)
        """
        if s is None:
            raise DecryptionError("Cannot decrypt None value")
        try:
            return self._fernet.decrypt(s.encode()).decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token (possibly encrypted with different key)")
            raise DecryptionError("Invalid or corrupted encrypted data. Token may have been encrypted with a different key.")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise DecryptionError(f"Failed to decrypt data: {str(e)}")


def load_encryptor(master_key: str | None = None) -> TokenEncryptor:
    """
    Load encryptor with master key.

    Args:
        master_key: Master secret key. If not provided, will try to load from environment.

    Returns:
        TokenEncryptor instance

    Raises:
        KeyConfigurationError: If master key is missing or invalid
    """
    key = master_key or os.environ.get("MASTER_SECRET_KEY")
    if not key:
        logger.error("MASTER_SECRET_KEY not found in environment or parameters")
        raise KeyConfigurationError("MASTER_SECRET_KEY missing. Please set this environment variable.")

    # accept both raw key and base64-encoded
    try:
        base64.urlsafe_b64decode(key.encode())
    except Exception:
        # If decoding fails, it's likely a raw key - encode it
        key = base64.urlsafe_b64encode(key.encode()).decode()

    try:
        return TokenEncryptor(key)
    except KeyConfigurationError:
        raise
    except Exception as e:
        logger.error(f"Failed to create encryptor: {e}")
        raise KeyConfigurationError(f"Failed to initialize encryption: {str(e)}")
