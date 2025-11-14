# app/core/crypto.py
from cryptography.fernet import Fernet, InvalidToken
import base64, os

class TokenEncryptor:
    def __init__(self, key_b64: str):
        self._fernet = Fernet(key_b64.encode())

    def enc(self, s: str) -> str:
        return self._fernet.encrypt(s.encode()).decode()

    def dec(self, s: str) -> str:
        return self._fernet.decrypt(s.encode()).decode()

def load_encryptor(master_key: str | None = None) -> TokenEncryptor:
    """
    Load encryptor with master key.
    Args:
        master_key: Master secret key. If not provided, will try to load from environment.
    """
    key = master_key or os.environ.get("MASTER_SECRET_KEY")
    if not key:
        raise RuntimeError("MASTER_SECRET_KEY missing")
    # accept both raw key and base64-encoded
    try:
        base64.urlsafe_b64decode(key.encode())
    except Exception:
        key = base64.urlsafe_b64encode(key.encode()).decode()
    return TokenEncryptor(key)
