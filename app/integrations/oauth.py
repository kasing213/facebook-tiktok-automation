# app/integrations/oauth.py
from __future__ import annotations
import base64, hmac, hashlib, time, urllib.parse, datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, Optional
import httpx
from app.core.models import AdToken, Platform
from app.core.crypto import load_encryptor
from app.core.config import get_settings

# ——— state helpers (HMAC-signed, optional Redis) ———
class StateStore:
    async def put(self, key: str, val: str, ttl_s: int): ...
    async def get(self, key: str) -> Optional[str]: ...

class MemoryState(StateStore):
    _store: dict[str, tuple[str, float]] = {}
    async def put(self, k, v, ttl_s: int):
        self._store[k] = (v, time.time() + ttl_s)
    async def get(self, k):
        v = self._store.get(k)
        if not v: return None
        if v[1] < time.time(): self._store.pop(k, None); return None
        self._store.pop(k, None)  # one-time use
        return v[0]

try:
    import redis.asyncio as aioredis
    class RedisState(StateStore):
        def __init__(self, url: str): self.r = aioredis.from_url(url, decode_responses=True)
        async def put(self, k, v, ttl_s: int): await self.r.setex(f"oauth:{k}", ttl_s, v)
        async def get(self, k): 
            key=f"oauth:{k}"; p = await self.r.get(key); 
            if p: await self.r.delete(key)
            return p
except Exception:
    RedisState = None

# ——— platform adapters ———
@dataclass
class OAuthResult:
    platform: Platform
    account_ref: str | None
    access_token: str
    refresh_token: str | None
    scope: str | None
    expires_at: dt.datetime | None
    raw: Dict[str, Any]

class OAuthProvider:
    def __init__(self, s=None):
        self.s = s or get_settings()
        self.enc = load_encryptor()
        self.state_store: StateStore = (
            RedisState(self.s.REDIS_URL) if self.s.REDIS_URL and RedisState else MemoryState()
        )

    # ——— utils ———
    def _sign(self, payload: str) -> str:
        mac = hmac.new(self.s.OAUTH_STATE_SECRET.get_secret_value().encode(), payload.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(mac).decode().rstrip("=")

    def create_state(self, tenant_id: str, platform: Platform) -> str:
        # embed tenant + ts; put one-time copy in store for replay protection
        payload = f"{tenant_id}.{platform.value}.{int(time.time())}"
        sig = self._sign(payload)
        key = f"{payload}.{sig}"
        return key

    async def validate_state(self, state: str) -> dict:
        # (optional) look up in store (one-time)
        stored = await self.state_store.get(state)
        # accept both modes: signed-only or redis+signed
        parts = state.split(".")
        assert len(parts) >= 4, "bad_state"
        tenant_id, platform, ts, sig = parts[0], parts[1], parts[2], parts[-1]
        payload = ".".join(parts[:-1])
        if self._sign(payload) != sig:
            raise ValueError("state_sig_mismatch")
        if (time.time() - int(ts)) > 900:
            raise ValueError("state_expired")   # 15 minutes
        return {"tenant_id": tenant_id, "platform": platform}

class FacebookOAuth(OAuthProvider):
    auth_base = "https://www.facebook.com/v23.0/dialog/oauth"
    token_url = "https://graph.facebook.com/v23.0/oauth/access_token"
    exchange_url = "https://graph.facebook.com/v23.0/oauth/access_token"  # for long-lived exchange

    def auth_url(self, tenant_id: str) -> str:
        state = self.create_state(tenant_id, Platform.facebook)
        q = {
            "client_id": self.s.FB_APP_ID,
            "redirect_uri": f"{self.s.BASE_URL}/oauth/facebook/callback",
            "state": state,
            "response_type": "code",
            "scope": self.s.FB_SCOPES,
        }
        return f"{self.auth_base}?{urllib.parse.urlencode(q)}"

    async def exchange(self, code: str) -> OAuthResult:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(self.token_url, params={
                "client_id": self.s.FB_APP_ID,
                "client_secret": self.s.FB_APP_SECRET.get_secret_value(),
                "redirect_uri": f"{self.s.BASE_URL}/oauth/facebook/callback",
                "code": code,
            })
            r.raise_for_status()
            data = r.json()
        short = data["access_token"]
        # Optional: extend to long-lived (≈ 60 days)
        async with httpx.AsyncClient(timeout=30) as c:
            rr = await c.get(self.exchange_url, params={
                "grant_type": "fb_exchange_token",
                "client_id": self.s.FB_APP_ID,
                "client_secret": self.s.FB_APP_SECRET.get_secret_value(),
                "fb_exchange_token": short,
            })
            rr.raise_for_status()
            x = rr.json()
        # FB does not issue refresh_token for Login flow; re-auth when nearing expiry.
        expires_at = (
            dt.datetime.utcnow() + dt.timedelta(seconds=int(x.get("expires_in", 0)))
            if x.get("expires_in") else None
        )
        return OAuthResult(
            platform=Platform.facebook,
            account_ref=None,                      # fill later after /me or adaccount lookup
            access_token=x["access_token"],
            refresh_token=None,
            scope=self.s.FB_SCOPES,
            expires_at=expires_at,
            raw={"short": data, "long": x},
        )

class TikTokOAuth(OAuthProvider):
    auth_base = "https://www.tiktok.com/v2/auth/authorize/"
    token_url = "https://open.tiktokapis.com/v2/oauth/token/"

    def auth_url(self, tenant_id: str) -> str:
        state = self.create_state(tenant_id, Platform.tiktok)
        q = {
            "client_key": self.s.TIKTOK_CLIENT_KEY,
            "response_type": "code",
            "scope": self.s.TIKTOK_SCOPES,
            "redirect_uri": f"{self.s.BASE_URL}/oauth/tiktok/callback",
            "state": state,
        }
        return f"{self.auth_base}?{urllib.parse.urlencode(q)}"

    async def exchange(self, code: str) -> OAuthResult:
        form = {
            "client_key": self.s.TIKTOK_CLIENT_KEY,
            "client_secret": self.s.TIKTOK_CLIENT_SECRET.get_secret_value(),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{self.s.BASE_URL}/oauth/tiktok/callback",
        }
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(self.token_url, data=form, headers={"Content-Type":"application/x-www-form-urlencoded"})
            r.raise_for_status()
            x = r.json()
        expires_at = dt.datetime.utcnow() + dt.timedelta(seconds=int(x.get("expires_in", 0)))
        return OAuthResult(
            platform=Platform.tiktok,
            account_ref=x.get("open_id"),
            access_token=x["access_token"],
            refresh_token=x.get("refresh_token"),
            scope=x.get("scope"),
            expires_at=expires_at,
            raw=x,
        )
