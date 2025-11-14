# app/services/destination_sender.py
"""
Service for sending automation results to various destinations.

Supports:
- Telegram chat messages
- Webhook POST requests
- Email notifications
"""

from typing import Dict, Any, Optional
from uuid import UUID
import httpx
from sqlalchemy.orm import Session
from loguru import logger

from app.core.models import Destination, DestinationType
from app.repositories.destination import DestinationRepository


class DestinationSenderService:
    """Service for sending messages to destinations"""

    def __init__(self, db: Session):
        self.db = db
        self.destination_repo = DestinationRepository(db)

    async def send_to_destination(
        self,
        destination_id: UUID,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send content to a specific destination.

        Args:
            destination_id: UUID of the destination
            content: Text content to send
            metadata: Optional metadata about the content

        Returns:
            Result dictionary with status and details
        """
        destination = self.destination_repo.get_by_id(destination_id)

        if not destination:
            return {
                "success": False,
                "error": f"Destination {destination_id} not found"
            }

        if not destination.is_active:
            return {
                "success": False,
                "error": f"Destination {destination.name} is not active"
            }

        try:
            if destination.type == DestinationType.telegram_chat:
                return await self._send_to_telegram(destination, content, metadata)
            elif destination.type == DestinationType.webhook:
                return await self._send_to_webhook(destination, content, metadata)
            elif destination.type == DestinationType.email:
                return await self._send_to_email(destination, content, metadata)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported destination type: {destination.type}"
                }

        except Exception as e:
            logger.error(f"Error sending to destination {destination.name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _send_to_telegram(
        self,
        destination: Destination,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message to Telegram chat"""

        from app.core.config import get_settings
        settings = get_settings()

        config = destination.config
        chat_id = config.get("chat_id")

        if not chat_id:
            return {
                "success": False,
                "error": "Telegram chat_id not configured"
            }

        # Telegram Bot API endpoint
        bot_token = settings.TELEGRAM_BOT_TOKEN
        if not bot_token:
            return {
                "success": False,
                "error": "Telegram bot token not configured"
            }

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # Prepare message
        payload = {
            "chat_id": chat_id,
            "text": content,
            "parse_mode": "HTML"  # Support HTML formatting
        }

        # Add metadata as a separate message if needed
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()

                if result.get("ok"):
                    return {
                        "success": True,
                        "destination_type": "telegram",
                        "message_id": result.get("result", {}).get("message_id")
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("description", "Unknown error")
                    }

        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}"
            }

    async def _send_to_webhook(
        self,
        destination: Destination,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send data to webhook endpoint"""

        config = destination.config
        webhook_url = config.get("webhook_url")

        if not webhook_url:
            return {
                "success": False,
                "error": "Webhook URL not configured"
            }

        # Prepare payload
        payload = {
            "destination": destination.name,
            "content": content,
            "timestamp": metadata.get("timestamp") if metadata else None,
            "metadata": metadata or {}
        }

        # Get custom headers and auth config
        headers = config.get("headers", {})
        auth_config = config.get("auth_config", {})
        timeout = config.get("timeout", 30)

        # Add authorization header if configured
        if auth_config.get("type") == "bearer":
            headers["Authorization"] = f"Bearer {auth_config.get('token')}"
        elif auth_config.get("type") == "basic":
            import base64
            username = auth_config.get("username", "")
            password = auth_config.get("password", "")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()

                return {
                    "success": True,
                    "destination_type": "webhook",
                    "status_code": response.status_code,
                    "response": response.text[:500]  # Limit response size
                }

        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"Webhook request failed: {str(e)}"
            }

    async def _send_to_email(
        self,
        destination: Destination,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email notification"""

        config = destination.config
        email_to = config.get("email")

        if not email_to:
            return {
                "success": False,
                "error": "Email address not configured"
            }

        # Email sending would require SMTP configuration
        # This is a placeholder for future implementation

        logger.warning(f"Email sending not implemented yet. Would send to: {email_to}")

        return {
            "success": False,
            "error": "Email sending not implemented yet",
            "note": f"Would send to {email_to}"
        }

    async def send_test_message(
        self,
        destination_id: UUID,
        test_message: str = None
    ) -> Dict[str, Any]:
        """
        Send a test message to verify destination configuration.

        Args:
            destination_id: UUID of the destination
            test_message: Optional custom test message

        Returns:
            Result dictionary
        """
        destination = self.destination_repo.get_by_id(destination_id)

        if not destination:
            return {
                "success": False,
                "error": f"Destination {destination_id} not found"
            }

        if test_message is None:
            test_message = f"🧪 Test message from {destination.name}\n\nThis is a test to verify your destination is configured correctly."

        return await self.send_to_destination(
            destination_id,
            test_message,
            metadata={"is_test": True}
        )

    async def broadcast_to_multiple(
        self,
        destination_ids: list[UUID],
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send the same content to multiple destinations.

        Args:
            destination_ids: List of destination UUIDs
            content: Content to send
            metadata: Optional metadata

        Returns:
            Summary of results
        """
        results = []

        for dest_id in destination_ids:
            result = await self.send_to_destination(dest_id, content, metadata)
            results.append({
                "destination_id": str(dest_id),
                "result": result
            })

        successful = sum(1 for r in results if r["result"].get("success"))
        failed = len(results) - successful

        return {
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        }


class TelegramMessageFormatter:
    """Helper class for formatting messages for Telegram"""

    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML special characters"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def format_report(report_data: Dict[str, Any]) -> str:
        """Format automation report for Telegram"""
        lines = [
            f"<b>{report_data.get('report_name', 'Report')}</b>",
            f"<i>{report_data.get('generated_at', '')}</i>",
            ""
        ]

        # Add platform summaries
        platforms = report_data.get("platforms", {})
        for platform_name, platform_data in platforms.items():
            lines.append(f"📱 <b>{platform_name.upper()}</b>")

            if "error" in platform_data:
                lines.append(f"❌ Error: {platform_data['error']}")
            else:
                # Add key metrics
                metrics = platform_data.get("metrics", {})
                if metrics:
                    lines.append(TelegramMessageFormatter._format_metrics(metrics))

            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_metrics(metrics: Dict[str, Any]) -> str:
        """Format metrics dictionary"""
        if not metrics:
            return "No metrics available"

        lines = []
        for key, value in metrics.items():
            if isinstance(value, dict):
                # Nested metrics
                for sub_key, sub_value in value.items():
                    lines.append(f"  • {sub_key}: {sub_value}")
            else:
                lines.append(f"  • {key}: {value}")

        return "\n".join(lines)

    @staticmethod
    def format_alert(alert_data: Dict[str, Any]) -> str:
        """Format alert message for Telegram"""
        lines = [
            "🚨 <b>ALERT</b>",
            f"<i>{alert_data.get('timestamp', '')}</i>",
            ""
        ]

        alerts = alert_data.get("alerts", [])
        for alert in alerts:
            platform = alert.get("platform", "Unknown")
            lines.append(f"<b>{platform.upper()}</b>")

            for detail in alert.get("alerts", []):
                lines.append(f"⚠️ {detail['message']}")

            lines.append("")

        return "\n".join(lines)
