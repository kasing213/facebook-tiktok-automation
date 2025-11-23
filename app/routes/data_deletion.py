# app/routes/data_deletion.py
"""
Facebook Data Deletion Callback Endpoint
Handles data deletion requests from Facebook when users remove the app
"""
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
import hmac
import hashlib
import json
from datetime import datetime
from sqlalchemy import select, delete
from app.core.config import get_settings
from app.core.db import get_db_session
from app.core.models import AdToken, Platform
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data-deletion", tags=["data-deletion"])


def verify_facebook_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """
    Verify that the request came from Facebook
    Facebook sends signed_request parameter with format: encoded_signature.payload
    """
    try:
        # Facebook sends signature in format: sha256=SIGNATURE
        if signature.startswith('sha256='):
            signature = signature[7:]

        # Calculate expected signature
        expected_sig = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature)
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


@router.post("/facebook")
async def facebook_data_deletion(request: Request):
    """
    Facebook Data Deletion Callback

    When a user deauthorizes your app, Facebook makes a POST request to this endpoint
    with a signed_request parameter containing the user's ID.

    You must:
    1. Verify the request signature
    2. Delete the user's data
    3. Return a confirmation URL and code

    Docs: https://developers.facebook.com/docs/development/create-an-app/app-dashboard/data-deletion-callback
    """
    settings = get_settings()

    try:
        # Get the signed_request parameter
        form_data = await request.form()
        signed_request = form_data.get("signed_request")

        if not signed_request:
            logger.error("No signed_request in data deletion callback")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signed_request parameter"
            )

        # Parse signed_request (format: encoded_signature.payload)
        try:
            encoded_sig, payload = signed_request.split('.', 1)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signed_request format"
            )

        # Decode payload (base64url)
        import base64
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded_payload = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded_payload)

        # Verify signature
        app_secret = settings.FB_APP_SECRET.get_secret_value()
        if not verify_facebook_signature(decoded_payload, encoded_sig, app_secret):
            logger.error("Invalid signature in data deletion callback")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid request signature"
            )

        # Extract user ID
        user_id = data.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing user_id in request"
            )

        logger.info(f"Data deletion request for Facebook user: {user_id}")

        # Delete user's Facebook data from database
        db = next(get_db_session())
        try:
            # Delete all Facebook tokens for this user
            stmt = delete(AdToken).where(
                AdToken.platform == Platform.facebook,
                AdToken.account_ref == user_id
            )
            result = db.execute(stmt)
            deleted_count = result.rowcount
            db.commit()

            logger.info(f"Deleted {deleted_count} Facebook tokens for user {user_id}")
        finally:
            db.close()

        # Generate confirmation code
        confirmation_code = f"fb_{user_id}_{int(datetime.utcnow().timestamp())}"

        # Return confirmation URL (required by Facebook)
        confirmation_url = f"{settings.FRONTEND_URL}/data-deletion?code={confirmation_code}&status=deleted"

        return JSONResponse({
            "url": confirmation_url,
            "confirmation_code": confirmation_code,
            "message": "Data deletion request processed successfully"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing data deletion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process data deletion request"
        )


@router.get("/")
async def data_deletion_info():
    """
    Information page about data deletion
    This is what users see when they want to know how to delete their data
    """
    settings = get_settings()

    return {
        "message": "Data Deletion Instructions",
        "instructions": [
            "Option 1: Remove the app from your Facebook settings at https://www.facebook.com/settings?tab=applications",
            "Option 2: Delete your account from our platform dashboard",
            "Option 3: Contact us at privacy@facebooktiktokautomation.app"
        ],
        "deletion_policy": {
            "facebook_data": "Deleted within 48 hours of app removal",
            "account_data": "Deleted within 30 days of account deletion request",
            "legal_retention": "Some logs retained for 90 days for security compliance"
        },
        "data_deleted": [
            "Facebook OAuth access tokens",
            "Facebook profile information",
            "Facebook Page data and tokens",
            "Page engagement metrics",
            "Cached Facebook data"
        ],
        "privacy_policy": f"{settings.FRONTEND_URL}/privacy-policy",
        "contact": "privacy@facebooktiktokautomation.app"
    }
