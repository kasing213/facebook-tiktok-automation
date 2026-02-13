# app/core/crypto.py
import logging
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
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


# Module-level cache: ensures PBKDF2 (100K iterations) runs at most once per process
_cached_encryptor: TokenEncryptor | None = None
_cached_key_source: str | None = None


def load_encryptor(master_key: str | None = None) -> TokenEncryptor:
    """
    Load encryptor with master key. Results are cached at module level
    so PBKDF2 derivation only runs once per process.

    Args:
        master_key: Master secret key. If not provided, will try to load from environment.

    Returns:
        TokenEncryptor instance

    Raises:
        KeyConfigurationError: If master key is missing or invalid
    """
    global _cached_encryptor, _cached_key_source

    key = master_key or os.environ.get("MASTER_SECRET_KEY")
    if not key:
        logger.error("MASTER_SECRET_KEY not found in environment or parameters")
        raise KeyConfigurationError("MASTER_SECRET_KEY missing. Please set this environment variable.")

    # Return cached encryptor if the key hasn't changed
    if _cached_encryptor is not None and _cached_key_source == key:
        return _cached_encryptor

    # Check if key is already a valid Fernet key (32 bytes base64-encoded = 44 chars with padding)
    try:
        decoded = base64.urlsafe_b64decode(key.encode())
        if len(decoded) == 32:
            # Valid Fernet key, use as-is
            logger.info("Using provided Fernet key")
            encryptor = TokenEncryptor(key)
            _cached_encryptor = encryptor
            _cached_key_source = key
            return encryptor
    except Exception:
        pass

    # Key is not a valid Fernet key - derive one using PBKDF2
    # This ensures any input string produces a valid 32-byte key
    logger.info("Deriving Fernet key from MASTER_SECRET_KEY using PBKDF2")

    # Use fixed salt for deterministic key derivation (same input = same key)
    # This is acceptable because MASTER_SECRET_KEY should be high-entropy
    salt = b"facebook-automation-salt-v1"

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))

    try:
        encryptor = TokenEncryptor(derived_key.decode())
        _cached_encryptor = encryptor
        _cached_key_source = key
        return encryptor
    except KeyConfigurationError:
        raise
    except Exception as e:
        logger.error(f"Failed to create encryptor: {e}")
        raise KeyConfigurationError(f"Failed to initialize encryption: {str(e)}")
