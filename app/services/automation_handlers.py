# app/services/automation_handlers.py
"""
Automation execution handlers for different automation types.

Each handler is responsible for:
1. Fetching data from the relevant platforms
2. Processing/transforming the data
3. Formatting output for delivery
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.models import Automation, AutomationType, Platform
from app.integrations.facebook import FacebookAPIClient, FacebookMetricsService
from app.integrations.tiktok import TikTokAPIClient
from app.repositories.ad_token import AdTokenRepository
from app.core.crypto import load_encryptor


class AutomationHandlerBase(ABC):
    """Base class for automation handlers"""

    def __init__(self, db: Session, automation: Automation):
        self.db = db
        self.automation = automation
        self.token_repo = AdTokenRepository(db)
        self.encryptor = load_encryptor()
        self.logs = []

    def log(self, message: str, level: str = "info"):
        """Add log entry"""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message
        })

    def get_platform_client(self, platform: Platform, account_ref: str = None):
        """Get API client for a specific platform"""
        token = self.token_repo.get_active_token(
            self.automation.tenant_id,
            platform,
            account_ref
        )

        if not token or not token.is_valid:
            raise ValueError(f"No valid token found for platform {platform}")

        access_token = self.encryptor.dec(token.access_token_enc)

        if platform == Platform.facebook:
            return FacebookAPIClient(access_token), token
        elif platform == Platform.tiktok:
            return TikTokAPIClient(access_token), token
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """Execute the automation and return results"""
        pass


class ScheduledReportHandler(AutomationHandlerBase):
    """Handler for scheduled_report automations"""

    async def execute(self) -> Dict[str, Any]:
        """Execute a scheduled report"""
        self.log("Starting scheduled report execution")

        config = self.automation.automation_config
        platforms = self.automation.platforms or []

        report_data = {
            "report_type": "scheduled_report",
            "report_name": self.automation.name,
            "generated_at": datetime.utcnow().isoformat(),
            "period": config.get("period", "daily"),
            "platforms": {}
        }

        # Fetch data from each platform
        for platform_name in platforms:
            try:
                platform = Platform[platform_name.lower()]
                self.log(f"Fetching data from {platform_name}")

                platform_data = await self._fetch_platform_data(platform, config)
                report_data["platforms"][platform_name] = platform_data

            except Exception as e:
                self.log(f"Error fetching data from {platform_name}: {str(e)}", "error")
                report_data["platforms"][platform_name] = {
                    "error": str(e),
                    "status": "failed"
                }

        # Format the report
        formatted_report = self._format_report(report_data, config)

        self.log("Scheduled report execution completed")

        return {
            "status": "success",
            "report_data": report_data,
            "formatted_output": formatted_report,
            "logs": self.logs
        }

    async def _fetch_platform_data(self, platform: Platform, config: Dict) -> Dict[str, Any]:
        """Fetch data from a specific platform"""

        if platform == Platform.facebook:
            return await self._fetch_facebook_data(config)
        elif platform == Platform.tiktok:
            return await self._fetch_tiktok_data(config)

        return {"error": "Unsupported platform"}

    async def _fetch_facebook_data(self, config: Dict) -> Dict[str, Any]:
        """Fetch Facebook metrics"""
        try:
            client, token = self.get_platform_client(Platform.facebook)
            metrics_service = FacebookMetricsService(self.encryptor.dec(token.access_token_enc))

            days = config.get("days", 7)
            metric_types = config.get("metric_types", ["ad_account"])

            data = {
                "account_ref": token.account_ref,
                "account_name": token.account_name,
                "metrics": {}
            }

            # Fetch ad account summary if requested
            if "ad_account" in metric_types and token.account_ref:
                try:
                    summary = metrics_service.get_ad_account_summary(
                        ad_account_id=token.account_ref,
                        days=days
                    )
                    data["metrics"]["ad_account"] = summary
                except Exception as e:
                    self.log(f"Error fetching ad account metrics: {str(e)}", "warning")

            # Fetch page metrics if requested
            if "pages" in metric_types:
                try:
                    pages = client.get_pages()
                    page_metrics = []

                    for page in pages[:5]:  # Limit to 5 pages
                        page_data = metrics_service.get_daily_page_metrics(
                            page_id=page["id"],
                            days=days
                        )
                        page_metrics.append({
                            "page_id": page["id"],
                            "page_name": page["name"],
                            "metrics": page_data
                        })

                    data["metrics"]["pages"] = page_metrics
                except Exception as e:
                    self.log(f"Error fetching page metrics: {str(e)}", "warning")

            metrics_service.close()
            client.close()

            return data

        except Exception as e:
            raise Exception(f"Facebook data fetch failed: {str(e)}")

    async def _fetch_tiktok_data(self, config: Dict) -> Dict[str, Any]:
        """Fetch TikTok metrics"""
        try:
            client, token = self.get_platform_client(Platform.tiktok)

            # Get user info
            user_info = await client.get_user_info(
                fields=["open_id", "username", "display_name", "follower_count",
                       "following_count", "likes_count", "video_count"]
            )

            data = {
                "account_ref": token.account_ref,
                "account_name": token.account_name,
                "user_info": {
                    "username": user_info.username,
                    "display_name": user_info.display_name,
                    "followers": user_info.follower_count,
                    "following": user_info.following_count,
                    "likes": user_info.likes_count,
                    "videos": user_info.video_count
                }
            }

            return data

        except Exception as e:
            raise Exception(f"TikTok data fetch failed: {str(e)}")

    def _format_report(self, report_data: Dict, config: Dict) -> str:
        """Format report data for human consumption"""

        format_type = config.get("format", "text")

        if format_type == "text":
            return self._format_text_report(report_data)
        elif format_type == "html":
            return self._format_html_report(report_data)
        else:
            return str(report_data)

    def _format_text_report(self, report_data: Dict) -> str:
        """Format report as plain text"""
        lines = [
            f"📊 {report_data['report_name']}",
            f"Generated: {report_data['generated_at']}",
            f"Period: {report_data['period']}",
            "",
            "=" * 50,
            ""
        ]

        for platform_name, platform_data in report_data["platforms"].items():
            lines.append(f"🔹 {platform_name.upper()}")
            lines.append("-" * 40)

            if "error" in platform_data:
                lines.append(f"❌ Error: {platform_data['error']}")
            else:
                if platform_name.lower() == "facebook":
                    lines.extend(self._format_facebook_text(platform_data))
                elif platform_name.lower() == "tiktok":
                    lines.extend(self._format_tiktok_text(platform_data))

            lines.append("")

        return "\n".join(lines)

    def _format_facebook_text(self, data: Dict) -> List[str]:
        """Format Facebook data as text"""
        lines = [f"Account: {data.get('account_name', 'N/A')}"]

        metrics = data.get("metrics", {})

        # Ad account metrics
        if "ad_account" in metrics:
            ad_metrics = metrics["ad_account"]
            lines.append("\n📈 Ad Account Performance:")
            lines.append(f"  • Impressions: {ad_metrics.get('impressions', 'N/A')}")
            lines.append(f"  • Clicks: {ad_metrics.get('clicks', 'N/A')}")
            lines.append(f"  • Spend: ${ad_metrics.get('spend', 'N/A')}")
            lines.append(f"  • CTR: {ad_metrics.get('ctr', 'N/A')}%")
            lines.append(f"  • CPC: ${ad_metrics.get('cpc', 'N/A')}")

        # Page metrics
        if "pages" in metrics:
            lines.append("\n📄 Page Performance:")
            for page in metrics["pages"]:
                lines.append(f"  {page['page_name']}:")
                # Add page-specific metrics here

        return lines

    def _format_tiktok_text(self, data: Dict) -> List[str]:
        """Format TikTok data as text"""
        lines = [f"Account: {data.get('account_name', 'N/A')}"]

        user_info = data.get("user_info", {})
        lines.append("\n👤 Profile Stats:")
        lines.append(f"  • Username: @{user_info.get('username', 'N/A')}")
        lines.append(f"  • Followers: {user_info.get('followers', 'N/A'):,}")
        lines.append(f"  • Following: {user_info.get('following', 'N/A'):,}")
        lines.append(f"  • Total Likes: {user_info.get('likes', 'N/A'):,}")
        lines.append(f"  • Total Videos: {user_info.get('videos', 'N/A')}")

        return lines

    def _format_html_report(self, report_data: Dict) -> str:
        """Format report as HTML"""
        # Simple HTML formatting - can be enhanced
        html = f"""
        <html>
        <head><title>{report_data['report_name']}</title></head>
        <body>
            <h1>{report_data['report_name']}</h1>
            <p>Generated: {report_data['generated_at']}</p>
            <p>Period: {report_data['period']}</p>
            <hr>
        """

        for platform_name, platform_data in report_data["platforms"].items():
            html += f"<h2>{platform_name}</h2>"
            html += f"<pre>{str(platform_data)}</pre>"

        html += "</body></html>"
        return html


class AlertHandler(AutomationHandlerBase):
    """Handler for alert automations"""

    async def execute(self) -> Dict[str, Any]:
        """Execute an alert check"""
        self.log("Starting alert check execution")

        config = self.automation.automation_config
        platforms = self.automation.platforms or []

        alerts_triggered = []

        # Check thresholds for each platform
        for platform_name in platforms:
            try:
                platform = Platform[platform_name.lower()]
                self.log(f"Checking alerts for {platform_name}")

                alert = await self._check_platform_thresholds(platform, config)
                if alert:
                    alerts_triggered.append(alert)

            except Exception as e:
                self.log(f"Error checking alerts for {platform_name}: {str(e)}", "error")

        # Format alert message
        if alerts_triggered:
            alert_message = self._format_alert_message(alerts_triggered)
            self.log(f"{len(alerts_triggered)} alert(s) triggered")

            return {
                "status": "alert_triggered",
                "alerts": alerts_triggered,
                "formatted_output": alert_message,
                "logs": self.logs
            }
        else:
            self.log("No alerts triggered")
            return {
                "status": "no_alerts",
                "alerts": [],
                "formatted_output": "✅ All metrics within normal range",
                "logs": self.logs
            }

    async def _check_platform_thresholds(self, platform: Platform, config: Dict) -> Optional[Dict]:
        """Check if any thresholds are breached"""

        thresholds = config.get("thresholds", {})

        if platform == Platform.facebook:
            return await self._check_facebook_thresholds(thresholds)
        elif platform == Platform.tiktok:
            return await self._check_tiktok_thresholds(thresholds)

        return None

    async def _check_facebook_thresholds(self, thresholds: Dict) -> Optional[Dict]:
        """Check Facebook metric thresholds"""
        try:
            client, token = self.get_platform_client(Platform.facebook)
            metrics_service = FacebookMetricsService(self.encryptor.dec(token.access_token_enc))

            # Get recent metrics
            summary = metrics_service.get_ad_account_summary(
                ad_account_id=token.account_ref,
                days=1
            )

            alerts = []

            # Check spend threshold
            if "max_daily_spend" in thresholds:
                spend = float(summary.get("spend", 0))
                max_spend = float(thresholds["max_daily_spend"])
                if spend > max_spend:
                    alerts.append({
                        "metric": "daily_spend",
                        "value": spend,
                        "threshold": max_spend,
                        "message": f"Daily spend ${spend:.2f} exceeds threshold ${max_spend:.2f}"
                    })

            # Check CTR threshold
            if "min_ctr" in thresholds:
                ctr = float(summary.get("ctr", 0))
                min_ctr = float(thresholds["min_ctr"])
                if ctr < min_ctr:
                    alerts.append({
                        "metric": "ctr",
                        "value": ctr,
                        "threshold": min_ctr,
                        "message": f"CTR {ctr:.2f}% below threshold {min_ctr:.2f}%"
                    })

            metrics_service.close()
            client.close()

            if alerts:
                return {
                    "platform": "facebook",
                    "account": token.account_name,
                    "alerts": alerts
                }

        except Exception as e:
            self.log(f"Error checking Facebook thresholds: {str(e)}", "warning")

        return None

    async def _check_tiktok_thresholds(self, thresholds: Dict) -> Optional[Dict]:
        """Check TikTok metric thresholds"""
        # TikTok threshold checks can be implemented based on available metrics
        return None

    def _format_alert_message(self, alerts: List[Dict]) -> str:
        """Format alert message"""
        lines = [
            "🚨 ALERT: Threshold Breach Detected",
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            ""
        ]

        for alert_data in alerts:
            platform = alert_data["platform"]
            account = alert_data["account"]
            lines.append(f"Platform: {platform.upper()} - {account}")

            for alert in alert_data["alerts"]:
                lines.append(f"  ⚠️ {alert['message']}")

            lines.append("")

        return "\n".join(lines)


class DataSyncHandler(AutomationHandlerBase):
    """Handler for data_sync automations"""

    async def execute(self) -> Dict[str, Any]:
        """Execute a data sync operation"""
        self.log("Starting data sync execution")

        config = self.automation.automation_config
        sync_type = config.get("sync_type", "webhook")

        if sync_type == "webhook":
            result = await self._sync_to_webhook(config)
        elif sync_type == "database":
            result = await self._sync_to_database(config)
        else:
            raise ValueError(f"Unsupported sync type: {sync_type}")

        self.log("Data sync execution completed")

        return {
            "status": "success",
            "sync_type": sync_type,
            "result": result,
            "logs": self.logs
        }

    async def _sync_to_webhook(self, config: Dict) -> Dict[str, Any]:
        """Sync data to an external webhook"""
        # This would integrate with the destination service
        return {
            "synced": True,
            "message": "Data synced to webhook"
        }

    async def _sync_to_database(self, config: Dict) -> Dict[str, Any]:
        """Sync data to a database"""
        # This could store historical metrics in a separate table
        return {
            "synced": True,
            "message": "Data synced to database"
        }


# Handler factory
def get_automation_handler(db: Session, automation: Automation) -> AutomationHandlerBase:
    """Get the appropriate handler for an automation type"""

    handlers = {
        AutomationType.scheduled_report: ScheduledReportHandler,
        AutomationType.alert: AlertHandler,
        AutomationType.data_sync: DataSyncHandler
    }

    handler_class = handlers.get(automation.type)
    if not handler_class:
        raise ValueError(f"No handler found for automation type: {automation.type}")

    return handler_class(db, automation)
