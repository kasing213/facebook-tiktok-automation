# app/jobs/runners.py (add a refresher)
import datetime as dt, httpx
from sqlalchemy.orm import Session
from app.core.models import AdToken, Platform
from app.core.crypto import load_encryptor
from app.core.config import get_settings

async def maybe_refresh_tokens(db: Session):
    s = get_settings(); enc = load_encryptor()
    soon = dt.datetime.utcnow() + dt.timedelta(hours=12)
    rows = db.query(AdToken).all()
    for t in rows:
        if not t.expires_at or t.expires_at > soon: continue
        if t.platform == Platform.tiktok and t.refresh_token_enc:
            refresh_token = enc.dec(t.refresh_token_enc)
            form = {
                "client_key": s.TIKTOK_CLIENT_KEY,
                "client_secret": s.TIKTOK_CLIENT_SECRET.get_secret_value(),
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
            try:
                async with httpx.AsyncClient(timeout=30) as c:
                    r = await c.post("https://open.tiktokapis.com/v2/oauth/token/", data=form)
                    r.raise_for_status()
                    x = r.json()
                t.access_token_enc = enc.enc(x["access_token"])
                if "refresh_token" in x and x["refresh_token"]:
                    t.refresh_token_enc = enc.enc(x["refresh_token"])
                t.expires_at = dt.datetime.utcnow() + dt.timedelta(seconds=int(x.get("expires_in",0)))
                t.scope = x.get("scope", t.scope)
                db.add(t); db.commit()
            except httpx.HTTPError:
                # leave as-is; next run will try again
                pass
        elif t.platform == Platform.facebook:
            # no refresh flow; mark for re-auth or send a Telegram/Email reminder
            pass
