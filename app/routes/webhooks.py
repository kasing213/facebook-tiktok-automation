# app/routes/webhooks.py
"""
Webhook endpoints for Facebook and TikTok real-time updates.

These endpoints handle incoming webhook events from Facebook and TikTok platforms,
including subscription verification and event processing.
"""
import hmac
import hashlib
import json
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query, Request, Header, Response
from fastapi.responses import PlainTextResponse

from app.deps import LoggerDep, SettingsDep
from app.core.db import get_db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ============================================================================
# Facebook Webhooks
# ============================================================================

@router.get("/facebook")
async def facebook_webhook_verify(
    request: Request,
    settings: SettingsDep,
    logger: LoggerDep,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Facebook webhook verification endpoint.

    Facebook sends a GET request to verify webhook subscription.
    You must respond with the hub.challenge value to complete verification.

    Setup in Facebook App:
    1. Go to Facebook App Dashboard > Webhooks
    2. Click "Add Subscription"
    3. Enter Callback URL: https://your-ngrok-url.ngrok.io/webhooks/facebook
    4. Enter Verify Token: (set in FACEBOOK_WEBHOOK_VERIFY_TOKEN env var)
    5. Select webhook fields you want to subscribe to
    """
    logger.info(f"Facebook webhook verification request: mode={hub_mode}, token={hub_verify_token}")

    # Facebook sends these parameters for verification
    if hub_mode == "subscribe":
        # Verify the token matches what we configured
        expected_token = settings.FACEBOOK_WEBHOOK_VERIFY_TOKEN
        if hub_verify_token == expected_token:
            logger.info("Facebook webhook verification successful")
            # Respond with the challenge to complete verification
            return PlainTextResponse(content=hub_challenge, status_code=200)
        else:
            logger.error(f"Facebook webhook verification failed: token mismatch")
            raise HTTPException(status_code=403, detail="Verification token mismatch")

    logger.error(f"Facebook webhook verification failed: invalid mode={hub_mode}")
    raise HTTPException(status_code=400, detail="Invalid verification request")


@router.post("/facebook")
async def facebook_webhook_event(
    request: Request,
    settings: SettingsDep,
    logger: LoggerDep,
    x_hub_signature_256: str = Header(None, alias="x-hub-signature-256"),
):
    """
    Facebook webhook event receiver.

    Receives real-time updates from Facebook when subscribed events occur.

    Common event types:
    - feed: Post updates, comments, reactions
    - page: Page updates, ratings, mentions
    - ads: Ad account changes, campaign updates
    - lead_ads: New lead submissions

    Webhook fields (subscribe in Facebook App Dashboard):
    - feed (posts, comments, reactions, shares)
    - page (page changes, ratings, mentions)
    - leadgen (lead ads submissions)
    - messages (messenger messages - requires pages_messaging permission)
    """
    # Get raw body for signature verification
    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')

    # Verify the request signature
    if not verify_facebook_signature(body_bytes, x_hub_signature_256, settings.FB_APP_SECRET):
        logger.error("Facebook webhook signature verification failed")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Parse the webhook payload
    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        logger.error("Facebook webhook: invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.info(f"Facebook webhook received: {json.dumps(payload, indent=2)}")

    # Process webhook events
    object_type = payload.get("object")
    entries = payload.get("entry", [])

    for entry in entries:
        entry_id = entry.get("id")
        time = entry.get("time")
        changes = entry.get("changes", [])

        for change in changes:
            field = change.get("field")
            value = change.get("value")

            logger.info(f"Facebook webhook event: object={object_type}, field={field}, entry_id={entry_id}")

            # Handle different event types
            if field == "feed":
                await handle_facebook_feed_event(value, logger)
            elif field == "page":
                await handle_facebook_page_event(value, logger)
            elif field == "leadgen":
                await handle_facebook_leadgen_event(value, logger)
            elif field == "ads":
                await handle_facebook_ads_event(value, logger)
            else:
                logger.warning(f"Unhandled Facebook webhook field: {field}")

    # Facebook expects a 200 OK response
    return {"status": "received"}


def verify_facebook_signature(payload: bytes, signature_header: str, app_secret: str) -> bool:
    """
    Verify Facebook webhook signature using HMAC-SHA256.

    Facebook signs webhook payloads with your app secret so you can verify
    the request actually came from Facebook.
    """
    if not signature_header:
        return False

    # Facebook sends signature as "sha256=<signature>"
    try:
        method, signature = signature_header.split("=", 1)
    except ValueError:
        return False

    if method != "sha256":
        return False

    # Compute expected signature
    expected_signature = hmac.new(
        app_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature)


async def handle_facebook_feed_event(value: Dict[str, Any], logger):
    """Handle Facebook feed events (posts, comments, reactions)"""
    logger.info(f"Processing Facebook feed event: {value}")
    # TODO: Store event in database, trigger automations, send notifications
    # Example: New post created, comment added, post shared, etc.


async def handle_facebook_page_event(value: Dict[str, Any], logger):
    """Handle Facebook page events"""
    logger.info(f"Processing Facebook page event: {value}")
    # TODO: Handle page changes, ratings, mentions


async def handle_facebook_leadgen_event(value: Dict[str, Any], logger):
    """Handle Facebook lead ads events"""
    logger.info(f"Processing Facebook lead gen event: {value}")
    # TODO: Fetch lead data and process
    leadgen_id = value.get("leadgen_id")
    page_id = value.get("page_id")
    # Use Facebook API to fetch full lead details


async def handle_facebook_ads_event(value: Dict[str, Any], logger):
    """Handle Facebook ads events (account/campaign changes)"""
    logger.info(f"Processing Facebook ads event: {value}")
    # TODO: Sync campaign data, trigger performance alerts


# ============================================================================
# TikTok Webhooks
# ============================================================================

@router.get("/tiktok")
async def tiktok_webhook_verify(
    request: Request,
    settings: SettingsDep,
    logger: LoggerDep,
):
    """
    TikTok webhook verification endpoint.

    TikTok sends a verification request when you register your webhook URL.

    Setup in TikTok Developer Portal:
    1. Go to TikTok for Developers > Your App > Events
    2. Click "Add Webhook"
    3. Enter Webhook URL: https://your-ngrok-url.ngrok.io/webhooks/tiktok
    4. Select events to subscribe to
    """
    # TikTok sends verification in query params or headers
    # The exact format depends on TikTok's current API version
    logger.info(f"TikTok webhook verification request")

    # Parse verification challenge
    query_params = dict(request.query_params)
    logger.info(f"TikTok verification params: {query_params}")

    # TikTok may send a challenge parameter similar to Facebook
    challenge = query_params.get("challenge")
    if challenge:
        logger.info("TikTok webhook verification successful")
        return PlainTextResponse(content=challenge, status_code=200)

    # Return success for verification
    return {"status": "ok"}


@router.post("/tiktok")
async def tiktok_webhook_event(
    request: Request,
    settings: SettingsDep,
    logger: LoggerDep,
    x_tiktok_signature: str = Header(None, alias="x-tiktok-signature"),
):
    """
    TikTok webhook event receiver.

    Receives real-time updates from TikTok when subscribed events occur.

    Common event types:
    - video.publish: New video published
    - video.delete: Video deleted
    - user.follow: New follower
    - comment.create: New comment on video
    - ad.update: Ad campaign updates

    Event subscription (in TikTok Developer Portal):
    - Select your app
    - Go to Events section
    - Add webhook URL
    - Subscribe to desired event types
    """
    # Get raw body for signature verification
    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')

    # Verify the request signature (if TikTok provides one)
    if x_tiktok_signature:
        if not verify_tiktok_signature(body_bytes, x_tiktok_signature, settings.TIKTOK_CLIENT_SECRET):
            logger.error("TikTok webhook signature verification failed")
            raise HTTPException(status_code=403, detail="Invalid signature")

    # Parse the webhook payload
    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        logger.error("TikTok webhook: invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.info(f"TikTok webhook received: {json.dumps(payload, indent=2)}")

    # Process webhook events
    event_type = payload.get("event")
    data = payload.get("data", {})

    logger.info(f"TikTok webhook event: type={event_type}")

    # Handle different event types
    if event_type == "video.publish":
        await handle_tiktok_video_publish(data, logger)
    elif event_type == "video.delete":
        await handle_tiktok_video_delete(data, logger)
    elif event_type == "user.follow":
        await handle_tiktok_user_follow(data, logger)
    elif event_type == "comment.create":
        await handle_tiktok_comment_create(data, logger)
    elif event_type == "ad.update":
        await handle_tiktok_ad_update(data, logger)
    else:
        logger.warning(f"Unhandled TikTok webhook event: {event_type}")

    # TikTok expects a 200 OK response
    return {"status": "received"}


def verify_tiktok_signature(payload: bytes, signature_header: str, client_secret: str) -> bool:
    """
    Verify TikTok webhook signature.

    TikTok signs webhook payloads with your client secret.
    The exact signing method may vary - check TikTok's current documentation.
    """
    if not signature_header:
        return False

    # Compute expected signature (adjust based on TikTok's actual method)
    expected_signature = hmac.new(
        client_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature_header)


async def handle_tiktok_video_publish(data: Dict[str, Any], logger):
    """Handle TikTok video publish events"""
    logger.info(f"Processing TikTok video publish: {data}")
    # TODO: Store video info, trigger analytics collection


async def handle_tiktok_video_delete(data: Dict[str, Any], logger):
    """Handle TikTok video delete events"""
    logger.info(f"Processing TikTok video delete: {data}")
    # TODO: Update database, remove from analytics


async def handle_tiktok_user_follow(data: Dict[str, Any], logger):
    """Handle TikTok follower events"""
    logger.info(f"Processing TikTok follower event: {data}")
    # TODO: Track follower growth, send notifications


async def handle_tiktok_comment_create(data: Dict[str, Any], logger):
    """Handle TikTok comment events"""
    logger.info(f"Processing TikTok comment: {data}")
    # TODO: Store comment, trigger sentiment analysis, auto-respond


async def handle_tiktok_ad_update(data: Dict[str, Any], logger):
    """Handle TikTok ad campaign updates"""
    logger.info(f"Processing TikTok ad update: {data}")
    # TODO: Sync ad data, trigger performance alerts


# ============================================================================
# Webhook Management & Testing
# ============================================================================

@router.get("/test/facebook")
async def test_facebook_webhook(logger: LoggerDep):
    """
    Test endpoint to verify Facebook webhook is reachable.

    Use this to check if your ngrok tunnel is working before setting up
    the webhook in Facebook App Dashboard.
    """
    logger.info("Facebook webhook test endpoint called")
    return {
        "status": "ok",
        "message": "Facebook webhook endpoint is reachable",
        "instructions": [
            "1. Copy your ngrok URL: https://xxxx.ngrok.io",
            "2. Go to Facebook App Dashboard > Webhooks",
            "3. Add Subscription with URL: https://xxxx.ngrok.io/webhooks/facebook",
            "4. Set Verify Token to match FACEBOOK_WEBHOOK_VERIFY_TOKEN in .env",
            "5. Subscribe to desired fields (feed, page, leadgen, etc.)"
        ]
    }


@router.get("/test/tiktok")
async def test_tiktok_webhook(logger: LoggerDep):
    """
    Test endpoint to verify TikTok webhook is reachable.
    """
    logger.info("TikTok webhook test endpoint called")
    return {
        "status": "ok",
        "message": "TikTok webhook endpoint is reachable",
        "instructions": [
            "1. Copy your ngrok URL: https://xxxx.ngrok.io",
            "2. Go to TikTok Developer Portal > Your App > Events",
            "3. Add webhook URL: https://xxxx.ngrok.io/webhooks/tiktok",
            "4. Subscribe to desired events (video, user, comment, ad)",
            "5. Complete verification process"
        ]
    }


@router.get("/status")
async def webhook_status(settings: SettingsDep):
    """
    Get webhook configuration status.

    Shows which webhooks are configured and ready.
    """
    return {
        "facebook": {
            "configured": bool(settings.FACEBOOK_WEBHOOK_VERIFY_TOKEN),
            "verify_token_set": bool(settings.FACEBOOK_WEBHOOK_VERIFY_TOKEN),
            "app_secret_set": bool(settings.FB_APP_SECRET),
        },
        "tiktok": {
            "configured": bool(settings.TIKTOK_CLIENT_SECRET),
            "client_secret_set": bool(settings.TIKTOK_CLIENT_SECRET),
        },
        "base_url": settings.BASE_URL,
    }
