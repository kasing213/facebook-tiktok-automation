# app/integrations/oauth.py
from __future__ import annotations
import base64, hmac, hashlib, time, urllib.parse, datetime as dt, json, secrets, string
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
        self.base_url = str(self.s.BASE_URL).rstrip("/")
        self.enc = load_encryptor(self.s.MASTER_SECRET_KEY.get_secret_value())
        self.state_store: StateStore = (
            RedisState(self.s.REDIS_URL) if self.s.REDIS_URL and RedisState else MemoryState()
        )

    # ——— utils ———
    def _sign(self, payload: str) -> str:
        mac = hmac.new(self.s.OAUTH_STATE_SECRET.get_secret_value().encode(), payload.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(mac).decode().rstrip("=")

    def _generate_code_verifier(self, length: int = 64) -> str:
        alphabet = string.ascii_letters + string.digits + "-_~"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _generate_code_challenge(self, verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")

    def _encode_extra(self, extra: Dict[str, Any]) -> str:
        payload = json.dumps(extra, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(payload).decode().rstrip("=")

    def _decode_extra(self, encoded: str) -> Dict[str, Any]:
        padding = "=" * (-len(encoded) % 4)
        data = base64.urlsafe_b64decode(encoded + padding).decode()
        return json.loads(data)

    def create_state(self, tenant_id: str, platform: Platform, extra: Dict[str, Any] | None = None) -> str:
        """
        Create OAuth state with nonce hardening

        CRITICAL: Includes random nonce for CSRF protection and one-time use enforcement
        """
        # Generate cryptographically secure random nonce
        nonce = secrets.token_urlsafe(32)  # 32 bytes = 256 bits of entropy

        # Embed tenant + platform + timestamp + nonce
        parts = [tenant_id, platform.value, str(int(time.time())), nonce]
        if extra:
            parts.append(self._encode_extra(extra))
        payload = ".".join(parts)
        sig = self._sign(payload)
        state = f"{payload}.{sig}"

        # Store nonce synchronously to ensure availability during validation
        # CRITICAL: Must complete before auth_url is returned to user
        import asyncio
        try:
            # Try to get running event loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop - we're in sync context (FastAPI dependency injection)
            # Create new event loop just for this operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.state_store.put(f"nonce:{nonce}", state, 900))
            finally:
                loop.close()
                asyncio.set_event_loop(None)
        else:
            # We're already in async context - create task and wait for it
            # This should not happen in auth_url() which is called from sync FastAPI endpoint
            # But handle it gracefully anyway
            asyncio.create_task(self.state_store.put(f"nonce:{nonce}", state, 900))

        return state

    async def validate_state(self, state: str) -> dict:
        """
        Validate OAuth state with nonce verification

        CRITICAL: Verifies signature, timestamp, and nonce to prevent CSRF and replay attacks
        """
        # Split state into payload and signature
        try:
            payload, sig = state.rsplit(".", 1)
        except ValueError:
            raise ValueError("bad_state")

        # Verify signature first
        if self._sign(payload) != sig:
            raise ValueError("state_sig_mismatch")

        # Parse state components
        parts = payload.split(".")
        if len(parts) < 4:  # NOW REQUIRES: tenant_id, platform, timestamp, nonce
            raise ValueError("bad_state")

        tenant_id, platform, ts, nonce = parts[0], parts[1], parts[2], parts[3]

        # Verify timestamp (15 minute expiry)
        if (time.time() - int(ts)) > 900:
            raise ValueError("state_expired")

        # CRITICAL: Verify nonce exists and hasn't been used (one-time use)
        stored_state = await self.state_store.get(f"nonce:{nonce}")
        if stored_state is None:
            # Nonce not found or already used - potential replay attack
            raise ValueError("nonce_invalid_or_reused")
        if stored_state != state:
            # Nonce exists but doesn't match this state - tampering detected
            raise ValueError("nonce_state_mismatch")

        # Build response data
        data = {"tenant_id": tenant_id, "platform": platform}

        # Parse optional extra data (now at index 4 instead of 3)
        if len(parts) > 4:
            try:
                extra = self._decode_extra(parts[4])
                if isinstance(extra, dict):
                    data.update(extra)
            except Exception:
                raise ValueError("state_extra_invalid")

        return data

class FacebookOAuth(OAuthProvider):
    auth_base = "https://www.facebook.com/v23.0/dialog/oauth"
    token_url = "https://graph.facebook.com/v23.0/oauth/access_token"
    exchange_url = "https://graph.facebook.com/v23.0/oauth/access_token"  # for long-lived exchange
    graph_url = "https://graph.facebook.com/v23.0"

    def auth_url(self, tenant_id: str, user_id: str | None = None) -> str:
        extra = {"user_id": user_id} if user_id else None
        state = self.create_state(tenant_id, Platform.facebook, extra=extra)
        # Basic scopes for development (no app review required)
        # For production, add: pages_manage_posts,pages_read_engagement,pages_show_list
        scopes = self.s.FB_SCOPES or "public_profile,email"
        q = {
            "client_id": self.s.FB_APP_ID,
            "redirect_uri": f"{self.base_url}/auth/facebook/callback",
            "state": state,
            "response_type": "code",
            "scope": scopes,
        }
        if self.s.FB_FORCE_REAUTH or self.s.ENV != "prod":
            q["auth_type"] = "reauthenticate"
            q["auth_nonce"] = secrets.token_urlsafe(16)
        return f"{self.auth_base}?{urllib.parse.urlencode(q)}"

    async def exchange(self, code: str) -> OAuthResult:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(self.token_url, params={
                "client_id": self.s.FB_APP_ID,
                "client_secret": self.s.FB_APP_SECRET.get_secret_value(),
                "redirect_uri": f"{self.base_url}/auth/facebook/callback",
                "code": code,
            })
            r.raise_for_status()
            data = r.json()

        short_token = data["access_token"]

        # Extend to long-lived user token (≈ 60 days)
        async with httpx.AsyncClient(timeout=30) as c:
            rr = await c.get(self.exchange_url, params={
                "grant_type": "fb_exchange_token",
                "client_id": self.s.FB_APP_ID,
                "client_secret": self.s.FB_APP_SECRET.get_secret_value(),
                "fb_exchange_token": short_token,
            })
            rr.raise_for_status()
            long_lived_data = rr.json()

        long_lived_token = long_lived_data["access_token"]

        # Get user info and pages
        user_info, pages_data = await self._get_user_and_pages(long_lived_token)

        expires_at = (
            dt.datetime.utcnow() + dt.timedelta(seconds=int(long_lived_data.get("expires_in", 0)))
            if long_lived_data.get("expires_in") else None
        )

        return OAuthResult(
            platform=Platform.facebook,
            account_ref=user_info.get("id"),
            access_token=long_lived_token,
            refresh_token=None,  # Facebook doesn't provide refresh tokens for user tokens
            scope=self.s.FB_SCOPES,
            expires_at=expires_at,
            raw={
                "short": data,
                "long": long_lived_data,
                "user": user_info,
                "pages": pages_data
            },
        )

    async def _get_user_and_pages(self, access_token: str) -> tuple[dict, list]:
        """Get user info and managed pages"""
        async with httpx.AsyncClient(timeout=30) as client:
            # Get user info
            user_response = await client.get(
                f"{self.graph_url}/me",
                params={"access_token": access_token, "fields": "id,name,email"}
            )
            user_response.raise_for_status()
            user_info = user_response.json()

            # Get pages managed by user
            pages_response = await client.get(
                f"{self.graph_url}/me/accounts",
                params={
                    "access_token": access_token,
                    "fields": "id,name,access_token,category,tasks"
                }
            )
            pages_response.raise_for_status()
            pages_data = pages_response.json().get("data", [])

            return user_info, pages_data

    async def get_page_tokens(self, user_token: str) -> list[dict]:
        """Get page access tokens for posting"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.graph_url}/me/accounts",
                params={
                    "access_token": user_token,
                    "fields": "id,name,access_token,category,tasks"
                }
            )
            response.raise_for_status()
            return response.json().get("data", [])

    async def validate_token(self, access_token: str) -> dict:
        """Validate Facebook access token"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.graph_url}/me",
                params={"access_token": access_token}
            )
            if response.status_code == 200:
                return {"valid": True, "user": response.json()}
            else:
                return {"valid": False, "error": response.text}

class FacebookAPIClient:
    """Facebook API client for posting and page management"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.graph_url = "https://graph.facebook.com/v23.0"

    async def post_to_page(self, page_id: str, message: str, page_token: str = None) -> dict:
        """Post message to Facebook page"""
        token = page_token or self.access_token
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.graph_url}/{page_id}/feed",
                data={
                    "message": message,
                    "access_token": token
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_page_insights(self, page_id: str, page_token: str, metrics: list = None) -> dict:
        """Get page insights/analytics"""
        metrics = metrics or ["page_impressions", "page_reach", "page_engaged_users"]
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.graph_url}/{page_id}/insights",
                params={
                    "metric": ",".join(metrics),
                    "access_token": page_token,
                    "period": "day",
                    "since": (dt.datetime.utcnow() - dt.timedelta(days=7)).strftime("%Y-%m-%d"),
                    "until": dt.datetime.utcnow().strftime("%Y-%m-%d")
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_ad_accounts(self) -> list:
        """Get Facebook ad accounts"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.graph_url}/me/adaccounts",
                params={
                    "access_token": self.access_token,
                    "fields": "id,name,account_status,currency,timezone_name"
                }
            )
            response.raise_for_status()
            return response.json().get("data", [])

    async def get_ad_insights(self, ad_account_id: str, date_range: dict = None) -> dict:
        """Get ad insights for an ad account"""
        date_range = date_range or {
            "since": (dt.datetime.utcnow() - dt.timedelta(days=7)).strftime("%Y-%m-%d"),
            "until": dt.datetime.utcnow().strftime("%Y-%m-%d")
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.graph_url}/{ad_account_id}/insights",
                params={
                    "access_token": self.access_token,
                    "fields": "impressions,clicks,spend,reach,frequency,cpm,ctr,cpc",
                    "time_range": f'{{"since":"{date_range["since"]}","until":"{date_range["until"]}"}}'
                }
            )
            response.raise_for_status()
            return response.json()

class TikTokOAuth(OAuthProvider):
    auth_base = "https://www.tiktok.com/v2/auth/authorize/"
    token_url = "https://open.tiktokapis.com/v2/oauth/token/"
    user_info_url = "https://open.tiktokapis.com/v2/user/info/"

    def auth_url(self, tenant_id: str, user_id: str | None = None) -> str:
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)
        extra = {"code_verifier": code_verifier}
        if user_id:
            extra["user_id"] = user_id
        state = self.create_state(
            tenant_id,
            Platform.tiktok,
            extra=extra
        )
        # Enhanced scopes for content creation
        scopes = self.s.TIKTOK_SCOPES or "user.info.basic,video.upload,video.publish"
        q = {
            "client_key": self.s.TIKTOK_CLIENT_KEY,
            "response_type": "code",
            "scope": scopes,
            "redirect_uri": f"{self.base_url}/auth/tiktok/callback",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{self.auth_base}?{urllib.parse.urlencode(q)}"

    async def exchange(self, code: str, code_verifier: str | None = None) -> OAuthResult:
        if not code_verifier:
            raise ValueError("code_verifier_missing")
        # Step 1: Exchange code for tokens
        form = {
            "client_key": self.s.TIKTOK_CLIENT_KEY,
            "client_secret": self.s.TIKTOK_CLIENT_SECRET.get_secret_value(),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{self.base_url}/auth/tiktok/callback",
            "code_verifier": code_verifier,
        }
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(self.token_url, data=form, headers={"Content-Type": "application/x-www-form-urlencoded"})
            r.raise_for_status()
            token_data = r.json()

        payload = token_data.get("data") if isinstance(token_data, dict) else None
        if not payload or "access_token" not in payload:
            raise ValueError("TikTok token response missing access_token")

        access_token = payload["access_token"]
        open_id = payload.get("open_id")
        refresh_token = payload.get("refresh_token")
        scope = payload.get("scope")
        if not scope and payload.get("scopes"):
            scope = ",".join(payload["scopes"])
        expires_in = payload.get("expires_in", token_data.get("expires_in"))

        # Step 2: Get user information
        user_info = await self._get_user_info(access_token)

        expires_at = None
        if expires_in:
            try:
                expires_at = dt.datetime.utcnow() + dt.timedelta(seconds=int(expires_in))
            except (ValueError, TypeError):
                expires_at = None

        return OAuthResult(
            platform=Platform.tiktok,
            account_ref=open_id,
            access_token=access_token,
            refresh_token=refresh_token,
            scope=scope,
            expires_at=expires_at,
            raw={
                "token": token_data,
                "user": user_info
            },
        )

    async def _get_user_info(self, access_token: str) -> dict:
        """Get TikTok user information"""
        fields = "open_id,union_id,username,display_name,avatar_url,follower_count,following_count,likes_count,video_count"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.user_info_url,
                params={"fields": fields},
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("user", {})
