import pytest
from app.integrations.oauth import OAuthProvider
from app.core.models import Platform

@pytest.mark.anyio
async def test_state_sign_and_validate(monkeypatch):
    monkeypatch.setenv("OAUTH_STATE_SECRET", "supersecret")
    s = OAuthProvider()
    st = s.create_state("11111111-1111-1111-1111-111111111111", Platform.facebook)
    info = await s.validate_state(st)
    assert info["platform"] == "facebook"
