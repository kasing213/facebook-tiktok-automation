# api-gateway/src/services/sales_service.py
"""Sales/Audit Sales service for PostgreSQL operations."""

import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional

from sqlalchemy import text

from src.db.postgres import get_db_session

logger = logging.getLogger(__name__)


class SalesService:
    """Service for interacting with Audit Sales schema in PostgreSQL."""

    async def get_stats(self) -> Dict[str, Any]:
        """Get sales service statistics."""
        try:
            with get_db_session() as db:
                total_records = db.execute(
                    text("SELECT COUNT(*) FROM audit_sales.sale")
                ).scalar() or 0

                # Get this month's count
                this_month = db.execute(
                    text("""
                        SELECT COUNT(*) FROM audit_sales.sale
                        WHERE date >= date_trunc('month', CURRENT_DATE)
                    """)
                ).scalar() or 0

                return {
                    "status": "connected",
                    "total_records": total_records,
                    "this_month": this_month
                }
        except Exception as e:
            logger.error(f"Error getting sales stats: {e}")
            return {"status": "error", "message": str(e)}

    async def get_daily_summary(self, date_str: str) -> Optional[Dict[str, Any]]:
        """Get daily sales summary."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT
                            COALESCE(SUM(amount), 0) as total,
                            COUNT(*) as count,
                            COALESCE(AVG(amount), 0) as average
                        FROM audit_sales.sale
                        WHERE date = :target_date
                    """),
                    {"target_date": date_str}
                )
                row = result.fetchone()
                if row:
                    return {
                        "total": float(row.total),
                        "count": row.count,
                        "average": float(row.average)
                    }
                return {"total": 0, "count": 0, "average": 0}
        except Exception as e:
            logger.error(f"Error getting daily summary: {e}")
            return None

    async def get_sales(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of sales records."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, tenant_id, date, amount, description, category, meta, created_at, updated_at
                        FROM audit_sales.sale
                        ORDER BY date DESC
                        LIMIT :limit
                    """),
                    {"limit": limit}
                )
                rows = result.fetchall()
                return [
                    {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "date": row.date.isoformat() if row.date else None,
                        "amount": float(row.amount),
                        "description": row.description,
                        "category": row.category,
                        "meta": row.meta or {},
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting sales: {e}")
            return []


# Global service instance
sales_service = SalesService()
