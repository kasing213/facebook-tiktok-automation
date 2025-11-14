"""
Facebook Graph API integration module.

This module provides a client for interacting with the Facebook Graph API,
including methods for fetching ad insights, managing pages, and retrieving
campaign performance data.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from loguru import logger


class FacebookAPIClient:
    """
    Client for interacting with Facebook Graph API.

    This client handles authentication, request formatting, and data retrieval
    from the Facebook Marketing API and Graph API.
    """

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token: str):
        """
        Initialize the Facebook API client.

        Args:
            access_token: Facebook access token with appropriate permissions
        """
        self.access_token = access_token
        self.client = httpx.Client(timeout=30.0)

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Facebook Graph API.

        Args:
            endpoint: API endpoint (e.g., '/me', '/act_123/insights')
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data

        Returns:
            Response data as dictionary

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}{endpoint}"

        if params is None:
            params = {}

        # Add access token to all requests
        params["access_token"] = self.access_token

        try:
            response = self.client.request(
                method=method,
                url=url,
                params=params,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Facebook API request failed: {e}")
            raise

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.

        Returns:
            User information dictionary
        """
        return self._make_request("/me", params={"fields": "id,name,email"})

    def get_ad_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all ad accounts accessible to the user.

        Returns:
            List of ad account dictionaries
        """
        response = self._make_request(
            "/me/adaccounts",
            params={"fields": "id,name,account_status,currency,timezone_name"}
        )
        return response.get("data", [])

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Get all pages accessible to the user.

        Returns:
            List of page dictionaries
        """
        response = self._make_request(
            "/me/accounts",
            params={"fields": "id,name,access_token,category,tasks"}
        )
        return response.get("data", [])

    def get_page_insights(
        self,
        page_id: str,
        metrics: List[str],
        period: str = "day",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get insights for a Facebook page.

        Args:
            page_id: Facebook page ID
            metrics: List of metric names to fetch
            period: Time period (day, week, days_28, lifetime)
            since: Start date for the insights
            until: End date for the insights

        Returns:
            List of insight data dictionaries
        """
        params = {
            "metric": ",".join(metrics),
            "period": period
        }

        if since:
            params["since"] = since.strftime("%Y-%m-%d")
        if until:
            params["until"] = until.strftime("%Y-%m-%d")

        response = self._make_request(f"/{page_id}/insights", params=params)
        return response.get("data", [])

    def get_ad_insights(
        self,
        ad_account_id: str,
        fields: List[str],
        time_range: Optional[Dict[str, str]] = None,
        filtering: Optional[List[Dict[str, Any]]] = None,
        level: str = "account"
    ) -> List[Dict[str, Any]]:
        """
        Get insights for an ad account.

        Args:
            ad_account_id: Ad account ID (e.g., 'act_123456')
            fields: List of fields to retrieve
            time_range: Time range dict with 'since' and 'until' keys
            filtering: List of filter conditions
            level: Aggregation level (account, campaign, adset, ad)

        Returns:
            List of insight dictionaries
        """
        params = {
            "fields": ",".join(fields),
            "level": level
        }

        if time_range:
            params["time_range"] = str(time_range)

        if filtering:
            params["filtering"] = str(filtering)

        response = self._make_request(f"/{ad_account_id}/insights", params=params)
        return response.get("data", [])

    def get_campaigns(
        self,
        ad_account_id: str,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get campaigns for an ad account.

        Args:
            ad_account_id: Ad account ID
            fields: Optional list of fields to retrieve

        Returns:
            List of campaign dictionaries
        """
        if fields is None:
            fields = ["id", "name", "status", "objective", "created_time"]

        params = {"fields": ",".join(fields)}
        response = self._make_request(f"/{ad_account_id}/campaigns", params=params)
        return response.get("data", [])

    def get_adsets(
        self,
        campaign_id: str,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get ad sets for a campaign.

        Args:
            campaign_id: Campaign ID
            fields: Optional list of fields to retrieve

        Returns:
            List of ad set dictionaries
        """
        if fields is None:
            fields = ["id", "name", "status", "daily_budget", "lifetime_budget"]

        params = {"fields": ",".join(fields)}
        response = self._make_request(f"/{campaign_id}/adsets", params=params)
        return response.get("data", [])

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class FacebookMetricsService:
    """
    Service for retrieving and formatting Facebook metrics.

    Provides higher-level methods for common metric retrieval patterns.
    """

    # Common metric sets
    PAGE_METRICS = [
        "page_impressions",
        "page_engaged_users",
        "page_post_engagements",
        "page_fan_adds",
        "page_views_total"
    ]

    AD_METRICS = [
        "impressions",
        "clicks",
        "spend",
        "reach",
        "frequency",
        "ctr",
        "cpc",
        "cpm",
        "cpp"
    ]

    def __init__(self, access_token: str):
        """
        Initialize the metrics service.

        Args:
            access_token: Facebook access token
        """
        self.client = FacebookAPIClient(access_token)

    def get_daily_page_metrics(
        self,
        page_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get daily page metrics for the last N days.

        Args:
            page_id: Facebook page ID
            days: Number of days to retrieve

        Returns:
            Formatted metrics dictionary
        """
        until = datetime.now()
        since = until - timedelta(days=days)

        insights = self.client.get_page_insights(
            page_id=page_id,
            metrics=self.PAGE_METRICS,
            period="day",
            since=since,
            until=until
        )

        return self._format_page_insights(insights)

    def get_ad_account_summary(
        self,
        ad_account_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get summary metrics for an ad account.

        Args:
            ad_account_id: Ad account ID
            days: Number of days to retrieve

        Returns:
            Summary metrics dictionary
        """
        until = datetime.now().strftime("%Y-%m-%d")
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        insights = self.client.get_ad_insights(
            ad_account_id=ad_account_id,
            fields=self.AD_METRICS,
            time_range={"since": since, "until": until},
            level="account"
        )

        return self._format_ad_insights(insights)

    def _format_page_insights(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format page insights for easier consumption."""
        formatted = {}
        for metric in insights:
            name = metric.get("name")
            values = metric.get("values", [])
            formatted[name] = values
        return formatted

    def _format_ad_insights(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format ad insights for easier consumption."""
        if not insights:
            return {}
        return insights[0] if insights else {}

    def close(self):
        """Close the underlying client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
